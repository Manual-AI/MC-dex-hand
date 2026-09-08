"""Shared scene specification and evidence; no simulator or 3D renderer imports."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import uuid

ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / "build/simulation/native"
SPEC = json.loads((ROOT / "simulation/native_scene.json").read_text())
POLICY = json.loads((ROOT / "simulation/pick_place.json").read_text())
JOINTS = [f"openarm_joint{i}" for i in range(1, 8)] + [
    f"md_{finger}_{stage}" for finger in ("index", "middle", "pinkyring", "thumb")
    for stage in ("proximal", "distal")]
DT = SPEC["physics_dt_s"]
STEPS = round(SPEC["duration_s"] / DT)
STRIDE = round(1 / SPEC["fps"] / DT)


def targets(t):
    """Smooth joint-drive references; never set an object's pose or force."""
    points = POLICY["waypoints"]
    t = max(points[0]["t_s"], min(t, points[-1]["t_s"]))
    for a, b in zip(points, points[1:]):
        if t <= b["t_s"]:
            u = (t-a["t_s"])/(b["t_s"]-a["t_s"])
            u = u*u*(3-2*u)
            return dict(zip(JOINTS, (x*(1-u)+y*u for x,y in zip(a["q_rad"], b["q_rad"]))))


def phase(t):
    return next(p["phase"] for p in reversed(POLICY["waypoints"]) if t >= p["t_s"])


