# OpenArm + Manual-Dex in Isaac Sim

This example imports the connected 15-joint URDF into USD, fixes the OpenArm base,
initializes a PhysX articulation, and plays arm and finger motion by joint name.
It targets **Isaac Sim 5.1.0 and Python 3.11** on Linux x86-64.

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

`--screenshot` deliberately enables the renderer. **Local validation passed the numerical
test, but both GUI and screenshot startup crashed in NVIDIA's renderer before model
import on the test machine.** Rendering is therefore not claimed as verified here.
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
