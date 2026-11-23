#!/usr/bin/env python3
"""Place SolidWorks STL and STEP exports in the release directories and check the BOM.

Pass a combined export directory or separate hand and glove export directories.
"""
import argparse
import csv
import filecmp
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
LEGACY_STEP_NAMES = {
    "manu_dex_hand_robot_hand": "mc_dex_hand_robot_hand",
    "manu_dex_hand_glove": "mc_dex_hand_glove",
}


def expected_names():
    with open(ROOT / "bom/rename_map.csv", newline="") as f:
        return {row["proposed_name"] for row in csv.DictReader(f)}


def main(export_dir, *other_dirs):
    expected = expected_names()
    copies = {}
    found = set()
    unknown = set()
    for directory in map(Path, (export_dir, *other_dirs)):
        if not directory.is_dir():
            print(f"Export directory does not exist: {directory}", file=sys.stderr)
            return 1
        for source in sorted(directory.rglob("*")):
            suffix = source.suffix.lower()
            stem = source.stem
            if suffix == ".stl":
                if stem not in expected:
                    unknown.add(stem)
                    continue
                dest = DEST[stem[:3]] / f"{stem}.stl"
                found.add(stem)
            elif suffix in {".step", ".stp"}:
                dest = STEP_DIR / (LEGACY_STEP_NAMES.get(stem, stem) + ".step")
            else:
                continue
            previous = copies.get(dest)
            if previous is not None and not filecmp.cmp(previous, source, shallow=False):
                print(f"Conflicting exports for {dest.name}: {previous} and {source}", file=sys.stderr)
                return 1
            copies[dest] = source

    for dest, source in copies.items():
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.resolve() != source.resolve():
            shutil.copy2(source, dest)
    print(f"Placed {len(found)} STL files and {len(copies) - len(found)} STEP assemblies.")
    if unknown:
        print("STLs outside the BOM (left in the export directories):", ", ".join(sorted(unknown)))
    missing = expected - found
    if missing:
        print("Missing BOM STLs:", ", ".join(sorted(missing)))
    return int(bool(missing))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export_dirs", nargs="+", metavar="EXPORT_DIR")
    sys.exit(main(*parser.parse_args().export_dirs))
