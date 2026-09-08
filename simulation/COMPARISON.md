# Native four-engine simulation

<img src="../docs/assets/simulation/all-engines.gif" alt="Synchronized native MuJoCo, Genesis, SuperDex and Isaac Sim tabletop simulations" width="1160">

| MuJoCo | Genesis |
|---|---|
| [Setup and tutorial](mujoco/README.md) | [Setup and tutorial](genesis/README.md) |
| **SuperDex** | **Isaac Sim** |
| [Setup and tutorial](superdex/README.md) | [Setup and tutorial](isaacsim/README.md) |

Each engine imports the connected OpenArm + Manual-Dex robot, runs its own physics,
and renders its own camera. The montage only labels and combines those captured images;
it never re-poses another engine's states in MuJoCo.

## Scene and motion

The common [scene specification](native_scene.json) defines metres, gravity, camera,
table dimensions, a loose 60 mm cube, joint-drive gains and a five-second target cycle.
All engines use 1,200 physics steps at 240 Hz and capture 100 frames at 20 fps.
The arm reaches through a gentle sweep while all eight finger joints open and close.
The cube falls under gravity and settles on the table. **This is not a grasp demonstration.**

| Engine | Physics/control | Native capture |
|---|---|---|
| MuJoCo | Position actuators, implicit integration, gravity/contact | MuJoCo EGL renderer |
| Genesis | PD joint drives, rigid-body gravity/contact | Genesis rasterizer |
| SuperDex | Articulated pose controller, gravity/contact | SuperDex SDK offscreen viewer, built on Polyscope |
| Isaac Sim | PhysX force drives, gravity/contact | Isaac Sim RTX renderer and Replicator RGB |

Joint positions are assigned only for the initial condition. During playback each
engine evolves its own state from drive targets; it is not teleported to the command
at every step. Robot/environment contacts are enabled; robot self-collisions are
disabled. Lighting and material response differ between native renderers, while
geometry, camera pose/field of view, scene layout and target timing are matched.

Illustrative hand masses, inertias and gains are explicit in the specification;
friction/contact settings are set in each engine's `native.py`.
They are not measured hardware parameters or evidence of payload, grasp stability,
servo performance or safe physical operation. The generated dynamic-demo package
is separate from the released CAD-derived models and the older zero-gravity playback examples.

## One-command setup and capture

From the repository root, run in this order. Each command installs its own isolated
dependencies, prepares the robot, runs the full native environment, and validates
its capture. Review NVIDIA's terms before using the final acceptance flag.

```bash
python3 simulation/run.py mujoco --native --headless
python3 simulation/run.py genesis --native --headless
python3 simulation/run.py superdex --native --headless
python3 simulation/run.py isaacsim --native --headless --accept-isaac-eula
```

Then publish the compressed panel GIFs and synchronized montage:

```bash
build/simulation/envs/prepare/bin/python simulation/comparison.py
```

Publishing uses Pillow from the prepare environment and DejaVu Sans fonts (Ubuntu
package `fonts-dejavu-core`). Optional `gifsicle` improves lossless compression.

Use `--no-setup` after the first setup for cached/offline runs. These captures need
working native graphics backends even with `--headless`; that flag means no desktop
window, not no rendering. EGL is used for the first three engines; Isaac requires
a compatible NVIDIA RTX runtime. The [engine tutorials](README.md) cover dependencies.

## Evidence and reproducibility

A successful launcher run must have a fresh run ID, exactly 100 native PNG frames,
100 post-step state samples, finite positions for all 15 joints, motion on every
commanded joint, a falling cube, and measured cube/table contact with a settled final height.
Captures and full state records stay under `build/simulation/native/captures/<engine>/<run-id>/`.
The current successful manifest is `build/simulation/native/<engine>.json`.
Preview/physics-only diagnostic runs cannot replace it.

[`comparison.py`](comparison.py) checks manifest identity, joint names, timestep,
frame dimensions and sample indices before publishing. It uses PIL for labels and
image composition, not a simulator. [Provenance](../docs/assets/simulation/provenance.json)
records engine versions, renderer names, run IDs, frame/state hashes and scene parameters.
The montage has one synchronized clock; separate README GIFs can start loading independently.

All seven repository GIFs have an enforced byte budget of **at most half their previous size**.
Their original durations and on-page display widths are retained. Fixed palettes and
optional lossless Gifsicle optimization keep static labels stable.
See the [size baseline](../docs/assets/gif-size-budget.json),
[showcase compression report](../docs/assets/simulation/compression.json), and
[title/paired-diagram report](../docs/assets/legacy-gif-compression.json).
Regenerate the original paired diagram with its [own workflow](../docs/visualization/README.md),
then run `tools/visualization/encode_gifs.py --legacy` with the prepare interpreter.

Native physics smoke tests do not constitute calibrated hardware validation.
See [the validation record](VALIDATION.md), [third-party notices](THIRD_PARTY.md)
and [licensing scope](../LICENSING.md).