def protocol_hash():
    return hashlib.sha256(json.dumps({"scene": SPEC, "policy": POLICY}, sort_keys=True).encode()).hexdigest()


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
        self.physics = []

    def record(self, step, positions, cube_position, contacts):
        positions = {n: float(positions[n]) for n in JOINTS}
        cube = [float(v) for v in cube_position]
        if not all(math.isfinite(v) for v in [*positions.values(), *cube]):
            raise RuntimeError("Non-finite native physics state")
        # Contacts are native per-counterpart forces [N], not overlap flags or
        # the cube's net force (opposing finger forces can cancel in that net).
        contacts = {str(n): float(f) for n, f in contacts.items()}
        if not all(math.isfinite(f) and f >= 0 for f in contacts.values()):
            raise RuntimeError("Non-finite native contact force")
        contacts = {n: f for n, f in contacts.items() if f > 1e-4}
        if contacts:
            self.contact_steps += 1
        sample = {"step": step, "joints": positions, "cube_xyz_m": cube,
                  "cube_contacts_N": contacts, "phase": phase((step+1)*DT)}
        self.physics.append(sample)
        if step % STRIDE == STRIDE - 1:
            self.states.append(sample)

    def frame(self, rgb):
        from PIL import Image
        Image.fromarray(rgb).convert("RGB").save(self.output / f"frame-{self.frames:04d}.png")
        self.frames += 1

    def finish(self, version, preview=False, extra=None, rendered=True):
        # Preserve readbacks even when validation fails; never replace a previous
        # successful manifest with a failed or physics-only run.
        (self.output / "physics.json").write_text(json.dumps(self.physics, indent=2) + "\n")
        metrics = {}
        if not preview:
            if len(self.physics) != STEPS or len(self.states) != 100 or self.frames != (100 if rendered else 0):
                raise RuntimeError(f"Incomplete native capture: states={len(self.states)}, frames={self.frames}")
            spans = {n: max(s["joints"][n] for s in self.states) - min(s["joints"][n] for s in self.states) for n in JOINTS}
            if max(spans[n] for n in JOINTS[:7]) < .1 or max(spans[n] for n in JOINTS[7:]) < .3:
                raise RuntimeError(f"Arm or fingers did not move: {spans}")
            metrics = validate_pick_place(self.physics)
        report = {"engine": self.engine, "version": version, "renderer": self.renderer,
            "status": "preview" if preview else ("passed" if rendered else "diagnostic"),
            "run_id": self.output.name, "native_physics": True, "native_rendering": rendered,
            "mode": "scripted physics-driven pick and place", "grasp_demonstrated": not preview,
            "learned_policy": False, "object_attachment": False, "object_pose_overwrite": False,
            "external_object_force": False, "protocol_sha256": protocol_hash(), "pick_place": metrics,
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
    for label, pos, color in (("pick", SPEC["cube"]["center"], [.20, .57, .88]),
                               ("place", SPEC["place_center_m"], [.20, .75, .43])):
        for axis in (0, 1):
            for sign in (-1, 1):
                center = [pos[0], pos[1], .0003]
                center[axis] += sign*.043
                size = [.089, .089, .0006]
                size[axis] = .003
                yield f"{label}_mark_{axis}_{sign+1}", center, size, color


def validate_pick_place(samples):
    """Reject drop-only, push-only, dropped-in-transit and unreleased captures."""
    if len(samples) != STEPS or [s["step"] for s in samples] != list(range(STEPS)):
        raise RuntimeError("Incomplete pick-and-place physics evidence")
    for sample in samples:
        values = [*sample["cube_xyz_m"], *sample["joints"].values(), *sample["cube_contacts_N"].values()]
        if (len(sample["cube_xyz_m"]) != 3 or set(sample["joints"]) != set(JOINTS)
                or not all(math.isfinite(v) for v in values)
                or any(f < 0 for f in sample["cube_contacts_N"].values())):
            raise RuntimeError("Invalid pick-and-place physics evidence")
    start, goal = SPEC["cube"]["center"], SPEC["place_center_m"]
    half = SPEC["cube"]["size"][2]/2
    def fingers(s):
        return {n for n,f in s["cube_contacts_N"].items() if n.startswith("md_") and f > .001}
    def held(s):
        names = fingers(s)
        return (any("thumb" in n for n in names) and any("thumb" not in n for n in names)
                and not any(n in s["cube_contacts_N"] for n in ("table", "floor"))
                and s["cube_xyz_m"][2] > half+SPEC["minimum_lift_m"])
    initial = samples[:60]
    if any(math.dist(s["cube_xyz_m"], [*start[:2], half]) > .003 for s in initial):
        raise RuntimeError("Cube must start at rest on the table, not drop from the air")
    if sum("table" in s["cube_contacts_N"] for s in initial) < 40:
        raise RuntimeError("Initial cube/table support not measured")
    transport = samples[round(2.45/DT):round(3.20/DT)]
    held_fraction = sum(held(s) for s in transport)/len(transport)
    if held_fraction < .85:
        raise RuntimeError(f"Unsupported opposing-finger grasp not sustained during transport: {held_fraction:.1%}")
    if math.dist(transport[-1]["cube_xyz_m"][:2], transport[0]["cube_xyz_m"][:2]) < .12:
        raise RuntimeError("Cube was not transported while grasped")
    final = samples[round(4.65/DT):]
    errors = [math.dist(s["cube_xyz_m"][:2], goal[:2]) for s in final]
    if max(errors) > SPEC["placement_tolerance_m"]:
        raise RuntimeError(f"Cube missed the placement target: {max(errors):.3f} m")
    if any(abs(s["cube_xyz_m"][2]-half) > .004 for s in final):
        raise RuntimeError("Cube did not settle flat on the destination table")
    if sum("table" in s["cube_contacts_N"] for s in final) < .9*len(final) or any(fingers(s) for s in final):
        raise RuntimeError("Cube must be released: table-supported with no finger contact")
    speed = max(math.dist(a["cube_xyz_m"], b["cube_xyz_m"])/DT for a,b in zip(final, final[1:]))
    if speed > .05:
        raise RuntimeError(f"Placed cube is still moving: {speed:.3f} m/s")
    return {"passed": True, "maximum_lift_m": max(s["cube_xyz_m"][2] for s in samples)-half,
            "opposing_contact_transport_fraction": held_fraction,
            "transport_distance_m": math.dist(transport[-1]["cube_xyz_m"][:2], transport[0]["cube_xyz_m"][:2]),
            "final_xy_error_m": errors[-1], "final_max_speed_m_s": speed,
            "released_and_table_supported": True}
