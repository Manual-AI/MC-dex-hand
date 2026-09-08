# Third-party designs

This file records source and attribution status for the current Quest mount and the
superseded controller cradle. The repository license has not yet been chosen.

## Current Quest mount

- **Files:** `hardware/common/stl/cm_quest_mount_base.stl`,
  `cm_quest_mount_hinged_cap.stl` and `cm_quest_mount_receiver.stl`.
- **CAD source:** the project-local `Quest_mount_assembly.SLDASM`, containing
  `01_Base`, `02_Hinged_cap` and `03_Receiver_8x9`.
- **Source / license:** TODO: confirm authorship, upstream source (if any), and applicable terms.
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
