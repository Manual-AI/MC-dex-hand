"""Build CAD-derived MuJoCo models and render one paired, ten-second animation.

Run cad.py for both STEP assemblies first. All dimensions from CAD are millimetres;
MJCF uses metres. Motion is prescribed for illustration, not a dynamics validation.
"""
import argparse
import json
import math
import os
from pathlib import Path
import shutil
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
MODELS = ROOT / "models/manual_dex"
FPS = 20
SECONDS = 10
FRAMES = FPS * SECONDS
WIDTH, HEIGHT = 2000, 1100
PANEL_W, PANEL_H = 700, 800
PANEL_Y = 150
REGISTER_X = 1440
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
    ET.SubElement(visual, "global", offwidth=str(VIEW_W), offheight=str(max(VIEW_H, PANEL_H)), fovy="36")
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
        # Small copper hinge markers expose the eight axes in the technical diagram.
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


def publish_models():
    """Version the actual MJCF, meshes and joint/part records used by the renderer."""
    for kind in ("glove", "hand"):
        source, destination = BUILD / kind, MODELS / kind
        destination.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source / "meshes", destination / "meshes", dirs_exist_ok=True)
        for name in ("scene.xml", "parts.json", "joints.json"):
            shutil.copy2(source / name, destination / name)
        parts = json.loads((source / "parts.json").read_text())
        for part in parts:
            part["source_cad_mesh"] = part.pop("file")
            part["mesh"] = f"meshes/part_{part['index']:03d}.stl"
        (destination / "parts.json").write_text(json.dumps(parts, indent=2) + "\n")
        # Keep checked-in models directly usable at either rendering resolution.
        tree = ET.parse(destination / "scene.xml")
        tree.getroot().find("visual/global").set("offheight", str(max(VIEW_H, PANEL_H)))
        ET.indent(tree)
        tree.write(destination / "scene.xml", encoding="unicode")
        print(f"Published MuJoCo model: {destination}", flush=True)


def annotate_panel(pixels, segmentation, kind, model, parts):
    """Label visible geometry; the permanent BOM register is drawn separately."""
    panel = Image.fromarray(pixels)
    draw = ImageDraw.Draw(panel)
    labels = []
    # Sites also have segmentation IDs; never mistake a hinge marker for a mesh.
    geom_mask = segmentation[:, :, 1] == int(mujoco.mjtObj.mjOBJ_GEOM)
    geom_ids, counts = np.unique(segmentation[:, :, 0][geom_mask], return_counts=True)
    visible_counts = dict(zip(geom_ids.tolist(), counts.tolist()))
    for number, preferred in representative_parts(parts):
        candidates = [p for p in parts if p["family"] == number]

        def visible_area(p):
            return visible_counts.get(model.geom(f"part_{p['index']:03d}").id, 0)

        part = preferred if visible_area(preferred) >= 12 else max(candidates, key=visible_area)
        if visible_area(part) < 12:
            continue
        region = np.argwhere(geom_mask & (segmentation[:, :, 0] == model.geom(f"part_{part['index']:03d}").id))
        center = region.mean(axis=0)
        y, x = region[np.argmin(np.sum((region - center) ** 2, axis=1))]
        pixel = np.array([x, y], dtype=float)
        target = pixel + np.array([-38 if x < PANEL_W / 2 else 38, -20])
        labels.append(dict(number=number, point=pixel, label=target))
    for _ in range(30):
        for i, a in enumerate(labels):
            for b in labels[i+1:]:
                delta = a["label"] - b["label"]
                if abs(delta[0]) < 57 and abs(delta[1]) < 31:
                    sign = 1 if delta[1] >= 0 else -1
                    a["label"][1] += 2 * sign
                    b["label"][1] -= 2 * sign
            a["label"] = np.clip(a["label"], [32, 24], [PANEL_W - 32, PANEL_H - 24])
    prefix = "G" if kind == "glove" else "H"
    for a in labels:
        x, y = a["label"]
        px, py = a["point"]
        draw.line((px, py, x, y), fill="#738993", width=1)
        draw.ellipse((px-2, py-2, px+2, py+2), fill=TEAL)
        draw.rectangle((x-24, y-13, x+24, y+13), fill="white", outline="#8e9ea6", width=1)
        draw.text((x, y), f"{prefix}{a['number']:02d}", font=font(15, bold=True), fill=TEAL, anchor="mm")
    return panel


