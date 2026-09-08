"""Build CAD-derived MuJoCo figure models and render five-second annotated loops.

Run cad.py for both STEP assemblies first. All dimensions from CAD are millimetres;
MJCF uses metres. Motion is prescribed for illustration, not a dynamics validation.
"""
import argparse
import json
import math
import os
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

os.environ.setdefault("MUJOCO_GL", "egl")
import mujoco
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import trimesh

ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / "build/manual-dex"
OUT = ROOT / "docs/assets"
FPS = 20
FRAMES = 100
WIDTH, HEIGHT = 1440, 1000
VIEW_W, VIEW_H = 980, 780
ROTATION = np.array([[1., 0., 0.], [0., 0., -1.], [0., 1., 0.]])
OFFSET = np.array([0., 0., .13])
INK = "#202c37"
MUTED = "#5c6771"
TEAL = "#286778"
COLORS = {
    "frame": (.68, .72, .76, 1),
    "link": (.33, .46, .53, 1),
    "tip": (.66, .71, .74, 1),
    "sensor": (.54, .34, .17, 1),
    "servo": (.22, .26, .29, 1),
    "metal": (.61, .63, .66, 1),
    "mount": (.39, .49, .53, 1),
    "electronics": (.24, .38, .34, 1),
    "controller": (.69, .71, .71, 1),
    "enclosure": (.66, .71, .75, .32),
}


def fmt(values):
    return " ".join(f"{x:.9g}" for x in values)


def world(point):
    return ROTATION @ (np.asarray(point) / 1000) + OFFSET


def joint_lines(parts, prefix):
    """Resolve the eight hinge axes from mating cylindrical CAD faces."""
    byname = {p["name"]: p for p in parts}
    joints = {}
    for finger in ("index", "middle", "pinkyring", "thumb"):
        parent = byname[f"{prefix}_" + ("palm_plate" if finger == "thumb" else "backplate")]
        proximal = byname[f"{prefix}_{finger}_" + ("link1" if finger == "thumb" else "proximal_link")]
        tip = byname[f"{prefix}_{finger}_tip"]
        for stage, a, b in (("proximal", parent, proximal), ("distal", proximal, tip)):
            if prefix == "gl":
                pairs = [(ca, cb) for ca in a["cylinders"] for cb in b["cylinders"]
                         if 2.4 < cb["radius"] < 4.0
                         and abs(np.dot(ca["axis"], cb["axis"])) > .999999
                         and np.linalg.norm(np.cross(ca["axis"], np.subtract(ca["point"], cb["point"]))) < .03]
                candidates = [pair[1] for pair in pairs]
            else:
                # Servo shaft clearance faces in the released printed robot links.
                candidates = [c for c in b["cylinders"] if abs(c["radius"] - 3.6) < .001]
            if not candidates:
                raise ValueError(f"No CAD hinge axis for {prefix} {finger} {stage}")
            c = candidates[0]
            axis = np.array(c["axis"])
            # Positive flexion points fingers toward the palm. Thumb axes differ.
            wanted = np.array([0, -1, 0]) if finger == "thumb" and stage == "proximal" else np.array([1 if finger == "thumb" else -1, 0, 0])
            if np.dot(axis, wanted) < 0:
                axis *= -1
            center = np.array(b["center"])
            point = np.array(c["point"])
            point += axis * np.dot(center - point, axis)
            # A CAD revision with two unrelated candidate axes needs manual review.
            if any(abs(np.dot(axis, q["axis"])) < .99999 or
                   np.linalg.norm(np.cross(axis, point - q["point"])) > .05 for q in candidates):
                raise ValueError(f"Ambiguous hinge axis for {prefix} {finger} {stage}")
            key = f"{finger}_{stage}"
            joints[key] = dict(point=point.tolist(), axis=axis.tolist(),
                               parent="frame" if stage == "proximal" else f"{finger}_proximal",
                               source=b["name"], clearance_radius_mm=c["radius"])
    return joints


def nearest_joint(point, joints):
    # Use the pivot's link-centred point, not an infinite axis: the nearly parallel
    # finger axes extend through neighbouring finger groups outside their links.
    return min(joints, key=lambda k: np.linalg.norm(np.asarray(point) - joints[k]["point"]))


