# Render the OpenArm object-to-bowl comparison

<p align="center">
  <a href="../../docs/assets/simulation/bowl/bowl-engines.mp4"><img src="../../docs/assets/simulation/bowl/preview.gif" width="768" height="432" alt="Native views of the programmed brick transfer with vertical force traces."></a>
</p>
<p align="center">
  <a href="../../docs/assets/simulation/bowl/bowl-engines.mp4">Watch the full comparison</a><br>
  <sub>Six seconds at simulation speed, from the lift through release and settling. Each native renderer receives the same camera, geometry and arm program.</sub>
</p>

The [comparison and measurements](../COMPARISON.md) describe the compliant grasp and the meaning of the forces. The [interactive browser task](../browser/bowl/README.md) uses a learned actor and physical finger contacts. All commands below run from the repository root.

## Prepare the scene once

Use Node.js 22 or newer with ES modules and WebAssembly, and a separate Python 3.11+ environment for MuJoCo, NumPy, trimesh and Pillow. Git LFS is required for the release media. The browser model, its mesh archive and the fixed motion program are bundled in the repository.

```sh
git lfs install --local
git lfs pull
mkdir -p build/bowl-showcase
python3 -m venv build/bowl-showcase/env
build/bowl-showcase/env/bin/python -m pip install -r simulation/requirements-prepare.txt
node simulation/bowl_showcase/reference.mjs simulation/browser simulation/bowl_showcase/program.json build/bowl-showcase/reference.json
build/bowl-showcase/env/bin/python simulation/bowl_showcase/prepare.py
```

The reference script executes the programmed wrist and finger targets in the browser plant and verifies that the brick reaches the bowl. The converter writes the CAD surfaces, one initial object pose, the grasp point and the arm keyframes under `build/bowl-showcase/scene/`. It discards the subsequent reference object poses. A GPU host can reuse this generated scene directory without rebuilding it.

## Capture one engine

Use an isolated interpreter for each runtime. Each command advances the brick through the entire scripted pickup and writes 130 camera frames and a `capture.json` containing its measured trajectory and forces under `build/bowl-showcase/captures/<engine>/`. The six native runtimes were tested on Linux x86-64 with NVIDIA drivers. The render modules use NumPy and Pillow in addition to the engine packages. SuperDex also uses trimesh. The `--scene` and `--out` options accept alternate absolute paths.

| Adapter | Tested runtime and setup | Command in that environment |
|---|---|---|
| Isaac Sim | Isaac Sim 6.0.1.0, Python 3.12, PhysX and RTX. Review NVIDIA’s terms and use an accepted installation. [Setup](../isaacsim/README.md) | `python simulation/bowl_showcase/isaacsim_capture.py` |
| MuJoCo | MuJoCo 3.6.0, Python 3.11, EGL. [Environment dependencies](../mujoco/requirements.txt) | `python simulation/bowl_showcase/mujoco_capture.py` |
| Genesis | Genesis-World 1.4.6 and Torch 2.15.0, Python 3.12, offscreen rasterizer. [Genesis installation](https://genesis-world.readthedocs.io/en/latest/user_guide/overview/installation.html) | `python simulation/bowl_showcase/genesis_capture.py` |
| SuperDex | SuperDex 1.0.0, Python 3.12, Polyscope EGL. [Environment dependencies](../superdex/requirements.txt) | `python simulation/bowl_showcase/superdex_capture.py` |
| Alloy | `alloy-engine==0.1.2`, Python 3.12. Its rigid engine and path tracer use CUDA on the capture host. [Package](https://pypi.org/project/alloy-engine/) | `python simulation/bowl_showcase/alloy_capture.py` |
| Steel | SolverSteel in Newton 1.9.0.dev0, Python 3.13. In the pinned Steel checkout, use `cd examples && uv sync` to create the runtime, then use its interpreter from this repository. [Steel example environment](https://github.com/skild-ai/steel/tree/a8471c460ba7e36b1c4bb6e63eacd28e282b6e5a/examples) · [Newton revision](https://github.com/skild-ai/newton/tree/f6fc82a8b06d036e1e6d02a61d77a2d300476e8d) | `python simulation/bowl_showcase/steel_capture.py` |

An Isaac Sim installation that prompts for per-process license acceptance can run headlessly after the operator reviews and accepts NVIDIA’s terms. For that invocation, prefix the Isaac Sim command above with `OMNI_KIT_ACCEPT_EULA=YES`. The adapter itself leaves the environment setting to the operator.

For example, after installing the MuJoCo requirements in the active interpreter, run `python simulation/bowl_showcase/mujoco_capture.py --smoke`. The smoke run integrates the entire motion and writes three inspection frames under `captures/mujoco/smoke/`. A full run verifies the lift, final position, image dimensions and changing camera frames.

## Publish the montage and traces

Install FFmpeg with the H.264 encoder, and use the preparation environment. The compositor reads the native pixels, adds engine names, phase labels and force traces, and writes a 1920 × 1080 video, individual native clips, the README excerpt and the public metrics. On Linux install the DejaVu Sans fonts.

```sh
build/bowl-showcase/env/bin/python simulation/bowl_showcase/publish.py
```

The [force CSV](../../docs/assets/simulation/bowl/forces.csv) includes the time, engine, vertical interaction force, applied grasp-force magnitude and measured brick position. The [results JSON](../../docs/assets/simulation/bowl/results.json) identifies the engine versions, common scene, native frames and native state samples by SHA-256. A recorded comparison diagnoses this programmed manipulation case. Broader learned-policy performance is measured separately in the [browser evaluation](../browser/bowl/evaluation.json).
