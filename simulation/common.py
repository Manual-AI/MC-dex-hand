"""Shared names, example motion, CLI and machine-readable run results."""
import argparse
import json
import math
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build/simulation"
PACKAGE = BUILD / "generated"
ARM_JOINTS = [f"openarm_joint{i}" for i in range(1, 8)]
HAND_JOINTS = [f"md_{finger}_{stage}" for finger in ("index", "middle", "pinkyring", "thumb")
               for stage in ("proximal", "distal")]
JOINT_NAMES = ARM_JOINTS + HAND_JOINTS
DT = 1 / 240


def target_positions(t):
    """Small arm sweep and one five-second finger cycle; radians, not hardware commands."""
    phase = 2 * math.pi * t / 5
    positions = dict(zip(ARM_JOINTS, [0.2 * math.sin(phase), -.35, .1 * math.sin(phase),
                                    .8 + .15 * math.sin(phase), 0., -.1, .15 * math.sin(phase)]))
    for finger, shift in (("index", 0), ("middle", .035), ("pinkyring", .07), ("thumb", .025)):
        wave = .5 - .5 * math.cos(phase + 2 * math.pi * shift)
        for stage, degrees in (("proximal", 24 if finger == "thumb" else 32),
                               ("distal", 36 if finger == "thumb" else 45)):
            positions[f"md_{finger}_{stage}"] = math.radians(degrees) * wave
    return positions


def arguments(engine):
    parser = argparse.ArgumentParser(description=f"OpenArm + Manual-Dex in {engine}: prescribed joint-motion demo")
    parser.add_argument("--headless", action="store_true", help="No interactive window")
    parser.add_argument("--steps", type=int, default=1200, help="Finite 240 Hz steps (default: five simulated seconds)")
    parser.add_argument("--screenshot", action="store_true", help="Save an engine-rendered PNG where supported")
    parser.add_argument("--trace", action="store_true", help="Record actual joint states at 20 Hz for the shared comparison viewer")
    parser.add_argument("--backend", choices=["cpu", "gpu"], default="cpu", help="Genesis backend")
    args = parser.parse_args()
    if args.steps < 1:
        parser.error("--steps must be positive")
    return args


class TraceRecorder:
    """Record readbacks, never the requested targets, for cross-engine visualization."""

    def __init__(self, engine, enabled):
        self.engine, self.enabled, self.states = engine, enabled, []

    def wants(self, step):
        return self.enabled and step % 12 == 0

    def capture(self, step, positions):
        if self.wants(step):
            values = {name: float(positions[name]) for name in JOINT_NAMES}
            if not all(math.isfinite(v) for v in values.values()):
                raise RuntimeError("Non-finite state in engine trace")
            self.states.append({"step": step, "positions": values})

    def save(self):
        if self.enabled:
            path = BUILD / "results" / f"{self.engine}-trace.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({"engine": self.engine, "dt": DT, "sample_every": 12,
                "run_id": os.environ.get("MANUAL_DEX_RUN_ID", "direct"), "states": self.states}) + "\n")


def report(engine, positions, steps, extra=None):
    values = {name: float(positions[name]) for name in JOINT_NAMES}
    if not all(math.isfinite(value) for value in values.values()):
        raise RuntimeError("Simulator returned non-finite joint positions")
    if steps < 1:
        raise RuntimeError("No simulation steps completed")
    target = target_positions((steps - 1) * DT)
    error = max(abs(values[name] - target[name]) for name in JOINT_NAMES)
    if error > .03:
        raise RuntimeError(f"Joint playback readback differs from target by {error:.6f} rad")
    result = {"engine": engine, "status": "passed", "mode": "prescribed joint playback",
              "run_id": os.environ.get("MANUAL_DEX_RUN_ID", "direct"), "max_readback_error_rad": error,
              "joint_count": len(values), "steps": steps, "dt": DT,
              "joint_positions_rad": values, "dynamics_validated": False, **(extra or {})}
    directory = BUILD / "results"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{engine}.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result), flush=True)
