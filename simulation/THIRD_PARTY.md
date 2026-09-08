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
The project has not yet selected its own license. OpenArm's license does **not** relicense
Manual-Dex. See [`../bom/THIRD_PARTY.md`](../bom/THIRD_PARTY.md) for existing component
authorship and historical attribution.

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
