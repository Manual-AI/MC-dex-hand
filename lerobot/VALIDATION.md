# LeRobot integration validation

Recorded 2026-09-08 on Ubuntu 24.04 x86-64, 64 GB RAM, RTX 5090 Laptop GPU,
NVIDIA driver 595.84. These are observed local tests, not universal engine compatibility
or physical-hardware certification.

## Host environment and CLI

The integration was installed into a new isolated Python 3.12.3 environment with
LeRobot 0.6.1, Torch 2.7.0, torchvision 0.22.0, TorchCodec 0.3.0, NumPy 2.2.6 and
pyserial 3.5. `uv pip check` passed. Upstream plugin discovery found both the robot
and teleoperator registrations without patching LeRobot. The synthetic
`lerobot-calibrate` command created and loaded a device-specific mapping successfully.

## Teleoperation backend tests

The real upstream `lerobot-teleoperate --config_path=...` CLI drove each native engine
through the private process bridge. Each test ran for five seconds after startup,
at a target 30 Hz, with eight hand actions and a fixed seven-joint OpenArm pose.

| Engine | Interpreter | Observed result |
|---|---|---|
| MuJoCo 3.6.0 | Separate Python 3.11 | 150 actions, eight finite moving joint readbacks |
| Genesis 1.0.0, CPU | Separate Python 3.11 | 150 actions, eight finite moving joint readbacks |
| SuperDex 1.0.0 | Separate Python 3.12 | 150 actions, eight finite moving joint readbacks; post-step drift is present |
| Isaac Sim 5.1.0.0, headless PhysX | Separate Python 3.11 | 150 actions, eight finite moving joint readbacks; maximum post-step deviation < 3 × 10⁻⁸ rad in the tested run |

Isaac testing used explicitly approved EULA acceptance. The bridge retained the
imported USD stage while checking its default prim, fixing a temporary-stage lifetime
bug discovered during testing. LeRobot was not installed into the Isaac environment.

The tests demonstrate the host/plugin/import/IPC/action/readback path. Positions are
prescribed, with no validated actuator dynamics, gravity or contacts. SuperDex can
move away from prescribed positions during its step, particularly at the thumb; rate
clipping based on observed positions can consequently reduce achieved motion range.
The result JSON reports `max_post_step_deviation_rad` per joint. Passing the launcher
requires finite movement, **not** a tracking-error tolerance or full target-range
attainment. Do not use these demonstrations as physical or cross-engine benchmarks.

Native LeRobot viewers were not validated in these tests. Isaac RTX rendering still
has the startup crash documented in the [simulation validation record](../simulation/VALIDATION.md).
SuperDex's debugger requires Play; waiting in its paused state is not a successful
interactive teleoperation test.

## Local dataset recording

`python3 lerobot/run.py mujoco --record --seconds 5 --no-setup` passed with the stock
`lerobot-record` CLI: one completed episode, **150 frames at 30 Hz**, dataset format
`v3.0`, robot type `manual_dex_sim`. The saved Parquet file was opened independently;
`observation.state` and `action` both had shape `(150, 8)` and all values were finite.
The dataset also reloaded through upstream `LeRobotDataset`. No camera/video features
were present. Upload was disabled and execution used Hub/
dataset offline mode. No Hugging Face repository was created or modified.

The recorded actions are pre-robot-clipping glove requests; observations are preceding
step readbacks. See the [recording semantics](README.md#4-record-a-local-lerobot-episode).
Dataset recording in the other three backends is available through the same adapter
but was not independently exercised in this validation record.

## Unit tests and safeguards

**32 tests passed**, using fake sensors/drivers only. Coverage includes:

- Two-pose mapping endpoints, intermediate values, clipping and reversed polarity.
- Missing/extra channels, invalid types, NaNs, infinities and out-of-ADC-range samples.
- Insufficient calibration span, wrong device identity and overwrite refusal.
- Sensor freshness, timeout, counter ordering and explicit reconnect after device reset.
- Rejection of synthetic maps for real glove input and unmeasured maps for hardware.
- Interactive two-pose calibration with fake samples (no real serial port).
- Hardware disabled before driver import, unverified profiles, duplicate motor IDs,
  wrong hand identity and required controller watchdog capability.
- Simulator rate clipping/readback, fake-hand rate clipping, stalled commands and
  invalid actions requesting stop/disconnect.

```bash
env PYTHONPATH= PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  build/lerobot/env/bin/python -m pytest lerobot/tests -q
```

Disabling pytest plugin autoload prevents unrelated ROS test plugins in an interactive
shell from changing this suite. No physical glove, servo bus, arm, camera or Quest
device was opened or actuated. Hardware firmware, encoder conversions, actual watchdog
behavior, calibration accuracy and emergency-stop behavior remain unverified.

## Reproduce

From the repository root, with the prerequisites and NVIDIA agreement where relevant:

```bash
python3 lerobot/run.py mujoco --seconds 5
python3 lerobot/run.py genesis --seconds 5
python3 lerobot/run.py superdex --seconds 5
python3 lerobot/run.py isaacsim --accept-isaac-eula --seconds 5
python3 lerobot/run.py mujoco --record --seconds 5 --no-setup
```

Use one launcher at a time. Later runs may use `--no-setup` to reuse the prepared
models and installed environments offline. Verify exit status and current run ID;
old logs/results can remain after a failed invocation.
