# Simulation validation record

Recorded **2026-09-08** on Ubuntu 24.04 x86-64, 64 GB RAM, NVIDIA RTX 5090 Laptop
(24 GB VRAM), NVIDIA driver 595.84. These are observed tests on this machine, not
compatibility guarantees for every GPU, operating system or future engine release.

## Native physics and rendering

All four engines completed **1,200 physics steps at 240 Hz** with gravity, native
joint drives and table contacts, producing **100 native camera frames at 20 fps**.
The same OpenArm + Manual-Dex geometry, camera pose/FOV, targets and table/cube layout
were used. Native lighting/material response differs between renderers.

| Engine | Environment | Native physics | Native rendering |
|---|---|---|---|
| MuJoCo 3.6.0 | Python 3.11 | 15 moving joints; cube settles on table | MuJoCo EGL, 100 frames |
| Genesis 1.0.0 | Python 3.11, CPU physics | 15 moving joints; cube settles on table | Genesis rasterizer, 100 frames |
| SuperDex 1.0.0 | Python 3.12 | 15 moving joints; cube settles on table | SuperDex SDK offscreen Polyscope viewer, 100 frames |
| Isaac Sim 6.0.1.0 | Separate Python 3.12 environment, Torch 2.11.0 | PhysX force drives; 15 moving joints; cube settles on table | Native RTX / Replicator RGB, 100 frames |

Each run uses the initial joint pose once, then sends drive targets rather than
overwriting joint positions/velocities at every step. The acceptance checks require
finite readbacks, more than 0.015 rad of motion on every commanded joint, at least
100 measured cube-contact steps, initial falling motion, a final cube center between
0.015 and 0.07 m above the tabletop, and exactly 100 frames/state samples.
The successful captures recorded over 1,140 contact steps each.

Isaac additionally checks the physics clock: its 1,200-step run advanced approximately
5.00000026 seconds. Replicator capture advances the timeline by zero seconds, so
render warmup and capture do not add physics time. Native-resolution DLAA avoids
half-resolution DLSS upscaling at this small capture size.

The demonstration is **reach-and-flex with a falling cube, not pickup or grasping**.
Hand mass/inertia and gains are illustrative and declared in
[`native_scene.json`](native_scene.json); friction/contact settings are in each engine's
`native.py`. Robot/environment contacts are enabled;
robot self-collisions are disabled. These checks do not establish physical servo
performance, payload, grasp stability, measured collision accuracy or hardware safety.

## Native montage and GIF checks

The [comparison publisher](comparison.py) accepts only successful native manifests,
checks their capture-directory identity and expected frame/sample counts, and loads
each engine's actual PNGs. It adds labels and makes the 2×2 layout with PIL; it does
not import a 3D renderer or re-render another engine's states in MuJoCo.

The [published provenance](../docs/assets/simulation/provenance.json) records engine
versions, renderer names, run IDs, frame/state SHA-256 hashes and scene settings.
Native first/midpoint frames and the montage were inspected. The title GIF and paired
CAD illustration retain their original four- and ten-second durations; the native
engine panels and synchronized montage are each five seconds. All seven GIFs are
checked against [half-size byte budgets](../docs/assets/gif-size-budget.json).
The fixed component register in the compressed paired GIF is pixel-identical across
all 200 decoded frames.

Reproduce from the repository root, after reviewing the prerequisites and NVIDIA terms:

```bash
python3 simulation/run.py mujoco --native --headless
python3 simulation/run.py genesis --native --headless
python3 simulation/run.py superdex --native --headless
python3 simulation/run.py isaacsim --native --headless --accept-isaac-eula
build/simulation/envs/prepare/bin/python simulation/comparison.py
build/simulation/envs/prepare/bin/python -m unittest discover -s simulation -v
```

Native manifests and full state readbacks remain in ignored `build/simulation/native/`;
logs are `build/simulation/logs/<engine>-native.log`. The launcher requires a fresh
matching run ID and does not count an older successful result after a failed run.

## Isaac runtime separation and historical failure

The original Isaac Sim **5.1.0 / Python 3.11** environment passed the numerical
zero-gravity playback test, but native RTX startup segfaulted in
`librtx.scenedb.plugin.so`. The failure was reproduced with inherited ROS/CUDA library
paths removed. Disabling viewport startup could avoid activating the failing RTX
path, but did not produce a usable native camera capture.

The native showcase instead uses **Isaac Sim 6.0.1 / Python 3.12**, installed separately
under `build/simulation/envs/isaacsim-native/`. All 166 installed packages passed
`uv pip check`; its new URDF importer and RTX capture completed on the same host
without changing GPU drivers, BIOS settings or unrelated processes. The older
environment remains available for the original playback/LeRobot paths.
NVIDIA's [5.1 driver-compatibility discussion](https://github.com/isaac-sim/IsaacSim/issues/619)
and [6.0.1 installation instructions](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/installation/install_python.html)
provide upstream context. This is not a promise that upgrading fixes every renderer failure.

## Model and regression checks

`simulation/check.py` passed these checks:

- The composed URDF has 15 moving joints and one root; the standalone hand has eight.
- Every link has a complete visual and all referenced meshes exist, not LFS pointers.
- Serialized collision proxies are watertight with finite positive volume.
- MuJoCo loads the composed MJCF, composed URDF and standalone hand URDF.
- All joint names match and example targets stay within the model's bounds.
- MJCF/URDF joint-body world positions and rotations agree at four poses within
  2 × 10⁻⁷ absolute tolerance.

The tolerance checks coordinate conversion, not CAD-to-hardware calibration. The
native-demo builder creates a separate dynamic asset package, leaving the released
models and the original zero-gravity playback examples unchanged.

Two offline vendor-checkout regression tests passed, including preservation of
locally modified vendor files. Native tests cover timing/trajectory, scene geometry,
forbidden cross-engine MuJoCo imports, rejection of incomplete/motionless/contactless
captures, GIF byte/duration budgets and static-label stability. All 32 existing
LeRobot unit tests also passed in its isolated environment with inherited ROS paths removed.

## Original playback and LeRobot coverage

The older `demo.py` examples remain import/kinematic smoke tests with zero gravity,
disabled contacts and prescribed joint positions. All four completed 1,200 steps:
MuJoCo final readback error 0 rad, Genesis and Isaac 5.1 below 6 × 10⁻⁹ rad, and
SuperDex approximately 0.00104 rad. Those values are playback checks, not controller
accuracy measurements. Their old shared-MuJoCo-renderer GIFs have been replaced by
the independently rendered native showcase.

The [LeRobot validation record](../lerobot/VALIDATION.md) covers host commands through
all four workers, glove calibration and local recording. Those workers were not
silently switched to this dynamic demonstration or the newer Isaac environment.
