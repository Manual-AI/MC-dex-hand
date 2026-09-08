"""Render technical index-linkage stills from the generated Manual-Dex MuJoCo models."""
import json
import math
import os

os.environ.setdefault("MUJOCO_GL", "egl")

import mujoco
import numpy as np
from PIL import Image, ImageDraw

from render import BUILD, ROOT, VIEW_W, VIEW_H, font, project, world, nearest_joint, INK, MUTED, TEAL


def render_closeup(kind):
    directory = BUILD / kind
    model = mujoco.MjModel.from_xml_path(str(directory / "scene.xml"))
    parts = json.loads((directory / "parts.json").read_text())
    joints = json.loads((directory / "joints.json").read_text())
    servo_groups = {p["path"].split("/")[1]: nearest_joint(p["center"], joints)
                    for p in parts if "TOPCABINET" in p["name"]}
    keep = []
    for p in parts:
        if "FEETECH" in p["path"]:
            selected = servo_groups[p["path"].split("/")[1]].startswith("index_")
        else:
            selected = p["body"].startswith("index_") or p["name"].endswith("backplate") or (
                p["family"] in (6, 7, 8) and nearest_joint(p["center"], joints).startswith("index_"))
        if selected:
            keep.append(p)
        else:
            model.geom_group[model.geom(f"part_{p['index']:03d}").id] = 5
    options = mujoco.MjvOption()
    options.geomgroup[5] = 0
    options.sitegroup[:] = 0
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    camera = mujoco.MjvCamera()
    corners = np.array([world(corner) for p in keep for corner in p["bounds"]])
    lower, upper = corners.min(axis=0), corners.max(axis=0)
    camera.lookat[:] = (lower + upper) / 2
    camera.distance = np.linalg.norm(upper - lower) / (2 * math.sin(math.radians(18))) * 1.12
    camera.azimuth = 135
    camera.elevation = -30
    with mujoco.Renderer(model, height=VIEW_H, width=VIEW_W) as renderer:
        renderer.update_scene(data, camera=camera, scene_option=options)
        pixels = renderer.render()
        sheet = Image.new("RGB", (1440, 1000), "white")
        sheet.paste(Image.fromarray(pixels), (0, 118))
        draw = ImageDraw.Draw(sheet)
        draw.text((30, 17), f"Manual-Dex {kind}: Index-Finger Linkage", font=font(36, serif=True), fill=INK)
        draw.text((32, 68), "Isolated CAD components in their assembled positions | Two revolute joints", font=font(19), fill=MUTED)
        draw.line((30, 105, 1410, 105), fill="#aeb7bd")
        draw.line((998, 128, 998, 878), fill="#d1d6da")
        prefix = "gl" if kind == "glove" else "rh"
        descriptions = [
            ("A", "Fixed backplate", "Supports the finger's proximal pivot.", "ABS or PETG; GL-002 / RH-002.", next(p["center"] for p in keep if p["name"].endswith("backplate"))),
            ("B", "Proximal rotation axis", "Hinge / sensor" if kind == "glove" else "Base servo output", "Axis recovered from CAD cylinder faces.", joints["index_proximal"]["point"]),
            ("C", "Proximal moving link", "Connects the proximal and distal pivots.", "ABS or PETG; GL-003 / RH-003.", next(p["center"] for p in keep if p["name"] == f"{prefix}_index_proximal_link")),
            ("D", "Distal rotation axis", "Hinge / sensor" if kind == "glove" else "Distal servo output", "Moves with the proximal link.", joints["index_distal"]["point"]),
            ("E", "Distal contact link", "Carries the fingertip contact geometry.", "ABS or PETG; GL-004 / RH-004.", next(p["center"] for p in keep if p["name"] == f"{prefix}_index_tip")),
        ]
        draw.text((1020, 137), "KINEMATIC CONNECTIONS", font=font(19, bold=True), fill=INK)
        for i, (letter, title, line1, line2, point) in enumerate(descriptions):
            y = 198 + 123*i
            draw.text((1020,y), letter, font=font(20, bold=True), fill=TEAL)
            draw.text((1053,y), title, font=font(19,bold=True), fill=INK)
            draw.text((1053,y+32),line1,font=font(15),fill=MUTED)
            draw.text((1053,y+57),line2,font=font(15),fill=MUTED)
            x0,y0=project(world(point),renderer.scene)
            x,y=x0+(-60 if i%2 else 70), y0-32
            draw.line((x0,y0,x,y),fill=TEAL,width=2)
            draw.ellipse((x0-3,y0-3,x0+3,y0+3),fill=TEAL)
            draw.rectangle((x-15,y-15,x+15,y+15),fill="white",outline=TEAL)
            draw.text((x,y),letter,font=font(19,bold=True),fill=TEAL,anchor="mm")
        draw.line((30,902,1410,902),fill="#aeb7bd")
        draw.text((32,922), "MuJoCo render of the released STEP geometry. Surrounding finger groups and shared attachments are hidden.",font=font(17),fill=INK)
        draw.text((32,953), "The diagram shows connection topology. Fastener selection, sensor alignment and joint calibration require the BOM and build notes.",font=font(16),fill=MUTED)
        destination=ROOT / f"docs/images/manual-dex-{kind}-linkage.png"
        sheet.save(destination)
        print(f"Rendered {destination}")


if __name__ == "__main__":
    for kind in ("glove", "hand"):
        render_closeup(kind)
