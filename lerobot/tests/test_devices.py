"""No ports, motor writes, simulator installs, desktop interaction or network access."""
import copy
import json
import time
from types import SimpleNamespace

import pytest

from lerobot_robot_manual_dex.calibration import (
    JOINTS, FEATURES, finite_joints, load_mapping, map_raw, save_mapping,
    synthetic_mapping, validate_mapping,
)
from lerobot_robot_manual_dex.glove import ManualDexGlove, ManualDexGloveConfig
from lerobot_robot_manual_dex.hardware import ManualDexHardware, ManualDexHardwareConfig, load_profile
from lerobot_robot_manual_dex.sim_robot import ManualDexSim, ManualDexSimConfig


def test_mapping_endpoints_clamps_and_polarity():
    mapping = synthetic_mapping("test-glove")
    for raw, fraction in ((0, 0), (500, 0), (2000, .5), (3500, 1), (4095, 1)):
        result = map_raw(mapping, {n: raw for n in JOINTS})
        for n in JOINTS:
            assert result[f"{n}.pos"] == pytest.approx(mapping["joints"][n]["closed_rad"] * fraction)
    reversed_map = copy.deepcopy(mapping)
    for row in reversed_map["joints"].values():
        row["raw_open"], row["raw_closed"] = 3500, 500
    validate_mapping(reversed_map)
    assert map_raw(reversed_map, {n: 3500 for n in JOINTS}) == dict.fromkeys(FEATURES, 0.)
    assert map_raw(reversed_map, {n: 500 for n in JOINTS}) == map_raw(mapping, {n: 3500 for n in JOINTS})


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), True, "12", None])
def test_non_numeric_or_nonfinite_joint(bad):
    values = dict.fromkeys(JOINTS, 1000.)
    values[JOINTS[0]] = bad
    with pytest.raises(ValueError):
        finite_joints(values)


@pytest.mark.parametrize("raw", [-1, 4096])
def test_out_of_adc_range(raw):
    with pytest.raises(ValueError):
        map_raw(synthetic_mapping("test"), dict.fromkeys(JOINTS, raw))


def test_missing_or_extra_channels():
    for values in ({}, {**dict.fromkeys(JOINTS, 1), "unexpected": 1}, None):
        with pytest.raises(ValueError):
            finite_joints(values)


@pytest.mark.parametrize("field,value", [("raw_closed", 510), ("raw_open", -5),
                                          ("closed_rad", 0), ("open_rad", float("nan"))])
def test_invalid_calibration(field, value):
    mapping = synthetic_mapping("test")
    mapping["joints"][JOINTS[0]][field] = value
    with pytest.raises(ValueError):
        validate_mapping(mapping)


def test_mapping_identity_and_no_overwrite(tmp_path):
    path = tmp_path / "glove.json"
    save_mapping(path, synthetic_mapping("a"))
    assert load_mapping(path, device_id="a")["kind"] == "synthetic"
    with pytest.raises(ValueError):
        load_mapping(path, device_id="b")
    with pytest.raises(ValueError):
        load_mapping(path, require_measured=True)
    with pytest.raises(FileExistsError):
        save_mapping(path, synthetic_mapping("b"))
    assert load_mapping(path)["device_id"] == "a"


def test_synthetic_glove_round_trip(tmp_path):
    glove = ManualDexGlove(ManualDexGloveConfig(id="test", calibration_dir=tmp_path / "meta",
        mapping_file=str(tmp_path / "mapping.json")))
    try:
        glove.connect()
        assert glove.is_calibrated
        assert set(glove.get_action()) == set(FEATURES)
        with pytest.raises(ValueError):
            glove.send_feedback({"force": 1})
    finally:
        glove.disconnect()
    assert not glove.is_connected


class FakeSerial:
    def __init__(self, *args, **kwargs):
        self.lines = []
        self.closed = False

    def reset_input_buffer(self):
        pass

    def read_until(self, *args, **kwargs):
        return self.lines.pop(0) if self.lines else b""

    def close(self):
        self.closed = True


@pytest.fixture
def serial_glove(tmp_path, monkeypatch):
    import serial
    monkeypatch.setattr(serial, "Serial", FakeSerial)
    glove = ManualDexGlove(ManualDexGloveConfig(id="test", source="serial", port="FAKE_ONLY",
        calibration_dir=tmp_path / "meta", mapping_file=str(tmp_path / "mapping.json"), timeout_s=.001))
    glove.connect(calibrate=False)
    yield glove
    glove.disconnect()