def static_sheet():
    """Draw one unchanging, full-contrast legend shared by the paired animation."""
    sheet = Image.new("RGB", (WIDTH, HEIGHT), "white")
    draw = ImageDraw.Draw(sheet)
    draw.text((30, 17), "Manual-Dex: Wearable Glove and Actuated Hand", font=font(40, serif=True), fill=INK)
    draw.text((32, 73), "Matched CAD-derived kinematics  |  Four finger groups per device  |  Eight revolute joints per device", font=font(21), fill=MUTED)
    draw.line((30, 111, WIDTH - 30, 111), fill="#aeb7bd", width=1)
    draw.text((350, 131), "G  /  Instrumented glove", font=font(23, bold=True), fill=INK, anchor="mm")
    draw.text((1050, 131), "H  /  Actuated hand (gripper)", font=font(23, bold=True), fill=INK, anchor="mm")
    draw.line((REGISTER_X - 20, 128, REGISTER_X - 20, 974), fill="#d1d6da", width=1)
    draw.text((REGISTER_X, 128), "COMPONENT REGISTER / BOM", font=font(21, bold=True), fill=INK)
    draw.text((REGISTER_X, 161), "G = glove  |  H = hand  |  All entries remain visible", font=font(16), fill=MUTED)
    names = [
        "Palm / backplate",
        "Proximal links: index, middle, ring + little",
        "Distal contact links: index, middle, ring + little",
        "Thumb proximal assembly",
        "Thumb distal contact link",
        "G: joint sensing  /  H: servo actuation",
        "G: sensor housings / lids  /  H: thumb bearing",
        "G: hinge pins / couplers  /  H: wrist flange",
        "Wrist camera + mount / adaptor",
        "Pose tracking controller",
        "Tracking mount: base / cap / receiver",
        "G: enclosure + ESP32  /  H: enclosure",
    ]
    for i, (name, glove, hand) in enumerate(zip(names, families("glove"), families("hand"))):
        y = 206 + i * 63
        draw.text((REGISTER_X, y), f"{i+1:02d}", font=font(20, bold=True), fill=TEAL)
        draw.text((REGISTER_X + 40, y), name, font=font(17, bold=True), fill=INK)
        draw.text((REGISTER_X + 40, y + 23), "G  " + glove[1], font=font(16), fill=MUTED)
        draw.text((REGISTER_X + 40, y + 43), "H  " + hand[1], font=font(16), fill=MUTED)
    draw.text((32, 964), "Synchronized views at equal scale. Copper markers: joint axes. Callouts identify visible surfaces.", font=font(18), fill=MUTED)
    draw.line((30, 996, WIDTH - 30, 996), fill="#aeb7bd", width=1)
    draw.text((32, 1041), "Printed components: ABS or PETG. Colors identify component classes; enclosures shown transparent.", font=font(18), fill=MUTED)
    draw.text((32, 1073), "Prescribed motion only: joint limits, inertia, collisions and hardware performance have not been validated.", font=font(17), fill=MUTED)
    return sheet


def pose_at(data, time_seconds):
    # Keep finger motion at its original five-second period; only halve orbit speed.
    phase = time_seconds / 5
    for finger, shift in (("index", 0), ("middle", .035), ("pinkyring", .07), ("thumb", .025)):
        wave = .5 - .5 * math.cos(2 * math.pi * (phase + shift))
        for stage, angle in (("proximal", 32 if finger != "thumb" else 24),
                             ("distal", 45 if finger != "thumb" else 36)):
            data.joint(f"{finger}_{stage}").qpos[0] = math.radians(angle) * wave


