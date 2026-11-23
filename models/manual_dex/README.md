# Manual-Dex robot models

Original model definitions, meshes and part/joint records are licensed under
[CERN-OHL-P-2.0](LICENSE). Keep the [notice](NOTICE) with redistributed model packages;
see the [repository licensing guide](../../LICENSING.md) for scope and exceptions.

These are the **actual MJCF models and mesh assets used by the paired visualization**.
They were generated directly from the released STEP assemblies, not from URDF files.
Each model has eight articulated revolute joints. All mesh coordinates are in metres.

A [derived standalone hand URDF](urdf/README.md) with portable visual/collision meshes
is also included. The [OpenArm simulation tutorials](../../simulation/README.md) compose
the native hand with OpenArm v1 and provide one-command MuJoCo, Isaac Sim, SuperDex and
Genesis examples. The original visualization still uses the native MJCF files below.

| Model | Native definition | Geometry | Records |
|---|---|---|---|
| Instrumented glove | [glove/scene.xml](glove/scene.xml) | [86 CAD-occurrence meshes](glove/meshes/) | [Parts](glove/parts.json), [hinge axes](glove/joints.json) |
| Actuated hand / gripper | [hand/scene.xml](hand/scene.xml) | [178 CAD-occurrence meshes](hand/meshes/) | [Parts](hand/parts.json), [hinge axes](hand/joints.json) |

The mesh filenames are occurrence IDs, including bought-component internals and repeated
parts. `parts.json` maps each relative `mesh` path to its original CAD name, assembly
path, component family, moving body and material-display class. `source_cad_mesh` records
the intermediate tessellation filename, which is not needed to load the model.
Its original CAD coordinates are in
millimetres; `joints.json` also records axes in the source CAD frame. The model geometry
is transformed to metres and Z-up as described in the [methods](../../docs/visualization/README.md).
Actual BOM materials and specifications are listed in the
[complete part register](../../docs/visualization/PARTS.md).

## Load or inspect

Fetch mesh files with `git lfs pull`. From the repository root, with the visualization
dependencies installed:

```bash
.venv/bin/python -m mujoco.viewer --mjcf=models/manual_dex/glove/scene.xml
.venv/bin/python -m mujoco.viewer --mjcf=models/manual_dex/hand/scene.xml

# Reproduce the one side-by-side animation directly from these models.
MUJOCO_GL=egl .venv/bin/python tools/visualization/render.py --models

# Run the model checks without a graphics context.
.venv/bin/python tools/visualization/check_models.py

# Also verify the combined GIF's timing, static register and unclipped viewports.
.venv/bin/python tools/visualization/check_models.py --animation
```

Use the viewer's joint controls to inspect articulation. The MJCF definitions do not
contain controllers or an animation trajectory; the renderer prescribes joint positions
with `mj_forward`. The two native models provide synchronized, equal-scale views in one
combined GIF rather than separate animations.

## Scope and limitations

These are **kinematic visualization models**, not validated simulation-ready robot models.
Gravity and collision response are disabled. The moving-body masses (1 g), diagonal
inertias (10⁻⁶ kg·m²), and joint bounds (±1.5 rad) are compile/display placeholders,
not measured hardware properties. Actuator dynamics, contact behavior, calibrated travel
limits and mechanical clearances have not been identified. Do not treat them as a
validated dynamics, control or reinforcement-learning environment.

The [regeneration workflow](../../docs/visualization/README.md#4-regeneration) rebuilds
both MJCF files, their meshes and records from the versioned STEP inputs. Generated
model files should be updated through that workflow rather than edited individually.
