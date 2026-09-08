"""Publish independently rendered native captures. PIL only; no 3D renderer here."""
import argparse
import hashlib
import json
import sys

from PIL import Image, ImageDraw, ImageFont
from native_common import ROOT, NATIVE, SPEC, JOINTS

sys.path.insert(0, str(ROOT / "tools/visualization"))
from encode_gifs import encode

ENGINES = [("mujoco", "MuJoCo"), ("genesis", "Genesis"),
           ("superdex", "SuperDex"), ("isaacsim", "Isaac Sim")]


def read_capture(engine):
    path = NATIVE / f"{engine}.json"
    data = json.loads(path.read_text())
    capture = NATIVE / "captures" / engine / data["run_id"]
    if json.loads((capture / "result.json").read_text()) != data:
        raise ValueError(f"Mismatched capture manifest: {engine}")
    assert data["engine"] == engine and data["status"] == "passed"
    assert data["native_physics"] and data["native_rendering"]
    assert not data["state_overwrite_during_playback"]
    assert data["frames"] == 100 and data["fps"] == 20 and data["contact_steps"] >= 100
    assert data["gravity_m_s2"] == SPEC["gravity_m_s2"] and data["dt_s"] == SPEC["physics_dt_s"]
    assert [s["step"] for s in data["states"]] == list(range(11, 1200, 12))
    assert all(set(s["joints"]) == set(JOINTS) for s in data["states"])
    paths = sorted(capture.glob("frame-*.png"))
    assert len(paths) == 100
    digest = hashlib.sha256()
    frames = []
    for path in paths:
        digest.update(path.read_bytes())
        with Image.open(path) as frame:
            assert frame.size == (580, 460)
            frames.append(frame.convert("RGB"))
    source = {k: v for k, v in data.items() if k not in ("capture_dir", "states")}
    source["capture_sha256"] = digest.hexdigest()
    source["physics_states_sha256"] = hashlib.sha256(json.dumps(data["states"], sort_keys=True).encode()).hexdigest()
    return frames, source


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview", action="store_true", help="Build one montage PNG without replacing GIFs")
    args = parser.parse_args()
    fonts = "/usr/share/fonts/truetype/dejavu/"
    title = ImageFont.truetype(fonts + "DejaVuSans-Bold.ttf", 24)
    text = ImageFont.truetype(fonts + "DejaVuSans.ttf", 15)
    native, provenance, panels = {}, {}, {}
    for engine, label in ENGINES:
        native[engine], provenance[engine] = read_capture(engine)
        panels[engine] = []
    combined = []
    for frame in range(1 if args.preview else 100):
        grid = Image.new("RGB", (1160, 1100), "#f0f4f8")
        for index, (engine, label) in enumerate(ENGINES):
            panel = Image.new("RGB", (580, 550), "#f0f4f8")
            panel.paste(native[engine][frame], (0, 62))
            draw = ImageDraw.Draw(panel)
            draw.text((18, 9), f"{label} {provenance[engine]['version']}", font=title, fill="#152a40")
            renderer = {"mujoco": "MuJoCo EGL", "genesis": "Genesis rasterizer",
                        "superdex": "SuperDex SDK / Polyscope", "isaacsim": "Isaac Sim RTX"}[engine]
            draw.text((18, 39), f"Native physics + {renderer}", font=text, fill="#41596e")
            draw.text((18, 526), f"OpenArm + Manual-Dex  |  15 joints  |  t = {(frame+1)/20:0.2f} s", font=text, fill="#152a40")
            panels[engine].append(panel)
            grid.paste(panel, ((index % 2)*580, (index // 2)*550))
        combined.append(grid)
    if args.preview:
        combined[0].save(NATIVE / "montage-preview.png")
        return
    compression = {}
    for name, sequence in [*panels.items(), ("all-engines", combined)]:
        compression[name] = encode(sequence, [50]*100, f"simulation/{name}.gif")
    out = ROOT / "docs/assets/simulation"
    (out / "provenance.json").write_text(json.dumps({"rendering": "each engine's own renderer",
        "native_engine_screenshots": True, "duration_s": 5, "fps": 20,
        "scene": SPEC, "grasp_demonstrated": False, "dynamics_calibrated_to_hardware": False,
        "engines": provenance}, indent=2) + "\n")
    (out / "compression.json").write_text(json.dumps(compression, indent=2) + "\n")


if __name__ == "__main__":
    main()
