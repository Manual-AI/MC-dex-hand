# Third-party designs

For the bundled simulation models and browser libraries, see the [simulation credits](../simulation/THIRD_PARTY.md).

## Components used by the project

| Component | Used for | License | Source |
|---|---|---|---|
| SAM 2 (Meta) | segmenting visible skin in the wrist camera | Apache-2.0 (code and checkpoints) | <https://ai.meta.com/sam2> |
| LeRobot (Hugging Face) | recording, dataset format, ACT training | Apache-2.0 | <https://github.com/huggingface/lerobot> |
| ACT | policy architecture | MIT | <https://github.com/tonyzhaozh/act> |
| Isaac GR00T (NVIDIA) | policy architecture | [Code and model licenses](https://github.com/NVIDIA/Isaac-GR00T#license) | <https://github.com/NVIDIA/Isaac-GR00T> |
| Feetech servo SDK (`ftservo`) | robot hand servo bus | MIT | [Feetech SDK](https://github.com/ftservo/FTServo_Python) |
| OpenArm (Enactic) | robot arm used in the paper | [Software (Apache-2.0)](https://github.com/enactic/openarm/blob/main/LICENSE) · [Hardware (CERN-OHL-S-2.0)](https://github.com/enactic/openarm_hardware/blob/main/LICENSE.txt) | <https://github.com/enactic/openarm> |

The [wrist adapter](../hardware/robot_hand/stl/rh_openarm_adaptor.stl) connects the MC-DexHand frame to the OpenArm flange.

The [PiPER wrist adapter](../hardware/robot_hand/stl/rh_piper_adaptor.stl) is a separate STL outside the standard hand BOM. Its source CAD is unrecorded.

## Purchased components in the CAD

The [hand](../models/manual_dex/hand/parts.json) and [glove](../models/manual_dex/glove/parts.json) registers identify geometry for the Feetech servos, Bourns potentiometers, Quest controller, ESP32 module and bearings. CAD authorship and redistribution terms for those component representations are unverified.

## Current Quest mount

- **Files:** `hardware/common/stl/cm_quest_mount_base.stl`,
  `cm_quest_mount_hinged_cap.stl` and `cm_quest_mount_receiver.stl`.
- **CAD source:** the project-local `Quest_mount_assembly.SLDASM`, containing
  `01_Base`, `02_Hinged_cap` and `03_Receiver_8x9`.
- **Design credit:** Roman, Manual Cognition. [Hardware terms](../hardware/LICENSE).
- **Receiver modification:** four rectangular pads retained at 8 x 5 x 3 mm;
  centered edge-to-edge gaps changed from 6 x 11 mm to 8 x 9 mm.

## Superseded Quest controller adapters (`cm_quest_adapter_lower`, `cm_quest_adapter_upper`)

Earlier revisions contain modified [udCap VR Gloves Quest adapter files](https://udcap-vr-gloves-document.gitbook.io/udcap/hardware-setup/other-adapter-3d-print-file). No redistribution permission is recorded for those files. The current release uses the three-part mount above.
