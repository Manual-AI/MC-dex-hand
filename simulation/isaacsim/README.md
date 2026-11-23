# OpenArm + Manual-Dex in Isaac Sim

## Native PhysX and RTX showcase — Isaac Sim 6.0.1

After agreeing to NVIDIA's [Omniverse terms](https://docs.omniverse.nvidia.com/platform/latest/common/NVIDIA_Omniverse_License_Agreement.html):

```bash
python3 simulation/run.py isaacsim --native --headless --accept-isaac-eula
```

This profile uses **Isaac Sim 6.0.1 and Python 3.12** in the separate
`build/simulation/envs/isaacsim-native/` environment. It preserves the older 5.1
environment used by the existing playback and LeRobot workers. Review the
[6.0.1 requirements](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/installation/requirements.html)
and allow substantial download/shader-compilation time; use `--timeout 1800` if needed.
No host driver, BIOS setting or existing external environment is modified.

[`native.py`](native.py) uses the 6.x `URDFImporter`/`URDFImporterConfig` API to convert
the attached robot into USD, fixes the base, and configures PhysX force drives. After
setting the initial pose once, it sends `ArticulationAction` position targets through
the native articulation controller. Gravity and table contacts remain enabled. An
RTX camera captures the scene through Replicator RGB: no MuJoCo rendering, desktop
capture or external viewer is used.

The same five-second [scripted pick and place](../PICK_PLACE.md) runs in all engines.
Native capture success requires 100 frames, opposing finger contact during unsupported
lift/transport, and a released cube at the green destination. PhysX contact filters
identify each cube-contact counterpart. Outputs are in `build/simulation/native/`; see
[scene parameters, evidence checks and GIF publishing](../CUBE_COMPARISON.md). Replicator
capture uses zero simulation-time increments so camera capture does not advance physics.
The illustrative gains/inertias are not a calibrated grasp or hardware-control test.

The launcher removes inherited `PYTHONPATH`, `PYTHONHOME` and `LD_LIBRARY_PATH` only
from the native Isaac child process to avoid mixing ROS/system CUDA packages with Kit.
It uses NVIDIA's index and PyPI for the pinned SDK dependencies; the upstream
`tinyobjloader` dependency requires allowing its explicitly pinned prerelease.

## Original import/playback profile — Isaac Sim 5.1

The older [`demo.py`](demo.py) imports the connected 15-joint URDF into USD, fixes the OpenArm base,
initializes a PhysX articulation, and plays arm and finger motion by joint name.
It targets **Isaac Sim 5.1.0 and Python 3.11** on Linux x86-64.
All commands below omit `--native` and refer specifically to that older profile.

## 1. Requirements and one-command setup

