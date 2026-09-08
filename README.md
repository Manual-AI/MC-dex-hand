<h1 align="center">Manual-Dex</h1>

<p align="center"><strong>A Kinematically Matched Robot Hand and Wearable Glove for Manipulation Data Collection</strong></p>
<p align="center"><a href="https://github.com/Manual-AI">Manual Cognition</a></p>

<p align="center">
  <img src="docs/assets/manual-dex-demo.gif" alt="Manual-Dex prototype: wearable glove, corresponding robot hand, and joint visualization" width="640">
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/Software-Apache%202.0-blue" alt="Software license: Apache 2.0"></a>
  <a href="hardware/LICENSE"><img src="https://img.shields.io/badge/Hardware-CERN--OHL--P%202.0-blue" alt="Hardware license: CERN-OHL-P 2.0"></a>
  <a href="tools/"><img src="https://img.shields.io/badge/Tooling-Python%203-3776AB?logo=python&logoColor=white" alt="Python 3 tooling"></a>
  <a href="simulation/COMPARISON.md"><img src="https://img.shields.io/badge/Simulation-4%20native%20engines-286778" alt="Native MuJoCo, Genesis, SuperDex and Isaac Sim simulation"></a>
  <a href="lerobot/README.md"><img src="https://img.shields.io/badge/Teleoperation-LeRobot%200.6.1-FFD21E" alt="LeRobot 0.6.1 teleoperation"></a>
  <img src="https://img.shields.io/badge/Kinematics-8%20DOF-526777" alt="Eight degrees of freedom">
  <a href="hardware/step/"><img src="https://img.shields.io/badge/CAD-STL%20%2F%20STEP-526777" alt="STL and STEP CAD"></a>
  <a href="firmware/esp32_glove/"><img src="https://img.shields.io/badge/Glove%20MCU-ESP32-526777" alt="ESP32 glove microcontroller"></a>
</p>

<p align="center">
  <a href="#system-architecture">Architecture</a> ·
  <a href="bom/BOM.md">Bill of materials</a> ·
  <a href="hardware/step/">CAD assemblies</a> ·
  <a href="docs/assembly/README.md">Assembly guide</a> ·
  <a href="simulation/README.md">Simulation tutorials</a> ·
  <a href="lerobot/README.md">LeRobot teleoperation</a> ·
  <a href="docs/visualization/README.md">Visualization methods</a>
</p>

*Manual-Dex prototype demonstration. The wearable glove generates the motion of
the corresponding robot-hand joints.*

## Overview

Manual-Dex is a co-designed dexterous robot hand and wearable sensing glove designed for
collecting manipulation demonstrations with corresponding joint coordinates and contact
geometry. Each device has eight revolute joints arranged in four groups: index, middle,
combined ring–little finger, and thumb. The robot hand uses eight serial-bus servos; the
glove measures the corresponding joints with eight rotary potentiometers. Shared camera
mounts and a rigid Quest-controller mount provide a common mechanical basis for visual
and spatial observations. The controller is retained on the actuated hand to match the
glove's appearance to an overhead camera; the operator wears a black, fingertip-less
under-glove to support visual matching from the hand camera after simple inpainting.
Includes CAD, a BOM, four-engine OpenArm simulation tutorials, and LeRobot teleoperation
and calibration tools.

## Simulation quick start

Manual-Dex on a **seven-joint OpenArm v1** performs a five-second, scripted
physics-driven pick and place: grasp, lift, carry from blue to green, and release.
Each engine runs its own physics and rendering.