def families(kind):
    """Callout number, engineering description, and BOM-backed material/spec."""
    if kind == "hand":
        return [
            ("Palm / backplate", "RH-001, 002 | FDM ABS or PETG"),
            ("Proximal links: I, M, R+P", "RH-003, 005, 007 | ABS or PETG"),
            ("Distal contact links: I, M, R+P", "RH-004, 006, 008 | ABS or PETG"),
            ("Thumb link, support rod, pin", "RH-009-011 | FDM ABS or PETG"),
            ("Thumb distal contact link", "RH-012 | FDM ABS or PETG"),
            ("Actuation: 8 serial-bus servos", "RH-101 | Feetech HLS3606"),
            ("Thumb bearing", "RH-102 | MR105ZZ, 5 x 10 x 4 mm"),
            ("OpenArm wrist flange", "RH-013 | FDM ABS or PETG"),
            ("Wrist camera + mount / adaptor", "RH-103, 016, 017 | 2 MP USB UVC"),
            ("Pose tracking controller", "RH-104 | Meta Quest Touch Plus"),
            ("Mount: base / cap / receiver", "RH-018-020 | ABS or PETG + M3"),
            ("Electronics enclosure + lid", "RH-014, 015 | ABS or PETG"),
        ]
    return [
        ("Palm / backplate", "GL-001, 002 | FDM ABS or PETG"),
        ("Proximal links: I, M, R+P", "GL-003, 005, 007 | ABS or PETG"),
        ("Distal contact links: I, M, R+P", "GL-004, 006, 008 | ABS or PETG"),
        ("Thumb link with sensor seat", "GL-009 | FDM ABS or PETG"),
        ("Thumb distal contact link", "GL-010 | FDM ABS or PETG"),
        ("Joint sensing: 8 potentiometers", "GL-101 | Bourns 3382G, 10 kOhm"),
        ("Encoder cases / retention lids", "GL-011-015 | ABS or PETG"),
        ("Hinge pins / encoder couplers", "GL-016-029 | ABS or PETG"),
        ("Wrist camera + mount / adaptor", "GL-103, 032, 033 | 2 MP USB UVC"),
        ("Pose tracking controller", "GL-104 | Meta Quest Touch Plus"),
        ("Mount: base / cap / receiver", "GL-034-036 | ABS or PETG + M3"),
        ("Enclosure / lid + ESP32 board", "GL-030, 031, 102 | ABS or PETG"),
    ]


def classify(part, kind, joints, servo_joints):
    name, path = part["name"], part["path"]
    body, color, family = "frame", "frame", 1
    if "FEETECH" in path:
        joint = servo_joints[path.split("/")[1]]
        body = joint if "SERVOARM" in name or "SECONDARM" in name else joints[joint]["parent"]
        return body, "metal" if "ARM" in name else "servo", 6
    if name == "3382g-001-xxx":
        return joints[nearest_joint(part["center"], joints)]["parent"], "sensor", 6
    if name.startswith(("rh_", "gl_")):
        finger = next((f for f in ("index", "middle", "pinkyring", "thumb") if f in name), None)
        if name.endswith("_tip"):
            return f"{finger}_distal", "tip", 5 if finger == "thumb" else 3
        if name.endswith("_proximal_link") or name.endswith("thumb_link1"):
            return f"{finger}_proximal", "link", 4 if finger == "thumb" else 2
        if "encoder_case" in name or "encoder_lid" in name:
            joint = nearest_joint(part["center"], joints)
            return joints[joint]["parent"], "mount", 7
        if "pin" in name:
            joint = nearest_joint(part["center"], joints)
            return joint, "sensor" if "encoder" in name else "frame", 8 if kind == "glove" else 4
        if "support_rod" in name:
            return "thumb_proximal", "link", 4
        if "openarm" in name:
            return body, "frame", 8
    if "bearing" in name:
        return body, "metal", 7
    if "Quest_Controller" in name:
        return body, "controller", 10
    if "Quest_mount" in path:
        return body, "metal" if name.startswith(("04_", "05_", "06_")) else "mount", 11
    if "camera" in name or "usbcam" in name:
        return body, "servo" if "usbcam" in name else "mount", 9
    if "electronics" in name:
        return body, "enclosure", 12
    if "PCB Component" in path:
        return body, "electronics", 12
    return body, color, family


