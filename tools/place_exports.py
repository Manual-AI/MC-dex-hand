#!/usr/bin/env python3
"""Sort files produced by tools/solidworks/export_cad.bas into the repo and check them against the BOM.

Usage:  python tools/place_exports.py <export_dir> [--assembly hand|glove]
        <export_dir> is the folder containing stl/ and step/ as written by the macro
        (or any folder containing the .stl / .step files).
"""
import argparse
import csv
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEST = {
    "rh_": ROOT / "hardware/robot_hand/stl",
    "gl_": ROOT / "hardware/glove/stl",
    "cm_": ROOT / "hardware/common/stl",
}
STEP_DIR = ROOT / "hardware/step"


def expected_names(assembly=None):
    with open(ROOT / "bom/rename_map.csv", newline="") as f:
        groups = {"common", "robot hand" if assembly == "hand" else "glove"}
        return {r["proposed_name"] for r in csv.DictReader(f)
                if assembly is None or r["group"] in groups}


def main(export_dir, assembly=None):
    export_dir = Path(export_dir)
    if not export_dir.is_dir():
        print(f"Export folder does not exist: {export_dir}")
        return 1
    expected = expected_names(assembly)
    step_files = [p for p in export_dir.rglob("*") if p.suffix.lower() in (".step", ".stp")]
    if assembly and len(step_files) > 1:
        print("Expected one STEP assembly; refusing to overwrite it with multiple inputs")
        return 1
    found = {}
    for p in export_dir.rglob("*"):
        if p.suffix.lower() == ".stl":
            found[p.stem] = p
        elif p.suffix.lower() in (".step", ".stp"):
            STEP_DIR.mkdir(parents=True, exist_ok=True)
            filename = f"manual_dex_{assembly}.step" if assembly else p.stem + ".step"
            shutil.copy2(p, STEP_DIR / filename)
            print(f"step  {p.name} -> hardware/step/")

    placed, unknown = 0, []
    for stem, p in sorted(found.items()):
        dest = next((d for pre, d in DEST.items() if stem.startswith(pre)), None)
        if dest is None or stem not in expected:
            unknown.append(stem)
            continue
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dest / (stem + ".stl"))
        placed += 1
    missing = sorted(expected - set(found))
    print(f"\nplaced {placed} STL files")
    if unknown:
        print("NOT in BOM (left in export folder):", ", ".join(unknown))
    if missing:
        print("MISSING - in BOM but no STL exported:", ", ".join(missing))
    else:
        print("all BOM printed parts have an STL")
    return 0 if not missing else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export_dir")
    parser.add_argument("--assembly", choices=("hand", "glove"))
    args = parser.parse_args()
    sys.exit(main(args.export_dir, args.assembly))
