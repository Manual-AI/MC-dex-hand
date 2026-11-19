# MC-dex-hand

<p align="center">
  <b>Democratizing Data-Efficient Robot Learning with Robot-Free Demonstrations</b><br>
  TODO: author list &middot; Manual Cognition<br>
  <i>TODO: workshop name, NeurIPS 2026</i>
</p>

<p align="center">
  <a href="docs/paper/mc-dex-hand-neurips2026.pdf"><b>Paper (PDF)</b></a> &middot;
  <a href="https://arxiv.org/abs/TODO">arXiv</a> &middot;
  <a href="https://openreview.net/forum?id=TODO">OpenReview</a> &middot;
  <a href="software/">Code</a> &middot;
  <a href="bom/BOM.md">Bill of materials</a> &middot;
  <a href="#citation">BibTeX</a>
</p>

<p align="center">
  <img src="docs/assets/mc-dex-hand-demo.gif" alt="MC-dex-hand robot hand mirroring the wearable data-collection glove" width="800">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/NeurIPS-2026%20Workshop-8C1D40" alt="NeurIPS 2026 Workshop">
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

> **Status:** hardware release in progress. A [visual assembly guide](docs/assembly/README.md)
> covers the main link connections. Firmware, host software and detailed build instructions are TODO.
> **License:** open for commercial use - Apache-2.0 (software), CERN-OHL-P-2.0 (hardware),
> CC BY 4.0 (docs). See [License](#license).

## Paper

Collecting robot demonstrations by teleoperation ties up the robot and is slower than natural human
manipulation. The glove costs about $300 to build and records wrist-camera video, 6-DOF wrist motion
and 8 finger joints without a robot in the loop. Two offline steps adapt each demonstration to the
robot, and neither replays it on the robot hand:

1. **Appearance normalization.** [SAM 2](https://ai.meta.com/sam2) segments visible skin in the wrist camera and recolors it to
   the glove's black, RGB(18, 18, 20).
2. **Temporal alignment.** Ten teleoperated trajectories, collected once per arm and shared across
   tasks, set the robot's execution speed. Every glove episode (video, wrist pose, fingers) is
   resampled to that tempo.

A glove demonstration takes about 6 s to collect. DexUMI's collect-and-replay pipeline takes about
14 s, and its teleoperation baseline about 26 s.

**Real-robot success, 150 glove demonstrations per task (20 trials each).** DexUMI rows are its
published results, not a re-implementation.

| Method | Policy | Cube in Cup demos | Cube in Cup | Egg Carton demos | Egg Carton |
|---|---|---|---|---|---|
| DexUMI | Diffusion | 310 | 0.95 | 175 | 0.90 |
| Ours | ACT | 150 | 0.80 | 150 | 0.75 |
| Ours | GR00T | 150 | 0.75 | 150 | 0.80 |

**Scaling glove data on Cube in Cup**, against 60 teleoperated demonstrations:

| Training data | Demos | ACT | GR00T |
|---|---|---|---|
| Teleoperation | 60 | 0.95 | 0.95 |
| Glove | 60 | 0.65 | 0.60 |
| Glove | 90 | 0.70 | 0.65 |
| Glove | 120 | 0.75 | 0.70 |
| Glove | 150 | 0.80 | 0.75 |
| Glove | 240 | 0.95 | 0.90 |

60 glove demonstrations take about a quarter of the collection time of 60 teleoperated ones. At 240,
ACT matches teleoperation.

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
docs/assembly/       visual guide to the main parts and link connections
docs/paper/          camera-ready paper PDF
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
4. Follow the [visual assembly guide](docs/assembly/README.md) for the main link connections.

## Meet the glove and robot hand

![Wearable glove CAD overview](docs/images/wearable-glove-overview.png)

![Robot hand CAD overview](docs/images/robot-hand-overview.png)

See the [link connection close-ups](docs/assembly/README.md) for a short guide to how the
backplate, proximal links and fingertips fit together.

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

## License

See the [licenses and attribution](NOTICE).

## Citation

```bibtex
@inproceedings{TODO2026democratizing,
  title     = {Democratizing Data-Efficient Robot Learning with Robot-Free Demonstrations},
  author    = {TODO},
  booktitle = {TODO Workshop at the 40th Conference on Neural Information Processing Systems (NeurIPS)},
  year      = {2026},
  url       = {https://github.com/Manual-AI/MC-dex-hand}
}
```