def build_model(kind):
    directory = BUILD / kind
    parts = json.loads((directory / "cad/cad.json").read_text())
    joints = joint_lines(parts, "rh" if kind == "hand" else "gl")
    servo_joints = {p["path"].split("/")[1]: nearest_joint(p["center"], joints)
                    for p in parts if "TOPCABINET" in p["name"]}
    if kind == "hand" and set(servo_joints.values()) != set(joints):
        raise ValueError("The eight servo occurrences must map one-to-one to the hinge axes")
    mjcf = ET.Element("mujoco", model=f"Manual-Dex {kind} | kinematic visualization")
    ET.SubElement(mjcf, "compiler", angle="radian", meshdir="meshes", autolimits="true")
    ET.SubElement(mjcf, "option", gravity="0 0 0")
    visual = ET.SubElement(mjcf, "visual")
    ET.SubElement(visual, "global", offwidth=str(VIEW_W), offheight=str(VIEW_H), fovy="36")
    ET.SubElement(visual, "quality", shadowsize="4096", offsamples="4")
    ET.SubElement(visual, "headlight", ambient=".28 .28 .28", diffuse=".4 .4 .4", specular=".08 .08 .08")
    ET.SubElement(visual, "map", znear=".01", zfar="20", shadowclip="2")
    default = ET.SubElement(mjcf, "default")
    ET.SubElement(default, "geom", contype="0", conaffinity="0", group="1", density="0")
    asset = ET.SubElement(mjcf, "asset")
    for key, rgba in COLORS.items():
        ET.SubElement(asset, "material", name=key, rgba=fmt(rgba), specular=".15", shininess=".15")
    ET.SubElement(asset, "texture", name="background", type="skybox", builtin="flat", rgb1="1 1 1", rgb2="1 1 1", width="64", height="64")
    worldbody = ET.SubElement(mjcf, "worldbody")
    ET.SubElement(worldbody, "light", pos="-.3 -.4 1", dir=".3 .4 -1", diffuse=".4 .4 .4", castshadow="true")
    ET.SubElement(worldbody, "light", pos=".5 .2 .5", dir="-.5 -.2 -.4", diffuse=".2 .2 .2", castshadow="false")
    frame = ET.SubElement(worldbody, "body", name="frame")
    bodies = {"frame": frame}
    origins = {"frame": np.zeros(3)}
    for key, j in joints.items():
        position = world(j["point"])
        parent = j["parent"]
        bodies[key] = ET.SubElement(bodies[parent], "body", name=key, pos=fmt(position - origins[parent]))
        origins[key] = position
        ET.SubElement(bodies[key], "inertial", pos="0 0 0", mass=".001", diaginertia="1e-6 1e-6 1e-6")
        ET.SubElement(bodies[key], "joint", name=key, axis=fmt(ROTATION @ j["axis"]), type="hinge", range="-1.5 1.5")
        # Small copper hinge markers expose the eight axes in the technical figure.
        ET.SubElement(bodies[key], "site", name=f"axis_{key}", type="sphere", size=".0018", rgba=".63 .36 .16 1")
    meshdir = directory / "meshes"
    meshdir.mkdir(exist_ok=True)
    for p in parts:
        body, color, family = classify(p, kind, joints, servo_joints)
        surface = trimesh.load_mesh(directory / "cad" / p["file"])
        surface.vertices = (surface.vertices / 1000) @ ROTATION.T + OFFSET - origins[body]
        filename = f"part_{p['index']:03d}.stl"
        surface.export(meshdir / filename)
        key = f"part_{p['index']:03d}"
        ET.SubElement(asset, "mesh", name=key, file=filename)
        ET.SubElement(bodies[body], "geom", name=key, type="mesh", mesh=key, material=color)
        center = world(p["center"]) - origins[body]
        ET.SubElement(bodies[body], "site", name=f"label_{p['index']}", pos=fmt(center), size=".0001", rgba="0 0 0 0")
        p.update(body=body, family=family, material_style=color)
    ET.indent(mjcf)
    ET.ElementTree(mjcf).write(directory / "scene.xml", encoding="unicode")
    (directory / "joints.json").write_text(json.dumps(joints, indent=2) + "\n")
    (directory / "parts.json").write_text(json.dumps(parts, indent=2) + "\n")
    return directory, parts, joints


def font(size, bold=False, serif=False):
    base = Path("/usr/share/fonts/truetype")
    path = base / ("liberation2/LiberationSerif-Regular.ttf" if serif else
                   "dejavu/DejaVuSans-Bold.ttf" if bold else "dejavu/DejaVuSans.ttf")
    return ImageFont.truetype(str(path), size)


