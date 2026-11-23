# Physical Manual-Dex hand: integration gates

The software seam is included; **a working physical-hand driver is not yet included**.
The BOM specifies eight Feetech HLS3606 dual-shaft serial-bus servos, while the final
serial controller, wiring and measured travel are pending. LeRobot 0.6.1 does not list
HLS3606 in its [Feetech model tables](https://github.com/huggingface/lerobot/blob/v0.6.1/src/lerobot/motors/feetech/tables.py).
Do not configure an HLS3606 as STS3215 simply because both are Feetech servos.

## 1. Files and information the hardware maintainer must supply

| Required deliverable | Why YAML alone is insufficient |
|---|---|
| ESP32 firmware, board variant, ADC pin map and verified wiring | Provides the eight live sensor channels in [PROTOCOL.md](PROTOCOL.md) |
| Hand controller model, wiring, supply/protection details and explicit port | Determines bus access and the safe power/control path |
| Authoritative HLS3606 model ID, packet/register map, units and limits | Needed to read encoders and command the actual model; not guessed here |
| Per-hand motor IDs and encoder offsets/signs/conversion | Maps each encoder to the eight CAD-relative joint radians |
| Measured travel/rate limits and two matched glove/hand poses | Produces the device-specific profile and `kind: measured` glove mapping |
| Tested controller-side command watchdog, stop behavior and accessible E-stop | A host exception cannot guarantee stopping on host/bus failure |

Keep board-specific code, protocol sources and measurement records versioned with the
hardware release. Never place account credentials or private machine-specific data in
the repository. General example configurations are not measured calibration files.

## 2. Implement the driver interface

Start from the inert [driver template](src/lerobot_robot_manual_dex/driver_template.py).
Provide an installed `module:Class` factory taking `port` and `profile`, with:

| Method / attribute | Required behavior |
|---|---|
| `hardware_watchdog_supported = True` | Set only after a controller-side watchdog has been physically tested |
| `connect(read_only=True)` | Open the verified bus, identify expected motors, do not enable torque |
| `read_positions_rad()` | Fresh measured positions for exactly eight named joints; reject stale/invalid bus data |
| `arm(watchdog_s, hold_positions)` | Configure the real watchdog, begin from the measured current pose, then enable controlled motion |
| `send_positions_rad(positions)` | Convert reviewed CAD-relative radians to verified servo commands, with bounded I/O time |
| `stop()` | Execute the tested safe-stop behavior; idempotent, appropriate to the real mechanism |
| `disconnect()` | Close the bus; idempotent even after partial connection failure |

The factory constructor must be inert: do not connect or enable torque in `__init__`.
The adapter checks the watchdog capability before calling `connect`. `stop()` must
not assume zero angle is safe. Decide whether torque-off, holding or another strategy
is appropriate through the hardware risk assessment, not by guessing in this adapter.
This interface is software scaffolding, not a safety-certified controller.

## 3. Measure and review a per-hand profile

Copy [hand_profile.example.json](configs/hand_profile.example.json) into a local
calibration directory. Its values are deliberately `null` and `hardware_verified`
starts `false`, so the example cannot arm a hand.

For each of the eight joints, enter its unique verified `motor_id`, measured
`min_rad`, `max_rad` and `max_velocity_rad_s`. The driver must additionally store and
use verified encoder units, offsets, directions and other model-specific fields.
`hand_id` must match `--robot.id`; `servo_model` must be `HLS3606` for this adapter.
Review all values against the assembled hand before setting `hardware_verified: true`.
That boolean records a human decision; it does not itself verify hardware.

Use the [calibration procedure](CALIBRATION.md#5-physical-hand-calibration-is-a-separate-gate)
to produce a **measured** glove mapping. Both reference angles must lie inside the
reviewed hand travel. Virtual and synthetic maps are rejected by the hand adapter.
Use the exact same measured map for `teleop.mapping_file` and
`robot.glove_mapping_file`, and match `teleop.id` to the glove's device ID.

## 4. Controlled first motion, only after the gates above

Make a local copy of [teleop_hardware.yaml](configs/teleop_hardware.yaml). Replace
the glove/hand IDs, both ports, profile path, mapping paths and `driver_factory` with
the verified implementation. Leave `enable_motion: false` while reviewing and testing
read-only driver behavior. The bundled template raises `NotImplementedError` and
cannot be made operational merely by changing a flag.

Start with the hand secured, the workspace clear, no payload, a conservative measured
rate and a tested emergency stop within reach. Follow the controller's commissioning
procedure. When the hardware maintainer deliberately authorizes motion:

```bash
build/lerobot/env/bin/lerobot-teleoperate \
  --config_path=build/lerobot/teleop-hardware-reviewed.yaml \
  --robot.enable_motion=true --teleop_time_s=10
```

The adapter checks profile identity, measured calibration, soft limits and watchdog
capability **before** opening the driver. On arming, it holds the measured current
pose. Each command is bounded by measured travel and rate. A command gap beyond
`watchdog_s`, invalid readback or I/O exception requests stop and disconnect; a real
controller watchdog must independently handle a stalled/killed host process.

Verify wrong-device rejection, glove unplug, hand bus unplug, host termination and
E-stop behavior through the qualified commissioning procedure before normal operation.
No physical tests are claimed by this release. Arm teleoperation, Quest pose, camera
synchronization and a complete training/data-collection stack remain separate work.
