# Glove-to-hand joint calibration

This procedure calibrates **eight glove potentiometers into eight named hand joint
angles**. It does not identify servo registers, move motors automatically, find hard
stops, calibrate an arm or estimate wrist pose. Begin in simulation.

## 1. Joint convention

All angles are in radians in the CAD-derived URDF/MJCF frames. Each distal coordinate
is relative to its proximal link, not a global fingertip orientation.

| Finger group | Proximal channel / joint | Distal channel / joint |
|---|---|---|
| Index | `md_index_proximal` | `md_index_distal` |
| Middle | `md_middle_proximal` | `md_middle_distal` |
| Ring + little (coupled group) | `md_pinkyring_proximal` | `md_pinkyring_distal` |
| Thumb | `md_thumb_proximal` | `md_thumb_distal` |

The serial message and JSON calibration use these names. LeRobot appends `.pos` to
each action/observation feature. Inspect the [model joint records](../models/manual_dex/README.md)
and actual assembly before assigning wires to names. The physical ESP32 ADC pin map
must be provided by the hardware maintainer; it is not inferred from mesh order.

## 2. Synthetic smoke test

```bash
python3 lerobot/run.py mujoco
```

This creates a `kind: synthetic` mapping at
`build/lerobot/calibration/synthetic-glove.json`. Raw values 500–3500 and flexion
0.55/0.78 rad are **display examples**, not measured potentiometer or HLS3606 travel.
The serial-glove adapter and physical-hand adapter reject synthetic calibration.

The stock calibration CLI can also create a separately named synthetic map:

```bash
build/lerobot/env/bin/lerobot-calibrate \
  --teleop.type=manual_dex_glove --teleop.id=synthetic-check \
  --teleop.calibration_dir=build/lerobot/metadata \
  --teleop.source=synthetic \
  --teleop.mapping_file=build/lerobot/calibration/synthetic-check.json
```

Calibration files are created exclusively: an existing file is never silently
overwritten. Keep previous measurements and select a new filename when recalibrating.

## 3. Real glove → virtual hand

1. Implement and verify the read-only glove stream in [PROTOCOL.md](PROTOCOL.md).
   Verify all eight channels, stable device ID, sample counters and ADC ranges without
   any powered hand attached. Serial ports are never auto-discovered.
2. Make a local copy of [reference.example.json](configs/reference.example.json).
   Keep `kind` as `virtual`, review the two simulated reference poses, and set
   `reviewed` to `true` only after verifying the intended joint correspondence.
   These need not be fully extended/closed poses: use two comfortable, reproducible
   positions with useful sensor span. The key names `open` / `closed` denote the two
   endpoints, not permission to push to mechanical stops.
3. Set the serial port and device ID to match your firmware. Run:

```bash
build/lerobot/env/bin/lerobot-calibrate \
  --teleop.type=manual_dex_glove --teleop.id=YOUR_GLOVE_ID \
  --teleop.calibration_dir=build/lerobot/metadata \
  --teleop.source=serial --teleop.port=/dev/serial/by-id/YOUR_GLOVE \
  --teleop.reference_file=build/lerobot/reference-virtual.json \
  --teleop.mapping_file=build/lerobot/calibration/YOUR_GLOVE_ID-virtual.json
```

At each prompt, hold the reviewed reference pose and press Enter. The adapter reads
20 fresh samples per channel and uses the median. It requires at least 32 ADC counts
between the two reference readings, rejects invalid values and saves the mapping.
That threshold is a basic wiring/span check, not an accuracy or noise specification.

4. After calibration, run the actual glove against the simulated hand:

```bash
build/lerobot/env/bin/lerobot-teleoperate \
  --config_path=lerobot/configs/teleop_glove_to_sim.yaml \
  --teleop.id=YOUR_GLOVE_ID \
  --teleop.port=/dev/serial/by-id/YOUR_GLOVE \
  --teleop.mapping_file=build/lerobot/calibration/YOUR_GLOVE_ID-virtual.json \
  --robot.engine=mujoco --teleop_time_s=30
```

Use `--robot.headless=true` for a numerical-only run. To change engines, set up the
engine with `lerobot/run.py` first, then override `--robot.engine`; Isaac additionally
requires explicit EULA agreement and currently has the noted local renderer limitation.

5. Move one channel at a time, then both joints within each finger group. Verify the
   correct joint, direction, neutral pose, comfortable span and repeatability at
   intermediate poses. Record residual error in radians with independently measured
   references. A two-point fit does not prove linearity, remove backlash or quantify
   hysteresis; add measured piecewise calibration if residuals require it.

## 4. Mapping equation and rejection behavior

For channel `j`, the saved row has `raw_open`, `raw_closed`, `open_rad`, `closed_rad`:

```text
u = clamp((raw - raw_open) / (raw_closed - raw_open), 0, 1)
q_rad = open_rad + u * (closed_rad - open_rad)
```

This handles reversed potentiometer wiring and reversed angle conventions without
swapping joint names. All eight rows must be present. Missing/extra channels, NaNs,
infinities, values outside 0–4095, a wrong device ID, insufficient span or repeated/
out-of-order samples are rejected. A missing fresh sample times out (default 250 ms).
The simulation adapter also clips travel to ±1.5 rad and limits rate; those are
conservative display bounds, **not** identified physical safety limits.

## 5. Physical hand calibration is a separate gate

Before using `kind: measured`, a qualified hardware integrator must establish each
servo's encoder-to-CAD-radian conversion, mechanical direction/offset, safe soft
travel and rate limits on the actual assembly. Use two independently measured matched
glove/hand reference poses; keep fingers clear and follow the verified controller's
safe measurement procedure. Do not use unpowered backdriving unless the hardware
manufacturer permits it, and never discover limits by commanding into hard stops.

Store the measured reference and hand profile per device. Recalibrate after rewiring,
reassembly, sensor replacement or a changed glove fit. Do not relabel a virtual file
as measured to bypass checks. [HARDWARE.md](HARDWARE.md) describes the remaining driver
and watchdog requirements; no physical-hand motion was used to develop these examples.