def project(point, scene):
    camera = scene.camera[0]
    forward, up = np.array(camera.forward), np.array(camera.up)
    right = np.cross(forward, up)
    position = (np.array(scene.camera[0].pos) + np.array(scene.camera[1].pos)) / 2
    delta = np.asarray(point) - position
    depth = np.dot(delta, forward)
    focal = VIEW_H / (2 * math.tan(math.radians(36) / 2))
    return np.array([VIEW_W / 2 + focal * np.dot(delta, right) / depth,
                     VIEW_H / 2 - focal * np.dot(delta, up) / depth + 118])


def representative_parts(parts):
    # Prefer an exposed named surface for each callout; all occurrences are indexed
    # in the generated part register. The legend applies to repeated components.
    preferences = {
        1: "backplate", 2: "middle_proximal_link", 3: "index_tip",
        4: "thumb_link1", 5: "thumb_tip", 6: "TOPCABINET",
        7: "encoder_case_distal", 8: "openarm", 9: "usbcam",
        10: "Quest_Controller", 11: "02_Hinged_cap", 12: "electronics_box",
    }
    selected = []
    for family in range(1, 13):
        group = [p for p in parts if p["family"] == family]
        matches = [p for p in group if preferences[family] in p["name"]]
        selected.append((family, (matches or group)[0]))
    return selected


def annotate(pixels, segmentation, kind, frame_index, model, parts):
    sheet = Image.new("RGB", (WIDTH, HEIGHT), "white")
    sheet.paste(Image.fromarray(pixels), (0, 118))
    draw = ImageDraw.Draw(sheet)
    title = "Manual-Dex: " + ("Actuated Robot Hand" if kind == "hand" else "Instrumented Wearable Glove")
    draw.text((30, 17), title, font=font(36, serif=True), fill=INK)
    draw.text((32, 68), "CAD-derived kinematic structure  |  Four finger groups  |  Eight revolute joints", font=font(19), fill=MUTED)
    draw.line((30, 105, 1410, 105), fill="#aeb7bd", width=1)
    draw.line((998, 128, 998, 878), fill="#d1d6da", width=1)
    draw.text((1020, 127), "COMPONENT REGISTER / BOM", font=font(18, bold=True), fill=INK)
    labels = []
    geom_ids, counts = np.unique(segmentation[:, :, 0], return_counts=True)
    visible_counts = dict(zip(geom_ids.tolist(), counts.tolist()))
    for number, preferred in representative_parts(parts):
        candidates = [p for p in parts if p["family"] == number]
        def visible_area(p):
            return visible_counts.get(model.geom(f"part_{p['index']:03d}").id, 0)
        part = preferred if visible_area(preferred) >= 12 else max(candidates, key=visible_area)
        if visible_area(part) < 12:
            continue
        # Anchor on an actually visible pixel of the labeled component. Projected
        # centroids may lie behind another finger during an orbit and mislabel it.
        region = np.argwhere(segmentation[:, :, 0] == model.geom(f"part_{part['index']:03d}").id)
        center = region.mean(axis=0)
        y, x = region[np.argmin(np.sum((region - center) ** 2, axis=1))]
        pixel = np.array([x, y + 118], dtype=float)
        target = pixel + np.array([-35 if pixel[0] < VIEW_W / 2 else 35, -17])
        target = np.clip(target, [38, 165], [950, 856])
        labels.append(dict(number=number, point=pixel, label=target))
    visible_families = {a["number"] for a in labels}
    for i, (name, spec) in enumerate(families(kind)):
        y = 169 + i * 57
        visible = i + 1 in visible_families
        draw.text((1020, y), f"{i+1:02d}", font=font(19, bold=True), fill=TEAL if visible else "#a7afb5")
        draw.text((1057, y), name, font=font(17, bold=True), fill=INK if visible else "#a7afb5")
        draw.text((1057, y + 24), spec, font=font(15), fill=MUTED if visible else "#a7afb5")
    # Repel callout tags, preserving leader lines to the actual moving geometry.
    for _ in range(30):
        for i, a in enumerate(labels):
            for b in labels[i+1:]:
                delta = a["label"] - b["label"]
                if abs(delta[0]) < 41 and abs(delta[1]) < 29:
                    sign = 1 if delta[1] >= 0 else -1
                    a["label"][1] += 2 * sign
                    b["label"][1] -= 2 * sign
            a["label"] = np.clip(a["label"], [30, 158], [954, 867])
    for a in labels:
        x, y = a["label"]
        px, py = a["point"]
        draw.line((px, py, x, y), fill="#738993", width=1)
        draw.ellipse((px-2, py-2, px+2, py+2), fill=TEAL)
        draw.rectangle((x-17, y-12, x+17, y+12), fill="white", outline="#8e9ea6", width=1)
        draw.text((x, y), f"{a['number']:02d}", font=font(16, bold=True), fill=TEAL, anchor="mm")
    draw.text((32, 872), "Gray register entries: occluded in this view. Copper markers: joint axes.", font=font(15), fill=MUTED)
    draw.line((30, 902, 1410, 902), fill="#aeb7bd", width=1)
    t = frame_index / FPS
    orbit = (125 + frame_index / FRAMES * 360) % 360
    draw.text((32, 917), f"MuJoCo {mujoco.__version__}   |   t = {t:04.2f} s / 5.00 s   |   camera azimuth = {orbit:05.1f} deg", font=font(17), fill=INK)
    draw.text((32, 949), "Printed components: ABS or PETG. Colors identify component classes; enclosure shown transparent.", font=font(16), fill=MUTED)
    draw.text((32, 975), "Prescribed flexion; joint limits, inertia, contacts and hardware performance are not validated by this figure.", font=font(15), fill=MUTED)
    return sheet


