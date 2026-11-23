"""Assemble OpenArm v1 + Manual-Dex MJCF and portable, single-visual-per-link URDFs.

Upstream OpenArm assets retain Enactic's Apache-2.0 license. This exporter deliberately
supports only the fixed-base, zero-reference, one-hinge-per-body models used here.
It rejects unsupported topology instead of silently changing robot kinematics.
"""
import argparse
import copy
import json
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET

import mujoco
import numpy as np
import trimesh
from scipy.spatial.transform import Rotation

from common import ROOT, BUILD, PACKAGE, JOINT_NAMES


def fmt(values):
    return " ".join(f"{float(x):.12g}" for x in values)


def rotation(quat):
    return Rotation.from_quat(np.asarray(quat)[[1, 2, 3, 0]])


def write_xml(tree, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    ET.indent(tree)
    ET.ElementTree(tree).write(path, encoding="utf-8", xml_declaration=True)


def openarm_source():
    versions = json.loads((ROOT / "simulation/versions.json").read_text())
    dest = BUILD / "vendor/openarm_mujoco"
    new_checkout = not dest.exists()
    if new_checkout:
        dest.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "--no-checkout", "--filter=blob:none",
                        versions["openarm_repository"], str(dest)], check=True)
    # A fresh --no-checkout clone appears to have every tracked file deleted;
    # only inspect dirtiness after the initial checkout has been materialized.
    if not new_checkout and subprocess.check_output(["git", "-C", str(dest), "status", "--porcelain"], text=True).strip():
        raise RuntimeError(f"Refusing to overwrite modified vendor checkout: {dest}")
    if subprocess.run(["git", "-C", str(dest), "cat-file", "-e", versions["openarm_commit"]],
                      capture_output=True).returncode:
        subprocess.run(["git", "-C", str(dest), "fetch", "origin", versions["openarm_commit"]], check=True)
    subprocess.run(["git", "-C", str(dest), "checkout", "--detach", versions["openarm_commit"]], check=True)
    actual = subprocess.check_output(["git", "-C", str(dest), "rev-parse", "HEAD"], text=True).strip()
    assert actual == versions["openarm_commit"]
    return dest / versions["openarm_model"]


def hand_tree():
    source = ROOT / "models/manual_dex/hand"
    tree = ET.parse(source / "scene.xml").getroot()
    # Isolate all native hand names from upstream arm materials, bodies and joints.
    refs = ("name", "mesh", "material", "body", "joint", "texture")
    for element in tree.iter():
        for key in refs:
            if key in element.attrib:
                element.set(key, "md_" + element.get(key))
    for mesh in tree.findall("asset/mesh"):
        mesh.set("file", str((source / "meshes" / mesh.get("file")).resolve()))
    tree.find("compiler").attrib.pop("meshdir", None)
    frame = tree.find("worldbody/body")
    config = json.loads((ROOT / "simulation/mount.json").read_text())
    frame.set("pos", fmt(-np.asarray(config["hand_flange_center_m"])))
    # This fixed body's inertia does not affect standalone motion; keep it explicit
    # for URDF consumers. Like the finger masses, it is NOT a physical estimate.
    ET.SubElement(frame, "inertial", pos="0 0 0", mass=".001", diaginertia="1e-6 1e-6 1e-6")
    return tree


