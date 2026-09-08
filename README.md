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
  <a href="docs/visualization/README.md"><img src="https://img.shields.io/badge/Rendering-MuJoCo%203.6-286778" alt="MuJoCo 3.6 rendering"></a>
  <img src="https://img.shields.io/badge/Kinematics-8%20DOF-526777" alt="Eight degrees of freedom">
  <a href="hardware/step/"><img src="https://img.shields.io/badge/CAD-STL%20%2F%20STEP-526777" alt="STL and STEP CAD"></a>
  <a href="firmware/esp32_glove/"><img src="https://img.shields.io/badge/Glove%20MCU-ESP32-526777" alt="ESP32 glove microcontroller"></a>
</p>

<p align="center">
  <a href="#2-system-architecture">Architecture</a> ·
  <a href="bom/BOM.md">Bill of materials</a> ·
  <a href="hardware/step/">CAD assemblies</a> ·
  <a href="docs/assembly/README.md">Assembly guide</a> ·
  <a href="simulation/README.md">Simulation tutorials</a> ·
  <a href="docs/visualization/README.md">Visualization methods</a>
</p>

*Manual-Dex prototype demonstration. The wearable glove measures the motion of
the corresponding robot-hand joints.*

## Overview

Manual-Dex is a co-designed dexterous robot hand and wearable sensing glove designed for
collecting manipulation demonstrations with corresponding joint coordinates and contact
geometry. Each device has eight revolute joints arranged in four groups: index, middle,
combined ring–little finger, and thumb. The robot hand uses eight serial-bus servos; the
glove measures the corresponding joints with eight rotary potentiometers. Shared camera
mounts and a rigid Quest-controller mount provide a common mechanical basis for visual
and spatial observations. The repository contains the mechanical design, bill of
materials, CAD export tooling, reproducible MuJoCo visualizations, and OpenArm integration
examples for four simulation engines. Firmware,
host-side acquisition, calibration, and quantitative validation remain under development.

## Simulation quick start

Run Manual-Dex attached to a **seven-joint OpenArm v1**, with all eight hand joints
flexing in one connected articulation. From this repository's root on Linux:

| Engine | Single-command setup and launch | Tutorial |
|---|---|---|
| MuJoCo | `python3 simulation/run.py mujoco` | [Native MJCF, viewer and headless test](simulation/mujoco/README.md) |
| Genesis | `python3 simulation/run.py genesis` | [URDF import, CPU/GPU and control hooks](simulation/genesis/README.md) |
| SuperDex | `python3 simulation/run.py superdex` | [URDF runtime import and debugger](simulation/superdex/README.md) |
| Isaac Sim | `python3 simulation/run.py isaacsim --accept-isaac-eula` | [URDF-to-USD import and PhysX articulation](simulation/isaacsim/README.md) |

The launcher obtains pinned dependencies and OpenArm assets, creates isolated environments,
builds and checks the model, then runs five simulated seconds. Git, Git LFS and Python
with `venv`/`pip` are prerequisites; Isaac Sim also needs compatible NVIDIA hardware and
your agreement to its EULA before passing the acceptance flag.

For a finite, non-interactive run, add `--headless --steps 1200`. See the
[complete simulation guide](simulation/README.md) for prerequisites, expected JSON results,
mount configuration, offline use and agent-friendly commands. The
[standalone hand URDF and meshes](models/manual_dex/urdf/README.md) are included alongside
the [native MJCF models](models/manual_dex/README.md).

These are **kinematic integration examples**, not validated grasp dynamics. All four
engines passed the 15-joint headless playback test; local Isaac Sim rendering remains
unverified because its renderer crashed during startup. See [validation and limitations](simulation/VALIDATION.md).

## 1. Design motivation

The design aims to reduce the geometric differences between an operator's data-collection
device and the robot that replays a demonstration. Corresponding finger links and
fingertip surfaces are designed to share the same kinematic and contact geometry.
Joint measurements can therefore be calibrated into the robot's encoder coordinates,
without first fitting a separate human-hand model.

This correspondence is a mechanical design objective. The repository does not yet report
measured tracking accuracy, contact-transfer error, payload, or manipulation success rates.

## 2. System architecture

| Property | Manual-Dex hand | Manual-Dex glove |
|---|---|---|
| Joint structure | Four finger groups, two revolute joints per group | Corresponding eight joints |
| Actuation / sensing | 8 × Feetech HLS3606 dual-shaft serial-bus servos | 8 × Bourns 3382G-2-103G, 10 kΩ rotary potentiometers |
| Host interface | Serial-bus driver; final board selection pending | Adafruit HUZZAH32 ESP32 Feather; exact variant to be confirmed |
| Spatial tracking | Rigidly mounted right Meta Quest Touch Plus controller | Same controller and mount design |
| Wrist imaging | 2 MP USB 2.0 UVC camera | Corresponding camera placement |
| Structural components | FDM-printed ABS or PETG | FDM-printed ABS or PETG |
| Mechanical interface | OpenArm wrist-flange adaptor | Wearable frame; attachment straps not yet specified |

### 2.1 Joint correspondence

Let the joint vector be

$$
\mathbf{q} = [q_{I,p}, q_{I,d}, q_{M,p}, q_{M,d}, q_{R+L,p}, q_{R+L,d}, q_{T,p}, q_{T,d}]^{\mathsf T},
$$

where $p$ and $d$ denote the proximal and distal joints. The ring and little fingers share
one mechanical group. The glove potentiometer signals must be calibrated to robot servo
encoder values for each corresponding joint. A synchronized demonstration would combine
these eight joint coordinates, the controller's six-degree-of-freedom pose, and camera
frames. Acquisition, time synchronization, calibration parameters, and replay software
are not yet released.

