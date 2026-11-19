# Third-party designs

This file records the licenses of third-party software and hardware used with MC-dex-hand, and
source and attribution status for the Quest mount and the superseded controller cradle.
MC-dex-hand itself is Apache-2.0 (software), CERN-OHL-P-2.0 (hardware) and CC BY 4.0 (docs);
see `NOTICE`. Every component below also permits commercial use under its own license.

## Software and models used by the pipeline

These are dependencies, not copied into this repository. Each keeps its own license.

| Component | Used for | License | Source |
|---|---|---|---|
| SAM 2 (Meta) | segmenting visible skin in the wrist camera | Apache-2.0 (code and checkpoints) | <https://ai.meta.com/sam2> |
| LeRobot (Hugging Face) | recording, dataset format, ACT training | Apache-2.0 | <https://github.com/huggingface/lerobot> |
| ACT | policy architecture | MIT | <https://github.com/tonyzhaozh/act> |
| Isaac GR00T (NVIDIA) | policy architecture | Apache-2.0 (code); NVIDIA Open Model License (weights) | <https://github.com/NVIDIA/Isaac-GR00T> |
| Feetech servo SDK (`ftservo`) | robot hand servo bus | MIT | vendored in the host software |
| OpenArm (Enactic) | robot arm used in the paper | Apache-2.0 (software); CERN-OHL-S-2.0 (hardware) | <https://github.com/enactic/openarm> |

`rh_openarm_adaptor` is an original part that bolts to the OpenArm flange. It contains no OpenArm
design files, so OpenArm's CERN-OHL-S hardware license does not apply to it.

The GR00T weights are not redistributed here. Download them from NVIDIA and accept the NVIDIA
Open Model License yourself.

## Current Quest mount

- **Files:** `hardware/common/stl/cm_quest_mount_base.stl`,
  `cm_quest_mount_hinged_cap.stl` and `cm_quest_mount_receiver.stl`.
- **CAD source:** the project-local `Quest_mount_assembly.SLDASM`, containing
  `01_Base`, `02_Hinged_cap` and `03_Receiver_8x9`.
- **Author:** Roman (Manual Cognition), who confirmed that the new mount is his own design.
- **Source / license:** original project design; no third-party attribution is required for
  this mount. It is covered by the repository's hardware license, CERN-OHL-P-2.0.
- **Receiver modification:** four rectangular pads retained at 8 x 5 x 3 mm;
  centered edge-to-edge gaps changed from 6 x 11 mm to 8 x 9 mm.

## Superseded Quest controller adapters (`cm_quest_adapter_lower`, `cm_quest_adapter_upper`)

- **Origin:** "Quest adapter" 3D print files published by the udCap VR Gloves project,
  <https://udcap-vr-gloves-document.gitbook.io/udcap/hardware-setup/other-adapter-3d-print-file>
- **Modifications:** minor geometry changes to mount the cradle to this glove / robot hand
  (TODO: describe exactly what changed).
- **License:** the source page states no license. udCap were contacted on TODO-date to ask for
  permission to redistribute the modified files; status: **pending**.
  Until permission is granted these files are **not covered by the repository license** and are
  provided for personal, non-commercial use only. If you need different terms, download the
  originals from udCap and apply the modifications described above yourself.

These two legacy adapter STLs have been removed from the current release and BOM.
This attribution is retained for the files in earlier revisions.
