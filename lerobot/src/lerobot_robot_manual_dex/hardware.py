"""Fail-closed hardware integration seam; a verified HLS3606 driver is NOT supplied."""
from dataclasses import dataclass
import importlib
import json
import math
from pathlib import Path
import time

from lerobot.robots import Robot, RobotConfig
from .calibration import JOINTS, FEATURES, finite_joints, load_mapping


def load_profile(path):
    profile = json.loads(Path(path).read_text())
    if profile.get("schema") != "manual-dex-hand-profile-v1" or profile.get("hardware_verified") is not True:
        raise ValueError("A measured, hardware-verified hand profile is required; examples cannot enable motors")
    if not profile.get("hand_id") or profile.get("servo_model") != "HLS3606":
        raise ValueError("Profile must identify this hand and its HLS3606 servos")
    if set(profile.get("joints", {})) != set(JOINTS):
        raise ValueError("Hand profile must cover all eight joints")
    motor_ids = []
    for name, limits in profile["joints"].items():
        motor = limits.get("motor_id")
        if isinstance(motor, bool) or not isinstance(motor, int) or not 1 <= motor <= 253:
            raise ValueError(f"Unconfirmed motor ID for {name}")
        motor_ids.append(motor)
        for key in ("min_rad", "max_rad", "max_velocity_rad_s"):
            value = limits.get(key)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError(f"Unmeasured {key} for {name}")
        if limits["min_rad"] >= limits["max_rad"] or limits["max_velocity_rad_s"] <= 0:
            raise ValueError("Invalid measured travel/rate limits")
    if len(set(motor_ids)) != len(JOINTS):
        raise ValueError("Motor IDs must be unique")
    return profile


@RobotConfig.register_subclass("manual_dex_hardware")
@dataclass
class ManualDexHardwareConfig(RobotConfig):
    driver_factory: str = ""
    port: str = ""
    profile_file: str = ""
    glove_mapping_file: str = ""
    enable_motion: bool = False
    watchdog_s: float = .25


class ManualDexHardware(Robot):
    config_class = ManualDexHardwareConfig
    name = "manual_dex_hardware"

    def __init__(self, config):
        super().__init__(config)
        self.config, self.driver, self.profile = config, None, None
        self.cameras = {}

    @property
    def action_features(self):
        return dict(FEATURES)

    @property
    def observation_features(self):
        return dict(FEATURES)

    @property
    def is_connected(self):
        return self.driver is not None

    @property
    def is_calibrated(self):
        return self.profile is not None

    def connect(self, calibrate=True):
        if self.driver is not None:
            raise RuntimeError("Hardware already connected")
        if not self.config.enable_motion:
            raise PermissionError("Physical motion is disabled. Read HARDWARE.md and complete the hardware gates first.")
        if not self.config.driver_factory or not self.config.port:
            raise ValueError("Supply a verified driver factory and explicit port; HLS3606 support is not guessed")
        if not math.isfinite(self.config.watchdog_s) or not .05 <= self.config.watchdog_s <= .5:
            raise ValueError("Hardware watchdog must be between 50 and 500 ms")
        profile = load_profile(self.config.profile_file)
        if profile["hand_id"] != self.id:
            raise ValueError("Profile does not belong to this hand")
        mapping = load_mapping(self.config.glove_mapping_file, require_measured=True)
        for name, row in mapping["joints"].items():
            limits = profile["joints"][name]
            if not all(limits["min_rad"] <= row[k] <= limits["max_rad"] for k in ("open_rad", "closed_rad")):
                raise ValueError("Glove reference angles exceed the measured hand travel")
        module, factory = self.config.driver_factory.split(":", 1)
        driver = getattr(importlib.import_module(module), factory)(port=self.config.port, profile=profile)
        if getattr(driver, "hardware_watchdog_supported", False) is not True:
            raise ValueError("Driver must implement a tested controller-side watchdog; host cleanup is insufficient")
        try:
            driver.connect(read_only=True)
            current = finite_joints(driver.read_positions_rad())
            self._check_positions(current, profile)
            # The driver must start by holding its measured current pose, not zero.
            driver.arm(watchdog_s=self.config.watchdog_s, hold_positions=current)
            self.driver, self.profile = driver, profile
            self._last_command = time.monotonic()
        except BaseException:
            try:
                driver.stop()
            finally:
                driver.disconnect()
            raise

    @staticmethod
    def _check_positions(positions, profile):
        for name, value in positions.items():
            limits = profile["joints"][name]
            if not limits["min_rad"] <= value <= limits["max_rad"]:
                raise RuntimeError(f"Measured {name} lies outside reviewed soft limits; stop and inspect")

    def calibrate(self):
        raise RuntimeError("No automatic powered calibration: measure travel/encoder mapping using the verified driver; see CALIBRATION.md")

    def configure(self):
        pass

    def get_observation(self):
        if self.driver is None:
            raise RuntimeError("Hardware is not connected")
        try:
            positions = finite_joints(self.driver.read_positions_rad())
            self._check_positions(positions, self.profile)
            return {f"{name}.pos": value for name, value in positions.items()}
        except BaseException:
            self.disconnect()
            raise

    def send_action(self, action):
        if self.driver is None:
            raise RuntimeError("Hardware is not connected")
        try:
            if set(action) != set(FEATURES):
                raise ValueError("Expected eight named hand actions only")
            target = finite_joints({name: action[f"{name}.pos"] for name in JOINTS})
            now = time.monotonic()
            elapsed = now - self._last_command
            if elapsed > self.config.watchdog_s:
                raise TimeoutError("Command stream stalled; re-arm only after inspection")
            current = self.get_observation()
            sent = {}
            for name, value in target.items():
                limits = self.profile["joints"][name]
                delta = limits["max_velocity_rad_s"] * min(elapsed, .05)
                present = current[f"{name}.pos"]
                sent[name] = max(limits["min_rad"], min(limits["max_rad"], max(present-delta, min(present+delta, value))))
            self.driver.send_positions_rad(sent)
            self._last_command = time.monotonic()
            return {f"{name}.pos": value for name, value in sent.items()}
        except BaseException:
            self.disconnect()
            raise

    def disconnect(self):
        driver, self.driver = self.driver, None
        if driver is not None:
            try:
                driver.stop()
            finally:
                driver.disconnect()
