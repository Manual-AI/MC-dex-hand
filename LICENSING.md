# Manual-Dex licensing

Copyright 2026 Manual-Dex contributors.

Manual-Dex's original software and hardware designs are made available under permissive
open-source licenses. You may use, study, modify, share and redistribute them, including
for commercial purposes, without a license fee, subject to the applicable license terms.
You may manufacture and sell products based on the licensed hardware designs.

## Which license applies?

The default license for original project material is **Apache-2.0**, except for the
hardware-design material explicitly identified below and third-party exceptions.
This is a split by material, not a choice of either license for every file.

| Original project material | Applicable license |
|---|---|
| Software, firmware, Python tools, SolidWorks macros, simulation scripts, configuration and tutorials | [Apache License 2.0](LICENSE), SPDX `Apache-2.0` |
| General documentation, README files, photographs and demonstration animations, except the hardware-design records below | [Apache License 2.0](LICENSE) |
| All design files under `hardware/`, including STEP, STL, native CAD and any future PCB/schematic files | [CERN Open Hardware Licence v2 — Permissive](hardware/LICENSE), SPDX `CERN-OHL-P-2.0` |
| CAD-derived robot models, URDF/MJCF, meshes, and part/joint records under `models/manual_dex/` | [CERN-OHL-P-2.0](models/manual_dex/LICENSE) |
| BOM source CSVs and generated `bom/BOM.md`; `docs/assembly/`, `docs/images/`, and `docs/visualization/PARTS.md` hardware-design/assembly records | [CERN-OHL-P-2.0](hardware/LICENSE) |

The hardware rows expressly designate those original design materials as Covered Source
under **CERN-OHL-P-2.0**. General README and explanatory documentation within these
hardware/model directories also use CERN-OHL-P-2.0 so each such directory can be shared
as a coherent hardware-source package. License texts themselves retain their authors'
notices and are reproduced unchanged.

## Reuse and distribution

Both licenses permit private and commercial use and modification. Neither requires
you to release your own modifications under the same license. Preserve applicable
copyright, attribution and license notices, provide license copies where required,
and identify changes as required by the applicable license. For CERN-OHL-P-2.0 hardware,
make applicable notices available to recipients of the products you manufacture.
These are plain-language pointers; the full license texts govern.

The project is provided **as is, without warranty**. These licenses do not certify
hardware safety, grant unrestricted trademark rights, or clear rights held by unrelated
third parties. Buying parts, manufacturing hardware and operating infrastructure may
still cost money; permission to use the project's licensed work has no license fee.

When sharing a hardware/model package separately, include its CERN-OHL-P-2.0 license
and the [hardware notice](hardware/NOTICE). The standalone URDF directory includes both.
The simulation builder includes `MANUAL_DEX_LICENSE`, `MANUAL_DEX_NOTICE` and the separate
`OPENARM_LICENSE` with generated OpenArm + Manual-Dex packages.

## Third-party material

Existing third-party notices and licenses take precedence for the material they cover.
This licensing decision grants rights only in material the Manual-Dex contributors
are entitled to license. It does not relicense external engines, upstream robot models,
manufacturer-owned component designs, or other third-party intellectual property.

- [Hardware provenance and historical exclusions](bom/THIRD_PARTY.md): the superseded
  udCap adapters are absent from the current release. Their permissions remain unresolved
  in Git history; the new licenses do not retrospectively license those files.
- [Simulation dependencies and OpenArm attribution](simulation/THIRD_PARTY.md): OpenArm
  retains Apache-2.0; each engine retains its own terms. NVIDIA's Isaac Sim EULA still
  applies to Isaac Sim, not to the project's original tutorial code.

## License texts and GitHub detection

The root [`LICENSE`](LICENSE) is the unmodified
[Apache Software Foundation text](https://www.apache.org/licenses/LICENSE-2.0.txt).
The hardware license is the standard
[SPDX CERN-OHL-P-2.0 text](https://spdx.org/licenses/CERN-OHL-P-2.0.html), with its
permissive variant described by [CERN](https://cern-ohl.web.cern.ch/).

The license files are ordinary Git-tracked text, not Git LFS assets. The root Apache
license is kept separate from this scope guide and the thank-you notice to support
[GitHub's standard license detection](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository).
A repository-level badge cannot express every path-specific license or dependency.

## Thank you

Thank you to the open-source community. Manual-Dex is free to use and modify, including
for commercial use, under the licenses above. We welcome sharing, improvements and new
applications. This acknowledgment adds no restrictions or conditions to those licenses.
