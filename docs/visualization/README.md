# Manual-Dex: Visualization Methods

The glove and robot-hand figures are generated from the released CAD with MuJoCo 3.6.0.
Each GIF contains **100 frames at 20 fps, totaling exactly 5.00 seconds**, with one
360-degree camera orbit and one flexion–extension cycle. The repository retains the
original prototype demonstration separately; it is not one of these two technical GIFs.

## 1. Geometry and coordinate frames

The inputs are [`manual_dex_glove.step`](../../hardware/step/manual_dex_glove.step) and
[`manual_dex_hand.step`](../../hardware/step/manual_dex_hand.step). Open CASCADE reads the
named assembly occurrences and composes their STEP placements. This retains the current
Quest mount, bought components and repeated part instances. The reference CAD contains
86 leaf occurrences in the glove and 178 in the hand; a leaf is not necessarily a BOM
item, because bought assemblies contain internal CAD components.

Each B-rep is tessellated with 0.20 mm linear deflection and 0.25 rad angular deflection.
Face orientation and assembly transforms are retained. Mesh coordinates are converted
from millimetres to metres and rotated into a Z-up MuJoCo frame:

```text
x_world =  x_CAD / 1000
y_world = -z_CAD / 1000
z_world =  y_CAD / 1000 + 0.13
```

Generated meshes, MJCF, per-occurrence metadata and joint-axis records are written to
`build/manual-dex/{hand,glove}/`. This derived directory is ignored by Git; the STEP files,
generator source and final figures are versioned. Mechanical release STLs remain unchanged.

## 2. Articulation

Eight hinges are added to each model. For the glove, their axes are identified from
coaxial cylindrical faces on the adjacent printed components. For the robot, the
3.6 mm-radius servo-shaft clearance faces identify the axes. The generator rejects
missing or ambiguous axes and verifies a one-to-one assignment of eight servo
occurrences to the eight robot joints.

Each distal body is a child of its proximal body. Robot base-servo housings remain fixed;
distal-servo housings move with proximal links, and output arms move with the driven
body. Glove sensor bodies and cases attach to the parent of the measured joint, while
encoder pins rotate with that joint. Shared tracking, camera and enclosure components
remain fixed to the frame.

Flexion is prescribed relative to the CAD pose with a periodic raised cosine. The index,
middle and ring–little groups use amplitudes of 32° proximal and 45° distal; the thumb
uses 24° and 36°. Small phase offsets distinguish the groups. These are **illustration
parameters**, not measured travel limits. The 5.00 s seam is periodic in both camera
orientation and joint state.

The scene uses forward kinematics (`mj_forward`), not a simulated control task. Collision
response is disabled. Each moving body has a placeholder 1 g mass and diagonal inertia
of 10⁻⁶ kg·m² so the model can compile; these values are not estimates of hardware mass
or inertia. MJCF joint ranges of ±1.5 rad are display bounds, not calibrated joint limits.
Do not use this figure model as a validated dynamics or reinforcement-learning model.

## 3. Labels and materials

Twelve callout families identify the printed structure, finger links, joint hardware,
sensing or actuation, tracking assembly, camera and enclosure. Numbered labels anchor
to visible surface pixels using MuJoCo's segmentation output. A family that is fully
occluded in the current view is grayed out in the register, rather than labeled through
an unrelated component. One representative is labeled for a repeated family.

The [complete part register](PARTS.md) resolves those families into individual BOM IDs,
release filenames, quantities, material specifications and functions. Generate it from
the BOM CSVs rather than editing its tables by hand.

Muted colors distinguish structural polymer, links, contact links, joint hardware and
electronics. They are diagram conventions. The BOM specifies ABS or PETG for printed
parts; no rubber, silicone or TPU coating is asserted. The enclosure is partially
transparent to expose the CAD electronics. Purchased-part composition is not inferred
from its rendered color, and unresolved BOM materials remain TODO.

## 4. Regeneration

The reference environment is Linux, Python 3.13, MuJoCo 3.6.0 and an EGL-capable graphics
driver. Use Python 3.11 or newer, `ffmpeg`, and the DejaVu Sans / Liberation Serif fonts
installed under `/usr/share/fonts/truetype/`. No generative image model is used.

From the repository root:

```bash
git lfs pull
python3 -m venv .venv
.venv/bin/python -m pip install -r tools/visualization/requirements.txt

.venv/bin/python tools/visualization/cad.py hardware/step/manual_dex_glove.step --out build/manual-dex/glove/cad
.venv/bin/python tools/visualization/cad.py hardware/step/manual_dex_hand.step --out build/manual-dex/hand/cad

MUJOCO_GL=egl .venv/bin/python tools/visualization/render.py glove
MUJOCO_GL=egl .venv/bin/python tools/visualization/render.py hand
MUJOCO_GL=egl .venv/bin/python tools/visualization/closeups.py
.venv/bin/python tools/visualization/register.py
```

Use `render.py hand --preview` (or `glove`) to generate four inspection frames at
0, 1.25, 2.50 and 3.75 seconds. `--reuse` skips rebuilding MJCF and meshes when only
the overlay is being adjusted. After modifying CAD or the geometry/material builder,
omit `--reuse` and re-extract the CAD if needed.

The renderer checks for exactly eight joints and verifies each final GIF's frame count
and duration. The generated `scene.xml` files can also be opened with MuJoCo's viewer
for inspection, subject to the kinematic-model limitations above.

## 5. Outputs

| File | Description |
|---|---|
| [`manual-dex-glove-kinematics.gif`](../assets/manual-dex-glove-kinematics.gif) | Labeled glove orbit and flexion, 5 seconds |
| [`manual-dex-hand-kinematics.gif`](../assets/manual-dex-hand-kinematics.gif) | Labeled robot-hand orbit and flexion, 5 seconds |
| [`manual-dex-glove-linkage.png`](../images/manual-dex-glove-linkage.png) | Isolated index-finger connection diagram |
| [`manual-dex-hand-linkage.png`](../images/manual-dex-hand-linkage.png) | Isolated actuated index-finger connection diagram |
| [`PARTS.md`](PARTS.md) | Complete BOM-to-figure component and material register |

The [MuJoCo Python API](https://mujoco.readthedocs.io/en/3.6.0/python.html) and
[MJCF reference](https://mujoco.readthedocs.io/en/3.6.0/XMLreference.html) document the
rendering and model interfaces used by this pipeline.
