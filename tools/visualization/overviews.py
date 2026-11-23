"""Render matched hardware figures from the released CAD and browser palette."""

import json
import tempfile
import textwrap
import xml.etree.ElementTree as ET
from pathlib import Path
import mujoco
import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
PALETTE = json.loads((ROOT / "simulation/browser/assets/appearance.json").read_text())[
    "palette"
]
SHEETS = {
    "glove": (
        "Glove shell driven by human hand",
        "Wearable glove",
        [
            (
                "Finger links",
                "Two pivots per finger group. The ring and little fingers move together.",
                "proximal_link",
            ),
            (
                "Joint sensing",
                "Eight rotary potentiometers measure the angles of the moving links.",
                "encoder_case",
            ),
            (
                "Wrist tracking",
                "The printed mount fixes the Quest controller to the back of the glove.",
                "Quest_Controller",
            ),
            (
                "Electronics enclosure",
                "The wrist enclosure houses the ESP32 that reads the eight sensor channels.",
                "cm_electronics_box",
            ),
        ],
    ),
    "hand": (
        "Matched robot shell driven by compact actuators",
        "Robot hand",
        [
            (
                "Finger links",
                "The four finger groups match the glove’s linkage and contact geometry.",
                "proximal_link",
            ),
            (
                "Servo joints",
                "Eight Feetech HLS3606 servos drive the proximal and distal joints.",
                "MIDDLECASE",
            ),
            (
                "Wrist tracking",
                "The matching mount places the Quest controller in the same position as on the glove.",
                "Quest_Controller",
            ),
            (
                "Electronics enclosure",
                "The hand uses the same printed wrist enclosure as the glove.",
                "cm_electronics_box",
            ),
        ],
    ),
}


def rgba(hexcode):
    return (
        " ".join(f"{int(hexcode[i : i + 2], 16) / 255:.5f}" for i in (1, 3, 5)) + " 1"
    )


def material(part):
    n = part["name"]
    if "FEETECH" in part["path"]:
        return "servo_case" if "MIDDLECASE" in n else "servo_end"
    if part["material_style"] == "metal" or "screw" in n.lower() or "nut_" in n.lower():
        return "pins"
    if part["material_style"] == "electronics":
        return "camera_pcb" if "Board" in n else "servo_end"
    if part["material_style"] == "sensor" and not n.startswith("gl_"):
        return "servo_end"
    return "printed_shell"


