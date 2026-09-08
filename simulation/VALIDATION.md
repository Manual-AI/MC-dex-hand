# Simulation validation record

Recorded **2026-09-08** on Ubuntu 24.04 x86-64, 64 GB RAM, NVIDIA RTX 5090 Laptop
(24 GB VRAM), NVIDIA driver 595.84. This records observed tests, not compatibility with
every Linux distribution, GPU or future engine release.

## Model checks

`simulation/check.py` verifies:

- The composed URDF has 15 moving joints and one root; the standalone hand has eight.
- Every link has one complete visual, and every referenced mesh exists locally and is
  a real asset rather than an unresolved Git LFS pointer.
- Serialized collision proxies are watertight with finite positive volume.
- MuJoCo loads the native composed MJCF, composed URDF and standalone hand URDF.
- All 15 joint names match, and the example targets remain inside the model's bounds.
- MJCF and URDF joint-body world positions and rotation matrices agree at four
  articulated poses, with an absolute numerical tolerance of 2 × 10⁻⁷.

These checks passed. The tolerance verifies coordinate conversion; it is not a statement
about the accuracy of CAD-to-hardware calibration.

Fresh download of the pinned OpenArm checkout, model generation and checks also passed.
Two offline regression tests exercise first-clone/reuse behavior and preservation of
locally modified vendor files (`simulation/test_prepare.py`).

## Engine runs

Each engine completed **1,200 steps at 240 Hz**, five simulated seconds, with the attached
arm and gripper. Results include a fresh launcher run ID, 15 finite named joint positions,
and `"dynamics_validated": false`.

| Engine | Environment | Numerical playback | Rendering coverage |
|---|---|---|---|
| MuJoCo 3.6.0 | Clean launcher-managed Python 3.11 environment | Passed; final readback error 0 rad | EGL screenshot generated and inspected |
| Genesis 1.0.0 | Clean launcher-managed Python 3.11, Torch 2.12.0; CPU backend | Passed; final error < 6 × 10⁻⁹ rad | Headless raster screenshot generated and inspected |
| SuperDex 1.0.0 | Clean launcher-managed Python 3.12 environment | Passed; final error ≈ 0.00104 rad | Headless test does not exercise debugger rendering |
| Isaac Sim 5.1.0 | Clean launcher-managed Python 3.11 environment; existing installation also tested | Passed; final error < 6 × 10⁻⁹ rad | Screenshot startup failed in both environments; GUI startup also failed in the existing environment |

The Genesis GPU backend is provided but was not exercised in this record. Initial Isaac
tests reused an existing, already-accepted installation without modifying it. After
explicit user approval of NVIDIA's EULA, the complete one-command installer was also
tested in a new `build/simulation/envs/isaacsim/` environment:

```bash
python3 simulation/run.py isaacsim --accept-isaac-eula --headless --steps 1200
```

The fresh installation and 1,200-step run passed. Its resolved stack includes Python
3.11.15, Isaac Sim 5.1.0.0, NumPy 1.26.0 and Torch 2.7.0. All 140 installed packages
passed `uv pip check`. Existing environments, system Python and GPU drivers were not
modified. The isolated environment is a fresh install, not a cold-cache download test;
the installer may reuse locally cached package wheels.

SuperDex's debugger connected successfully but remained in its default paused state;
the full-duration validation above used headless mode, not interactive playback.

The Isaac renderer failure was a segmentation fault in `librtx.scenedb.plugin.so` during
startup. The screenshot crash was reproduced in the fresh installation as well as the
existing one. The exact driver/runtime cause has not been established. Numerical headless
operation works with rendering disabled; adding `--screenshot` re-enables the failing
path on this machine. The example and tutorial retain the normal rendered path for a
compatible installation, but it is not presented as locally verified.

## Reproduce

For the README comparison, all four 1,200-step tests were also rerun with `--trace`.
Each produced 100 actual post-step samples with 15 finite named coordinates. The
[comparison renderer](COMPARISON.md) validated trace/report run IDs and generated
four panel GIFs plus a single synchronized 2×2 GIF, each 100 frames and exactly five
seconds. First and midpoint frames were visually inspected. These use one shared
MuJoCo renderer; they do not extend the native rendering coverage above.

The separate [LeRobot validation record](../lerobot/VALIDATION.md) covers real-time
host commands through all four engine workers, calibration and local recording.

From the repository root, after reviewing the prerequisites and NVIDIA terms where relevant:

```bash
python3 simulation/run.py prepare
build/simulation/envs/prepare/bin/python simulation/check.py
python3 simulation/run.py mujoco --headless --steps 1200 --screenshot
python3 simulation/run.py genesis --headless --steps 1200 --screenshot
python3 simulation/run.py superdex --headless --steps 1200
python3 simulation/run.py isaacsim --python /absolute/path/to/accepted/isaac-env/bin/python --headless --steps 1200
```

Use `--accept-isaac-eula` instead of `--python …` only if the user has agreed to the terms
and wants a new launcher-managed Isaac installation. Inspect both the launcher exit code
and the current JSON result; historical files can remain after a failed run.

## What this does not validate

The tests do not establish physical masses/inertias, hardware joint travel, servo torque,
closed-loop tracking, friction, grasp stability, collision accuracy, mount strength or
safe hardware operation. Zero gravity, disabled contact and prescribed joint playback
are intentional. SuperDex's small nonzero post-step readback error is included rather
than described as exact tracking. The acceptance threshold of 0.03 rad is only a gross
integration smoke check.
