# Manual-Dex: Visualization Methods

The glove and robot hand are shown side by side in **one combined MuJoCo animation**,
generated from the released CAD with MuJoCo 3.6.0. The GIF contains **200 frames at
20 fps, totaling exactly 10.00 seconds**. Both views use identical camera settings,
scale and timing. Their cameras each complete a 360-degree orbit at 36°/s, half the
previous 72°/s. Finger motion retains its original five-second period, giving two
flexion–extension cycles per orbit. The original prototype demonstration is retained
separately; there are no separate glove and hand animation files in the current release.

The separate [four-engine showcase](../../simulation/COMPARISON.md) uses each engine's
own physics and renderer. This page documents only the paired CAD illustration above.

The published title and paired GIFs are compressed to less than half their previous
file sizes, retaining their original durations and on-page widths. After regenerating
the paired illustration, use the model-builder interpreter to run:

```bash
build/simulation/envs/prepare/bin/python tools/visualization/encode_gifs.py --legacy
```

The encoder preserves first-seen originals under ignored `build/gif-originals/`, so
repeated compression does not degrade the input further. For a deliberately regenerated
new original, move the corresponding backup aside before running it. Optional `gifsicle`
on PATH adds lossless frame-difference optimization. See the [compression report](../assets/legacy-gif-compression.json).

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

Generated meshes, MJCF, per-occurrence metadata and joint-axis records are first written
to `build/manual-dex/{hand,glove}/`. The renderer publishes them to
[`models/manual_dex/`](../../models/manual_dex/README.md), which is **versioned**, with
meshes stored through Git LFS. The animation loads these published models directly.
The original models were generated as **MuJoCo MJCF, not URDF**; the repository includes
the actual native model definitions rather than a different-format reconstruction.
A [derived hand URDF](../../models/manual_dex/urdf/README.md) is provided separately for
the [four-engine OpenArm tutorials](../../simulation/README.md); it is exported from
these native models and checked for equivalent kinematics.
Temporary tessellation and animation frames remain under the ignored `build/` directory.
Mechanical release STLs remain unchanged.

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
parameters**, not measured travel limits. The 10.00 s seam is periodic in both camera
orientation and joint state.

The scene uses forward kinematics (`mj_forward`), not a simulated control task. Collision
response is disabled. Each moving body has a placeholder 1 g mass and diagonal inertia
of 10⁻⁶ kg·m² so the model can compile; these values are not estimates of hardware mass
or inertia. MJCF joint ranges of ±1.5 rad are display bounds, not calibrated joint limits.
Do not use these visualization models as validated dynamics or reinforcement-learning models.

## 3. Labels and materials

Twelve callout families identify the printed structure, finger links, joint hardware,
sensing or actuation, tracking assembly, camera and enclosure. Labels prefixed **G**
(glove) or **H** (hand) anchor to visible surface pixels using MuJoCo's segmentation
output. A surface callout is omitted when the entire family is occluded, so it never
points through an unrelated component. **Every name and specification in the right-hand
register remains visible at constant contrast in every frame**, regardless of occlusion.
One representative is labeled for a repeated family. The renderer verifies that the
register is pixel-identical across all decoded GIF frames.

The [complete part register](PARTS.md) resolves those families into individual BOM IDs,
release filenames, quantities, material specifications and functions. Generate it from
the BOM CSVs rather than editing its tables by hand.

Muted colors distinguish structural polymer, links, contact links, joint hardware and
electronics. They are diagram conventions. The BOM specifies ABS or PETG for printed
parts; no rubber, silicone or TPU coating is asserted. The enclosure is partially
transparent to expose the CAD electronics. Purchased-part composition is not inferred
from its rendered color, and unresolved BOM materials remain TODO.

The Quest 3 controller on the actuated hand is a deliberate appearance-matching
component: the same controller/mount geometry is present on both embodiments to remove
that visual difference for an overhead camera. For actual use, the operator also wears
a black, fingertip-less fabric glove beneath the sensing assembly, with simple inpainting
intended to address remaining differences in the hand-camera view. These are distinct
camera-view considerations; see the [design rationale](../../README.md#why-is-there-a-quest-3-controller-on-the-actuated-hand).
The CAD renders do not include the cloth or an inpainting process and do not demonstrate
that visual differences have been eliminated.

## 4. Regeneration

The reference environment is Linux, Python 3.13, MuJoCo 3.6.0 and an EGL-capable graphics
driver. Use Python 3.11 or newer, `ffmpeg`, and the DejaVu Sans / Liberation Serif fonts
installed under `/usr/share/fonts/truetype/`. No generative image model is used.

From the repository root:

```bash
git lfs pull
python3 -m venv .venv
.venv/bin/python -m pip install -r tools/visualization/requirements.txt

# Render directly from the included MJCF and meshes; no CAD extraction required.
MUJOCO_GL=egl .venv/bin/python tools/visualization/render.py --models
```

To rebuild the native models from the STEP assemblies instead:

```bash
.venv/bin/python tools/visualization/cad.py hardware/step/manual_dex_glove.step --out build/manual-dex/glove/cad
.venv/bin/python tools/visualization/cad.py hardware/step/manual_dex_hand.step --out build/manual-dex/hand/cad

MUJOCO_GL=egl .venv/bin/python tools/visualization/render.py
MUJOCO_GL=egl .venv/bin/python tools/visualization/closeups.py
.venv/bin/python tools/visualization/register.py
```

Use `render.py --models --preview` to generate four paired inspection frames at
0, 2.50, 5.00 and 7.50 seconds. `--reuse` publishes the existing build models without
rebuilding MJCF and meshes. After modifying CAD or the geometry/material builder,
omit `--models` and `--reuse`, and re-extract the CAD if needed. A normal rebuild updates
the versioned model directories as well as the animation.

The renderer checks for exactly eight joints per device and verifies the final GIF's
frame count, duration and unchanging register. The included `scene.xml` files can also
be opened with MuJoCo's viewer; see the [model instructions](../../models/manual_dex/README.md).

## 5. Outputs

| File | Description |
|---|---|
| [`manual-dex-paired-kinematics.gif`](../assets/manual-dex-paired-kinematics.gif) | Side-by-side glove and hand, synchronized half-speed orbit, 10 seconds |
| [`models/manual_dex/`](../../models/manual_dex/README.md) | Native MJCF models, meshes, and per-part/joint records used for rendering |
| [`manual-dex-glove-linkage.png`](../images/manual-dex-glove-linkage.png) | Isolated index-finger connection diagram |
| [`manual-dex-hand-linkage.png`](../images/manual-dex-hand-linkage.png) | Isolated actuated index-finger connection diagram |
| [`PARTS.md`](PARTS.md) | Complete BOM-linked component and material register |

The [MuJoCo Python API](https://mujoco.readthedocs.io/en/3.6.0/python.html) and
[MJCF reference](https://mujoco.readthedocs.io/en/3.6.0/XMLreference.html) document the
rendering and model interfaces used by this pipeline.
