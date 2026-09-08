"""Deterministic GIF size budgets; resize/re-encode frames, never synthesize scene content."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "docs/assets"
BUDGET = json.loads((ASSETS / "gif-size-budget.json").read_text())


def encode(frames, durations, relative_path):
    baseline = BUDGET["assets"][relative_path]
    path = ASSETS / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    trial = ROOT / "build/gif-encoding" / relative_path
    trial.parent.mkdir(parents=True, exist_ok=True)
    assert sum(durations) == baseline["duration_ms"]
    # Fixed palette prevents stationary component names changing brightness.
    for divisor, colors in ((1.4, 256), (1.4, 192), (1.5, 192), (1.6, 128), (1.8, 128)):
        size = (round(baseline["width"]/divisor), round(baseline["height"]/divisor))
        scaled = [frame.convert("RGB").resize(size, Image.Resampling.LANCZOS) for frame in frames]
        samples = scaled[::max(1, len(scaled)//8)]
        sheet = Image.new("RGB", (size[0]*len(samples), size[1]))
        for i, frame in enumerate(samples):
            sheet.paste(frame, (size[0]*i, 0))
        palette = sheet.quantize(colors=colors, method=Image.Quantize.MEDIANCUT)
        if relative_path.startswith("simulation/"):
            # Large gray floors otherwise consume the palette and turn the small
            # orange object gray. Reserve colors sampled from actual vivid pixels.
            vivid = [p for p in sheet.getdata() if max(p)-min(p) > 50 and max(p) > 90]
            if vivid:
                strip = Image.new("RGB", (len(vivid), 1))
                strip.putdata(vivid)
                accents = strip.quantize(colors=16, method=Image.Quantize.MEDIANCUT)
                base = sheet.quantize(colors=colors-16, method=Image.Quantize.MEDIANCUT)
                palette.putpalette(base.getpalette()[:(colors-16)*3] + accents.getpalette()[:48]
                                   + [0]*((256-colors)*3))
        encoded = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in scaled]
        for frame in encoded:
            frame.info.clear()  # Old RGB transparency tuples are not GIF palette indices.
        encoded[0].save(trial, save_all=True, append_images=encoded[1:], duration=durations,
                        loop=0, optimize=False, disposal=2)
        gifsicle = shutil.which("gifsicle") or str(ROOT / "build/gif-tools/runtime/usr/bin/gifsicle")
        if Path(gifsicle).is_file():
            optimized = trial.with_name(trial.stem + "-optimized.gif")
            subprocess.run([gifsicle, "--optimize=3", str(trial), "--output", str(optimized)], check=True)
            if optimized.stat().st_size < trial.stat().st_size:
                optimized.replace(trial)
        if trial.stat().st_size <= baseline["bytes"] * BUDGET["maximum_fraction"]:
            break
    else:
        raise RuntimeError(f"GIF exceeds its requested half-size budget: {path}")
    with Image.open(trial) as check:
        duration = 0
        for frame in range(check.n_frames):
            check.seek(frame)
            duration += check.info.get("duration", 0)
        assert duration == baseline["duration_ms"]
        info = {"bytes_before": baseline["bytes"], "bytes_after": trial.stat().st_size,
                "fraction": trial.stat().st_size/baseline["bytes"], "size": list(size),
                "frames": check.n_frames, "duration_ms": duration, "palette_colors": colors}
    shutil.copy2(trial, path)
    print(relative_path, json.dumps(info), flush=True)
    return info


def legacy():
    report = {}
    backup = ROOT / "build/gif-originals"
    backup.mkdir(parents=True, exist_ok=True)
    for name in ("manual-dex-demo.gif", "manual-dex-paired-kinematics.gif"):
        original = backup / name
        if not original.exists():
            shutil.copy2(ASSETS / name, original)
        with Image.open(original) as gif:
            frames, durations = [], []
            for index in range(gif.n_frames):
                gif.seek(index)
                frames.append(gif.convert("RGB"))
                durations.append(gif.info.get("duration", 50))
        report[name] = encode(frames, durations, name)
    (ASSETS / "legacy-gif-compression.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--legacy", action="store_true", required=True)
    parser.parse_args()
    legacy()
