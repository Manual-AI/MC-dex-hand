# Four-engine comparison in one visualization environment

![Synchronized 2×2 comparison: MuJoCo and Genesis above SuperDex and Isaac Sim, sharing the same OpenArm and Manual-Dex scene](../docs/assets/simulation/all-engines.gif)

| Top-left: MuJoCo | Top-right: Genesis |
|---|---|
| [MJCF setup and tutorial](mujoco/README.md) · [LeRobot setup](../lerobot/README.md#1-first-run-one-command-no-hardware) | [URDF setup and tutorial](genesis/README.md) · [LeRobot setup](../lerobot/README.md#1-first-run-one-command-no-hardware) |
| **Bottom-left: SuperDex** | **Bottom-right: Isaac Sim** |
| [Runtime/debugger setup and tutorial](superdex/README.md) · [LeRobot setup](../lerobot/README.md#1-first-run-one-command-no-hardware) | [URDF-to-USD setup and tutorial](isaacsim/README.md) · [LeRobot setup](../lerobot/README.md#1-first-run-one-command-no-hardware) |

Each panel shows the same connected OpenArm v1 + Manual-Dex robot, under identical
camera, lighting, floor and labeling. The single GIF keeps all four panels on the
same frame clock: **100 frames, 20 fps, five seconds**. Labels remain visible and
use one fixed GIF palette. Separate panels are also embedded in the main README
with their setup links directly underneath each image.

## What is actually being compared?

All four engines ran their own model imports and 1,200 simulation steps at 240 Hz.
Each recorded its **actual post-step joint readbacks** every 12 steps. The renderer
uses those 15 named coordinates to pose the shared native MJCF scene. It does not
substitute requested target coordinates for observed engine states.

This is a **shared-renderer kinematic comparison**, not a claim that MuJoCo, Genesis,
SuperDex and Isaac Sim have identical native renderers. In particular, the Isaac
panel uses actual PhysX joint states but is **not** an RTX screenshot. Native Isaac
rendering failed at startup on the test machine; see [VALIDATION.md](VALIDATION.md).
SuperDex's post-step states can differ from its prescribed targets. This comparison
shows those readbacks without establishing calibrated dynamics or exact tracking.

Gravity and contacts are disabled. The floor is added only to the visualization;
it is not a validated physical contact surface. The animation is a playback
comparison, not a live four-engine dashboard or a simultaneous LeRobot session.
Sample labels denote trajectory sample time; each readback follows its 1/240-second step.

## Regenerate from actual engine runs

From the root, run each engine with trace collection. The launcher handles dependencies
and model setup. Review NVIDIA's terms before the Isaac acceptance flag:

```bash
python3 simulation/run.py mujoco --headless --steps 1200 --trace
python3 simulation/run.py genesis --headless --steps 1200 --trace
python3 simulation/run.py superdex --headless --steps 1200 --trace
python3 simulation/run.py isaacsim --accept-isaac-eula --headless --steps 1200 --trace
build/simulation/envs/prepare/bin/python simulation/comparison.py
```

Rendering requires a working EGL/OpenGL stack and DejaVu Sans fonts (Ubuntu package
`fonts-dejavu-core`). The engine motion tests themselves do not require this shared
renderer. `--preview` renders just the first frame into
`build/simulation/results/comparison-preview.png` without replacing release GIFs.

[`comparison.py`](comparison.py) checks successful 1,200-step reports, matching run IDs,
all 15 joint names and the expected 100 sample indices. An old trace paired with a new
report is rejected; rerun that engine with `--trace`. Outputs are five GIFs under
`docs/assets/simulation/` plus [provenance.json](../docs/assets/simulation/provenance.json),
which records versions, run IDs, trace hashes and the shared-renderer disclosure.
The source traces remain in ignored `build/simulation/results/`.

Manual-Dex model and OpenArm source notices still apply; see
[THIRD_PARTY.md](THIRD_PARTY.md) and the [licensing scope](../LICENSING.md).
