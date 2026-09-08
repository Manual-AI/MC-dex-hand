# MC-dex-hand

<p align="center">
  <img src="docs/assets/mc-dex-hand-demo.gif" alt="MC-dex-hand robot hand mirroring the wearable data-collection glove" width="800">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3-3776AB?logo=python&logoColor=white" alt="Python 3">
  <img src="https://img.shields.io/badge/Hardware-8--DOF-F97316" alt="8-DOF hardware">
  <img src="https://img.shields.io/badge/Firmware-ESP32-E7352C?logo=espressif&logoColor=white" alt="ESP32 firmware">
  <img src="https://img.shields.io/badge/CAD-STL%20%7C%20STEP-5C6BC0" alt="STL and STEP CAD files">
  <img src="https://img.shields.io/badge/Git%20LFS-enabled-F64935?logo=git&logoColor=white" alt="Git LFS enabled">
</p>

An open-source dexterous robot hand and a matching wearable data-collection glove, built by
[Manual Cognition](https://github.com/Manual-AI).

The two share **identical kinematics and contact geometry**: what the glove's fingertips touch is what
the robot's fingertips touch. Wearing the glove and manipulating objects therefore produces
demonstrations that transfer directly to the robot hand (UMI-style data collection).

| | Robot hand | Glove |
|---|---|---|
| Joints | 8 DOF: index, middle, ring+pinky (combined), thumb - 2 joints each | same 8 joints |
| Actuation / sensing | 8x Feetech HLS3606 dual-shaft serial-bus servos | 8x Bourns 3382G-2-103G rotary potentiometers, read by an Adafruit HUZZAH32 ESP32 Feather |
| 6-DOF pose | mounted on the robot arm (OpenArm flange adaptor included) | Meta Quest Touch Plus controller, rigidly mounted |
| Wrist camera | 2 MP USB camera | same camera, same pose |
| Structure | FDM printed, ABS or PETG | FDM printed, ABS or PETG |

During data collection the glove's potentiometer readings are mapped to the corresponding robot servo
encoder values, so a recorded glove trajectory is a servo trajectory.

> **Status:** hardware release in progress. Firmware, host software and the assembly guide are TODO.
> **License:** not yet chosen - repository is private until it is. See `bom/THIRD_PARTY.md` for the
> current Quest mount source status and historical third-party attribution.

## Repository layout

```
bom/                 Bill of materials (CSV = source of truth, BOM.md rendered from it)
hardware/
  robot_hand/stl/    printed parts unique to the robot hand   (rh_*)
  glove/stl/         printed parts unique to the glove         (gl_*)
  common/stl/        printed parts used on both                (cm_*)
  step/              full assemblies as STEP (robot hand, glove)
third_party/udcap/   attribution for the superseded Quest cradle (see THIRD_PARTY.md)
firmware/esp32_glove ESP32 Feather firmware reading the glove encoders   (TODO)
software/            host-side collection / control / mapping code       (TODO)
docs/assembly/       build guide                                          (TODO)
tools/               BOM renderer + SolidWorks macros used to produce the release files
```

## Building one

1. Read `bom/BOM.md`. Buy everything in the *Buy* tables; rows marked `TODO` are still being
   finalised.
2. Print every part in the *Make* tables from `hardware/*/stl/`. Quantities are in the BOM
   (most are 1; `gl_tip_hinge_pin` x3, `gl_encoder_lid` x5, `gl_encoder_case_*` x2).
   ABS or PETG, 100 % infill for pins.
3. Each assembly uses the same Quest mount: print `cm_quest_mount_base`,
   `cm_quest_mount_hinged_cap` and `cm_quest_mount_receiver`. Add one 2 x 20 mm pin,
   one M3 x 12 mm screw and one M3 nut. The receiver pads have centered 8 x 9 mm
   edge-to-edge gaps. The previous two-piece udCap cradle is superseded.
4. Follow `docs/assembly/` (coming).

Right hand only for now. Parts flagged `mirror_for_left = yes` in the BOM need a mirrored print for a
left-hand variant. Quest mount handedness is marked TODO until checked.

## Part naming

`rh_` robot hand, `gl_` glove, `cm_` common to both; then finger (`index`, `middle`, `pinkyring`,
`thumb`) and part. `bom/rename_map.csv` maps historical CAD names to release names.
The imported Quest mount retains its source filenames;
`export_cad.bas` maps these to the three `cm_quest_mount_*` release filenames.

## Regenerating release files

- `python tools/gen_bom_md.py` - re-render `bom/BOM.md` after editing the CSVs.
- `tools/solidworks/rename_parts.bas` - renames CAD files per `rename_map.csv` (already applied).
- `tools/solidworks/export_cad.bas` - exports one STL per printed part and the assembly STEP.
- `python tools/place_exports.py <export folder>` - sorts exported STL/STEP into `hardware/` and
  checks them against the BOM.
