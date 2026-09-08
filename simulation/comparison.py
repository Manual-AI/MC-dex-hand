"""Render recorded engine joint states in one shared MuJoCo scene."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import xml.etree.ElementTree as ET

os.environ.setdefault("MUJOCO_GL", "egl")
import mujoco
from PIL import Image, ImageDraw, ImageFont

from common import ROOT, BUILD, PACKAGE, JOINT_NAMES

ENGINES = [("mujoco", "MuJoCo 3.6.0"), ("genesis", "Genesis 1.0.0"),
           ("superdex", "SuperDex 1.0.0"), ("isaacsim", "Isaac Sim 5.1.0")]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview", action="store_true")
    args = parser.parse_args()
    output = ROOT / "docs/assets/simulation"
    output.mkdir(parents=True, exist_ok=True)
    traces, provenance = {}, {}
    for key, label in ENGINES:
        path = BUILD / "results" / f"{key}-trace.json"
        trace = json.loads(path.read_text())
        result = json.loads((BUILD / "results" / f"{key}.json").read_text())
        assert result["status"] == "passed" and result["steps"] == 1200
        assert trace["run_id"] == result["run_id"], "Stale trace: rerun this engine with --trace"
        assert [s["step"] for s in trace["states"]] == list(range(0, 1200, 12))
        assert all(set(s["positions"]) == set(JOINT_NAMES) for s in trace["states"])
        traces[key] = trace["states"]
        provenance[key] = {"version": label, "run_id": trace["run_id"],
            "trace_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "steps": 1200, "source": "actual post-step joint readbacks"}
    tree = ET.parse(PACKAGE / "openarm_manual_dex.xml").getroot()
    ET.SubElement(tree.find("asset"), "texture", name="comparison_sky", type="skybox",
                  builtin="gradient", rgb1=".94 .96 .98", rgb2=".84 .87 .91", width="512", height="3072")
    ET.SubElement(tree.find("worldbody"), "geom", name="comparison_floor", type="plane",
                  size="2 2 .1", pos="0 0 -.008", rgba=".84 .87 .9 1", contype="0", conaffinity="0")
    model = mujoco.MjModel.from_xml_string(ET.tostring(tree, encoding="unicode"))
    data = mujoco.MjData(model)
    option = mujoco.MjvOption()
    option.geomgroup[3] = 0
    camera = mujoco.MjvCamera()
    camera.lookat[:] = [.12, 0, .37]
    camera.distance, camera.azimuth, camera.elevation = 1.2, 140, -18
    fonts = "/usr/share/fonts/truetype/dejavu/"
    title = ImageFont.truetype(fonts + "DejaVuSans-Bold.ttf", 24)
    text = ImageFont.truetype(fonts + "DejaVuSans.ttf", 15)
    frames = {key: [] for key, _ in ENGINES}
    combined = []
    with mujoco.Renderer(model, height=460, width=580) as renderer:
        for frame in range(1 if args.preview else 100):
            grid = Image.new("RGB", (1160, 1100), "#f0f4f8")
            for index, (key, label) in enumerate(ENGINES):
                for name, value in traces[key][frame]["positions"].items():
                    data.joint(name).qpos[0] = value
                mujoco.mj_forward(model, data)
                renderer.update_scene(data, camera=camera, scene_option=option)
                panel = Image.new("RGB", (580, 550), "#f0f4f8")
                panel.paste(Image.fromarray(renderer.render()), (0, 62))
                draw = ImageDraw.Draw(panel)
                draw.text((18, 10), label, font=title, fill="#152a40")
                draw.text((18, 40), "Actual engine state | shared MuJoCo renderer", font=text, fill="#41596e")
                draw.text((18, 526), f"OpenArm + Manual-Dex  |  15 joints  |  t = {frame/20:0.2f} s", font=text, fill="#152a40")
                frames[key].append(panel)
                grid.paste(panel, ((index % 2) * 580, (index // 2) * 550))
            combined.append(grid)
            if frame % 20 == 0:
                print(f"Rendered comparison frame {frame + 1}/100", flush=True)
    if args.preview:
        combined[0].save(BUILD / "results/comparison-preview.png")
        return
    for key, sequence in list(frames.items()) + [("all-engines", combined)]:
        # A fixed palette per animation prevents label/background color flicker.
        palette = sequence[0].quantize(colors=256)
        encoded = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in sequence]
        path = output / f"{key}.gif"
        encoded[0].save(path, save_all=True, append_images=encoded[1:], duration=50, loop=0, optimize=False, disposal=2)
        with Image.open(path) as gif:
            assert gif.n_frames == 100
            duration = 0
            for i in range(gif.n_frames):
                gif.seek(i)
                duration += gif.info["duration"]
            assert duration == 5000
    (output / "provenance.json").write_text(json.dumps({"rendering": "MuJoCo 3.6.0 shared scene",
        "native_engine_screenshots": False, "duration_s": 5, "fps": 20,
        "dynamics_validated": False, "engines": provenance}, indent=2) + "\n")


if __name__ == "__main__":
    main()