<table>
  <tr>
    <td width="50%" align="center">
      <img src="docs/assets/simulation/mujoco.gif" alt="MuJoCo native physics and rendering: OpenArm and Manual-Dex pick and place" width="100%"><br>
      <a href="simulation/mujoco/README.md">MuJoCo — setup and tutorial</a>
    </td>
    <td width="50%" align="center">
      <img src="docs/assets/simulation/genesis.gif" alt="Genesis native physics and rendering: OpenArm and Manual-Dex pick and place" width="100%"><br>
      <a href="simulation/genesis/README.md">Genesis — setup and tutorial</a>
    </td>
  </tr>
  <tr>
    <td width="50%" align="center">
      <img src="docs/assets/simulation/superdex.gif" alt="SuperDex native physics and SDK rendering: OpenArm and Manual-Dex pick and place" width="100%"><br>
      <a href="simulation/superdex/README.md">SuperDex — setup and tutorial</a>
    </td>
    <td width="50%" align="center">
      <img src="docs/assets/simulation/isaacsim.gif" alt="Isaac Sim native PhysX and RTX rendering: OpenArm and Manual-Dex pick and place" width="100%"><br>
      <a href="simulation/isaacsim/README.md">Isaac Sim — setup and tutorial</a>
    </td>
  </tr>
</table>

[Synchronized 2×2 animation](simulation/COMPARISON.md) ·
[Simulation guide](simulation/README.md) ·
[Pick-and-place controller](simulation/PICK_PLACE.md) ·
[URDF and meshes](models/manual_dex/urdf/README.md) · [MJCF models](models/manual_dex/README.md)

## LeRobot teleoperation quick start

Use the latest stable LeRobot release checked for this integration, **0.6.1**, to drive
the eight hand joints from a synthetic glove—no hardware or Hub account needed:

```bash
python3 lerobot/run.py mujoco
```

The [dedicated LeRobot tutorial](lerobot/README.md) includes one-command setup for all
four engines, editable YAML files, [glove-to-hand calibration](lerobot/CALIBRATION.md),
an explicit [ESP32 serial protocol](lerobot/PROTOCOL.md) and local dataset recording.
The OpenArm stays in a fixed pose during glove teleoperation; wrist/arm IK is not included yet [TODO].

Simulation is implemented and headless-tested. Real hardware additionally needs the
still-pending glove firmware and a verified HLS3606 driver, wiring, watchdog and measured
joint limits. The [physical-hand integration guide](lerobot/HARDWARE.md) identifies these
requirements; its driver template is inert and motion is disabled by default.

## Design motivation

Manual-Dex aims to reduce or even eliminate the embodiment gap physically and visually
between an operator's data-collection device and the robot that replays a demonstration.
Corresponding finger links and fingertip surfaces are designed to share the same
kinematic and contact geometry.
Joint measurements can therefore be calibrated into the robot's encoder coordinates,
without first fitting a separate human-hand model.

## System architecture

| Property | Manual-Dex hand | Manual-Dex glove |
|---|---|---|
| Joint structure | Four finger groups, two revolute joints per group | Corresponding eight joints |
| Actuation / sensing | 8 × Feetech HLS3606 dual-shaft serial-bus servos | 8 × Bourns 3382G-2-103G, 10 kΩ rotary potentiometers |
| Host interface | Serial-bus driver | Adafruit HUZZAH32 ESP32 Feather |
| Quest controller | Right Meta Quest Touch Plus; retained for overhead-view appearance matching | Same controller and mount design; intended 6-DOF pose input |
| Wrist imaging | 2 MP USB 2.0 UVC camera | Corresponding camera placement |
| Structural components | FDM-printed ABS or PETG | FDM-printed ABS or PETG |
| Mechanical interface | OpenArm wrist-flange adaptor | Wearable frame |

### Joint correspondence

Each finger group has proximal and distal joints; the ring and little fingers share
one group. Calibrate the eight glove potentiometers to their corresponding robot servos.
The [LeRobot examples](lerobot/README.md) provide sensor mapping, simulation teleoperation
and state-only recording. Synchronized Quest/camera acquisition and measured hardware
calibration remain future work.

### Why is there a Quest 3 controller on the actuated hand?

A controller on the actuated hand may seem redundant. It is deliberate: the matching
controller and mount remove the controller-related visual embodiment gap for an overhead
camera, while the glove's controller provides pose input. Match their placement and
orientation so that this attachment does not visually distinguish human demonstrations
from robot execution.

### Black fingerless under-glove and the hand-camera view

Wear a black, fingertip-less fabric glove beneath the instrumented glove, keeping sensors,
mechanisms and contact surfaces unobstructed. With matched hand-camera placement and
simple inpainting of remaining appearance differences, the aim is for the worn glove
and robot hand to look as similar as possible. Preserve objects and contact evidence
in any masks. The CAD animations show the mechanical assemblies; fabric and an inpainting
pipeline are not included.

