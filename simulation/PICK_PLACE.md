# Physics-driven pick and place

The native demos use an **automated scripted controller**, not a learned policy.
OpenArm approaches a 50 mm, 80 g cube, Manual-Dex closes around it, lifts it clear
of the table, carries it from the blue square to the green square, lowers it,
opens the fingers, and withdraws. Each engine supplies its own joint dynamics,
contact/friction solver, and camera renderer.

## Run it

From the repository root, choose one command:

```bash
python3 simulation/run.py mujoco --native --headless
python3 simulation/run.py genesis --native --headless
python3 simulation/run.py superdex --native --headless
python3 simulation/run.py isaacsim --native --headless --accept-isaac-eula
```

Use the Isaac acceptance flag only after agreeing to NVIDIA's terms. Prerequisites
and engine-specific instructions are linked from the [simulation guide](README.md).
After all four pass, [publish the GIFs](COMPARISON.md#one-command-setup-and-capture).
No training, dataset download, hardware connection, or interactive clicks are needed.

## Controller and timing

[`pick_place.json`](pick_place.json) contains the 15-joint reference waypoints, in
the order defined by `native_common.JOINTS`. [`targets()`](native_common.py) smoothly
interpolates them with `3u² − 2u³`. These are **position-drive references**, not
recorded poses assigned to the robot each frame. Native actuator/PD/force drives
produce the joint motion, and the free cube moves only through gravity and contact.
There is no weld, attachment, suction force, cube teleportation, or external cube force.

| Time (s) | Action |
|---|---|
| 0.00–0.35 | Cube rests on the table; open hand waits above it |
| 0.35–1.10 | Approach the cube |
| 1.10–1.80 | Close the fingers and thumb |
| 1.80–2.40 | Lift |
| 2.40–3.25 | Carry toward the green destination |
| 3.25–3.90 | Lower onto the table |
| 3.90–4.40 | Open and release |
| 4.40–5.00 | Withdraw; cube remains at the destination |

The waypoint sequence is scene-specific and open-loop at the task level; the native
joint drives provide feedback control. It is not a general grasp planner, learned
policy, or collision-aware arm planner. The thumb proximal joint is held near zero;
not every available joint needs to move to complete this grasp. Changing cube size,
source/destination, mount transform, or hand geometry requires new trajectory design
and native validation, not merely changing the success thresholds.

## What counts as success

[`validate_pick_place()`](native_common.py) evaluates all 1,200 physics readbacks,
not just the 100 rendered frames. A run cannot pass from a falling or pushed cube:

- The cube starts at rest on the table, within 3 mm of the source; table support
  must be measured during the initial settling interval.
- During 2.45–3.20 s, at least 85% of physics samples must show **both a thumb and
  a non-thumb finger exerting contact force**, no table/floor support, and a cube
  lift greater than 60 mm. The held cube must travel at least 120 mm horizontally.
- During the final 0.35 s, the cube must be within 30 mm of the destination, flat
  on the table, table-supported, free of finger contact, and moving below 50 mm/s.

The contact readbacks distinguish individual counterparts: MuJoCo `mj_contactForce`,
Genesis `get_contacts`, SuperDex `get_contact_force_from_actor_world`, and Isaac
`get_contact_force_matrix(dt=DT)`. A cube's net force alone cannot establish a pinch:
opposing finger forces can cancel in that sum.

Every capture saves `physics.json` (all steps) and `result.json` (metrics plus sampled
states) under `build/simulation/native/captures/<engine>/<run-id>/`. Failed runs retain
their physics diagnostics but cannot replace successful manifests or published GIFs.
The publisher reruns validation and rejects captures with an old scene/controller hash.

## Parameters and scope

[`native_scene.json`](native_scene.json) exposes cube mass/size, start/goal positions,
friction, camera, and drive gains. Arm gains are 1,500 / 80 and hand gains are 5 / 0.15
(stiffness / damping); drive effort limits are 150 N·m for arm joints and 5 N·m for
hand joints. These are illustrative simulation settings, **not physical servo ratings**.

MuJoCo and Genesis use implicit-fast integration and explicit joint armatures
(0.01 kg·m² arm, 0.001 kg·m² hand). Genesis's URDF loader otherwise defaults to
0.1 kg·m², which is too large for these small-finger reference dynamics. Other engines
use their own articulated solvers. Native contact and rendering responses differ;
matching the scene does not imply numerical identity.

The released CAD/URDF models are unchanged. The dynamic-demo builder uses their
per-link convex contact proxies with illustrative masses and inertias. Robot–object
and robot–environment contacts are enabled; self-collisions are disabled. Passing
this fixed simulation task is not evidence of a hardware-calibrated grasp, real payload
capacity, generalization to other objects, or safe physical execution.

See [measured validation results](VALIDATION.md) and [native rendering provenance](COMPARISON.md).
