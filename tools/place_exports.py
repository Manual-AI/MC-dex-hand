#!/usr/bin/env python3
"""Sort files produced by tools/solidworks/export_cad.bas into the repo and check them against the BOM.

Usage:  python tools/place_exports.py <export_dir>
        <export_dir> is the folder containing stl/ and step/ as written by the macro
        (or any folder containing the .stl / .step files).
"""
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
THIRD_PARTY = {"cm_quest_adapter_lower", "cm_quest_adapter_upper"}
THIRD_PARTY_DIR = ROOT / "third_party/udcap/stl"
STEP_DIR = ROOT / "hardware/step"


def expected_names():
    with open(ROOT / "bom/rename_map.csv", newline="") as f:
        return {r["proposed_name"] for r in csv.DictReader(f)}


def main(export_dir):
    export_dir = Path(export_dir)
    expected = expected_names()
    found = {}
    for p in export_dir.rglob("*"):
        if p.suffix.lower() == ".stl":
            found[p.stem] = p
        elif p.suffix.lower() in (".step", ".stp"):
            STEP_DIR.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, STEP_DIR / (p.stem + ".step"))
            print(f"step  {p.name} -> hardware/step/")

    placed, unknown = 0, []
    for stem, p in sorted(found.items()):
        if stem in THIRD_PARTY:
            dest = THIRD_PARTY_DIR
        else:
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
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
