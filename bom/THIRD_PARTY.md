# Third-party designs

This file records source and attribution status for the current Quest mount and the
superseded controller cradle. Original project hardware uses
[CERN-OHL-P-2.0](../hardware/LICENSE); see the [licensing scope](../LICENSING.md).
This does not grant rights in third-party material that the project does not own.

## Current Quest mount

- **Files:** `hardware/common/stl/cm_quest_mount_base.stl`,
  `cm_quest_mount_hinged_cap.stl` and `cm_quest_mount_receiver.stl`.
- **CAD source:** the project-local `Quest_mount_assembly.SLDASM`, containing
  `01_Base`, `02_Hinged_cap` and `03_Receiver_8x9`.
- **Author:** Roman (Manual Cognition), who confirmed that the new mount is his own design.
- **Source / license:** original project design; no third-party attribution is required for
  this mount. It is released under **CERN-OHL-P-2.0**, with the project's other original
  hardware designs. The authorship record above remains applicable.
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
