#!/usr/bin/env python3
"""Render bom/BOM.md from bom/robot_hand.csv and bom/glove.csv.

Usage:  python tools/gen_bom_md.py
The CSVs are the source of truth; edit them and re-run this script.
"""
import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOM = ROOT / "bom"
ASSEMBLIES = [
    ("Robot hand", "robot_hand.csv", "shared_with_glove"),
    ("Glove", "glove.csv", "shared_with_robot"),
]
CATEGORY_ORDER = ["structure", "encoder housing", "pin", "enclosure", "camera", "tracking",
                  "actuator", "sensor", "hardware", "electronics", "fastener", "wearable", "contact"]


def load(name):
    with open(BOM / name, newline="") as f:
        return list(csv.DictReader(f))


def table(rows, cols, headers):
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(r.get(c, "")).replace("|", "\\|") for c in cols) + " |")
    return "\n".join(out)


def qty_total(rows):
    tot, todo = 0, 0
    for r in rows:
        try:
            tot += int(r["qty"])
        except ValueError:
            todo += 1
    return tot, todo


def render():
    md = ["# Bill of Materials", "",
          "Generated from `bom/robot_hand.csv` and `bom/glove.csv` by `tools/gen_bom_md.py`. "
          "Edit the CSVs, not this file.", "",
          "**Status legend:** `in CAD` = present in the released STEP assembly; "
          "`TODO` = required for a working build but not modelled in CAD - fill in before release.", "",
          "All *make* parts are FDM printed in ABS or PETG. Parts marked *mirror for left* need a "
          "mirrored copy for a left-hand variant; the rest are symmetric or handedness-agnostic.", ""]

    shared_seen = {}
    for title, fname, shared_col in ASSEMBLIES:
        rows = load(fname)
        make = [r for r in rows if r["make_buy"] == "make"]
        buy = [r for r in rows if r["make_buy"] == "buy"]
        mk_tot, _ = qty_total(make)
        by_tot, by_todo = qty_total(buy)
        md += [f"## {title}", "",
               f"- **Make (3D printed):** {len(make)} unique parts, {mk_tot} pieces",
               f"- **Buy:** {len(buy)} line items ({by_tot} pieces counted, {by_todo} quantities still TODO)",
               f"- **Shared with the other assembly:** {sum(1 for r in rows if r[shared_col] == 'yes')} line items",
               ""]
        for label, subset in (("Make - 3D printed parts", make), ("Buy - off-the-shelf", buy)):
            md += [f"### {title}: {label}", ""]
            groups = defaultdict(list)
            for r in subset:
                groups[r["category"]].append(r)
            for cat in sorted(groups, key=lambda c: CATEGORY_ORDER.index(c) if c in CATEGORY_ORDER else 99):
                md += [f"#### {cat.capitalize()}", ""]
                if label.startswith("Make"):
                    cols = ["id", "part", "qty", "subsystem", "material_spec", "mirror_for_left", "status", "notes"]
                    hdr = ["ID", "Part (CAD name)", "Qty", "Subsystem", "Material", "Mirror for left", "Status", "Notes"]
                else:
                    cols = ["id", "part", "qty", "subsystem", "material_spec", "supplier", "part_number", "status", "notes"]
                    hdr = ["ID", "Item", "Qty", "Subsystem", "Spec", "Supplier", "Part no.", "Status", "Notes"]
                md += [table(groups[cat], cols, hdr), ""]
        for r in rows:
            if r[shared_col] == "yes":
                shared_seen.setdefault(r["part"], []).append(r["id"])

    md += ["## Shared parts (identical on robot hand and glove)", "",
           "These are the same physical design on both assemblies - print/buy two of each for a full system.", "",
           table([{"part": p, "ids": ", ".join(ids)} for p, ids in sorted(shared_seen.items())],
                 ["part", "ids"], ["Part", "BOM IDs"]), ""]
    (BOM / "BOM.md").write_text("\n".join(md))
    print(f"wrote {BOM / 'BOM.md'}")


if __name__ == "__main__":
    render()
