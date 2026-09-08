"""Verify composed MJCF/URDF topology, assets, mount frames and joint trajectories."""
from pathlib import Path
import xml.etree.ElementTree as ET

import mujoco
import numpy as np
import trimesh

from common import ROOT, PACKAGE, JOINT_NAMES, target_positions


def check_assets(path, expected_joints):
    tree = ET.parse(path)
    moving = [j for j in tree.findall("joint") if j.get("type") != "fixed"]
    assert len(moving) == expected_joints
    links = {l.get("name") for l in tree.findall("link")}
    children = [j.find("child").get("link") for j in tree.findall("joint")]
    assert len(set(children)) == len(children), "A child has multiple parent joints"
    assert len(links - set(children)) == 1, "URDF must have exactly one root"
    count = 0
    for link in tree.findall("link"):
        assert len(link.findall("visual")) == 1, "Keep exactly one complete visual per link for SuperDex"
        for mesh in link.findall(".//mesh"):
            file = (path.parent / mesh.get("filename")).resolve()
            assert file.is_relative_to(path.parent.resolve()), "URDF must use package-local mesh assets"
            assert file.is_file(), file
            with file.open("rb") as stream:
                assert not stream.read(80).startswith(b"version https://git-lfs"), f"Missing LFS object: {file}"
            count += 1
        collision = path.parent / link.find("collision/geometry/mesh").get("filename")
        surface = trimesh.load_mesh(collision)
        assert surface.is_watertight and np.isfinite(surface.volume) and surface.volume > 0, collision
    print(f"{path.name}: {expected_joints} joints, one root, {count} local meshes, closed collision proxies")


def main():
    for published, original in (("MANUAL_DEX_LICENSE", "LICENSE"), ("MANUAL_DEX_NOTICE", "NOTICE")):
        assert (PACKAGE / published).read_bytes() == (ROOT / "hardware" / original).read_bytes()
        assert (ROOT / "models/manual_dex/urdf" / original).read_bytes() == (ROOT / "hardware" / original).read_bytes()
    urdf_path = PACKAGE / "openarm_manual_dex.urdf"
    check_assets(urdf_path, 15)
    check_assets(ROOT / "models/manual_dex/urdf/manual_dex.urdf", 8)
    hand = mujoco.MjModel.from_xml_path(str(ROOT / "models/manual_dex/urdf/manual_dex.urdf"))
    assert hand.nq == 8
    native = mujoco.MjModel.from_xml_path(str(PACKAGE / "openarm_manual_dex.xml"))
    portable = mujoco.MjModel.from_xml_path(str(urdf_path))
    assert native.nq == portable.nq == 15
    assert {native.joint(i).name for i in range(native.njnt)} == set(JOINT_NAMES)
    assert {portable.joint(i).name for i in range(portable.njnt)} == set(JOINT_NAMES)
    a, b = mujoco.MjData(native), mujoco.MjData(portable)
    for t in (0, 1.25, 2.5, 4.95):
        for name, value in target_positions(t).items():
            assert native.joint(name).range[0] <= value <= native.joint(name).range[1]
            a.joint(name).qpos[:] = b.joint(name).qpos[:] = value
        mujoco.mj_forward(native, a)
        mujoco.mj_forward(portable, b)
        for name in JOINT_NAMES:
            source_body = native.joint(name).bodyid[0]
            target_body = portable.joint(name).bodyid[0]
            np.testing.assert_allclose(a.xpos[source_body], b.xpos[target_body], atol=2e-7, rtol=0)
            np.testing.assert_allclose(a.xmat[source_body], b.xmat[target_body], atol=2e-7, rtol=0)
    print("MJCF and URDF forward kinematics agree for all 15 joints at four articulated poses")


if __name__ == "__main__":
    main()
