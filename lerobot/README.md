# Manual-Dex teleoperation with LeRobot

Run a synthetic glove through the **real LeRobot CLI** into the Manual-Dex hand on
OpenArm in MuJoCo, Genesis, SuperDex or Isaac Sim. Then replace the synthetic input
with an instrumented glove using the calibration workflow below.

This integration targets **LeRobot 0.6.1**, the latest stable release checked on
2026-09-08. It includes an installable device plugin, YAML examples, a calibration
utility, a process bridge and a local recording example—not just illustrative commands.
See the [version research and source references](RESEARCH.md).

| Path | Readiness |
|---|---|
| Synthetic glove → four simulators | Implemented; headless motion tested through `lerobot-teleoperate` |
| Synthetic glove → local LeRobot dataset | Implemented; state-only recording, no upload |
| Physical glove → simulator | Host adapter/calibration included; needs glove firmware implementing [PROTOCOL.md](PROTOCOL.md) |
| Physical glove → physical hand | Guarded plugin/template included; **blocked on a verified HLS3606 driver, wiring and measured calibration** |

These simulations prescribe joint positions with gravity/contact disabled. They do
not validate grasp dynamics, physical calibration or safe actuator settings. Only the
eight hand joints are teleoperated; OpenArm's seven joints stay at a fixed inspection
pose. Quest tracking, wrist/arm IK, haptics and camera capture are not implemented.

## 1. First run: one command, no hardware