Review NVIDIA's [hardware/driver requirements](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/requirements.html)
and [license terms](https://docs.omniverse.nvidia.com/dev-guide/latest/common/NVIDIA_Omniverse_License_Agreement.html).
You need a supported NVIDIA RTX GPU even for the provided non-rendering path. Allow
substantial disk space and first-start time for Isaac Sim, its extension cache and shaders.
The launcher does not install a GPU driver or change your system configuration.

If you agree to the terms, run from the repository root:

```bash
python3 simulation/run.py isaacsim --accept-isaac-eula
```

The flag explicitly passes EULA acceptance to the child process. **An agent must not
use it without the user's agreement.** To reuse an already-installed, already-accepted
Isaac Sim environment without changing its packages:

```bash
python3 simulation/run.py isaacsim --python /absolute/path/to/isaac-environment/bin/python
```

The setup creates a separate Python 3.11 environment, installs the pinned NVIDIA packages,
builds the OpenArm + Manual-Dex model and starts the application. It does not install ROS,
Isaac Lab or a hardware driver. Close other GPU-heavy applications if resources are tight.

## 2. Headless numerical test

```bash
python3 simulation/run.py isaacsim --accept-isaac-eula --headless --steps 1200
```

This path disables viewport startup and rendering while still importing the robot,
stepping PhysX and checking all 15 articulation coordinates. Successful output is
`build/simulation/results/isaacsim.json` with `"status": "passed"` and 15 named joints.
The converted USD package is under `build/simulation/generated/`; keep its generated
supporting files and mesh directory together when moving it.

On a working rendering stack, request an image with:

```bash
python3 simulation/run.py isaacsim --accept-isaac-eula --headless --steps 240 --screenshot
```

`--screenshot` deliberately enables the renderer. **The fresh one-command installation
and numerical test passed. Screenshot startup still crashed in NVIDIA's renderer before
model import; the existing installation also failed GUI and screenshot startup.**
Rendering for this older 5.1 profile is therefore not claimed as verified.
The native 6.0.1 profile above passed full PhysX/RTX capture on the same host.
See [the validation record](../VALIDATION.md) for hardware and driver details.

## 3. How the import and connection work

The arm and gripper are already attached by the shared builder. Do not import them as
two independent articulations or add a second floating base. The important sequence in
[`demo.py`](demo.py) is:

1. Construct `SimulationApp` **before** importing `omni`, `pxr` or Isaac core APIs.
2. Enable `isaacsim.asset.importer.urdf` and create an import configuration.
3. Fix the base, import inertias, disable self-collision and set a default USD prim.
4. Execute `URDFParseAndImportFile` on `openarm_manual_dex.urdf`.
5. Reference the generated asset beneath `/World/OpenArmManualDex`.
6. Find its `UsdPhysics.ArticulationRootAPI` prim, add a `SingleArticulation`, and reset
   the world before resolving the joint indices.
7. Play named joint targets, step the world, and read back the articulation state.

Inside an initialized Isaac Sim application, the importer call is:

```python
import omni.kit.commands

ok, config = omni.kit.commands.execute("URDFCreateImportConfig")
assert ok
config.set_fix_base(True)
config.set_make_default_prim(True)
config.set_import_inertia_tensor(True)
ok, root = omni.kit.commands.execute(
    "URDFParseAndImportFile",
    urdf_path="/absolute/path/to/build/simulation/generated/openarm_manual_dex.urdf",
    import_config=config,
    dest_path="/absolute/path/to/build/simulation/generated/openarm_manual_dex.usd",
)
assert ok
```

For another arm or tool alignment, edit [`../mount.json`](../mount.json), then run the
launcher with `--rebuild`. The gripper's standalone URDF is also included at
[`../../models/manual_dex/urdf/`](../../models/manual_dex/urdf/README.md).

## 4. Replacing playback with control

The example calls `set_joint_positions` before stepping; this is not a servo model.
Use the initialized articulation's controller with `ArticulationAction` targets when
adding a control experiment. Configure drive gains, effort limits, measured inertias,
gravity and collision properties first. The import configuration here deliberately has
zero drive strength/damping, zero gravity and disabled proxy colliders. Do not infer
grasp stability or hardware torque capability from this demo.

## 5. Troubleshooting

- **Renderer crash before the URDF importer starts:** try the numerical `--headless`
  command without `--screenshot`. Check NVIDIA's requirements and compatibility tools;
  changing the robot's joints cannot fix a renderer initialization crash. No host driver
  changes are performed by this project.
- **Missing `omni` modules:** start the application before importing engine APIs, and
  use the pinned environment rather than system Python.
- **NumPy ABI/import error:** use the provided requirements, including NumPy 1.26.0;
  do not mix this environment with the NumPy 2-based model-builder environment.
- **No articulation or default prim:** inspect `build/simulation/logs/isaacsim.log`.
  The demo checks the USD default prim and finds the articulation root instead of
  assuming an importer-specific hierarchy.
- **Application exits with no result:** the launcher requires a fresh run-ID result,
  because Kit shutdown can otherwise hide a Python failure behind a zero exit status.
- **First start exceeds the time limit:** retry with `--timeout 1800`; cached models and
  environments can be reused with `--no-setup`.

Sources: [Python installation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_python.html),
[URDF importer](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/importer_exporter/import_urdf.html),
[importer API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.asset.importer.urdf/docs/index.html),
[SimulationApp](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.simulation_app/docs/index.html).
