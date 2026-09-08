# Finite simulation workflow for an agent

Read [`README.md`](README.md) and the selected engine tutorial before running commands.
This guide grants no permission to accept a license, install a system driver, alter an
existing environment, push changes, or connect physical hardware.

## Default: build and verify MuJoCo

From the repository root, the single command is:

```bash
python3 simulation/run.py mujoco --headless --steps 1200
```

It sets up isolated dependencies, obtains the pinned OpenArm model, composes the arm and
hand, checks MJCF/URDF compatibility and runs a finite numerical motion test. Omit
`--screenshot` when no renderer is available. Do not substitute a fabricated robot or
an image renderer for the actual engine.

## Other engines

```bash
python3 simulation/run.py genesis --headless --steps 1200
python3 simulation/run.py superdex --headless --steps 1200
```

For Isaac Sim, reuse an installation whose license the user has already accepted:

```bash
python3 simulation/run.py isaacsim --python /absolute/path/to/accepted/isaac-env/bin/python --headless --steps 1200
```

For a new Isaac installation, first ask whether the user agrees to NVIDIA's linked
terms in the [Isaac tutorial](isaacsim/README.md). Only after agreement, replace
`--python …` with `--accept-isaac-eula`. If agreement or supported hardware is missing,
report that limitation; do not silently accept, bypass the check or invent a passed test.

## Report the result

1. Require a zero launcher exit code. The launcher checks that JSON `run_id` belongs
   to this execution, not a previous successful run.
2. Inspect `build/simulation/results/<engine>.json`: status, 15 joint names, 1,200 steps,
   finite positions and `max_readback_error_rad` below 0.03.
3. Inspect `build/simulation/logs/<engine>.log` on failure. Renderer startup and model
   import are distinct stages; report which one failed.
4. State that this is zero-gravity, contact-disabled, prescribed joint playback—not
   validation of grasping, torque control, material properties or hardware safety.
5. Report only engines and rendering modes actually exercised. See [VALIDATION.md](VALIDATION.md).

Run one launcher per checkout at a time. A default 900-second engine timeout bounds
compilation/runtime; setup downloads can take longer. Reuse a successful cached setup
with `--no-setup` for offline operation. Do not overwrite a modified vendor checkout:
the builder intentionally stops and preserves it.
