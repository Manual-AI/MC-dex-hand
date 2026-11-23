# Simulation dependency and asset provenance

## OpenArm

- Source: [Enactic OpenArm MuJoCo models](https://github.com/enactic/openarm_mujoco).
- Revision: [`a8c979629f2591ad035d99d338ce114969e6cddc`](https://github.com/enactic/openarm_mujoco/tree/a8c979629f2591ad035d99d338ce114969e6cddc).
- Input: `v1/openarm.xml` and its referenced mesh files.
- License: [Apache License 2.0](https://github.com/enactic/openarm_mujoco/blob/a8c979629f2591ad035d99d338ce114969e6cddc/LICENSE).

The launcher downloads these assets into the ignored build directory. The builder
removes the stock parallel-jaw gripper and controls, attaches Manual-Dex, adds inspection
lighting and exports merged visual meshes and convex collision proxies. It copies the
upstream license to `build/simulation/generated/OPENARM_LICENSE` and records the revision
and mount configuration in `provenance.json`. Preserve the license and provenance when
redistributing an assembled package; satisfy the upstream license's other requirements.
The standalone versioned Manual-Dex URDF does not contain OpenArm geometry.

## Manual-Dex

The hand comes from this repository's original CAD-derived MJCF and mesh assets.
The original Manual-Dex hardware models use **CERN-OHL-P-2.0**; the simulation scripts
and tutorials use **Apache-2.0**. See the [licensing scope](../LICENSING.md).
OpenArm's license does **not** relicense Manual-Dex, and Manual-Dex's licenses do not
replace OpenArm's. The builder includes `MANUAL_DEX_LICENSE` and `MANUAL_DEX_NOTICE`
alongside `OPENARM_LICENSE` in the assembled output. Preserve the applicable notices
and license copies when redistributing it. See [`../bom/THIRD_PARTY.md`](../bom/THIRD_PARTY.md)
for existing component authorship and historical attribution.

## Runtime packages

Engine packages are installed into local ignored environments; their source and binary
distributions retain their own licenses. Version pins are in each engine's requirements
file, and interpreter/upstream pins are in [`versions.json`](versions.json).

- [MuJoCo](https://github.com/google-deepmind/mujoco)
- [Genesis](https://github.com/Genesis-Embodied-AI/Genesis)
- [SuperDex](https://github.com/facebookresearch/project_superdex)
- [Isaac Sim](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_python.html)

Isaac Sim requires the user's explicit agreement to NVIDIA's terms. The launcher exposes
`--accept-isaac-eula` for that choice; it does not infer agreement from a request to run
other engines. Using an existing accepted installation does not install or modify it.

## Browser demo

The [interactive bowl scene](browser/bowl/scene.xml) uses the same pinned OpenArm and MC-Dex models described above. The browser package includes simplified CAD visual meshes, convex palm and finger collision meshes, actuator settings, a bench, a bowl and the object catalog. The [mesh archive](browser/assets/meshes.tar.gz) contains standard STL files. Retained notices accompany the package. [OpenArm license](browser/licenses/OPENARM_LICENSE) · [MC-Dex hardware license](browser/licenses/MANUAL_DEX_LICENSE) · [MC-Dex notice](browser/licenses/MANUAL_DEX_NOTICE).

The vertical pedestal uses the six torso visual parts and the right shoulder transform from the pinned OpenArm bimanual model. The simplified torso meshes retain their upstream black and silver material groups. The worktable height, pedestal position relative to the table and inverse-kinematics calibration are specific to this task. [Upstream bimanual assembly](https://github.com/enactic/openarm_mujoco/blob/a8c979629f2591ad035d99d338ce114969e6cddc/v1/openarm_bimanual.xml).

The browser assigns materials to individual CAD surfaces. The MC-Dex palm and finger shells use the warm white visible in the prototype footage. The Quest has a white body and dark upper face, the camera has a green PCB and black M12 lens holder, and the eight Feetech servos have red housings with black ends. OpenArm uses the matte black and silver materials assigned to its links in the pinned model. [Appearance map](browser/assets/appearance.json) · [Prototype footage](../docs/assets/prototype-preview.gif) · [MC-Dex part register](../models/manual_dex/hand/parts.json) · [OpenArm materials](https://github.com/enactic/openarm_mujoco/blob/a8c979629f2591ad035d99d338ce114969e6cddc/v1/openarm.xml) · [Feetech product reference](https://ftservo.github.io/ftservo-wiki/products/models/hl-3606-c002/main/).

The WebAssembly engine and JavaScript loader come from `@mujoco/mujoco@3.6.0`. The loader starts with an empty worker pool and the scene compiles serially so the demo can run on a plain local static server. The graphics modules come from `three@0.180.0`. [MuJoCo source](https://github.com/google-deepmind/mujoco/tree/3.6.0/wasm) · [MuJoCo license](browser/licenses/MUJOCO_LICENSE) · [Upstream third-party notices](browser/licenses/MUJOCO_THIRD_PARTY.txt) · [Three.js license](browser/licenses/THREE_LICENSE).

The bowl policy uses the SuperMimic actor architecture from Leor’s mc-lrl implementation, with an object-conditioned trajectory decoder developed for this task. [Upstream attribution](https://github.com/Manual-AI/mc-lrl/blob/75e20985340c5424b39e1bf0268885e6d6b89c27/NOTICE.md) · [Controller and browser tests](browser/bowl/README.md).

The bowl task reuses the same OpenArm and MC-Dex geometry, MuJoCo runtime and Three.js renderer. Its bowl and 16 object models were constructed for this project from simple solids. The browser loads sampled object surfaces and trained weights for a PointNet-style encoder and the task-specific action-chunk policy. [Object catalog](browser/bowl/objects.json) · [Bowl policy and evaluation](browser/bowl/README.md) · [PointNet project](https://stanford.edu/~rqi/pointnet/).

The scripted bowl comparison uses independently installed engines. The Alloy panel uses its native camera, and the Steel panel uses SolverSteel and Newton ViewerGL. Engine binaries are obtained from their respective distributions. [Native capture environments](bowl_showcase/README.md) · [Alloy](https://alloy.argonrobotics.ai/) · [Steel and its Newton integration](https://github.com/skild-ai/steel).