## Mechanical structure and kinematics

The following animation uses tessellated geometry from the released STEP assemblies,
including the current three-part Quest mount. The glove and actuated hand are shown
**side by side in one ten-second loop at 20 fps**, with synchronized full camera orbits
at 36°/s—half the original rotation speed. Finger flexion retains its five-second cycle.
Labels follow the moving geometry; repeated parts share a numbered component-family label.
All component names and specifications remain visible in the fixed right-hand register.
The [part register](docs/visualization/PARTS.md) lists individual BOM entries, release
filenames, materials, and functions.

<img src="docs/assets/manual-dex-paired-kinematics.gif" alt="Manual-Dex glove and actuated hand side by side: ten-second MuJoCo orbit, flexing fingers, and persistent BOM-linked component labels" width="2000">

### Instrumented glove

*Manual-Dex glove (left). Printed links rotate about hinge pins; potentiometers measure
the corresponding joints. Sensor housings, retention lids, and encoder couplers are
identified separately. The electronics enclosure is transparent to expose the PCB from
the CAD assembly. The register distinguishes the index, middle, and combined
ring–little finger groups; the thumb is listed separately.*

### Actuated robot hand

*Manual-Dex hand (right). Two servos actuate each finger group. The distal servo housing
moves with its proximal link; its output carries the distal contact link. The thumb also
uses a support rod, printed pin, and MR105ZZ bearing. Shared camera, tracking, and
enclosure components preserve the paired-device layout.*

