# Manual-Dex: Mechanical Assembly Guide

This guide describes the principal mechanical connections in the released Manual-Dex
assemblies, including the current three-part Quest mount. The diagrams are MuJoCo renders
of the STEP geometry. Linkage close-ups isolate the index-finger chain; surrounding
components are hidden and retained components remain in their assembled positions.

All printed frames, links, housings and pins are specified as **ABS or PETG** in the BOM.
Refer to the [component and material register](../visualization/PARTS.md) for individual
part IDs, filenames, quantities and functions. Motion in the overview animation is
illustrative; see the [visualization methods](../visualization/README.md).

![Manual-Dex glove (left) and actuated hand (right): synchronized ten-second MuJoCo orbit with flexing fingers and a persistent component register](../assets/manual-dex-paired-kinematics.gif)

## 1. Manual-Dex glove

The operator's hand moves the printed links. Eight rotary position sensors measure the joints:
two each for the index, middle, combined ring/pinky, and thumb groups.

![Manual-Dex glove index linkage: fixed frame, proximal pivot, proximal link, distal pivot and contact link](../images/manual-dex-glove-linkage.png)

Build each main finger chain from the frame outward:

1. **Backplate to proximal link.** Align the lower pivot holes and install the matching
   printed hinge pin. The proximal link is the first moving link next to the hand frame.
2. **Proximal link to fingertip.** Place the fingertip around the upper pivot and install
   its hinge pin. The tip rotates relative to the proximal link.
3. **Add the sensors.** Seat the rotary sensors in their locations and engage the matching
   encoder pins with their shafts. Use the printed housings and lids where provided.

The middle and combined ring/pinky chains follow the same connection pattern, with their
own matching parts. The thumb connects at the palm plate and uses its dedicated link and pins.

## 2. Manual-Dex hand

The robot uses matching finger groups and fingertip geometry. Each group has two servos:
one drives the proximal link and the other drives the fingertip.

![Manual-Dex robot index linkage: fixed frame, base servo axis, proximal link, distal servo axis and contact link](../images/manual-dex-hand-linkage.png)

Build the main finger chains from the frame outward:

1. **Frame to base servo.** Mount the base servo in the frame at the corresponding finger position.
2. **Base servo to proximal link.** Attach the proximal link to the servo outputs using the
   matching mounting holes on both sides.
3. **Proximal link to fingertip.** Fit the distal servo inside the proximal link, then attach
   the fingertip to its outputs.

Repeat for the middle and combined ring/pinky chains. The thumb has its own support rod,
pin and MR105ZZ bearing arrangement; use the robot STEP assembly to follow that placement.
The OpenArm adaptor connects the completed hand frame to the robot arm.

## 3. Shared attachments

- Attach the camera mount and adaptor in the matching pose on both assemblies.
- Fit the electronics enclosure and lid.
- Fit the Quest receiver and controller mount. The mount uses the printed base, hinged cap
  and receiver, plus one 2 x 20 mm pin, one M3 x 12 mm screw and one M3 nut per assembly.

Use the [BOM](../../bom/BOM.md) for quantities and the [STEP assemblies](../../hardware/step/)
for exact part placement. This guide covers the mechanical connection pattern; detailed
fastener specifications, servo alignment, wiring and calibration are still to be documented.
