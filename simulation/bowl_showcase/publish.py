"""Assemble native camera images and force traces. No geometry is rendered here."""

import csv
import hashlib
import json
import subprocess
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "build/bowl-showcase"
OUT = ROOT / "docs/assets/simulation/bowl"
ENGINES = {
    "isaacsim": "Isaac Sim",
    "mujoco": "MuJoCo",
    "genesis": "Genesis",
    "superdex": "SuperDex",
    "alloy": "Alloy",
    "steel": "Steel",
}
FPS = 12


def font(size, bold=False):
    paths = [
        Path("/usr/share/fonts/truetype/dejavu")
        / ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"),
        Path("/System/Library/Fonts/Supplemental")
        / ("Arial Bold.ttf" if bold else "Arial.ttf"),
    ]
    return ImageFont.truetype(str(next(p for p in paths if p.exists())), size)


def digest(b):
    return hashlib.sha256(b).hexdigest()


def phase_at(tick, capture):
    if tick < 52:
        return "Approach"
    if tick < capture["gripTick"]:
        return "Close"
    if tick < 134:
        return "Lift"
    if tick < capture["releaseTick"]:
        return "Carry"
    return "Release" if tick < 209 else "Settle"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    scene = (WORK / "scene/scene.json").read_bytes()
    captures = {}
    summary = {}
    colors = {
        "paper": "#f3f4ee",
        "ink": "#182d23",
        "green": "#246449",
        "dim": "#4f6559",
        "line": "#bec6bb",
    }
    for name in ENGINES:
        folder = WORK / "captures" / name
        c = json.loads((folder / "capture.json").read_text())
        assert (
            c["sceneSha256"] == digest(scene)
            and c["engine"] == name
            and c["frames"] == list(range(0, 259, 2))
        )
        assert (
            c["liftHeightM"] > 0.045
            and abs(c["settledMeanN"] - c["massKg"] * 9.81) < 0.02
        )
        hashes = [digest((folder / f"{i:04}.jpg").read_bytes()) for i in c["frames"]]
        assert len(set(hashes)) > 40
        summary[name] = {
            k: c[k]
            for k in (
                "version",
                "renderer",
                "massKg",
                "gripTick",
                "releaseTick",
                "dt",
                "forceWindowSeconds",
                "peakWindowN",
                "maxGraspN",
                "liftHeightM",
                "settledMeanN",
                "finalCenter",
            )
        }
        summary[name].update(
            nativeFrameCount=len(hashes),
            nativeFramesSHA256=digest("".join(hashes).encode()),
            nativeSamplesSHA256=digest((folder / "capture.json").read_bytes()),
        )
        captures[name] = c
        inputs = np.array(c["graspForceN"]).reshape(-1, 10, 3)
        c["meanGrasp"] = np.linalg.norm(inputs, axis=2).mean(axis=1)
    width, height = 1920, 1080
    proc = subprocess.Popen(
        [
            "ffmpeg",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-s",
            f"{width}x{height}",
            "-framerate",
            str(FPS),
            "-i",
            "-",
            "-c:v",
            "libx264",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(OUT / "bowl-engines.mp4"),
        ],
        stdin=subprocess.PIPE,
    )
    fonts = [font(31, True), font(23), font(21, True), font(16)]
    for tick in range(0, 259, 2):
        sheet = Image.new("RGB", (width, height), colors["paper"])
        draw = ImageDraw.Draw(sheet)
        for j, (name, title) in enumerate(ENGINES.items()):
            x, y = (j % 3) * 640, (j // 3) * 540
            draw.text((x + 18, y + 8), title, font=fonts[0], fill=colors["ink"])
            c = captures[name]
            step = min(tick, len(c["verticalForceN"]) - 1)
            phase = phase_at(tick, c)
            draw.text(
                (x + 620, y + 28), phase, font=fonts[1], anchor="rm", fill=colors["dim"]
            )
            sheet.paste(
                Image.open(WORK / "captures" / name / f"{tick:04}.jpg"), (x, y + 51)
            )
            top = y + 489
            left = x + 192
            right = x + 618
            vals = c["verticalForceN"]
            project = lambda k, v: (
                left + (right - left) * k / (len(vals) - 1),
                top + 37 - np.clip(v, -0.04, 1.0) * 36,
            )
            draw.line((left, top + 37, right, top + 37), fill=colors["line"], width=1)
            draw.line(
                [project(k, v) for k, v in enumerate(vals)], fill="#91a99a", width=2
            )
            if step > 0:
                draw.line(
                    [project(k, vals[k]) for k in range(step + 1)],
                    fill=colors["green"],
                    width=2,
                )
            px, py = project(step, vals[step])
            draw.ellipse((px - 3, py - 3, px + 3, py + 3), fill=colors["green"])
            draw.text(
                (x + 18, top + 10),
                f"Fz   {vals[step]:.2f} N",
                font=fonts[2],
                fill=colors["green"],
            )
            draw.line((x + 639, y, x + 639, y + 539), fill=colors["line"])
            draw.line((x, y + 539, x + 639, y + 539), fill=colors["line"])
        proc.stdin.write(sheet.tobytes())
    proc.stdin.close()
    if proc.wait():
        raise RuntimeError("Video encoding failed")
    for name, c in captures.items():
        folder = WORK / "captures" / name
        listing = WORK / (name + "-frames.txt")
        listing.write_text(
            "".join(
                f"file '{folder}/{i:04}.jpg'\nduration {1 / FPS:.10f}\n"
                for i in c["frames"]
            )
            + f"file '{folder}/{c['frames'][-1]:04}.jpg'\n"
        )
        subprocess.run(
            [
                "ffmpeg",
                "-loglevel",
                "error",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(listing),
                "-r",
                str(FPS),
                "-frames:v",
                str(len(c["frames"])),
                "-c:v",
                "libx264",
                "-crf",
                "18",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                str(OUT / (name + ".mp4")),
            ],
            check=True,
        )
    # Crop the original native pixels before downsampling. Labels stay readable in a 768 px README.
    preview_frames = WORK / "preview-frames"
    preview_frames.mkdir(exist_ok=True)
    label_font, phase_font = font(16, True), font(13)
    preview_ticks = range(118, 259, 2)  # From the lift through the last native capture.
    previous_pixels = None
    for index, tick in enumerate(preview_ticks):
        card = Image.new("RGB", (768, 432), colors["paper"])
        draw = ImageDraw.Draw(card)
        for cell, (engine, title) in enumerate(ENGINES.items()):
            x, y = (cell % 3) * 256, (cell // 3) * 216
            phase = phase_at(tick, captures[engine])
            draw.text((x + 7, y + 4), title, font=label_font, fill=colors["ink"])
            draw.text(
                (x + 247, y + 15),
                phase,
                anchor="rm",
                font=phase_font,
                fill=colors["dim"],
            )
            frame = Image.open(WORK / "captures" / engine / f"{tick:04}.jpg")
            crop = frame.crop((186, 92, 554, 335)).resize(
                (256, 169), Image.Resampling.LANCZOS
            )
            card.paste(crop, (x, y + 25))
            forces = captures[engine]["verticalForceN"]
            force = forces[min(tick, len(forces) - 1)]
            draw.text(
                (x + 7, y + 197),
                f"Fz   {force:.2f} N",
                font=phase_font,
                fill=colors["green"],
            )
            draw.line((x + 255, y, x + 255, y + 215), fill=colors["line"])
        # Keep near-identical pixels stable between frames so small camera noise compresses well.
        pixels = np.array(card, dtype=np.int16)
        if previous_pixels is not None:
            stable = np.abs(pixels - previous_pixels).max(axis=2) < 22
            pixels[stable] = previous_pixels[stable]
        Image.fromarray(pixels.astype(np.uint8)).save(preview_frames / f"{index:03}.png")
        previous_pixels = pixels
    filters = (
        f"trim=end_frame={len(preview_ticks)},split[a][b];"
        "[a]palettegen=max_colors=176[p];[b][p]paletteuse=dither=bayer:bayer_scale=4"
    )
    subprocess.run(
        [
            "ffmpeg",
            "-loglevel",
            "error",
            "-y",
            "-framerate",
            str(FPS),
            "-i",
            str(preview_frames / "%03d.png"),
            "-frames:v",
            str(len(preview_ticks)),
            "-filter_complex",
            filters,
            "-loop",
            "0",
            # Hold the settled frame for one extra frame interval to complete six seconds.
            "-final_delay",
            str(round(2 * 100 / FPS)),
            str(OUT / "preview.gif"),
        ],
        check=True,
    )
    assert (OUT / "preview.gif").stat().st_size <= 1_000_000
    with (OUT / "forces.csv").open("w") as f:
        table = csv.writer(f)
        table.writerow(
            [
                "engine",
                "time_window_start_s",
                "vertical_interaction_N",
                "mean_grasp_force_norm_N",
                "end_x_m",
                "end_y_m",
                "end_z_m",
            ]
        )
        for name, c in captures.items():
            for i, force in enumerate(c["verticalForceN"]):
                table.writerow(
                    [
                        name,
                        f"{i / 24:.6f}",
                        f"{force:.6f}",
                        f"{c['meanGrasp'][i]:.6f}",
                        *[f"{n:.7f}" for n in c["poses"][(i + 1) * 10][:3]],
                    ]
                )
    record = dict(
        sceneSha256=digest(scene),
        programSha256=digest(
            (ROOT / "simulation/bowl_showcase/program.json").read_bytes()
        ),
        physicsHz=240,
        motionHz=24,
        videoFps=12,
        frames=130,
        object="building-brick",
        engines=summary,
    )
    (OUT / "results.json").write_text(json.dumps(record, indent=2) + "\n")


if __name__ == "__main__":
    main()