def assembled_tree(source):
    arm = ET.parse(source).getroot()
    arm.set("model", "OpenArm v1 + Manual-Dex | kinematic tutorial")
    for mesh in arm.findall("asset/mesh"):
        mesh.set("file", str((source.parent / "meshes" / mesh.get("file")).resolve()))
    arm.find("compiler").attrib.pop("meshdir", None)
    for tag in ("tendon", "equality", "actuator", "contact"):
        for element in arm.findall(tag):
            arm.remove(element)
    config = json.loads((ROOT / "simulation/mount.json").read_text())
    wrist = arm.find(f".//body[@name='{config['parent_body']}']")
    if wrist is None:
        raise RuntimeError("Pinned OpenArm model does not contain the configured wrist body")
    for child in list(wrist):
        if child.tag == "body" or child.get("name", "").startswith("openarm_hand_"):
            wrist.remove(child)
    hand = hand_tree()
    for asset in hand.find("asset"):
        if asset.tag != "texture":
            arm.find("asset").append(copy.deepcopy(asset))
    mount = ET.SubElement(wrist, "body", name="manual_dex_mount", pos=fmt(config["parent_xyz_m"]))
    quat_xyzw = Rotation.from_euler("xyz", config["parent_rpy_rad"]).as_quat()
    mount.set("quat", fmt(quat_xyzw[[3, 0, 1, 2]]))
    mount.append(copy.deepcopy(hand.find("worldbody/body")))
    # Preserve the source hand's no-collision visual semantics without modifying
    # OpenArm's default classes or relying on the class names in a second model.
    for geom in mount.iter("geom"):
        geom.set("contype", "0")
        geom.set("conaffinity", "0")
        geom.set("density", "0")
        geom.set("group", "1")
    world = arm.find("worldbody")
    base = ET.Element("body", name="openarm_base")
    for child in list(world):
        world.remove(child)
        base.append(child)
    world.append(base)
    ET.SubElement(arm, "option", gravity="0 0 0", timestep=str(1 / 240), integrator="implicitfast")
    for geom in world.iter("geom"):
        geom.set("contype", "0")
        geom.set("conaffinity", "0")
    # Keep a viewer-ready scene with a neutral background and explicit tool marker.
    visual = ET.SubElement(arm, "visual")
    ET.SubElement(visual, "global", offwidth="1280", offheight="960")
    ET.SubElement(world, "light", pos="1 -1 2", dir="-1 1 -2", diffuse=".8 .8 .8")
    ET.SubElement(mount, "site", name="manual_dex_flange", size=".006", rgba="1 .4 .1 1")
    return arm


def body_mesh(model, body, ids):
    pieces = []
    for geom in ids:
        if model.geom_type[geom] != mujoco.mjtGeom.mjGEOM_MESH:
            raise ValueError("Only mesh visuals are supported by this CAD exporter")
        mesh = model.geom_dataid[geom]
        va, vn = model.mesh_vertadr[mesh], model.mesh_vertnum[mesh]
        fa, fn = model.mesh_faceadr[mesh], model.mesh_facenum[mesh]
        vertices = rotation(model.geom_quat[geom]).apply(model.mesh_vert[va:va+vn]) + model.geom_pos[geom]
        pieces.append(trimesh.Trimesh(vertices=vertices, faces=model.mesh_face[fa:fa+fn], process=False))
    return trimesh.util.concatenate(pieces) if pieces else None


def export_urdf(model, destination, name):
    """Bake compiler mesh transforms, preserving all visual parts in one mesh/link."""
    destination.mkdir(parents=True, exist_ok=True)
    meshes = destination / "meshes"
    meshes.mkdir(exist_ok=True)
    robot = ET.Element("robot", name=name)
    # MuJoCo otherwise strips the relative directory from URDF mesh filenames.
    ET.SubElement(ET.SubElement(robot, "mujoco"), "compiler", strippath="false", meshdir=".", discardvisual="false")
    root_name = "world_base"
    for body in range(model.nbody):
        body_name = model.body(body).name if body else root_name
        link = ET.SubElement(robot, "link", name=body_name)
        inertial = ET.SubElement(link, "inertial")
        ET.SubElement(inertial, "origin", xyz=fmt(model.body_ipos[body]),
                      rpy=fmt(rotation(model.body_iquat[body]).as_euler("xyz")))
        mass = max(float(model.body_mass[body]), .001)
        inertia = np.maximum(model.body_inertia[body], 1e-6)
        ET.SubElement(inertial, "mass", value=str(mass))
        ET.SubElement(inertial, "inertia", ixx=str(inertia[0]), iyy=str(inertia[1]), izz=str(inertia[2]),
                      ixy="0", ixz="0", iyz="0")
        ids = [g for g in range(model.ngeom) if model.geom_bodyid[g] == body and model.geom_group[g] != 3]
        surface = body_mesh(model, body, ids)
        if surface is not None:
            # OBJ avoids MuJoCo's 200,000-triangle-per-STL decoder limit on the
            # combined wrist/frame mesh while retaining all detailed CAD geometry.
            surface.export(meshes / f"{body_name}.obj")
            visual = ET.SubElement(link, "visual")
            ET.SubElement(ET.SubElement(visual, "geometry"), "mesh", filename=f"meshes/{body_name}.obj")
            color = "0.36 0.48 0.55 1" if body_name.startswith("md_") else "0.38 0.39 0.42 1"
            ET.SubElement(ET.SubElement(visual, "material", name=f"{body_name}_color"), "color", rgba=color)
            # Watertight per-link proxy; explicit opt-in use in contact experiments.
            # Quantize before hulling: float32 STL serialization otherwise collapses
            # nearly coincident CAD vertices and can open an apparently closed hull.
            hull = trimesh.convex.convex_hull(np.unique(np.round(surface.vertices, 6), axis=0))
            hull.export(meshes / f"{body_name}_collision.stl")
            check = trimesh.load_mesh(meshes / f"{body_name}_collision.stl")
            if not check.is_watertight or not np.isfinite(check.volume) or check.volume <= 0:
                raise RuntimeError(f"Invalid serialized collision proxy: {body_name}")
            collision = ET.SubElement(link, "collision")
            ET.SubElement(ET.SubElement(collision, "geometry"), "mesh", filename=f"meshes/{body_name}_collision.stl")
        if body == 0:
            continue
        count = model.body_jntnum[body]
        if count > 1:
            raise ValueError("Multiple joints on one body are not supported")
        moving = count == 1
        joint_id = model.body_jntadr[body]
        if moving:
            assert model.jnt_type[joint_id] == mujoco.mjtJoint.mjJNT_HINGE
            assert np.allclose(model.jnt_pos[joint_id], 0)
            assert model.qpos0[model.jnt_qposadr[joint_id]] == 0
        joint = ET.SubElement(robot, "joint", name=model.joint(joint_id).name if moving else f"fixed_{body_name}",
                              type="revolute" if moving else "fixed")
        parent = model.body_parentid[body]
        ET.SubElement(joint, "parent", link=model.body(parent).name if parent else root_name)
        ET.SubElement(joint, "child", link=body_name)
        ET.SubElement(joint, "origin", xyz=fmt(model.body_pos[body]),
                      rpy=fmt(rotation(model.body_quat[body]).as_euler("xyz")))
        if moving:
            ET.SubElement(joint, "axis", xyz=fmt(model.jnt_axis[joint_id]))
            ET.SubElement(joint, "limit", lower=str(model.jnt_range[joint_id, 0]),
                          upper=str(model.jnt_range[joint_id, 1]), effort="10", velocity="2")
            ET.SubElement(joint, "dynamics", damping="0.01", friction="0")
    write_xml(robot, destination / f"{name}.urdf")


