# Manual-Dex standalone URDF

[`manual_dex.urdf`](manual_dex.urdf) contains the actual CAD-derived robot hand:
**eight revolute joints, nine rigid links, and package-local mesh files**. This is a
derived URDF export of the [native hand MJCF](../hand/scene.xml), not a replacement for
the CAD or an independently invented hand. No OpenArm meshes are included in this
standalone directory. The glove remains available as [native MJCF](../glove/scene.xml).

## Load the gripper

Fetch Git LFS objects first. With MuJoCo installed, from the repository root:

```bash
git lfs pull
python -m mujoco.viewer --mjcf=models/manual_dex/urdf/manual_dex.urdf
```

The default pose is the released CAD pose. Move joints in the viewer to inspect them.
For automatic motion **attached to OpenArm**, use the
[one-command engine tutorials](../../../simulation/README.md).

Keep `manual_dex.urdf` and `meshes/` together. Mesh filenames are relative, not
machine-specific or ROS `package://` paths. OBJ and STL files are stored in Git LFS;
small text pointer files are not usable meshes.

## Frames and named joints

The root link `world_base` is centered at the wrist adaptor's mounting flange, in
metres with Z pointing into the hand. Fixed CAD transforms are baked into root geometry.
When attaching it to another robot, connect this root to the robot's tool flange with
a fixed joint and verify bolt clocking/clearance; see
[`simulation/mount.json`](../../../simulation/mount.json) for the OpenArm example.

| Finger group | Proximal joint | Distal joint |
|---|---|---|
| Index | `md_index_proximal` | `md_index_distal` |
| Middle | `md_middle_proximal` | `md_middle_distal` |
| Ring + little | `md_pinkyring_proximal` | `md_pinkyring_distal` |
| Thumb | `md_thumb_proximal` | `md_thumb_distal` |

Joint coordinates are radians, with the native CAD pose at zero. The `md_` prefix
prevents name collisions when composing the hand with another robot. Native hand MJCF
joint names do not have this prefix. The export preserves hinge axes and relative poses.

## Geometry and physical limitations

Each link has one complete OBJ visual, combining all its CAD occurrences, and one
watertight convex-hull STL collision proxy. Merging visuals accommodates importers such
as SuperDex that only consume the first visual. Display color is uniform per link;
the original MJCF retains finer component colors and metadata.

**This is a kinematic integration asset, not a calibrated dynamics model.** Masses of
1 g, diagonal inertias of 10⁻⁶ kg·m², ±1.5 rad travel bounds, 10 N·m effort limits and
2 rad/s velocity limits are placeholders, not measured hardware or servo specifications.
Convex hulls can fill real openings and are not validated contact geometry. Disable
gravity and contacts for playback, as the engine demos do, until those values are measured
and replaced. The BOM's ABS/PETG choices do not supply inertial or friction calibration.

## Rebuild and verify

From the repository root:

```bash
python3 simulation/run.py prepare
build/simulation/envs/prepare/bin/python simulation/prepare.py --publish-hand
build/simulation/envs/prepare/bin/python simulation/check.py
```

The first command prepares the pinned builder and OpenArm model. The second deliberately
updates the versioned standalone URDF and meshes from the native hand MJCF. The final
command checks mesh availability, closed collision hulls, the 8/15-joint topology and
15-joint MJCF–URDF forward-kinematics agreement. Use a separate commit when publishing
regenerated assets. The exporter supports this model's one-hinge-per-body structure;
it is not a general MJCF-to-URDF converter.

Original Manual-Dex URDF and mesh assets are licensed under [CERN-OHL-P-2.0](LICENSE).
Keep this license and the [notice](NOTICE) when sharing the standalone package.
See [licensing scope](../../../LICENSING.md) and
[third-party provenance](../../../simulation/THIRD_PARTY.md).
