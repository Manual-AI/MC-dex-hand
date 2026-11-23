# Visual assembly guide

The figures show the right-hand SolidWorks assemblies. The close-ups isolate the index-finger
linkages in their assembled positions. Use the [bill of materials](../../bom/README.md) for
the print and purchase lists and the [STEP assemblies](../../hardware/step/) for placement.

Print the specified quantities in ABS or PETG, with 100% infill for printed pins. The glove
uses three tip hinge pins and five encoder lids. For a left-hand variant, consult the
`mirror_for_left` column in the BOM. Left-hand compatibility of the Quest mount is unverified.

## Wearable glove

![Wearable glove CAD overview with labels for the finger links, joint sensors, wrist tracker and electronics enclosure](../images/wearable-glove-wrist-side.png)

The glove backplate supports four pairs of links. Each proximal and distal hinge has a
rotary potentiometer. The ring and little fingers operate one pair together.

![Isolated glove index-finger chain showing the backplate pivot, fingertip pivot and sensor housing](../images/wearable-glove-link-connections.png)

Assemble each finger chain from the frame outward.

1. **Backplate to proximal link.** Align the lower pivot holes and install the matching
   printed hinge pin. The proximal link is the first moving link next to the hand frame.
2. **Proximal link to fingertip.** Place the fingertip around the upper pivot and install
   its hinge pin. The tip rotates relative to the proximal link.
3. **Add the sensors.** Seat the rotary sensors in their locations and engage the matching
   encoder pins with their shafts. Use the printed housings and lids where provided.

The middle and combined ring/pinky chains follow the same connection pattern, with their
own matching parts. The thumb connects at the palm plate and uses its dedicated link and pins.

## Robot hand

![Robot hand CAD overview with labels for the servo-driven finger chains, hand frame, Quest mount and electronics enclosure](../images/robot-hand-wrist-side.png)

Each finger group has one frame-mounted servo for the proximal joint and one servo in
the proximal link for the distal joint. The fingertip follows the glove’s contact geometry.

![Isolated robot index-finger chain showing the base servo output, distal servo output and distal servo body inside the proximal link](../images/robot-hand-link-connections.png)

Install the servos and links from the frame outward.

1. **Frame to base servo.** Mount the base servo in the frame at the corresponding finger position.
2. **Base servo to proximal link.** Attach the proximal link to the servo outputs using the
   matching mounting holes on both sides.
3. **Proximal link to fingertip.** Fit the distal servo inside the proximal link, then attach
   the fingertip to its outputs.

Repeat for the middle and combined ring/pinky chains. The thumb has its own support rod,
pin and MR105ZZ bearing arrangement; use the robot STEP assembly to follow that placement.
The OpenArm adaptor connects the completed hand frame to the robot arm.

## Finish the shared attachments

- Attach the camera mount and adaptor in the matching pose on both assemblies.
- Fit the electronics enclosure and lid.
- Fit the Quest receiver and controller mount. Each mount uses one `cm_quest_mount_base`, one
  `cm_quest_mount_hinged_cap` and one `cm_quest_mount_receiver`, plus one 2 × 20 mm pin,
  one M3 × 12 mm screw and one M3 nut. The receiver pads have centered 8 × 9 mm edge-to-edge gaps.

For commissioning, see the [glove calibration guide](../../lerobot/CALIBRATION.md)
and [physical-hand integration status](../../lerobot/HARDWARE.md). Some fastener
specifications, servo alignment details and wiring details are still unverified.