def orbit_azimuth(time_seconds):
    return 125 + 36 * time_seconds


def render(preview=False, reuse=False, published=False):
    if not published:
        if not reuse:
            for kind in ("glove", "hand"):
                build_model(kind)
        publish_models()
    contexts = []
    for kind in ("glove", "hand"):
        directory = MODELS / kind
        parts = json.loads((directory / "parts.json").read_text())
        model = mujoco.MjModel.from_xml_path(str(directory / "scene.xml"))
        assert model.nq == 8, f"Expected eight revolute joints, found {model.nq}"
        data = mujoco.MjData(model)
        renderer = mujoco.Renderer(model, height=PANEL_H, width=PANEL_W)
        camera = mujoco.MjvCamera()
        camera.lookat[:] = [0.007, 0.005, .12]
        camera.distance = .43
        camera.elevation = -24
        contexts.append((kind, parts, model, data, renderer, camera))
    frame_dir = BUILD / "paired/frames"
    frame_dir.mkdir(parents=True, exist_ok=True)
    background = static_sheet()
    indices = [0, 50, 100, 150] if preview else range(FRAMES)
    try:
        for i in indices:
            sheet = background.copy()
            t = i / FPS
            azimuth = orbit_azimuth(t)
            for column, (kind, parts, model, data, renderer, camera) in enumerate(contexts):
                camera.azimuth = azimuth
                pose_at(data, t)
                mujoco.mj_forward(model, data)
                renderer.update_scene(data, camera=camera)
                pixels = renderer.render()
                renderer.enable_segmentation_rendering()
                segmentation = renderer.render()
                renderer.disable_segmentation_rendering()
                sheet.paste(annotate_panel(pixels, segmentation, kind, model, parts),
                            (column * PANEL_W, PANEL_Y))
            draw = ImageDraw.Draw(sheet)
            draw.text((32, 1009),
                      f"MuJoCo {mujoco.__version__}  |  t = {t:04.2f} / {SECONDS:.2f} s  |  Orbit: 36 deg/s (half speed)  |  Azimuth: {azimuth % 360:05.1f} deg",
                      font=font(19), fill=INK)
            sheet.save(frame_dir / f"{i:03d}.png")
            if i % 25 == 0:
                print(f"paired: rendered {i}/{FRAMES} frames", flush=True)
    finally:
        for _, _, _, _, renderer, _ in contexts:
            renderer.close()
    if not preview:
        OUT.mkdir(exist_ok=True)
        destination = OUT / "manual-dex-paired-kinematics.gif"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", str(FPS),
                        "-i", str(frame_dir / "%03d.png"), "-frames:v", str(FRAMES),
                        "-filter_complex",
                        "split[a][b];[a]palettegen=max_colors=256:stats_mode=full[p];[b][p]paletteuse=dither=bayer:bayer_scale=3",
                        "-loop", "0", str(destination)], check=True)
        with Image.open(destination) as gif:
            duration = 0
            legend = None
            for n in range(gif.n_frames):
                gif.seek(n)
                duration += gif.info["duration"]
                region = gif.convert("RGB").crop((REGISTER_X, 128, WIDTH, 974)).tobytes()
                if legend is None:
                    legend = region
                assert region == legend, f"Legend flicker in frame {n}"
            assert gif.n_frames == FRAMES and duration == SECONDS * 1000, (gif.n_frames, duration)
        print(f"Verified {destination}: {FRAMES} frames, {SECONDS * 1000} ms, static legend, {destination.stat().st_size:,} bytes", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview", action="store_true")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--reuse", action="store_true", help="Publish existing build models without rebuilding CAD meshes")
    source.add_argument("--models", action="store_true", help="Render the checked-in MJCF models directly; no CAD extraction needed")
    args = parser.parse_args()
    render(args.preview, args.reuse, args.models)