The Quest 3 controller visible on the hand is intentional: see the
[overhead-camera appearance-matching rationale](#why-is-there-a-quest-3-controller-on-the-actuated-hand).
For the worn glove, follow the [black fingerless under-glove guidance](#black-fingerless-under-glove-and-the-hand-camera-view).

These are kinematic illustrations, not validated dynamics simulations. The hinge axes
are recovered from CAD cylindrical faces; flexion amplitudes are selected for visualization.
Joint limits, inertial properties, actuator dynamics, collisions, and contact behavior are
not identified by this animation. The actual [MuJoCo MJCF models and meshes](models/manual_dex/README.md)
are included in the repository; these models were generated directly as MJCF. A
[derived hand URDF](models/manual_dex/urdf/README.md) and
[OpenArm integration examples](simulation/README.md) are now provided separately.
See the [methods and regeneration instructions](docs/visualization/README.md).

## Materials and fabrication

The CSV files in [`bom/`](bom/) are the source of truth. Material colors in the diagrams
distinguish component classes; they do not identify measured material properties.

| Component | BOM specification | Manufacturing / selection notes |
|---|---|---|
| Palm plates, backplates, finger links, contact links | ABS or PETG | FDM print; match the hand and glove contact geometry |
| Sensor housings, lids, hinge pins, encoder couplers | ABS or PETG | Printed pins form plain glove hinges; use 100% infill for pins |
| Camera mounts, electronics enclosure, OpenArm adaptor | ABS or PETG | Print the release STLs; retain the assembly placements |
| Quest mount base, hinged cap, receiver | ABS or PETG | One of each per device; receiver pads are 8 × 5 × 3 mm with centered 8 × 9 mm clear gaps |
| Quest mount hardware | 2 × 20 mm pin, M3 × 12 mm screw, M3 nut | One of each per device |
| Robot thumb bearing | MR105ZZ, 5 × 10 × 4 mm, shielded | One bearing; the other robot joints rotate on the servo outputs |
| Glove sensors | Bourns 3382G-2-103G, 10 kΩ, linear taper | Eight sensors; five printed retention lids and three hot-glue fixations are recorded in the BOM |
| Optional fingertip covering | BOM options: TPU, silicone, or grip tape | Use matching coverings on corresponding hand and glove contact surfaces |
| Wearable attachments, wiring, structural fasteners | See the component BOM | Follow the assembly-specific quantities, dimensions and attachment details |

The current release is right-handed. The [BOM](bom/BOM.md) records quantities and
part-level mirroring requirements. Follow the [assembly guide](docs/assembly/README.md)
for the link-connection sequence.

## Reproducibility

1. Retrieve Git LFS assets with `git lfs pull` after cloning.
2. Review the [BOM](bom/BOM.md) for parts, quantities and material specifications.
3. Use [`manual_dex_hand.step`](hardware/step/manual_dex_hand.step) and
   [`manual_dex_glove.step`](hardware/step/manual_dex_glove.step) for assembled geometry,
   and `hardware/*/stl/` for individual printed parts.
4. Follow the [assembly guide](docs/assembly/README.md).
5. Open the [included MJCF models](models/manual_dex/README.md), or regenerate the models
   and diagrams using the [visualization workflow](docs/visualization/README.md).
6. Follow the [simulation tutorials](simulation/README.md) to attach the hand to OpenArm
   in MuJoCo, Isaac Sim, SuperDex or Genesis.
7. Follow the [LeRobot tutorial](lerobot/README.md) for teleoperation, calibration and
   state-only local demonstration recording.

The existing BOM and export utilities require Python 3. The visualization workflow uses
Python 3.11 or newer and has been exercised with Python 3.13 and MuJoCo 3.6.0.

```bash
python tools/gen_bom_md.py                  # Regenerate the human-readable BOM.
python tools/place_exports.py <export_dir> # Place exported STL/STEP assets.
```

The SolidWorks macros in [`tools/solidworks/`](tools/solidworks/) rename printed parts and
export the assemblies as `manual_dex_hand.step` and `manual_dex_glove.step`. Component
prefixes remain `rh_` for robot-hand parts, `gl_` for glove parts, and `cm_` for common
parts; these identifiers preserve the BOM mapping. Historical source-component names
are recorded in [`bom/rename_map.csv`](bom/rename_map.csv).

## Repository organization

```text
bom/                    Part inventory, materials, naming map, and attribution
hardware/
  robot_hand/stl/        Robot-hand printed parts (rh_*)
  glove/stl/             Wearable-glove printed parts (gl_*)
  common/stl/            Shared printed components (cm_*)
  step/                 Manual-Dex hand and glove assemblies
docs/
  assets/               Prototype demonstration and paired MuJoCo animation
  assembly/             Mechanical connection guide
  visualization/        Visualization methods and complete part register
models/manual_dex/      Native MJCF, standalone hand URDF, meshes, and joint/part records
simulation/            OpenArm model builder, one-command launcher, and validation
  mujoco/              Native MJCF tutorial and executable example
  isaacsim/            URDF-to-USD / PhysX tutorial and executable example
  superdex/            URDF runtime / debugger tutorial and executable example
  genesis/             URDF CPU/GPU tutorial and executable example
lerobot/               LeRobot 0.6.1 plugin, setup, calibration and teleoperation tutorials
  configs/             Simulation, serial-glove, guarded hardware and recording examples
  tests/               Calibration, protocol and device-guard tests (fake hardware only)
firmware/esp32_glove/    Glove acquisition firmware (pending)
software/               Host software index and remaining hardware integrations
tools/
  visualization/        STEP extraction, MJCF generation, and diagram renderer
  solidworks/           CAD naming and export macros
third_party/udcap/      Historical attribution for the superseded cradle
```

## License and community

Manual-Dex's original software and general documentation are licensed under the
[Apache License 2.0](LICENSE). Its original hardware designs, CAD, fabrication files,
BOMs and CAD-derived robot models are licensed under the
[CERN Open Hardware Licence v2 — Permissive](hardware/LICENSE), SPDX `CERN-OHL-P-2.0`.
The [licensing guide](LICENSING.md) defines exactly which files use each license.

You are free to use, study, modify, redistribute and build upon the licensed work,
including manufacturing and selling hardware or using the software commercially,
without a license fee. Preserve the required notices and comply with the applicable
license terms. The project is provided **as is, without warranty**. Third-party material
retains its own terms; see the [hardware notices](bom/THIRD_PARTY.md) and
[simulation notices](simulation/THIRD_PARTY.md).

Thank you to the open-source community. Manual-Dex is free to use and modify under
these licenses. We welcome sharing, improvements and new applications.
