"""Eight-channel, two-pose calibration; no guessed servo registers or physical travel."""
import json
import math
from pathlib import Path

JOINTS = tuple(f"md_{finger}_{part}" for finger in ("index", "middle", "pinkyring", "thumb")
               for part in ("proximal", "distal"))
FEATURES = {f"{name}.pos": float for name in JOINTS}


def finite_joints(values):
    if not isinstance(values, dict) or set(values) != set(JOINTS):
        raise ValueError("Expected exactly the eight named Manual-Dex hand joints")
    if any(isinstance(v, bool) or not isinstance(v, (float, int)) or not math.isfinite(v) for v in values.values()):
        raise ValueError("Joint values must be finite numbers")
    return {name: float(values[name]) for name in JOINTS}


def validate_mapping(mapping, device_id=None, require_measured=False):
    if mapping.get("schema") != "manual-dex-calibration-v1":
        raise ValueError("Unsupported calibration schema")
    if not isinstance(mapping.get("device_id"), str) or not mapping["device_id"].strip():
        raise ValueError("A stable calibration device ID is required")
    if device_id and mapping.get("device_id") != device_id:
        raise ValueError("Calibration device ID does not match this glove")
    if mapping.get("kind") not in ("synthetic", "virtual", "measured"):
        raise ValueError("Calibration must state synthetic, virtual or measured provenance")
    if require_measured and mapping["kind"] != "measured":
        raise ValueError("Physical hand requires measured calibration, not virtual/synthetic examples")
    if set(mapping.get("joints", {})) != set(JOINTS):
        raise ValueError("Calibration must cover all eight joints exactly")
    for joint, row in mapping["joints"].items():
        for field in ("raw_open", "raw_closed", "open_rad", "closed_rad"):
            value = row.get(field)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError(f"Invalid {field} for {joint}")
        if abs(row["raw_closed"] - row["raw_open"]) < 32:
            raise ValueError(f"Insufficient sensor span for {joint}; check wiring and movement")
        if not all(0 <= row[k] <= 4095 for k in ("raw_open", "raw_closed")):
            raise ValueError("Reference raw values must be 12-bit ADC counts")
        if abs(row["closed_rad"] - row["open_rad"]) < .001:
            raise ValueError(f"Reference angles do not span a range for {joint}")
    return mapping


def load_mapping(path, **kwargs):
    return validate_mapping(json.loads(Path(path).read_text()), **kwargs)


def map_raw(mapping, raw):
    raw = finite_joints(raw)
    action = {}
    for joint, value in raw.items():
        if not 0 <= value <= 4095:
            raise ValueError("Glove sample is outside 12-bit ADC range")
        row = mapping["joints"][joint]
        fraction = (value - row["raw_open"]) / (row["raw_closed"] - row["raw_open"])
        fraction = min(1., max(0., fraction))
        action[f"{joint}.pos"] = row["open_rad"] + fraction * (row["closed_rad"] - row["open_rad"])
    return action


def synthetic_mapping(device_id):
    return {"schema": "manual-dex-calibration-v1", "device_id": device_id, "kind": "synthetic",
            "joints": {name: {"raw_open": 500, "raw_closed": 3500, "open_rad": 0.,
                              "closed_rad": .55 if name.endswith("proximal") else .78} for name in JOINTS}}


def save_mapping(path, mapping):
    validate_mapping(mapping)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Never silently overwrite a measured calibration or another device's file.
    with path.open("x") as stream:
        json.dump(mapping, stream, indent=2)
        stream.write("\n")
