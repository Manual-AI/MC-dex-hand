"""LeRobot teleoperator: synthetic glove or explicitly documented read-only serial protocol."""
from dataclasses import dataclass
import json
import math
from pathlib import Path
import statistics
import time

from lerobot.teleoperators import Teleoperator, TeleoperatorConfig
from .calibration import JOINTS, FEATURES, finite_joints, load_mapping, map_raw, save_mapping, synthetic_mapping


@TeleoperatorConfig.register_subclass("manual_dex_glove")
@dataclass
class ManualDexGloveConfig(TeleoperatorConfig):
    source: str = "synthetic"
    port: str = ""
    baudrate: int = 115200
    mapping_file: str = "build/lerobot/calibration/synthetic-glove.json"
    reference_file: str = ""
    timeout_s: float = .25


class ManualDexGlove(Teleoperator):
    config_class = ManualDexGloveConfig
    name = "manual_dex_glove"

    def __init__(self, config):
        super().__init__(config)
        self.config, self._serial, self._connected = config, None, False
        self._last_seq, self._last_device_ms, self._mapping = -1, -1, None

    @property
    def action_features(self):
        return dict(FEATURES)

    @property
    def feedback_features(self):
        return {}

    @property
    def is_connected(self):
        return self._connected

    @property
    def is_calibrated(self):
        try:
            load_mapping(self.config.mapping_file, device_id=self.id)
            return True
        except (OSError, ValueError, TypeError, KeyError):
            return False

    def connect(self, calibrate=True):
        if self._connected:
            raise RuntimeError("Glove already connected")
        if not self.id:
            raise ValueError("Set a stable --teleop.id for calibration association")
        self._last_seq, self._last_device_ms, self._mapping = -1, -1, None
        if self.config.source not in ("synthetic", "serial"):
            raise ValueError("Glove source must be synthetic or serial")
        if not math.isfinite(self.config.timeout_s) or not 0 < self.config.timeout_s <= 1:
            raise ValueError("Sensor timeout must be in (0, 1] seconds")
        if self.config.source == "serial":
            if not self.config.port:
                raise ValueError("Serial glove needs an explicit port; ports are never auto-detected")
            import serial
            self._serial = serial.Serial(self.config.port, self.config.baudrate, timeout=self.config.timeout_s)
        self._connected = True
        self._start = time.monotonic()
        try:
            if calibrate and not self.is_calibrated:
                self.calibrate()
            if self.is_calibrated:
                self._mapping = load_mapping(self.config.mapping_file, device_id=self.id)
                if self.config.source == "serial" and self._mapping["kind"] == "synthetic":
                    raise ValueError("A physical glove cannot use synthetic calibration; measure its sensors first")
            if calibrate and self._mapping is None:
                raise RuntimeError("Glove needs calibration before teleoperation")
        except BaseException:
            self.disconnect()
            raise

    def _read_raw(self):
        if not self._connected or self._serial is None:
            raise RuntimeError("Serial glove is not connected")
        # Discard backlog so old buffered samples cannot keep a stalled device alive.
        self._serial.reset_input_buffer()
        deadline = time.monotonic() + self.config.timeout_s
        while time.monotonic() < deadline:
            line = self._serial.read_until(b"\n", size=4096)
            if not line.endswith(b"\n"):
                continue
            try:
                packet = json.loads(line)
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue  # Dropping a partial line after flushing is expected.
            if packet.get("schema") != "manual-dex-glove-v1" or packet.get("device_id") != self.id:
                raise ValueError("Glove firmware schema/device ID mismatch")
            seq, device_ms = packet.get("seq"), packet.get("device_ms")
            if type(seq) is not int or type(device_ms) is not int or seq <= self._last_seq or device_ms <= self._last_device_ms:
                raise ValueError("Repeated/out-of-order glove sample or device restart; reconnect")
            raw = finite_joints(packet.get("raw", {}))
            if any(not 0 <= value <= 4095 for value in raw.values()):
                raise ValueError("Glove raw readings must be 12-bit ADC counts in [0, 4095]")
            self._last_seq, self._last_device_ms = seq, device_ms
            return raw
        raise TimeoutError("No fresh glove sample; teleoperation must stop")

    def calibrate(self):
        if self.config.source == "synthetic":
            mapping = synthetic_mapping(self.id)
        else:
            if not self.config.reference_file:
                raise ValueError("Supply a reviewed two-pose reference file; see lerobot/CALIBRATION.md")
            reference = json.loads(Path(self.config.reference_file).read_text())
            if reference.get("reviewed") is not True or reference.get("kind") not in ("virtual", "measured"):
                raise ValueError("Reference must be reviewed and explicitly virtual or measured")
            poses = {}
            for pose in ("open", "closed"):
                angles = finite_joints(reference[f"{pose}_rad"])
                input(f"Place the glove in the reviewed {pose} reference pose, then press Enter (no motor commands): ")
                samples = [self._read_raw() for _ in range(20)]
                poses[pose] = ({name: statistics.median(s[name] for s in samples) for name in JOINTS}, angles)
            mapping = {"schema": "manual-dex-calibration-v1", "device_id": self.id, "kind": reference["kind"],
                "joints": {name: {"raw_open": poses["open"][0][name], "raw_closed": poses["closed"][0][name],
                                  "open_rad": poses["open"][1][name], "closed_rad": poses["closed"][1][name]} for name in JOINTS}}
        save_mapping(self.config.mapping_file, mapping)
        self._mapping = mapping
        print(f"Calibration saved: {self.config.mapping_file} ({mapping['kind']})")

    def configure(self):
        pass  # Sensor reads only; firmware and pin assignments are not configured here.

    def get_action(self):
        if not self._connected or self._mapping is None:
            raise RuntimeError("Connect and calibrate the glove first")
        if self.config.source == "synthetic":
            t = time.monotonic() - self._start
            raw = {name: 500 + 3000 * (.5 - .5 * math.cos(2 * math.pi * t / 5 + i * .02))
                   for i, name in enumerate(JOINTS)}
        else:
            raw = self._read_raw()
        return map_raw(self._mapping, raw)

    def send_feedback(self, feedback):
        if feedback:
            raise ValueError("This glove has no implemented haptic feedback")

    def disconnect(self):
        if self._serial is not None:
            self._serial.close()
            self._serial = None
        self._connected = False