## 3. Mechanical structure and kinematics

The following animation uses tessellated geometry from the released STEP assemblies,
including the current three-part Quest mount. The glove and actuated hand are shown
**side by side in one ten-second loop at 20 fps**, with synchronized full camera orbits
at 36°/s—half the original rotation speed. Finger flexion retains its five-second cycle.
Labels follow the moving geometry; repeated parts share a numbered component-family label.
All component names and specifications remain visible in the fixed right-hand register.
The [part register](docs/visualization/PARTS.md) lists individual BOM entries, release
filenames, materials, and functions.

![Manual-Dex glove and actuated hand side by side: ten-second MuJoCo orbit, flexing fingers, and persistent BOM-linked component labels](docs/assets/manual-dex-paired-kinematics.gif)

### 3.1 Instrumented glove

*Manual-Dex glove (left). Printed links rotate about hinge pins; potentiometers measure
the corresponding joints. Sensor housings, retention lids, and encoder couplers are
identified separately. The electronics enclosure is transparent to expose the PCB from
the CAD assembly. The register distinguishes the index, middle, and combined
ring–little finger groups; the thumb is listed separately.*

### 3.2 Actuated robot hand

*Manual-Dex hand (right). Two servos actuate each finger group. The distal servo housing
moves with its proximal link; its output carries the distal contact link. The thumb also
uses a support rod, printed pin, and MR105ZZ bearing. Shared camera, tracking, and
enclosure components preserve the paired-device layout.*

These are kinematic illustrations, not validated dynamics simulations. The hinge axes
are recovered from CAD cylindrical faces; flexion amplitudes are selected for visualization.
Joint limits, inertial properties, actuator dynamics, collisions, and contact behavior are
not identified by this animation. The actual [MuJoCo MJCF models and meshes](models/manual_dex/README.md)
are included in the repository; these models were generated directly as MJCF. A
[derived hand URDF](models/manual_dex/urdf/README.md) and
[OpenArm integration examples](simulation/README.md) are now provided separately.
See the [methods and regeneration instructions](docs/visualization/README.md).

## 4. Materials and fabrication

The CSV files in [`bom/`](bom/) are the source of truth. Material colors in the diagrams
distinguish component classes; they do not identify measured material properties.

| Component | BOM specification | Manufacturing / selection notes |
|---|---|---|
| Palm plates, backplates, finger links, contact links | ABS or PETG | FDM print; match the hand and glove contact geometry |
| Sensor housings, lids, hinge pins, encoder couplers | ABS or PETG | Printed pins form plain glove hinges; use 100% infill for pins |
| Camera mounts, electronics enclosure, OpenArm adaptor | ABS or PETG | Print the release STLs; retain the assembly placements |
| Quest mount base, hinged cap, receiver | ABS or PETG | One of each per device; receiver pads are 8 × 5 × 3 mm with centered 8 × 9 mm clear gaps |
| Quest mount hardware | 2 × 20 mm pin, M3 × 12 mm screw, M3 nut | One of each per device; pin material and fastener grades remain TODO |
| Robot thumb bearing | MR105ZZ, 5 × 10 × 4 mm, shielded | One bearing; the other robot joints rotate on the servo outputs |
| Glove sensors | Bourns 3382G-2-103G, 10 kΩ, linear taper | Eight sensors; five printed retention lids and three hot-glue fixations are recorded in the BOM |
| Fingertip covering | Not specified | TPU, silicone, or grip tape are candidates in the BOM, not finalized materials |
| Wearable attachments, wiring, structural fasteners | Partially specified / TODO | Confirm quantities, dimensions, and attachment method before fabrication |

The current release is right-handed. Parts marked `mirror_for_left = yes` need mirrored
prints for a left-hand variant; Quest-mount handedness remains unverified. Consult the
[BOM](bom/BOM.md) for quantities and the [assembly guide](docs/assembly/README.md) for the
link-connection sequence.

## 5. Reproducibility

1. Retrieve Git LFS assets with `git lfs pull` after cloning.
2. Review the [BOM](bom/BOM.md), including every unresolved `TODO` entry.
3. Use [`manual_dex_hand.step`](hardware/step/manual_dex_hand.step) and
   [`manual_dex_glove.step`](hardware/step/manual_dex_glove.step) for assembled geometry,
   and `hardware/*/stl/` for individual printed parts.
4. Follow the [assembly guide](docs/assembly/README.md).
5. Open the [included MJCF models](models/manual_dex/README.md), or regenerate the models
   and diagrams using the [visualization workflow](docs/visualization/README.md).
6. Follow the [simulation tutorials](simulation/README.md) to attach the hand to OpenArm
   in MuJoCo, Isaac Sim, SuperDex or Genesis.

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

## 6. Release status and limitations

The release includes CAD, a BOM, mechanical connection diagrams, a reproducible
visualization pipeline, native MJCF and derived hand URDF assets, and four-engine OpenArm
kinematic integration tutorials. It does not yet include finished firmware, host software, wiring
instructions, calibration data, a validated dynamics model, or experimental benchmarks.
Some bought-part specifications and quantities are unresolved in the BOM.

Original software is released under Apache-2.0; original hardware designs and robot
models use CERN-OHL-P-2.0. See [licensing and reuse](#8-license-and-community) below,
including the separate terms and historical exclusions for third-party material.

## 7. Repository organization

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
firmware/esp32_glove/    Glove acquisition firmware (pending)
software/               Host acquisition, calibration, and control (pending)
tools/
  visualization/        STEP extraction, MJCF generation, and diagram renderer
  solidworks/           CAD naming and export macros
third_party/udcap/      Historical attribution for the superseded cradle
```

## 8. License and community

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