def packet(seq=1, device_ms=1, device_id="test"):
    return (json.dumps({"schema": "manual-dex-glove-v1", "seq": seq, "device_ms": device_ms,
        "device_id": device_id, "raw": dict.fromkeys(JOINTS, 1500)}) + "\n").encode()


def test_serial_freshness_and_timeout(serial_glove):
    serial_glove._serial.lines = [b"partial\n", packet()]
    assert serial_glove._read_raw() == dict.fromkeys(JOINTS, 1500.)
    serial_glove._serial.lines = [packet()]
    with pytest.raises(ValueError, match="out-of-order"):
        serial_glove._read_raw()
    with pytest.raises(TimeoutError):
        serial_glove._read_raw()


@pytest.mark.parametrize("line", [packet(seq=True), packet(device_ms=False), packet(device_id="other")])
def test_serial_bad_identity_or_counter(serial_glove, line):
    serial_glove._serial.lines = [line]
    with pytest.raises(ValueError):
        serial_glove._read_raw()


def test_serial_rejects_synthetic_map(serial_glove):
    save_mapping(serial_glove.config.mapping_file, synthetic_mapping("test"))
    serial_glove.disconnect()
    with pytest.raises(ValueError, match="synthetic"):
        serial_glove.connect()
    assert not serial_glove.is_connected


def test_hardware_disabled_before_driver_import(tmp_path):
    robot = ManualDexHardware(ManualDexHardwareConfig(id="hand", calibration_dir=tmp_path,
        driver_factory="must_never_import:Driver", port="NEVER_OPEN"))
    with pytest.raises(PermissionError, match="disabled"):
        robot.connect()
    assert not robot.is_connected


def test_unverified_hardware_profile(tmp_path):
    path = tmp_path / "profile.json"
    path.write_text(json.dumps({"schema": "manual-dex-hand-profile-v1", "hardware_verified": False}))
    with pytest.raises(ValueError, match="verified"):
        load_profile(path)


def test_simulator_clips_and_reads_back(tmp_path):
    robot = ManualDexSim(ManualDexSimConfig(id="sim", calibration_dir=tmp_path,
        repo_root=str(tmp_path), control_dt_s=.05, max_velocity_rad_s=1.))
    def step(operation, **fields):
        assert operation == "step"
        robot.client.positions = fields["positions"]
    robot.client = SimpleNamespace(process=SimpleNamespace(poll=lambda: None),
        positions=dict.fromkeys(JOINTS, 0.), request=step, close=lambda: None)
    assert robot.send_action(dict.fromkeys(FEATURES, 1.)) == dict.fromkeys(FEATURES, .05)
    assert robot.get_observation() == dict.fromkeys(FEATURES, .05)
    assert robot.send_action(dict.fromkeys(FEATURES, -1.)) == dict.fromkeys(FEATURES, 0.)
    with pytest.raises(ValueError):
        robot.send_action({})
    with pytest.raises(ValueError):
        robot.send_action(dict.fromkeys(FEATURES, float("nan")))
    robot.disconnect()
    result = json.loads((tmp_path / "build/lerobot/results/mujoco.json").read_text())
    assert result["actions"] == 2
    assert result["motion_span_rad"] == dict.fromkeys(JOINTS, .05)


def test_serial_reconnect_resets_device_counters(serial_glove):
    serial_glove._serial.lines = [packet(seq=100, device_ms=100)]
    serial_glove._read_raw()
    serial_glove.disconnect()
    serial_glove.connect(calibrate=False)
    serial_glove._serial.lines = [packet(seq=1, device_ms=1)]
    serial_glove._read_raw()


def test_measured_two_pose_calibration(serial_glove, tmp_path, monkeypatch):
    reference = {"kind": "measured", "reviewed": True,
        "open_rad": dict.fromkeys(JOINTS, -.1), "closed_rad": dict.fromkeys(JOINTS, .4)}
    path = tmp_path / "reference.json"
    path.write_text(json.dumps(reference))
    serial_glove.config.reference_file = str(path)
    poses = iter([1000, 3000])
    current = [None]
    monkeypatch.setattr("builtins.input", lambda prompt: current.__setitem__(0, next(poses)))
    monkeypatch.setattr(serial_glove, "_read_raw", lambda: dict.fromkeys(JOINTS, current[0]))
    serial_glove.calibrate()
    mapping = load_mapping(serial_glove.config.mapping_file, device_id="test", require_measured=True)
    assert map_raw(mapping, dict.fromkeys(JOINTS, 2000)) == dict.fromkeys(FEATURES, .15)


