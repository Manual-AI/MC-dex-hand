# SuperDex: OpenArm v1 with Manual-Dex

## Native physics and rendered showcase

```bash
python3 simulation/run.py superdex --native --headless
```

[`native.py`](native.py) runs SuperDex's articulated pose controller, gravity and native
contacts, then captures the scene through **SuperDex's bundled Polyscope viewer** using
its offscreen EGL backend. No debugger clicks, desktop recording or MuJoCo rendering
are involved. This is the SDK viewer, not the separate Mochi renderer/server.

The URDF's visual CAD meshes are converted to the GLB/Y-up convention expected by the
SDK visual-model registry. SuperDex's actual link transforms drive those visuals;
collision hulls are not substituted for the visible assembly. Pose-controller gains
are indexed by link, including a zero-gain fixed root, while targets use the 15-DoF order.

The five-second [scripted pick-and-place scene](../PICK_PLACE.md) requires opposing
finger contact during lift/transport, then release at the green destination.
Per-counterpart contact forces distinguish a grasp from a dropped or pushed cube.
Captures and readbacks are under `build/simulation/native/`.
See [shared scene, validation and GIF publishing](../COMPARISON.md). The native gains
and inertias are illustrative; this is not a calibrated grasp or hardware-control test.

The sections below retain the simpler zero-gravity import/playback and debugger example.

## Run

```bash
python3 simulation/run.py superdex
```

For a finite, non-GUI validation:

```bash
python3 simulation/run.py superdex --headless --steps 240
```

The launcher creates a **Python 3.12** environment with SuperDex 1.0.0. The interactive
path opens and attaches the SuperDex Physics Debugger. **It starts paused:** select the
scene and press its Play button to begin motion. Select the robot and orbit its camera
to inspect the arm and fingers. The headless path steps the same articulation without
attaching the debugger and writes `build/simulation/results/superdex.json`.

Runtime import bakes collision fields on first load, which can take time. There is no
`--screenshot` option for this backend: use the debugger for visual inspection and the
JSON readback for automated testing. The installation includes native binaries; review
the upstream [installation and license notes](https://github.com/facebookresearch/project_superdex).

## What the example does

[`demo.py`](demo.py):

1. Initialize `superdex.physics`, create a scene and load the composed URDF through
   `robotics.load_bot_prefab_from_urdf_file`.
2. Change the loader's automatically inserted FREE world joint to HARD, fixing the base.
3. Map revolute-joint names to actor DOFs, then instantiate the bot.
4. Disable contact between the scene's actual contact layers for this playback example.
5. Set the actor's joint pose/velocity and step at 240 Hz; read the final pose back.

The debugger is given the **FLU** coordinate convention: X forward, Y left, Z up.
This prevents a correctly imported robot from appearing to use the wrong up axis.

## Why this URDF is prepared differently

The runtime loader uses only the **first visual and collision mesh per link** and ignores
primitive collision shapes. The exporter therefore combines *all* CAD visuals for each
rigid link into one OBJ and supplies one closed STL collision proxy. Fixed mount frames
are fused, preserving the joint transforms. Collision hull input is quantized to one
micrometre before export; the serialized meshes are checked for positive finite volume
and watertightness, avoiding degenerate float32 STL triangles.

Those convex proxies are **not** contact-validated finger surfaces. Contacts remain
disabled here. For high-quality contact work, import the URDF through SuperDex Studio,
review/remesh the detailed visual geometry and bake appropriate SDF assets offline.
Save the result as a native `.superdex_bot`; do not mistake on-the-fly proxy baking for
validated tactile simulation.

## Load in your own program

After preparation:

```python
import superdex.physics as physics
import superdex.robotics as robotics

physics.initialize(num_worker_threads=0)
scene = physics.create_scene("OpenArm + Manual-Dex")
prefab = robotics.load_bot_prefab_from_urdf_file(
    "build/simulation/generated/openarm_manual_dex.urdf")
prefab.joints[0].type = physics.ArticulatedJointType.HARD
context = robotics.create_context()
bot = robotics.create_bot(scene, prefab, context)
# Add scene/controller logic, then destroy_bot and physics.shutdown on exit.
```

Replace the path with `models/manual_dex/urdf/manual_dex.urdf` to load the hand alone.
The frame origin is the hand's mounting flange; it has eight revolute DOFs.

## Controllers and troubleshooting

For a controller experiment, replace the pose teleport with a SuperDex joint-space
controller (for example `BASIC_JSC_PD`), supply identified gains/limits and apply its
computed torques before stepping. The [upstream controller example](https://projectsuperdex.com/robotics/docs/examples/)
provides the lifecycle; physical parameters still need calibration for this hand.

- **Debugger cannot connect:** use `--headless` to distinguish installation/model errors
  from a display/debugger issue. Do not report a GUI connection failure as a passed run.
- **Connected but stationary:** press Play in the debugger; its default paused state
  blocks `scene.step`. Waiting beyond `--timeout` without pressing Play fails the run.
  Headless commands never wait for this manual action.
- **Volume or SDF warning:** rebuild with the provided exporter, and check that you did
  not substitute raw, open CAD surfaces for the supplied closed collision meshes.
- **Missing parts:** retain the single merged visual per link; adding extra `<visual>`
  elements can silently drop components in this importer.

References: [runtime URDF loading](https://projectsuperdex.com/robotics/docs/examples/basic/loading_from_urdf/),
[bot loading and world joints](https://projectsuperdex.com/robotics/docs/bots/),
[Studio importing](https://projectsuperdex.com/studio/docs/bot_editor/import/).
