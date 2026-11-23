# LeRobot version and integration decisions

Checked 2026-09-08 against live upstream release/PyPI metadata and the pinned source.
The latest stable version was **0.6.1**, released 2026-08-03, commit
`7e241bd630a3719a56157a497ce5d08f244784f1`.
Sources: [release](https://github.com/huggingface/lerobot/releases/tag/v0.6.1),
[PyPI package](https://pypi.org/project/lerobot/0.6.1/),
[dependency manifest](https://github.com/huggingface/lerobot/blob/v0.6.1/pyproject.toml).

## Why provide a plugin as well as YAML?

LeRobot's device interfaces require connection lifecycle methods, named action and
observation features, calibration and actual sensor/actuator I/O. A YAML cannot add
support for a new potentiometer stream or an unknown servo protocol. This repository
therefore supplies `ManualDexGlove`, `ManualDexSim` and a guarded `ManualDexHardware`
extension seam following the upstream
[hardware integration guide](https://huggingface.co/docs/lerobot/integrate_hardware),
[Robot interface](https://github.com/huggingface/lerobot/blob/v0.6.1/src/lerobot/robots/robot.py)
and [Teleoperator interface](https://github.com/huggingface/lerobot/blob/v0.6.1/src/lerobot/teleoperators/teleoperator.py).

The installed distribution is named `lerobot_robot_manual_dex` so upstream
[plugin discovery](https://github.com/huggingface/lerobot/blob/v0.6.1/src/lerobot/utils/import_utils.py)
imports its registration module. The same module registers the glove teleoperator.
No changes to the upstream LeRobot checkout or installed source are required.

## CLI and data semantics

The examples use `--config_path` YAML parsing plus ordinary command-line overrides.
They exercise the upstream
[teleoperate](https://github.com/huggingface/lerobot/blob/v0.6.1/src/lerobot/scripts/lerobot_teleoperate.py),
[calibrate](https://github.com/huggingface/lerobot/blob/v0.6.1/src/lerobot/scripts/lerobot_calibrate.py)
and [record](https://github.com/huggingface/lerobot/blob/v0.6.1/src/lerobot/scripts/lerobot_record.py)
entry points. The 0.6.1 recorder stores the processed teleoperator action before
`Robot.send_action` clipping, a distinction explicitly documented in our recording guide.
Local examples set `push_to_hub: false`; the launcher also enables Hub/dataset offline
mode during execution. No remote dataset or model download is required to teleoperate.

## Isolated interpreters

LeRobot 0.6.1 requires Python >=3.12 and NumPy >=2,<2.3. The tested Isaac Sim 5.1 pip
environment uses Python 3.11 and NumPy 1.26; see NVIDIA's
[pip installation guide](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_python.html).
Our design inference is to keep one process per engine and exchange simple joint-state
messages through a private socket. Installing LeRobot into Isaac's environment is
not part of these instructions.

The host environment pins Torch 2.7.0 and TorchCodec 0.3.0 as a compatible pair under
the upstream [TorchCodec compatibility table](https://github.com/meta-pytorch/torchcodec#compatibility-with-torch-versions).
This is a CPU state-teleoperation/recording host, not a claimed RTX 5090 policy-training
configuration. Genesis and Isaac retain their separate engine-specific Torch stacks.

## Physical-hand blocker

The latest [Feetech tables](https://github.com/huggingface/lerobot/blob/v0.6.1/src/lerobot/motors/feetech/tables.py)
do not list the HLS3606 model used in the [Manual-Dex BOM](../bom/BOM.md).
The repository's controller and firmware were still pending at integration time.
We therefore expose a driver contract rather than aliasing an unverified motor to a
supported model. The necessary missing artifacts are enumerated in
[HARDWARE.md](HARDWARE.md). This conclusion is about the pinned source and this release,
not a claim that no third-party HLS3606 driver could exist.
