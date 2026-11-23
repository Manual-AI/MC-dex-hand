"""Genesis-native raster rendering, PD joint drives and gravity/contact simulation."""
import os
from pathlib import Path
import sys

os.environ.setdefault("PYOPENGL_PLATFORM", "egl")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from native_common import NATIVE, SPEC, JOINTS, DT, STEPS, STRIDE, targets, arguments, Evidence, boxes
import genesis as gs
import numpy as np


def main():
    args = arguments("Genesis")
    gs.init(backend=gs.cpu, logging_level="warning")
    scene = gs.Scene(sim_options=gs.options.SimOptions(dt=DT, gravity=tuple(SPEC["gravity_m_s2"])),
        rigid_options=gs.options.RigidOptions(enable_collision=True, enable_self_collision=False,
                                              integrator=gs.integrator.implicitfast, iterations=80),
        vis_options=gs.options.VisOptions(ambient_light=(.4, .4, .4), background_color=(.88, .91, .94)),
        show_viewer=False)
    robot = scene.add_entity(gs.morphs.URDF(file=str(NATIVE / "robot.urdf"), fixed=True,
        merge_fixed_links=False, collision=True, default_armature=0.),
        material=gs.materials.Rigid(friction=SPEC["contact_friction"]))
    scene.add_entity(gs.morphs.Plane(pos=(0, 0, -.77)), surface=gs.surfaces.Default(color=(.78, .81, .85)))
    contact_names = {link.idx: link.name for link in robot.links}
    for name, pos, size, color in boxes():
        entity = scene.add_entity(gs.morphs.Box(pos=tuple(pos), size=tuple(size), fixed=True),
                         surface=gs.surfaces.Default(color=tuple(color)), material=gs.materials.Rigid(friction=SPEC["contact_friction"]))
        contact_names.update({link.idx: name for link in entity.links})
    cube_spec = SPEC["cube"]
    cube = scene.add_entity(gs.morphs.Box(pos=tuple(cube_spec["center"]), size=tuple(cube_spec["size"])),
        material=gs.materials.Rigid(rho=cube_spec["mass_kg"]/np.prod(cube_spec["size"]), friction=SPEC["contact_friction"]),
        surface=gs.surfaces.Default(color=tuple(cube_spec["color"])))
    camera = scene.add_camera(res=(580, 460), pos=tuple(SPEC["camera"]["eye"]),
        lookat=tuple(SPEC["camera"]["target"]), fov=SPEC["camera"]["fov_deg"], GUI=False)
    scene.build()
    dofs = [robot.get_joint(n).dofs_idx_local[0] for n in JOINTS]
    robot.set_dofs_armature(np.array([.01]*7+[.001]*8), dofs_idx_local=dofs)
    robot.set_dofs_kp(np.array([SPEC["arm_kp"]]*7+[SPEC["hand_kp"]]*8), dofs_idx_local=dofs)
    robot.set_dofs_kv(np.array([SPEC["arm_kd"]]*7+[SPEC["hand_kd"]]*8), dofs_idx_local=dofs)
    force = np.array([150.]*7+[5.]*8)
    robot.set_dofs_force_range(-force, force, dofs_idx_local=dofs)
    # Initial condition only. Position targets go through Genesis's PD controller thereafter.
    robot.set_dofs_position(np.array(list(targets(0).values())), dofs_idx_local=dofs, zero_velocity=True)
    evidence = Evidence("genesis", "Genesis native rasterizer")
    try:
        for step in range(1 if args.preview else STEPS):
            robot.control_dofs_position(np.array(list(targets(step*DT).values())), dofs_idx_local=dofs)
            scene.step()
            values = robot.get_dofs_position(dofs_idx_local=dofs).cpu().numpy().reshape(-1)
            position = cube.get_pos().cpu().numpy().reshape(-1)
            raw = cube.get_contacts()
            contacts = {}
            for a,b,f in zip(raw["link_a"].cpu().numpy(), raw["link_b"].cpu().numpy(), raw["force_a"].cpu().numpy()):
                name = contact_names.get(int(a), contact_names.get(int(b), "floor"))
                contacts[name] = contacts.get(name, 0.) + float(np.linalg.norm(f))
            evidence.record(step, dict(zip(JOINTS, values)), position, contacts)
            if args.preview or step % STRIDE == STRIDE-1:
                if not args.no_render:
                    rgb, *_ = camera.render(rgb=True)
                    evidence.frame(rgb)
                if step % 240 == STRIDE-1:
                    print(f"Genesis native: {step+1}/{STEPS} physics steps", flush=True)
        evidence.finish(gs.__version__, preview=args.preview, rendered=not args.no_render)
    finally:
        gs.destroy()


if __name__ == "__main__":
    main()