def render(kind, preview=False, reuse=False):
    if reuse:
        directory = BUILD / kind
        parts = json.loads((directory / "parts.json").read_text())
        joints = json.loads((directory / "joints.json").read_text())
    else:
        directory, parts, joints = build_model(kind)
    model = mujoco.MjModel.from_xml_path(str(directory / "scene.xml"))
    data = mujoco.MjData(model)
    assert model.nq == 8, f"Expected eight revolute joints, found {model.nq}"
    renderer = mujoco.Renderer(model, height=VIEW_H, width=VIEW_W)
    camera = mujoco.MjvCamera()
    camera.lookat[:] = [0.007, 0.005, .12]
    camera.distance = .40
    camera.elevation = -24
    frame_dir = directory / "frames"
    frame_dir.mkdir(exist_ok=True)
    indices = [0, 25, 50, 75] if preview else range(FRAMES)
    for i in indices:
        phase = i / FRAMES
        camera.azimuth = 125 + 360 * phase
        for finger, shift in (("index", 0), ("middle", .035), ("pinkyring", .07), ("thumb", .025)):
            wave = .5 - .5 * math.cos(2 * math.pi * (phase + shift))
            for stage, angle in (("proximal", 32 if finger != "thumb" else 24), ("distal", 45 if finger != "thumb" else 36)):
                data.joint(f"{finger}_{stage}").qpos[0] = math.radians(angle) * wave
        mujoco.mj_forward(model, data)
        renderer.update_scene(data, camera=camera)
        pixels = renderer.render()
        renderer.enable_segmentation_rendering()
        segmentation = renderer.render()
        renderer.disable_segmentation_rendering()
        image = annotate(pixels, segmentation, kind, i, model, parts)
        image.save(frame_dir / f"{i:03d}.png")
        if i % 25 == 0:
            print(f"{kind}: rendered {i}/{FRAMES} frames", flush=True)
    renderer.close()
    if not preview:
        OUT.mkdir(exist_ok=True)
        destination = OUT / f"manual-dex-{kind}-kinematics.gif"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", str(FPS),
                        "-i", str(frame_dir / "%03d.png"), "-filter_complex",
                        "split[a][b];[a]palettegen=max_colors=192:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=3",
                        "-loop", "0", str(destination)], check=True)
        with Image.open(destination) as gif:
            duration = 0
            for n in range(gif.n_frames):
                gif.seek(n)
                duration += gif.info["duration"]
            assert gif.n_frames == FRAMES and duration == 5000, (gif.n_frames, duration)
        print(f"Verified {destination}: {FRAMES} frames, 5000 ms, {destination.stat().st_size:,} bytes", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=["hand", "glove"])
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--reuse", action="store_true", help="Reuse the MJCF and mesh build")
    args = parser.parse_args()
    render(args.kind, args.preview, args.reuse)