def fused_model(tree):
    # URDF runtimes such as SuperDex require physical links with finite geometry.
    # Fuse fixed transforms into adjacent links so there are no empty mount bodies.
    tree = copy.deepcopy(tree)
    tree.find("compiler").set("fusestatic", "true")
    return mujoco.MjModel.from_xml_string(ET.tostring(tree, encoding="unicode"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--publish-hand", action="store_true", help="Update the versioned standalone URDF package")
    args = parser.parse_args()
    PACKAGE.mkdir(parents=True, exist_ok=True)
    source = openarm_source()
    assembled = assembled_tree(source)
    write_xml(assembled, PACKAGE / "openarm_manual_dex.xml")
    model = mujoco.MjModel.from_xml_path(str(PACKAGE / "openarm_manual_dex.xml"))
    assert model.nq == 15
    assert {model.joint(i).name for i in range(model.njnt)} == set(JOINT_NAMES)
    export_urdf(fused_model(assembled), PACKAGE, "openarm_manual_dex")
    shutil.copy2(source.parents[1] / "LICENSE", PACKAGE / "OPENARM_LICENSE")
    shutil.copy2(ROOT / "hardware/LICENSE", PACKAGE / "MANUAL_DEX_LICENSE")
    shutil.copy2(ROOT / "hardware/NOTICE", PACKAGE / "MANUAL_DEX_NOTICE")
    if args.publish_hand:
        hand = hand_tree()
        write_xml(hand, PACKAGE / "manual_dex.xml")
        export_urdf(fused_model(hand), ROOT / "models/manual_dex/urdf", "manual_dex")
        for filename in ("LICENSE", "NOTICE"):
            shutil.copy2(ROOT / "hardware" / filename, ROOT / "models/manual_dex/urdf" / filename)
    (PACKAGE / "provenance.json").write_text(json.dumps({
        "versions": json.loads((ROOT / "simulation/versions.json").read_text()),
        "mount": json.loads((ROOT / "simulation/mount.json").read_text()),
        "joint_names": JOINT_NAMES,
        "licenses": {"openarm": "Apache-2.0", "manual_dex_hardware": "CERN-OHL-P-2.0"},
        "dynamics_validated": False,
        "collision_geometry": "Unvalidated, watertight convex-hull proxy per rigid link"
    }, indent=2) + "\n")
    print(f"Prepared 15-joint MJCF + URDF: {PACKAGE}", flush=True)


if __name__ == "__main__":
    main()
