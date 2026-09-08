"""MuJoCo-native offscreen rendering with joint drives, gravity and table contacts."""
import os
from contextlib import nullcontext
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

os.environ.setdefault("MUJOCO_GL", "egl")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from native_common import NATIVE, SPEC, JOINTS, DT, STEPS, STRIDE, targets, arguments, Evidence, boxes
import mujoco
import numpy as np


def fmt(values):
    return " ".join(map(str, values))


def main():
    args = arguments("MuJoCo")
    tree = ET.parse(NATIVE / "robot.xml").getroot()
    tree.set("model", "Manual-Dex native MuJoCo tabletop drive demo")
    option = tree.find("option")
    if option is None:
        option = ET.SubElement(tree, "option")
    option.set("gravity", fmt(SPEC["gravity_m_s2"]))
    option.set("timestep", str(DT))
    option.set("integrator", "implicitfast")
    visual = tree.find("visual")
    if visual is None:
        visual = ET.SubElement(tree, "visual")
    ET.SubElement(visual, "global", offwidth="580", offheight="460")
    asset = tree.find("asset")
    for mesh in asset.findall("mesh"):
        path = Path(mesh.get("file"))
        if not path.is_absolute():
            mesh.set("file", str((NATIVE / path).resolve()))
    ET.SubElement(asset, "texture", name="sky", type="skybox", builtin="gradient",
        rgb1=".93 .95 .97", rgb2=".8 .84 .88", width="512", height="3072")
    # Robot/environment contacts enabled; per-link convex proxies, no self-collision.
    for geom in tree.findall(".//geom"):
        if geom.get("contype", "1") == "0":
            continue
        geom.set("contype", "1")
        geom.set("conaffinity", "2")
        geom.set("group", "3")
    world = tree.find("worldbody")
    eye, lookat = np.array(SPEC["camera"]["eye"]), np.array(SPEC["camera"]["target"])
    forward = lookat-eye
    forward /= np.linalg.norm(forward)
    right = np.cross(forward, [0., 0., 1.])
    right /= np.linalg.norm(right)
    up = np.cross(right, forward)
    ET.SubElement(world, "camera", name="inspection", pos=fmt(eye), xyaxes=fmt([*right, *up]),
                  fovy=str(SPEC["camera"]["fov_deg"]))
    ET.SubElement(world, "light", pos="0 -1 2", dir="0 .5 -1", directional="true",
                  ambient=".35 .35 .35", diffuse=".7 .7 .7")
    ET.SubElement(world, "geom", name="floor", type="plane", pos="0 0 -.77", size="100 100 .1",
        rgba=".78 .81 .85 1", contype="2", conaffinity="3")
    for name, pos, size, color in boxes():
        ET.SubElement(world, "geom", name=name, type="box", pos=fmt(pos), size=fmt(np.array(size)/2),
            rgba=fmt([*color, 1]), contype="2", conaffinity="3", friction=".7 .01 .001")
    cube = SPEC["cube"]
    body = ET.SubElement(world, "body", name="free_cube", pos=fmt(cube["center"]))
    ET.SubElement(body, "freejoint", name="cube_free")
    ET.SubElement(body, "geom", name="cube", type="box", size=fmt(np.array(cube["size"])/2),
        mass=str(cube["mass_kg"]), rgba=fmt([*cube["color"], 1]), contype="2", conaffinity="3",
        friction=".7 .01 .001", solref=".01 1")
    actuator = ET.SubElement(tree, "actuator")
    for name in JOINTS:
        kind = "hand" if name.startswith("md_") else "arm"
        joint = tree.find(f".//joint[@name='{name}']")
        joint.set("armature", ".001" if kind == "hand" else ".01")
        ET.SubElement(actuator, "position", name=name, joint=name, kp=str(SPEC[f"{kind}_kp"]),
            kv=str(SPEC[f"{kind}_kd"]), forcerange="-5 5" if kind == "hand" else "-150 150")
    model = mujoco.MjModel.from_xml_string(ET.tostring(tree, encoding="unicode"))
    data = mujoco.MjData(model)
    # Set only the initial state; every subsequent robot pose comes from dynamics.
    for name, value in targets(0).items():
        data.joint(name).qpos[0] = value
    mujoco.mj_forward(model, data)
    vis = mujoco.MjvOption()
    vis.geomgroup[3] = 0
    evidence = Evidence("mujoco", "MuJoCo OpenGL/EGL")
    cube_geom = model.geom("cube").id
    with (nullcontext() if args.no_render else mujoco.Renderer(model, height=460, width=580)) as renderer:
        for step in range(1 if args.preview else STEPS):
            target = targets(step*DT)
            data.ctrl[:] = [target[name] for name in JOINTS]
            mujoco.mj_step(model, data)
            mujoco.mj_forward(model, data)
            evidence.record(step, {name: data.joint(name).qpos[0] for name in JOINTS},
                data.body("free_cube").xpos,
                any(c.geom1 == cube_geom or c.geom2 == cube_geom for c in data.contact[:data.ncon]))
            if args.preview or step % STRIDE == STRIDE-1:
                if not args.no_render:
                    renderer.update_scene(data, camera="inspection", scene_option=vis)
                    evidence.frame(renderer.render())
                if step % 240 == STRIDE-1:
                    print(f"MuJoCo native: {step+1}/{STEPS} physics steps", flush=True)
    evidence.finish(mujoco.__version__, preview=args.preview, rendered=not args.no_render)


if __name__ == "__main__":
    main()
