"""Derive a separate dynamic-demo asset package without changing released CAD models."""
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

import mujoco
from native_common import ROOT, NATIVE, SPEC, POLICY, JOINTS


def write_xml(tree, path):
    ET.indent(tree, space="  ")
    ET.ElementTree(tree).write(path, encoding="utf-8", xml_declaration=True)


def main():
    source = ROOT / "build/simulation/generated"
    NATIVE.mkdir(parents=True, exist_ok=True)
    tree = ET.parse(source / "openarm_manual_dex.urdf").getroot()
    for mesh in tree.findall(".//mesh"):
        mesh.set("filename", str((source / mesh.get("filename")).resolve()))
    for link in tree.findall("link"):
        inertial = link.find("inertial")
        if link.get("name").startswith("md_"):
            inertial.find("mass").set("value", str(SPEC["hand_link_mass_kg"]))
            for key in ("ixx", "iyy", "izz"):
                inertial.find("inertia").set(key, str(SPEC["hand_link_diagonal_inertia_kg_m2"]))
        elif link.get("name") == "openarm_link7":
            mass = inertial.find("mass")
            mass.set("value", str(float(mass.get("value")) + SPEC["hand_frame_mass_kg"]))
    for joint in tree.findall("joint"):
        if joint.get("type") == "revolute":
            hand = joint.get("name").startswith("md_")
            joint.find("limit").set("effort", "5" if hand else "150")
            joint.find("dynamics").set("damping", ".01" if hand else ".1")
    write_xml(tree, NATIVE / "robot.urdf")
    model = mujoco.MjModel.from_xml_path(str(NATIVE / "robot.urdf"))
    for point in POLICY["waypoints"]:
        if len(point["q_rad"]) != len(JOINTS):
            raise ValueError("Pick-and-place waypoint must contain all 15 named joints")
        for name, q in zip(JOINTS, point["q_rad"]):
            lower, upper = model.joint(name).range
            if not lower <= q <= upper:
                raise ValueError(f"Pick-and-place waypoint exceeds {name} range: {q}")
    mujoco.mj_saveLastXML(str(NATIVE / "robot.xml"), model)
    # Keep the public engine interchange file standard URDF. Genesis adds its own
    # parser settings and otherwise duplicates this optional MuJoCo extension.
    for extension in tree.findall("mujoco"):
        tree.remove(extension)
    write_xml(tree, NATIVE / "robot.urdf")
    for name in ("OPENARM_LICENSE", "MANUAL_DEX_LICENSE", "MANUAL_DEX_NOTICE"):
        shutil.copy2(source / name, NATIVE / name)
    (NATIVE / "scene-spec.json").write_text(json.dumps(SPEC, indent=2) + "\n")
    print(f"Native demo robot package: {NATIVE}")


if __name__ == "__main__":
    main()
