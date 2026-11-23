"""SuperDex physics + the SDK's Polyscope offscreen viewer; no other simulator."""
from pathlib import Path
import sys
from importlib.metadata import version

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from native_common import NATIVE, SPEC, JOINTS, DT, STEPS, STRIDE, targets, arguments, Evidence, boxes
import numpy as np
import trimesh
import superdex.physics as physics
import superdex.robotics as robotics
from superdex.physics.viewer import Viewer, ViewerCfg
from superdex.physics.viewer.backend import polyscope as ps
from superdex.physics.utils import render_model_registry


def main():
    args = arguments("SuperDex")
    physics.initialize(num_worker_threads=0)
    scene = physics.create_scene("Manual-Dex native tabletop")
    scene.set_gravity(SPEC["gravity_m_s2"])
    prefab = robotics.load_bot_prefab_from_urdf_file(str(NATIVE / "robot.urdf"))
    prefab.joints[0].type = physics.ArticulatedJointType.HARD
    names = [j.name for j in prefab.joints if j.type == physics.ArticulatedJointType.REVOLUTE]
    assert set(names) == set(JOINTS)
    context = robotics.create_context()
    bot = robotics.create_bot(scene, prefab, context)
    actor = bot.get_articulated_actor()
    dtype = np.float64 if physics.uses_double_precision() else np.float32
    actor.set_articulated_pose_from_joints(np.array([targets(0)[n] for n in names], dtype=dtype))
    controller = physics.PoseControllerParams()
    # Tracking arrays are indexed by link, including the fixed root, NOT by DoF.
    for link in prefab.links:
        if link.parent_link == -1:
            controller.joint_tracking.append(physics.PoseTrackingParams())
            continue
        hand = link.name.startswith("md_")
        controller.joint_tracking.append(physics.PoseTrackingParams(
            stiffness=SPEC["hand_kp" if hand else "arm_kp"],
            damping=SPEC["hand_kd" if hand else "arm_kd"], saturation=5 if hand else 150))
    actor.add_articulated_pose_controller(controller)
    # The SDK viewer accepts GLB visual overrides. Its loader undoes the SDK's
    # Y-up export convention, so encode that convention explicitly here. This
    # converts CAD mesh data only; all transforms and pixels come from SuperDex.
    visuals = NATIVE / "superdex-visuals"
    visuals.mkdir(exist_ok=True)
    for link, handle in zip(prefab.links, actor.get_nested_link_actors()):
        mesh = trimesh.load(link.render_model_file, force="mesh")
        mesh.apply_scale(np.asarray(link.render_model_scale))
        mesh.apply_transform(trimesh.transformations.rotation_matrix(-np.pi/2, [1, 0, 0]))
        path = visuals / f"{link.name}.glb"
        mesh.export(path)
        render_model_registry.register(scene, handle, str(path),
            physics.TransformRT(link.render_model_rotation, link.render_model_translation), physics.Real3(1, 1, 1))
    contact_actors = {}
    for handle in actor.get_nested_link_actors():
        link_actor = scene.get_actor(handle)
        link_actor.set_contact_layer("Robot")
        params = link_actor.get_contact_params()
        params.coulomb_friction_coefficient = SPEC["contact_friction"]
        link_actor.set_contact_params(params)
        contact_actors[link_actor.get_name().rsplit("/", 1)[-1]] = link_actor
    scene.enable_layer_contact_symmetric("Robot", "Robot", False)
    scene.enable_layer_contact_symmetric("Robot", "Environment", True)
    scene.enable_layer_contact_symmetric("Robot", "Object", True)
    scene.enable_layer_contact_symmetric("Object", "Environment", True)
    colors = {}

    def box(name, center, size, color, mass=None):
        mesh = trimesh.creation.box(extents=size)
        shape = physics.create_tri_mesh_shape(np.asarray(mesh.vertices, dtype=dtype).ravel(),
            np.asarray(mesh.faces, dtype=np.int32).ravel())
        contact = physics.ContactParams()
        contact.coulomb_friction_coefficient = SPEC["contact_friction"]
        obj = scene.create_rigid_actor(name=name, layer="Object" if mass else "Environment", shape=shape,
            world_from_local=physics.TransformRT(physics.Real3(*center)), collider_type=physics.ColliderType.BOX,
            is_static=mass is None, contact=contact, **({"mass": mass} if mass else {}))
        colors[name] = color
        if mass is None:
            contact_actors[name] = obj
        return obj

    box("floor", [0, 0, -.82], [200, 200, .1], [.78, .81, .85])
    for item in boxes():
        box(*item)
    c = SPEC["cube"]
    cube = box("cube", c["center"], c["size"], c["color"], c["mass_kg"])
    cube.register_query(physics.QueryType.TOTAL_CONTACT_FORCE)
    viewer = None
    evidence = Evidence("superdex", "SuperDex SDK offscreen viewer (Polyscope)")
    try:
        if not args.no_render:
            viewer = Viewer(ViewerCfg(backend="openGL3_egl", offscreen=True, size=(580, 460), coordinate_system="ros"))
            viewer.set_scene(scene)
            viewer.set_paused(False)
            viewer.set_enable_follow_camera(False)
            viewer.set_compute_automatic_distance(False)
            viewer.set_camera_view(SPEC["camera"]["eye"], SPEC["camera"]["target"], [0, 0, 1])
            ps.set_view_projection_mode("perspective")
            ps.set_vertical_fov_degrees(SPEC["camera"]["fov_deg"])
            ps.set_background_color((.88, .91, .94))
            for renderer in viewer.get_actor_renderers():
                renderer.set_enable_edges(False)
                renderer.set_enable_axes(False)
                name = renderer.get_actor().get_name().rsplit("/", 1)[-1]
                renderer.set_front_face_color(colors.get(name,
                    (.38, .43, .47) if name.startswith("md_") or name == "openarm_link7" else (.16, .18, .20)))
        sampled = physics.DynamicArrayReal(15)
        for step in range(1 if args.preview else STEPS):
            actor.set_articulated_target_pose(np.array([targets(step*DT)[n] for n in names], dtype=dtype))
            scene.step(DT)
            actor.get_articulated_pose(sampled)
            pos = cube.get_root_transform().translation
            contacts = {name: float(np.linalg.norm(np.asarray(cube.get_contact_force_from_actor_world(other))))
                        for name, other in contact_actors.items()}
            evidence.record(step, {n: sampled[i] for i, n in enumerate(names)}, pos, contacts)
            if args.preview or step % STRIDE == STRIDE - 1:
                if viewer:
                    viewer.render()
                    evidence.frame(viewer.take_screenshot()[:, :, :3])
                if step % 240 == STRIDE-1:
                    print(f"SuperDex native: {step+1}/{STEPS} physics steps", flush=True)
        evidence.finish(version("superdex"), preview=args.preview, rendered=not args.no_render)
    finally:
        if viewer:
            viewer.close()
        robotics.destroy_bot(scene, bot)
        physics.shutdown()


if __name__ == "__main__":
    main()
