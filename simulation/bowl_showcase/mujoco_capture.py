"""MuJoCo CPU rigid contacts and native OpenGL offscreen renderer."""

import os

os.environ.setdefault("MUJOCO_GL", "egl")
import numpy as np
import mujoco as mj
from common import Capture, DT, HALF, rgb
from xml.etree import ElementTree as ET


def fmt(x):
    return " ".join(str(float(v)) for v in x)


def main():
    c = Capture("mujoco")
    s = c.s
    root = ET.Element("mujoco")
    ET.SubElement(root, "option", timestep=str(DT))
    bodies = ET.SubElement(root, "worldbody")
    for f in s["fixtures"]:
        ET.SubElement(
            bodies,
            "geom",
            type=f["type"],
            size=fmt(f["size"]),
            pos=fmt(f["pos"]),
            quat=fmt(f["quat"]),
        )
    obj = ET.SubElement(bodies, "body", pos=fmt(c.initial[:3]), quat=fmt(c.initial[3:]))
    ET.SubElement(obj, "freejoint")
    ET.SubElement(
        obj,
        "geom",
        type="box",
        size=fmt(HALF),
        mass=str(s["mass"]),
        friction=".65 .004 .0003",
    )
    m = mj.MjModel.from_xml_string(ET.tostring(root, encoding="unicode"))
    d = mj.MjData(m)

    def step(force):
        d.xfrc_applied[1, :3] = force
        mj.mj_step(m, d)
        return d.qpos.copy()

    c.physics(step)
    root = ET.Element("mujoco")
    assets = ET.SubElement(root, "asset")
    world = ET.SubElement(root, "worldbody")
    vis = ET.SubElement(root, "visual")
    ET.SubElement(vis, "global", offwidth=str(s["width"]), offheight=str(s["height"]))
    ET.SubElement(vis, "headlight", ambient=".42 .42 .42", diffuse=".60 .60 .60")
    ET.SubElement(world, "light", pos=".4 -.2 1.6", dir="0 .1 -1", directional="true")
    bodies = []
    for i, pose in enumerate(c.frames[0]):
        bodies.append(
            ET.SubElement(
                world,
                "body",
                name="part" + str(i),
                mocap="true",
                pos=fmt(pose[:3]),
                quat=fmt(pose[3:]),
            )
        )
    for x in s["surfaces"]:
        n = x["name"]
        ET.SubElement(assets, "mesh", name=n, file=str(c.root / (n + ".obj")))
        ET.SubElement(
            bodies[x["body"]],
            "geom",
            type="mesh",
            mesh=n,
            rgba=fmt([*rgb(x["color"]), 1]),
            contype="0",
            conaffinity="0",
        )
    eye = np.array(s["eye"])
    forward = np.array(s["target"]) - eye
    forward /= np.linalg.norm(forward)
    right = np.cross(forward, [0, 0, 1])
    right /= np.linalg.norm(right)
    ET.SubElement(
        world,
        "camera",
        name="shot",
        pos=fmt(eye),
        xyaxes=fmt([*right, *np.cross(right, forward)]),
        fovy=str(s["fov"]),
    )
    m = mj.MjModel.from_xml_string(ET.tostring(root, encoding="unicode"))
    d = mj.MjData(m)
    with mj.Renderer(m, height=s["height"], width=s["width"]) as renderer:
        for i in c.draw:
            d.mocap_pos[:] = c.frames[i, :, :3]
            d.mocap_quat[:] = c.frames[i, :, 3:]
            mj.mj_forward(m, d)
            renderer.update_scene(d, camera="shot")
            c.save_frame(i, renderer.render())
    c.finish(mj.__version__, "MuJoCo offscreen OpenGL")


if __name__ == "__main__":
    main()