@pytest.fixture
def hardware_config(tmp_path):
    profile = {"schema": "manual-dex-hand-profile-v1", "hardware_verified": True,
        "hand_id": "test-hand", "servo_model": "HLS3606",
        "joints": {n: {"motor_id": i+1, "min_rad": -1., "max_rad": 1., "max_velocity_rad_s": .5}
                   for i, n in enumerate(JOINTS)}}
    profile_path = tmp_path / "profile.json"
    profile_path.write_text(json.dumps(profile))
    mapping = synthetic_mapping("test-glove")
    mapping["kind"] = "measured"  # Fictional test fixture only, never a physical calibration.
    mapping_path = tmp_path / "mapping.json"
    save_mapping(mapping_path, mapping)
    return ManualDexHardwareConfig(id="test-hand", calibration_dir=tmp_path / "meta",
        port="FAKE_ONLY", driver_factory="fake_test_driver:Driver", profile_file=str(profile_path),
        glove_mapping_file=str(mapping_path), enable_motion=True)


class FakeHandDriver:
    hardware_watchdog_supported = True

    def __init__(self, **kwargs):
        self.stopped, self.closed, self.armed = False, False, False
        self.positions = dict.fromkeys(JOINTS, 0.)

    def connect(self, *, read_only):
        assert read_only is True

    def read_positions_rad(self):
        return self.positions.copy()

    def arm(self, *, watchdog_s, hold_positions):
        assert hold_positions == self.positions
        self.armed = True

    def send_positions_rad(self, positions):
        assert self.armed
        self.positions = positions.copy()

    def stop(self):
        self.stopped = True

    def disconnect(self):
        self.closed = True


def test_fake_hardware_rate_limit_and_stall_stop(hardware_config, monkeypatch):
    monkeypatch.setattr("lerobot_robot_manual_dex.hardware.importlib.import_module",
                        lambda name: SimpleNamespace(Driver=FakeHandDriver))
    robot = ManualDexHardware(hardware_config)
    robot.connect()
    driver = robot.driver
    robot._last_command = time.monotonic() - .02
    sent = robot.send_action(dict.fromkeys(FEATURES, 5.))
    assert all(.009 <= value <= .025 for value in sent.values())
    robot._last_command = time.monotonic() - 1.
    with pytest.raises(TimeoutError):
        robot.send_action(dict.fromkeys(FEATURES, .1))
    assert driver.stopped and driver.closed and not robot.is_connected


def test_fake_hardware_bad_action_stops(hardware_config, monkeypatch):
    monkeypatch.setattr("lerobot_robot_manual_dex.hardware.importlib.import_module",
                        lambda name: SimpleNamespace(Driver=FakeHandDriver))
    robot = ManualDexHardware(hardware_config)
    robot.connect()
    driver = robot.driver
    with pytest.raises(ValueError):
        robot.send_action(dict.fromkeys(FEATURES, float("nan")))
    assert driver.stopped and driver.closed


def test_hardware_wrong_hand_id(hardware_config):
    hardware_config.id = "wrong-hand"
    with pytest.raises(ValueError, match="belong"):
        ManualDexHardware(hardware_config).connect()


@pytest.mark.parametrize("kind", ["virtual", "synthetic"])
def test_hardware_rejects_unmeasured_glove(hardware_config, kind):
    from pathlib import Path
    path = Path(hardware_config.glove_mapping_file)
    mapping = json.loads(path.read_text())
    mapping["kind"] = kind
    path.write_text(json.dumps(mapping))
    with pytest.raises(ValueError, match="measured"):
        ManualDexHardware(hardware_config).connect()


def test_hardware_requires_controller_watchdog(hardware_config, monkeypatch):
    monkeypatch.setattr("lerobot_robot_manual_dex.hardware.importlib.import_module",
        lambda name: SimpleNamespace(Driver=lambda **kwargs: SimpleNamespace(hardware_watchdog_supported=False)))
    with pytest.raises(ValueError, match="controller-side watchdog"):
        ManualDexHardware(hardware_config).connect()


def test_duplicate_motor_ids(hardware_config):
    from pathlib import Path
    path = Path(hardware_config.profile_file)
    profile = json.loads(path.read_text())
    profile["joints"][JOINTS[0]]["motor_id"] = profile["joints"][JOINTS[1]]["motor_id"]
    path.write_text(json.dumps(profile))
    with pytest.raises(ValueError, match="unique"):
        load_profile(path)
