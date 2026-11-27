# Third-party designs

This file records the licenses of third-party software and hardware used with MC-dex-hand, and
source and attribution status for the Quest mount and the superseded controller cradle.
See the [licensing guide](../LICENSING.md) for original project material and the
[simulation notices](../simulation/THIRD_PARTY.md) for the OpenArm model and engine dependencies.

## Software and models used by the pipeline

These are dependencies, not copied into this repository. Each keeps its own license.

| Component | Used for | License | Source |
|---|---|---|---|
| SAM 2 (Meta) | segmenting visible skin in the wrist camera | Apache-2.0 (code and checkpoints) | <https://ai.meta.com/sam2> |
| LeRobot (Hugging Face) | recording, dataset format, ACT training | Apache-2.0 | <https://github.com/huggingface/lerobot> |
| ACT | policy architecture | MIT | <https://github.com/tonyzhaozh/act> |
| Isaac GR00T (NVIDIA) | policy architecture | Apache-2.0 (code); NVIDIA Open Model License (weights) | <https://github.com/NVIDIA/Isaac-GR00T> |
| Feetech servo SDK (`ftservo`) | robot hand servo bus | MIT | [Feetech SDK](https://github.com/ftservo/FTServo_Python) |
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
- **Source / license:** original MC-DexHand design under the [hardware terms](../hardware/LICENSE).
- **Receiver modification:** four rectangular pads retained at 8 x 5 x 3 mm;
  centered edge-to-edge gaps changed from 6 x 11 mm to 8 x 9 mm.

## Superseded Quest controller adapters (`cm_quest_adapter_lower`, `cm_quest_adapter_upper`)

- **Origin:** "Quest adapter" 3D print files published by the udCap VR Gloves project,
  <https://udcap-vr-gloves-document.gitbook.io/udcap/hardware-setup/other-adapter-3d-print-file>
- **Modifications:** minor geometry changes to mount the cradle to this glove / robot hand
  (TODO: describe exactly what changed).
- **License:** no license was identified in the existing source record; permission to
  redistribute the modified files remains **pending**, with no dated grant recorded here.
  These historical files are **not covered by Apache-2.0 or CERN-OHL-P-2.0**. The project
  cannot grant personal, non-commercial or commercial permissions on udCap's behalf.
  Obtain permission or applicable terms from the original rightsholder before reusing them.

These two legacy adapter STLs have been removed from the current release and BOM.
This attribution is retained for the files in earlier revisions.
