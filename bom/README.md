# Bill of materials

Use the [print and purchase lists](BOM.md) for quantities, materials and part numbers.
The [robot-hand CSV](robot_hand.csv) and [glove CSV](glove.csv) are the source data.

## Hardware comparison

| Component | Robot hand | Wearable glove |
|---|---|---|
| Finger joints | Two per group for the index, middle, coupled ring/little fingers and thumb (eight total) | Same joint arrangement and fingertip contact geometry |
| Actuation or sensing | Eight Feetech HLS3606 dual-shaft serial-bus servos | Eight Bourns 3382G-2-103G rotary potentiometers read by an ESP32 Feather |
| Wrist pose and mounting | OpenArm wrist-flange adaptor. The Quest mount matches the glove’s controller placement. | A rigidly mounted Meta Quest Touch Plus controller provides six-degree-of-freedom wrist tracking. |
| Wrist camera | 2 MP USB camera | Same camera module and mounting pose |
| Printed structure | FDM-printed ABS or PETG | FDM-printed ABS or PETG |

## Find a part

- **Printing.** Download the [hand STLs](../hardware/robot_hand/stl/), [glove STLs](../hardware/glove/stl/) and [shared STLs](../hardware/common/stl/). The filenames begin with `rh_`, `gl_` and `cm_`, respectively. The [rename map](rename_map.csv) connects the BOM IDs and CAD names to release filenames.
- **Assembly.** The [robot hand STEP](../hardware/step/mc_dex_hand_robot_hand.step) and [glove STEP](../hardware/step/mc_dex_hand_glove.step) show part placement. The [assembly guide](../docs/assembly/README.md) covers the finger joints and shared mounts.
- **Reading the CSVs.** `RH-` and `GL-` identify the assembly. `0xx` denotes printed parts, `1xx` purchased parts represented in CAD, and `2xx` purchased hardware outside the assembly model. Use the `qty`, `make_buy`, `status` and `mirror_for_left` fields when filtering parts.

## Regenerate the release files

From the repository root, run `python3 tools/gen_bom_md.py` after editing either parts CSV.
The [SolidWorks export macro](../tools/solidworks/export_cad.bas) exports the printable STLs and assembly STEP.
Run the [placement tool](../tools/place_exports.py) with one combined export directory or the hand and glove directories as separate arguments.

```bash
python3 tools/place_exports.py path/to/hand/export path/to/glove/export
```

The tool places recognized STLs and STEP assemblies and reports missing BOM parts.
Review `git diff` before committing. On Windows, `setup_and_push.bat` wraps the same import.
Its separate `--push` mode publishes commits on the checked-out branch to the configured `origin`.
For third-party component attribution, see the [source and license records](THIRD_PARTY.md).