def build(kind, work):
    direct = ROOT / "models/manual_dex" / kind
    parts = json.loads((direct / "parts.json").read_text())
    tree = ET.parse(direct / "scene.xml")
    tree.find("compiler").set("meshdir", str(direct / "meshes"))
    tree.find("visual/global").attrib.update(offwidth="1100", offheight="900")
    tree.find("visual/headlight").attrib.update(
        ambient=".38 .38 .38", diffuse=".38 .38 .38", specular=".05 .05 .05"
    )
    asset = tree.find("asset")
    sky = asset.find("texture[@name='background']")
    sky.attrib.update(rgb1=".87 .89 .875", rgb2=".87 .89 .875")
    for n, color in PALETTE.items():
        ET.SubElement(
            asset,
            "material",
            name="hw_" + n,
            rgba=rgba(color),
            specular=".12",
            shininess=".14",
        )
    for parent in tree.findall(".//body"):
        for g in parent.findall("geom"):
            stem = g.get("name")
            index = int(stem.split("_")[1])
            part = parts[index]
            n = part["name"]
            g.set("material", "hw_" + material(part))
            if not ("Quest_Controller" in n or n == "2mp_usbcam"):
                continue
            path = direct / "meshes" / (stem + ".stl")
            m = trimesh.load(path, process=False)
            if n == "2mp_usbcam":
                axis = np.array([0.76604444, 0.45451948, 0.45451948])
                height = m.triangles_center @ axis
                ids = np.where(
                    (height > -0.01195) & (height < -0.01015),
                    "camera_pcb",
                    "lens_holder",
                )
                ids[(height > 0.0084) & (m.face_normals @ axis > 0.85)] = "lens_glass"
                surfaces = {
                    name: m.submesh(
                        [np.flatnonzero(ids == name)], append=True, repair=False
                    )
                    for name in np.unique(ids)
                }
            else:
                axis = np.array([-0.49, -0.105, -0.867])
                axis /= np.linalg.norm(axis)
                seam = -0.035 * axis
                surfaces = {}
                for name, normal in (("quest_face", axis), ("quest_shell", -axis)):
                    vertices, faces, _ = trimesh.intersections.slice_faces_plane(
                        m.vertices, m.faces, normal, seam
                    )
                    surfaces[name] = trimesh.Trimesh(vertices, faces, process=False)
            parent.remove(g)
            for name, mesh in surfaces.items():
                tag = stem + "_" + name
                file = work / (tag + ".stl")
                mesh.export(file)
                ET.SubElement(asset, "mesh", name=tag, file=str(file))
                ET.SubElement(
                    parent,
                    "geom",
                    name=tag,
                    type="mesh",
                    mesh=tag,
                    material="hw_" + name,
                )
    details = []
    for part in parts:
        is_quest = "Quest_Controller" in part["name"]
        if not is_quest and part["name"] != "2mp_usbcam":
            continue
        stem = f"part_{part['index']:03d}"
        raw = trimesh.load(direct / "meshes" / (stem + ".stl"), process=False)
        center = raw.bounds.mean(axis=0)
        direction = np.array([-0.60, -0.52, -0.66] if is_quest else [0.90, 0.32, 0.31])
        direction /= np.linalg.norm(direction)
        right = np.cross(-direction, [0.0, 0.0, 1.0])
        right /= np.linalg.norm(right)
        up = np.cross(right, -direction)
        # Frame the two CAD parts individually at native resolution.
        spread = raw.vertices - center
        distance = max(
            abs(spread @ up).max(), abs(spread @ right).max() / 1.94
        ) / np.tan(np.deg2rad(17))
        eye = center + direction * (distance * 1.18 + abs(spread @ direction).max())
        name = "tracker" if is_quest else "camera_detail"
        ET.SubElement(
            tree.find("worldbody"),
            "camera",
            name=name,
            pos=" ".join(map(str, eye)),
            xyaxes=" ".join(map(str, [*right, *up])),
            fovy="34",
        )
        details.append((name, stem))
    model = mujoco.MjModel.from_xml_string(
        ET.tostring(tree.getroot(), encoding="unicode")
    )
    data = mujoco.MjData(model)
    data.qpos[:] = [0.34, 0.25, 0.40, 0.29, 0.43, 0.34, 0.16, 0.25]
    mujoco.mj_forward(model, data)
    cam = mujoco.MjvCamera()
    cam.lookat[:] = [0.002, 0.001, 0.112]
    cam.distance = 0.385
    cam.azimuth = 51
    cam.elevation = 0
    opt = mujoco.MjvOption()
    opt.sitegroup[:] = 0
    with mujoco.Renderer(model, height=790, width=940) as renderer:
        renderer.update_scene(data, camera=cam, scene_option=opt)
        img = Image.fromarray(renderer.render().copy())
        renderer.enable_segmentation_rendering()
        renderer.update_scene(data, camera=cam, scene_option=opt)
        seg = renderer.render()[:, :, 0].copy()
    inserts = {}
    with mujoco.Renderer(model, height=260, width=504) as renderer:
        for name, stem in details:
            model.geom_group[:] = 5
            for geom in range(model.ngeom):
                if model.geom(geom).name.startswith(stem + "_"):
                    model.geom_group[geom] = 1
            opt.geomgroup[5] = 0
            renderer.update_scene(data, camera=name, scene_option=opt)
            detail = Image.fromarray(renderer.render().copy())
            renderer.enable_segmentation_rendering()
            renderer.update_scene(data, camera=name, scene_option=opt)
            mask = renderer.render()[:, :, 0] >= 0
            renderer.disable_segmentation_rendering()
            ys, xs = np.where(mask)
            crop = detail.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
            crop.thumbnail((232, 114), Image.Resampling.LANCZOS)
            tile = Image.new("RGB", (252, 130), detail.getpixel((0, 0)))
            tile.paste(crop, ((252 - crop.width) // 2, (130 - crop.height) // 2))
            inserts[name] = tile
    return img, seg, model, parts, inserts


def font(size, bold=False):
    roots = [
        Path("/usr/share/fonts/truetype/dejavu")
        / ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"),
        Path("/System/Library/Fonts/Supplemental")
        / ("Arial Bold.ttf" if bold else "Arial.ttf"),
    ]
    return ImageFont.truetype(str(next(x for x in roots if x.exists())), size)


def sheet(kind):
    title, kicker, labels = SHEETS[kind]
    with tempfile.TemporaryDirectory() as tmp:
        image, seg, model, parts, inserts = build(kind, Path(tmp))
    canvas = Image.new("RGB", (1600, 940), "#f6f7f3")
    d = ImageDraw.Draw(canvas)
    d.text((52, 40), kicker.upper(), font=font(23, True), fill="#326550")
    d.text((50, 80), title, font=font(53, True), fill="#182c24")
    rect = (628, 167, 1568, 877)
    view = image.crop((0, 40, 940, 750))
    canvas.paste(view, rect[:2])
    placed = []
    for i, (label, desc, match) in enumerate(labels, 1):
        y = 180 + (i - 1) * 131
        d.ellipse((52, y, 90, y + 38), fill="#244b3b")
        d.text((71, y + 19), str(i), font=font(22, True), fill="white", anchor="mm")
        d.text((108, y - 2), label, font=font(29, True), fill="#182c24")
        d.multiline_text(
            (108, y + 44),
            "\n".join(textwrap.wrap(desc, 35)),
            font=font(23),
            fill="#344c40",
            spacing=6,
        )
        ids = [
            g
            for g in range(model.ngeom)
            if model.geom(g).name.startswith("part_")
            and match in parts[int(model.geom(g).name.split("_")[1])]["name"]
        ]
        mask = np.isin(seg[40:750], ids)
        yy, xx = np.where(mask)
        for prior_x, prior_y in placed:
            keep = (xx - prior_x) ** 2 + (yy - prior_y) ** 2 > 85**2
            if keep.any():
                xx, yy = xx[keep], yy[keep]
        if len(xx):
            idx = np.argmin((xx - np.median(xx)) ** 2 + (yy - np.median(yy)) ** 2)
            placed.append((int(xx[idx]), int(yy[idx])))
            x, y = 628 + int(xx[idx]), 167 + int(yy[idx])
            d.ellipse(
                (x - 19, y - 19, x + 19, y + 19),
                fill="#244b3b",
                outline="#ffffff",
                width=3,
            )
            d.text((x, y), str(i), font=font(21, True), fill="white", anchor="mm")
    for x, key, caption in [
        (52, "tracker", "Quest Touch Plus"),
        (334, "camera_detail", "Arducam · M12 lens"),
    ]:
        canvas.paste(inserts[key], (x, 710))
        d.text((x, 847), caption, font=font(20, True), fill="#344c40")
    d.line((52, 891, 1568, 891), fill="#b9c4ba", width=2)
    d.text((52, 904), "MC-Dex   /   Right-hand assembly", font=font(17), fill="#486252")
    name = "wearable-glove" if kind == "glove" else "robot-hand"
    canvas.save(ROOT / "docs/images" / (name + "-wrist-side.png"), optimize=True)


if __name__ == "__main__":
    for kind in SHEETS:
        sheet(kind)
