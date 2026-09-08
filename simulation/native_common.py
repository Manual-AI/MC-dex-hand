"""Shared scene specification and evidence; no simulator or 3D renderer imports."""
import argparse
import json
import math
import os
from pathlib import Path
import uuid

ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / "build/simulation/native"
SPEC = json.loads((ROOT / "simulation/native_scene.json").read_text())
JOINTS = [f"openarm_joint{i}" for i in range(1, 8)] + [
    f"md_{finger}_{stage}" for finger in ("index", "middle", "pinkyring", "thumb")
    for stage in ("proximal", "distal")]
DT = SPEC["physics_dt_s"]
STEPS = round(SPEC["duration_s"] / DT)
STRIDE = round(1 / SPEC["fps"] / DT)


def targets(t):
    phase = 2 * math.pi * t / SPEC["duration_s"]
    q = [.32 * math.sin(phase), -.35 + .1 * math.sin(phase), .12 * math.sin(phase),
         .85 + .18 * math.sin(phase), .1 * math.sin(phase), -.1 + .06 * math.sin(phase), .12 * math.sin(phase)]
    for i in range(8):
        wave = .5 - .5 * math.cos(phase + .03 * i)
        q.append((.42 if i >= 6 else .55) * wave if i % 2 == 0 else (.62 if i >= 6 else .78) * wave)
    return dict(zip(JOINTS, q))


def arguments(engine):
    parser = argparse.ArgumentParser(description=f"Native {engine} gravity, contact, joint-drive and rendering demo")
    parser.add_argument("--preview", action="store_true", help="Render one frame after initialization")
    parser.add_argument("--no-render", action="store_true", help="Numerical diagnostic only; cannot publish a GIF")
    parser.add_argument("--headless", action="store_true", help="Retained for launcher compatibility; captures are offscreen")
    return parser.parse_args()


class Evidence:
    def __init__(self, engine, renderer):
        self.engine, self.renderer, self.states = engine, renderer, []
        self.output = NATIVE / "captures" / engine / os.environ.get("MANUAL_DEX_RUN_ID", uuid.uuid4().hex)
        self.output.mkdir(parents=True, exist_ok=True)
        self.frames = 0
        self.contact_steps = 0

    def record(self, step, positions, cube_position, contacts):
        positions = {n: float(positions[n]) for n in JOINTS}
        cube = [float(v) for v in cube_position]
        if not all(math.isfinite(v) for v in [*positions.values(), *cube]):
            raise RuntimeError("Non-finite native physics state")
        if contacts:
            self.contact_steps += 1
        if step % STRIDE == STRIDE - 1:
            self.states.append({"step": step, "joints": positions, "cube_xyz_m": cube})

    def frame(self, rgb):
        from PIL import Image
        Image.fromarray(rgb).convert("RGB").save(self.output / f"frame-{self.frames:04d}.png")
        self.frames += 1

    def finish(self, version, preview=False, extra=None, rendered=True):
        if not preview:
            if len(self.states) != 100 or self.frames != (100 if rendered else 0):
                raise RuntimeError(f"Incomplete native capture: states={len(self.states)}, frames={self.frames}")
            spans = {n: max(s["joints"][n] for s in self.states) - min(s["joints"][n] for s in self.states) for n in JOINTS}
            if min(spans.values()) < .015:
                raise RuntimeError(f"A commanded joint did not move: {spans}")
            if not .015 < self.states[-1]["cube_xyz_m"][2] < .07:
                raise RuntimeError("The free cube did not settle on the table")
            if self.contact_steps < 100:
                raise RuntimeError("Insufficient measured cube/table contact")
            if max(s["cube_xyz_m"][2] for s in self.states) < .20:
                raise RuntimeError("The free cube did not fall from its initial height")
        report = {"engine": self.engine, "version": version, "renderer": self.renderer,
            "status": "preview" if preview else ("passed" if rendered else "diagnostic"),
            "run_id": self.output.name, "native_physics": True, "native_rendering": rendered,
            "mode": "joint drives, gravity and free-cube table contact", "grasp_demonstrated": False,
            "state_overwrite_during_playback": False, "dynamics_calibrated_to_hardware": False,
            "self_collision": False, "gravity_m_s2": SPEC["gravity_m_s2"],
            "dt_s": DT, "frames": self.frames, "fps": SPEC["fps"], "contact_steps": self.contact_steps,
            "capture_dir": str(self.output), "states": self.states, **(extra or {})}
        (self.output / "result.json").write_text(json.dumps(report, indent=2) + "\n")
        if not preview and rendered:
            (NATIVE / f"{self.engine}.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps({k: v for k, v in report.items() if k != "states"}, indent=2), flush=True)


def boxes():
    """Matching table and four legs, all dimensions full extents in metres."""
    table = SPEC["table"]
    yield "table", table["center"], table["size"], table["color"]
    for i, (x, y) in enumerate(((-.24, -.37), (-.24, .37), (.74, -.37), (.74, .37))):
        yield f"leg{i}", [x, y, -.42], [.05, .05, .68], [.2, .24, .27]