Use Linux x86-64 with Python 3, Git and Git LFS. Follow the
[simulation prerequisites](../simulation/README.md#1-prerequisites), including the
additional GPU requirements for Isaac Sim. From the repository root:

```bash
python3 lerobot/run.py mujoco
```

The launcher downloads pinned model/dependency sources, prepares OpenArm + Manual-Dex,
installs the selected engine and creates a separate Python 3.12.3 LeRobot environment.
It runs ten seconds of synthetic glove input at a target 30 Hz, checks fresh joint
readbacks and exits. No activation, serial device, camera, Hugging Face login or upload
is required. Initial downloads can be large, especially PyTorch and Isaac Sim.
The finite run begins after engine startup; first-time compilation can take minutes.

| Engine | Setup + headless teleoperation | Native viewer |
|---|---|---|
| [MuJoCo](../simulation/mujoco/README.md) | `python3 lerobot/run.py mujoco` | Add `--viewer` |
| [Genesis](../simulation/genesis/README.md) | `python3 lerobot/run.py genesis` | Add `--viewer`; bridge uses CPU backend |
| [SuperDex](../simulation/superdex/README.md) | `python3 lerobot/run.py superdex` | Add `--viewer`; press Play in the debugger |
| [Isaac Sim](../simulation/isaacsim/README.md) | `python3 lerobot/run.py isaacsim --accept-isaac-eula` | Implemented but locally **unverified**; RTX startup crashes on the test machine |

Pass `--accept-isaac-eula` only after reviewing and agreeing to
[NVIDIA's terms](https://docs.omniverse.nvidia.com/dev-guide/latest/common/NVIDIA_Omniverse_License_Agreement.html).
An agent must obtain the user's agreement first. No launcher accepts it silently.
Headless is the tested path for all four LeRobot adapters; a working native-viewer
environment is an additional requirement, not implied by the numerical test.

After the first setup:

```bash
python3 lerobot/run.py mujoco --no-setup --seconds 5
python3 lerobot/run.py mujoco --no-setup --viewer --seconds 60
```

Success is exit code zero, at least one action, eight finite observed joint positions,
motion in all eight channels, and a result matching this invocation's unique run ID.
Results are `build/lerobot/results/<engine>.json`; CLI and worker logs are under
`build/lerobot/logs/`. A saved JSON alone is not proof of a successful run. The launcher
rejects stale results, enforces a timeout and prevents simultaneous launcher runs in
one checkout. All environments, calibration output, logs and datasets stay in ignored
`build/`; no system Python packages are modified.

## 2. Use ordinary LeRobot commands and YAML

The setup installs the editable `lerobot_robot_manual_dex` distribution. LeRobot's
standard plugin discovery registers `manual_dex_glove`, `manual_dex_sim`, and
`manual_dex_hardware`. Use the installed CLI from the repository root:

```bash
build/lerobot/env/bin/lerobot-teleoperate \
  --config_path=lerobot/configs/teleop_sim.yaml \
  --robot.engine=mujoco --robot.headless=true --teleop_time_s=10
```

Change `--robot.engine` to `genesis`, `superdex` or `isaacsim` after setting up that
engine. Isaac also requires `--robot.accept_isaac_eula=true` after agreement.
`--robot.repo_root` accepts an absolute checkout path; `--robot.engine_python` can
select an already-configured simulator interpreter without installing into it.
Keep `robot.control_dt_s = 1 / fps` when changing the control frequency.

| File | Purpose |
|---|---|
| [teleop_sim.yaml](configs/teleop_sim.yaml) | Synthetic eight-channel glove → simulator |
| [teleop_glove_to_sim.yaml](configs/teleop_glove_to_sim.yaml) | Explicit serial glove → simulator; replace device placeholders |
| [teleop_hardware.yaml](configs/teleop_hardware.yaml) | Physical-hand integration template; motion **disabled** |
| [record_sim.yaml](configs/record_sim.yaml) | One local, state-only episode; Hub upload **disabled** |
| [reference.example.json](configs/reference.example.json) | Two-pose virtual angle reference; review gate starts false |
| [hand_profile.example.json](configs/hand_profile.example.json) | Unmeasured hand profile; hardware gate starts false |
| [protocol_frame.example.json](configs/protocol_frame.example.json) | Glove serial message field example |

If a ROS shell exports `PYTHONPATH`, clear it when using the direct CLI to avoid
mixing environments. The one-command launcher and simulator bridge clear inherited
`PYTHONPATH` / `PYTHONHOME` themselves.

## 3. Calibrate a real glove, first against the virtual hand

Read [CALIBRATION.md](CALIBRATION.md) for the complete two-pose procedure and commands.
The workflow measures each potentiometer at two corresponding reference angles,
detects reversed sensor polarity, clamps the mapped range and saves a device-specific
JSON. The glove adapter reads sensors only; calibration sends **no motor commands**.

The firmware source and ADC pin map are still pending in
[`firmware/esp32_glove/`](../firmware/esp32_glove/README.md). Implement the explicitly
versioned [serial contract](PROTOCOL.md) before using the serial YAML. Do not assume
an existing glove emits this new protocol. Use `kind: virtual` references while
checking joint correspondence in simulation, not guessed physical encoder limits.

For physical teleoperation, complete [HARDWARE.md](HARDWARE.md). The bundled driver
template cannot actuate anything, even if a YAML flag is changed. LeRobot's current
Feetech tables do not list the BOM's HLS3606; STS3215 register values are not a substitute.

## 4. Record a local LeRobot episode

```bash
python3 lerobot/run.py mujoco --record --seconds 5
```

This uses upstream `lerobot-record`, writes a new uniquely named directory under
`build/lerobot/datasets/`, verifies a completed episode and never uploads it.
Use `--no-setup` on later runs. Other engines use the same `--record` option, though
the recorded-dataset validation was performed with MuJoCo; see [VALIDATION.md](VALIDATION.md).

The direct equivalent is:

```bash
build/lerobot/env/bin/lerobot-record \
  --config_path=lerobot/configs/record_sim.yaml
```

The direct YAML has a fixed dataset root: choose a new `--dataset.root` for another
recording, or deliberately use upstream's resume workflow. Do not delete an earlier
dataset merely to rerun an example. The launcher chooses a fresh root automatically.

The dataset contains eight `observation.state` coordinates and eight `action` values,
in **radians**, plus standard episode/frame/task metadata. There are no images.
In LeRobot 0.6.1's stock recorder, `action` is the processed glove request **before**
the robot plugin's rate/position clipping; `observation.state` is the actual simulator
readback from before that step. Do not describe this as a dataset of post-clipping
commands or use it as measured physical training data. A controller-aware processor,
cameras, task resets, rewards and policy evaluation are separate follow-on work.

For a future camera-based capture setup, follow the
[visual embodiment-matching guidance](../README.md#why-is-there-a-quest-3-controller-on-the-actuated-hand):
retain corresponding Quest 3 controllers for the overhead-camera view, and wear a black,
fingertip-less fabric glove beneath the sensing assembly for hand-camera appearance
matching after simple inpainting. The state-only example above does not capture images
or implement inpainting; those remain separate from the working joint-teleoperation path.

## 5. Implementation and reproducibility

```text
glove raw ADC counts (or synthetic samples)
  → device-specific two-pose mapping
  → eight LeRobot <joint>.pos actions, radians
  → ManualDexSim robot plugin: travel/rate clipping
  → private local socket → separate engine Python
  → actual engine joint readback → LeRobot observation.state
```

The socket is an inherited Unix socket pair, not a listening TCP server. Each worker
loads the same prepared OpenArm + Manual-Dex model; only simulator processes are
started. The process boundary keeps LeRobot's Python 3.12 / NumPy 2 separate from
Isaac Sim 5.1's Python 3.11 / NumPy 1 environment.

The plugin lives in [`src/lerobot_robot_manual_dex/`](src/lerobot_robot_manual_dex/);
the engine-side worker is [`../simulation/teleop_worker.py`](../simulation/teleop_worker.py).
Dependencies are pinned in [requirements.txt](requirements.txt). Run unit tests with:

```bash
env PYTHONPATH= PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  build/lerobot/env/bin/python -m pytest lerobot/tests -q
```

The unit suite uses fake devices only. See [VALIDATION.md](VALIDATION.md) for actual
engine tests and [RESEARCH.md](RESEARCH.md) for the APIs inspected. Original adapter
code/configuration/tutorials use the root [Apache-2.0 license](../LICENSE); models
retain their [separate hardware and upstream terms](../LICENSING.md).
