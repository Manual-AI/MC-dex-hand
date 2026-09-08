# Genesis: OpenArm v1 with Manual-Dex

## Native physics and rendered showcase

```bash
python3 simulation/run.py genesis --native --headless
```

[`native.py`](native.py) creates the robot, table, floor and loose cube directly in
Genesis, with gravity, contacts and native PD drives. It uses Genesis's own offscreen
raster camera, not MuJoCo. After initialization, `control_dofs_position` supplies
targets and `scene.step` evolves the state; joint positions are not overwritten.

The five-second CPU-physics demo captures 100 native frames of a
[scripted pick and place](../PICK_PLACE.md), requiring opposing finger contact during
lift/transport and a released cube at the target. Explicit joint armatures and the
implicit-fast integrator avoid the loader's oversized default finger inertia.
The fixed camera and geometry match the other engines through
[`native_scene.json`](../native_scene.json). Outputs are in `build/simulation/native/`;
see [capture validation and GIF publishing](../COMPARISON.md). EGL graphics support is
required even though no window is opened. The gains/inertias are illustrative, not
calibrated hardware or grasp performance. The native showcase uses the CPU backend;
`--backend` below applies only to the older playback example.

The sections below retain the simpler zero-gravity import/playback example.

## Run

```bash
python3 simulation/run.py genesis
```

For a headless run with an engine-rendered image:

```bash
python3 simulation/run.py genesis --headless --steps 240 --screenshot
```

The launcher installs the pinned Genesis 1.0.0 environment and loads the composed URDF.
The default simulation backend is CPU. For a compatible GPU stack, opt in with
`--backend gpu`; see [Genesis installation guidance](https://genesis-world.readthedocs.io/en/latest/user_guide/overview/installation.html).
PyTorch and Genesis are substantial downloads, and first-run kernel compilation can
take minutes. The viewport/screenshot renderer still needs working graphics libraries
even when the physics backend is CPU.

Expected outputs: `build/simulation/results/genesis.json` and, when requested,
`genesis.png`. Success reports 15 finite named joint states. See the
[validation record](../VALIDATION.md) for tested versions and modes.

## What the example does

[`demo.py`](demo.py):

1. Initialize Genesis and create a zero-gravity scene.
2. Add one `gs.morphs.URDF` from `build/simulation/generated/openarm_manual_dex.urdf`
   with a fixed base, fixed-link merging disabled and collision checking disabled.
3. Build the scene, then obtain each joint's local DOF index by name.
4. Apply the shared arm/finger trajectory with `set_dofs_position`, zero velocities,
   and step the scene. Read the joint states back for the result.

The URDF is already assembled: the hand is a descendant of OpenArm's wrist joint.
Do not add the hand as a second free entity or move it independently after stepping.

## Load in your own scene

After the preparation command, from the repository root:

```python
import genesis as gs

gs.init(backend=gs.cpu)
scene = gs.Scene(show_viewer=False)
robot = scene.add_entity(gs.morphs.URDF(
    file="build/simulation/generated/openarm_manual_dex.urdf",
    fixed=True, merge_fixed_links=False, collision=False,
))
scene.build()
index_dof = robot.get_joint("md_index_proximal").dofs_idx_local[0]
robot.set_dofs_position([0.3], dofs_idx_local=[index_dof])
```

For just the gripper, substitute `models/manual_dex/urdf/manual_dex.urdf` and expect
eight DOFs. Use the [flange-rooted URDF notes](../../models/manual_dex/urdf/README.md).

## Moving toward position control

Genesis exposes `set_dofs_kp`, `set_dofs_kv` and `control_dofs_position`. To test a real
position controller, configure identified gains and replace the direct state-setting
line with a target command; do not teleport the state every frame. Calibrate the
inertias and contact model first. The supplied trajectory/readback test establishes
import and joint wiring, not stable control under gravity.

## Troubleshooting

- **First frame takes a long time:** allow kernel compilation to finish; use
  `--timeout 1800` on slower systems.
- **GPU/CUDA initialization fails:** use the CPU backend or install a PyTorch build
  compatible with your driver in a separate environment and pass `--python`.
- **No display / renderer error:** use `--headless` and omit `--screenshot` to test motion.
- **Unexpected joint ordering:** query by name as the example does; do not hard-code
  MuJoCo's joint indices in Genesis.

References: [Genesis rigid bodies](https://genesis-world.readthedocs.io/en/latest/user_guide/physics/rigid_bodies.html),
[Genesis source](https://github.com/Genesis-Embodied-AI/Genesis).
