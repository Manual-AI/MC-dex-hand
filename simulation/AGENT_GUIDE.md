# Simulation checks

## Object-to-bowl checks

For a quick browser-runtime check, run `node simulation/browser/bowl/check.mjs` from the repository root with Node.js 22 or newer. This executes the shipped actor in MuJoCo WASM on a fixed, held-out barbell throw. Success prints JSON with `deposited: true` after at least one second of stable release and exits with code zero. The [policy guide](browser/bowl/README.md) documents the controls and the [paired evaluation](browser/bowl/evaluation.json) separates actor-only trials from inference with physics preview.

After changing the interactive app, [rebuild the standalone HTML](browser/bowl/README.md#rebuild-the-standalone-file) and check a throw in each controller mode offline.

For the programmed montage, use the [native capture commands](bowl_showcase/README.md). Each adapter writes `capture.json` beside its native frames. Match `sceneSha256` across runs, verify 130 frames and inspect `liftHeightM`, `peakWindowN` and the final brick pose. The [published results](../docs/assets/simulation/bowl/results.json) and [time series](../docs/assets/simulation/bowl/forces.csv) are generated from those records.

## Cube tutorial and joint playback

Use the [simulation setup guide](README.md#1-prerequisites) to check the Linux x86-64
host and install dependencies. Run one launcher at a time per checkout. Each launch
creates a run ID and checks that its result has the same ID before returning success.

The machine-readable inputs are the [pinned OpenArm revision and Python versions](versions.json),
[scene parameters](native_scene.json), and [controller waypoints](pick_place.json).


## Run one engine

For the scripted, contact-driven pick and place, choose an engine in the
[four-engine guide](README.md#native-physics-and-capture). Running the command with
`--native --headless` also captures frames and requires the engine’s offscreen renderer.
For a fresh Isaac Sim installation, review and accept NVIDIA’s terms before using
`--accept-isaac-eula`. See the [Isaac Sim guide](isaacsim/README.md).

For a numerical import and joint-playback check, run from the repository root.

```bash
python3 simulation/run.py mujoco --headless --steps 1200
```

The launcher also accepts `genesis`, `superdex`, and `isaacsim`. To reuse an
already accepted Isaac Sim playback environment, pass
`--python /absolute/path/to/isaac-env/bin/python`. After initial setup, `--no-setup`
reuses cached dependencies and generated models. The default engine timeout is 900 seconds.

## Verify the result

Paths below are relative to `build/simulation/`. Replace `<engine>` with the launcher name.

| Run | Result file | What to check |
|---|---|---|
| Native pick and place | `native/<engine>.json` | `status == "passed"`, `pick_place.passed == true`, `native_rendering == true`, and `frames == 100`. Inspect `capture_dir` for this run’s frames and `physics.json`. |
| Joint playback | `results/<engine>.json` | `status == "passed"`, `joint_count == 15`, the requested number of `steps`, and `max_readback_error_rad <= 0.03`. |

Report the engine, run ID, mode and result from the invocation that exited successfully.
After a failure, an earlier result file can still exist. Inspect `logs/<engine>-native.log`
for the pick and place or `logs/<engine>.log` for playback. The [pick-and-place criteria](PICK_PLACE.md)
define grasp, transport and release. The [validation record](VALIDATION.md) lists previously tested environments.
