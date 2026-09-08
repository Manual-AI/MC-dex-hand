# MuJoCo: OpenArm v1 with Manual-Dex

## Native physics and rendered showcase

```bash
python3 simulation/run.py mujoco --native --headless
```

This one command prepares the robot and runs [`native.py`](native.py): native MuJoCo
position actuators run a [scripted pick and place](../PICK_PLACE.md), with gravity and
finger/cube/table contacts enabled. The EGL renderer captures 100 frames over five seconds.
The cube is grasped, lifted, carried and released; it is never attached or teleported.
No desktop window is opened.

The initial pose is set once. Each subsequent step writes `data.ctrl`, calls `mj_step`,
reads actual joint/cube states and renders that same `MjData`. The capture and JSON
evidence are under `build/simulation/native/`; see [scene, validation and GIF publishing](../COMPARISON.md).
The camera, table, gains and illustrative inertias are in [`native_scene.json`](../native_scene.json).
This smoke test is not a calibrated grasp or hardware-control demonstration.

The sections below retain the simpler zero-gravity import/playback example.

## Run

From the repository root:

```bash
python3 simulation/run.py mujoco
```

For an agent or a machine without a desktop:

```bash
python3 simulation/run.py mujoco --headless --steps 240 --screenshot
```

The launcher creates a Python 3.11 environment with MuJoCo 3.6.0, prepares the composed
model and opens the native viewer. The fixed arm sweeps gently while all four finger
groups flex. The orange marker identifies the wrist-to-hand mounting plane. Close the
viewer to finish early, or use `--steps 14400` for a longer session.

Headless motion testing without `--screenshot` does not create an OpenGL context.
Screenshots use EGL and require compatible graphics libraries. A successful run writes
`build/simulation/results/mujoco.json` and, if requested, `mujoco.png`.

## What the example does

[`demo.py`](demo.py) contains three labeled sections:

1. Load `build/simulation/generated/openarm_manual_dex.xml` with
   `mujoco.MjModel.from_xml_path`; assert that the combined articulation has 15 joints.
2. Resolve joints by name, assign the shared trajectory to `data.joint(name).qpos`,
   clear velocities and call `mj_step` / `mj_forward`.
3. Read back all joint positions, check them against the target and save the result.

The native model keeps the CAD component colors and articulation hierarchy. OpenArm's
stock gripper has been removed. The mount is specified in [`../mount.json`](../mount.json),
not a visual-only offset applied after simulation.

## Load in your own program

After `python3 simulation/run.py prepare`, from the repository root:

```python
import mujoco

model = mujoco.MjModel.from_xml_path("build/simulation/generated/openarm_manual_dex.xml")
data = mujoco.MjData(model)
data.joint("md_index_proximal").qpos[0] = 0.3
mujoco.mj_forward(model, data)
```

For the gripper alone, load `models/manual_dex/hand/scene.xml` (original native frame,
joint names without `md_`) or `models/manual_dex/urdf/manual_dex.urdf` (flange-rooted,
`md_` joint names). The URDF includes MuJoCo mesh-path settings so it can be loaded directly.

## Adding a controller

The tutorial sets state directly; it is not torque control. For a control experiment,
add actuators to the assembled MJCF, set gains/limits from identified hardware data,
write actuator targets through `data.ctrl` and let `mj_step` evolve the state instead
of assigning `qpos` every step. `mj_forward` alone performs kinematics, not time integration.
Keep the hand's [model limitations](../README.md#6-from-playback-to-dynamics-and-control) in mind.

## Troubleshooting

- **Missing mesh / LFS pointer:** run without `--no-setup` to retrieve the required LFS objects.
- **GLFW cannot open display:** use `--headless`; omit `--screenshot` for a non-rendering test.
- **EGL error:** verify your graphics driver and EGL libraries; a numerical smoke test
  still works without screenshots.
- **Hand mount looks wrong for your arm:** this example targets OpenArm v1. Adjust the
  mount and rebuild; do not treat a v2 or OpenArmX mount as interchangeable.

References: [MuJoCo Python API](https://mujoco.readthedocs.io/en/3.6.0/python.html),
[MJCF compiler settings](https://mujoco.readthedocs.io/en/3.6.0/XMLreference.html#compiler),
[official OpenArm models](https://github.com/enactic/openarm_mujoco).
