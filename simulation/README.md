# Simulate the MC-Dex hand on OpenArm

## Try the object-to-bowl policy

[Run the interactive browser demo](https://manual-ai.github.io/MC-dex-hand/bowl/). Throw one of 16 objects onto the table and watch the MC-Dex hand pick it up and drop it in the bowl. Push the object during a reach or drag it back out to trigger another attempt. The learned policy and MuJoCo physics run in your browser. [Controls](browser/bowl/README.md#play-in-your-browser) · [Policy evaluation](browser/bowl/README.md#browser-evaluation).

## Compare six simulation engines

Isaac Sim, MuJoCo, Genesis, SuperDex, Alloy and Steel each render the same programmed brick transfer with the hand mounted on a vertical OpenArm. A compliant grasp carries the brick until release. Each engine simulates the landing and produces a vertical force estimate from the brick’s motion. [Videos and force traces](COMPARISON.md) · [Force data (CSV)](../docs/assets/simulation/bowl/forces.csv) · [Reproduce the captures](bowl_showcase/README.md).

## Models and tutorials

- Import the standalone eight-joint hand using [MuJoCo MJCF](../models/manual_dex/README.md) or [URDF](../models/manual_dex/urdf/README.md).
- Test a grasp driven by opposing finger contacts in the [four-engine cube tutorial](CUBE_COMPARISON.md).
- Drive the simulated hand with a synthetic glove in the [LeRobot teleoperation tutorial](../lerobot/README.md).

<details>
<summary><strong>OpenArm setup for the four-engine cube and joint-playback tutorials</strong></summary>

## 1. Prerequisites

- Linux x86-64; the reference machine runs Ubuntu 24.04. Other platforms are not covered
  by the automatic bootstrap, even if an individual engine supports them.
- Python 3 with `venv`/`pip`, Git and Git LFS on `PATH`. On Ubuntu, install the missing
  prerequisites with `sudo apt install python3-venv python3-pip git git-lfs`.
- Internet access for the first setup, disk space for the engine and model caches,
  and your usual GitHub access to this repository.
- A desktop/OpenGL driver for interactive MuJoCo, Genesis or SuperDex. CPU-only headless
  motion tests are available for those engines. Screenshots still need a working renderer.
- Isaac Sim additionally requires a supported NVIDIA RTX GPU, compatible driver and
  acceptance of NVIDIA's EULA. Its installation is substantially larger than MuJoCo's;
  review the selected profile's [requirements](isaacsim/README.md)
  before installing. The launcher does not install drivers or accept terms silently.

Start in the repository root. Each command below performs its own setup; no separate
environment activation is necessary. The launcher uses `uv` if installed, or installs a
pinned copy in `build/simulation/bootstrap/`. It obtains the required Python version,
creates isolated engine environments, fetches required LFS meshes, retrieves the pinned
OpenArm source, assembles the robot, checks the model and starts the selected example.
It does not modify system Python or an existing environment passed with `--python`.
Run one launcher at a time in a checkout: a local lock protects the shared build assets,
environments and result files from simultaneous writes.

## 2. Choose an engine: one command

### Native physics and capture

These commands run the contact-driven cube tutorial in each native engine.

```bash
python3 simulation/run.py mujoco --native --headless
python3 simulation/run.py genesis --native --headless
python3 simulation/run.py superdex --native --headless
python3 simulation/run.py isaacsim --native --headless --accept-isaac-eula
```

Pass the Isaac flag only after agreeing to NVIDIA's terms. The native run captures
100 frames during a five-second [scripted pick and place](PICK_PLACE.md) and verifies
opposing finger contact, unsupported lift/transport, target placement and release.
See [the complete scene and publishing guide](CUBE_COMPARISON.md)
for outputs and acceptance criteria. `--native` always uses an offscreen renderer,
even without `--headless`; it needs working graphics support. Native Genesis physics
uses CPU. The following older playback options, such as arbitrary `--steps`,
`--screenshot` and `--trace`, do not apply to this fixed-duration showcase.
Native Isaac uses a separate 6.0.1 / Python 3.12 environment; the older playback
and LeRobot paths keep their existing 5.1 / Python 3.11 environment.

### Original import/playback examples

For an unattended workflow and explicit pass/fail criteria, see the
[agent runbook](AGENT_GUIDE.md).

| Engine tutorial | Interactive setup + launch from the repository root | Model path used |
|---|---|---|
| [MuJoCo](mujoco/README.md) | `python3 simulation/run.py mujoco` | Native assembled MJCF |
| [Genesis](genesis/README.md) | `python3 simulation/run.py genesis` | Composed URDF |
| [SuperDex](superdex/README.md) | `python3 simulation/run.py superdex` | Composed URDF via the runtime loader |
| [Isaac Sim](isaacsim/README.md) | `python3 simulation/run.py isaacsim --accept-isaac-eula` | Composed URDF converted to USD |

Only pass `--accept-isaac-eula` after reviewing and agreeing to the
[NVIDIA terms](https://docs.omniverse.nvidia.com/dev-guide/latest/common/NVIDIA_Omniverse_License_Agreement.html).
An agent must obtain the user's agreement before passing that flag.

By default, examples run **1,200 steps at 240 Hz**: five simulated seconds of arm motion
and finger flexion. Use `--steps 14400` for a longer interactive session. The first Genesis
run compiles kernels; the first SuperDex load bakes collision fields. Startup is not part
of the simulated duration. The default engine timeout is 900 seconds; increase it with
`--timeout 1800` on a slower machine.
SuperDex's interactive debugger starts paused: select the scene and press Play. Its
headless command needs no clicks and is the appropriate entry point for an agent.

### Headless runs for humans, agents and CI

```bash
python3 simulation/run.py mujoco --headless --steps 240 --screenshot
python3 simulation/run.py genesis --headless --steps 240 --screenshot
python3 simulation/run.py superdex --headless --steps 240
python3 simulation/run.py isaacsim --accept-isaac-eula --headless --steps 240
```

Success means exit code zero and a **fresh, run-ID-matched** JSON result containing
`"status": "passed"`, `"joint_count": 15`, finite joint positions, and a playback readback
error below 0.03 rad. This tolerance is a smoke-test threshold, not a hardware accuracy claim.
The launcher rejects a stale result from an earlier run even if an engine exits with zero.

Outputs are under `build/simulation/results/` (`mujoco.json`, `genesis.json`,
`superdex.json`, `isaacsim.json`, and requested screenshots). Full engine logs are under
`build/simulation/logs/`. SuperDex's headless path produces JSON, not a screenshot;
use its desktop debugger to inspect the robot visually.

For actual test coverage and known rendering limitations, see [VALIDATION.md](VALIDATION.md).

## 3. How the robot is connected

```text
OpenArm v1 fixed base
  └─ openarm_joint1 … openarm_joint7       7 arm DOFs
       └─ openarm_link7: wrist output
            └─ manual_dex_mount          fixed transform from mount.json
                 └─ Manual-Dex frame and shared attachments
                      ├─ index proximal → distal
                      ├─ middle proximal → distal
                      ├─ ring + little proximal → distal
                      └─ thumb proximal → distal     8 hand DOFs
```

The builder removes OpenArm's stock parallel-jaw gripper geometry, finger joints,
finger coupling and stock actuators before attaching Manual-Dex. This is one connected
articulation, not two robots placed near one another.

[`mount.json`](mount.json) exposes the parent body, wrist translation/rotation and the
hand's flange-center offset. Coordinates are in **metres**; RPY rotations and joint
positions are in **radians**. The default uses the OpenArm v1 wrist's top face and the
center of the Manual-Dex adaptor's 57 mm-diameter CAD flange. Its Z axis points from the
wrist into the hand. Bolt clocking and loaded clearances have not been calibrated.

After changing the mount, rebuild and inspect:

```bash
python3 simulation/run.py mujoco --rebuild
```

This tutorial targets the pinned **OpenArm v1 single arm**, not OpenArmX, a bimanual
configuration or an unverified v2 adaptor. To integrate another arm, replace the source
and mount in [`prepare.py`](prepare.py), preserve joint names deliberately, and extend
the checks before claiming compatibility.

## 4. Included files and generated assets

| Location | Purpose |
|---|---|
| [`../models/manual_dex/hand/scene.xml`](../models/manual_dex/hand/scene.xml) | Original eight-joint native MuJoCo hand |
| [`../models/manual_dex/urdf/manual_dex.urdf`](../models/manual_dex/urdf/manual_dex.urdf) | Included standalone hand URDF, rooted at the mounting flange |
| [`../models/manual_dex/urdf/README.md`](../models/manual_dex/urdf/README.md) | Standalone import, mesh conventions and limitations |
| [`versions.json`](versions.json) | Pinned upstream OpenArm commit and interpreter versions |
| [`prepare.py`](prepare.py) | Compose models; export a portable URDF and merged meshes |
| [`common.py`](common.py) | Named joints, example trajectory, CLI and result contract |
| [`check.py`](check.py) | Check model topology, mesh availability and cross-format kinematics |
| `build/simulation/generated/` | Locally assembled MJCF, URDF, meshes, provenance and OpenArm license |
| `build/simulation/envs/` | Isolated environments managed by the launcher |

The URDF uses **one complete OBJ visual per rigid link**, preserving all CAD occurrences.
This avoids SuperDex's first-visual-only behavior and MuJoCo's per-STL triangle limit.
Fixed mount frames are fused into neighboring links for import portability; kinematics
are checked against the unfused native MJCF. Collision meshes are separate watertight
convex-hull stand-ins, not detailed validated contact surfaces. The original playback
examples disable them; the native showcase enables robot/environment contacts.

OpenArm's upstream assets are downloaded at the exact commit in `versions.json`; they
are not silently replaced with whatever is on the upstream default branch. Its Apache-2.0
license is copied into the generated package. See [THIRD_PARTY.md](THIRD_PARTY.md).
The builder also includes the Manual-Dex hardware license and notice. Original tutorial
code uses Apache-2.0; original hand models use CERN-OHL-P-2.0. See
[the licensing scope](../LICENSING.md) before redistributing a mixed model package.

## 5. Existing environments and offline operation

An installed engine can be reused without changing its packages:

```bash
python3 simulation/run.py genesis --python /absolute/path/to/engine/bin/python --headless
```

After the initial online setup, reuse the cached files without network/setup operations:

```bash
python3 simulation/run.py mujoco --no-setup --headless --steps 240
python3 simulation/run.py prepare --no-setup
```

`--prepare-python /absolute/path/to/python` similarly selects an existing builder
environment. Direct entry points are available under each engine directory for users
who already have the models and dependencies. Use the launcher for reproducible result
checking, logs and timeouts.

## 6. From playback to dynamics and control

The original `demo.py` examples intentionally set joint positions before stepping. They do **not** implement
servo control, calibrated torque limits, grasp contact or a policy-learning task. Each
engine tutorial identifies where to replace playback with a controller. The separate
`native.py` showcase already uses native drives and contacts with illustrative parameters.
For a calibrated experiment:

1. Identify the real hand's link masses, centers of mass and inertia tensors. The hand
   currently uses 1 g / 10⁻⁶ kg·m² placeholders; fixed-body inertias may be merged.
2. Calibrate joint travel and drive/velocity limits. URDF effort 10 N·m and velocity
   2 rad/s are interface placeholders, **not** Feetech specifications.
3. Validate mount orientation, self-collision exclusions, contact geometry and friction.
4. Replace the convex proxies where necessary, then enable gravity/contact deliberately.
5. Test controllers and contacts in simulation before attempting hardware integration.

No example here opens a CAN bus, serial port, robot driver or network control endpoint.

</details>
