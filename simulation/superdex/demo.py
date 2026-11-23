"""Import a complete OpenArm + Manual-Dex URDF into SuperDex, including render meshes."""
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from simulation.common import arguments, PACKAGE, JOINT_NAMES, DT, target_positions, report
from simulation.common import TraceRecorder


def main():
    args = arguments("SuperDex")
    trace = TraceRecorder("superdex", args.trace)
    if args.screenshot:
        raise SystemExit("SuperDex screenshots use the desktop debugger; omit --screenshot for headless JSON validation.")
    import numpy as np
    import superdex.physics as physics
    import superdex.robotics as robotics

    physics.initialize(num_worker_threads=0)
    scene = physics.create_scene("OpenArm v1 + Manual-Dex: 7 arm + 8 hand joints")
    scene.set_gravity([0, 0, 0])
    # 1. The runtime importer adds a FREE world joint; weld it for a tabletop arm.
    prefab = robotics.load_bot_prefab_from_urdf_file(str(PACKAGE / "openarm_manual_dex.urdf"))
    prefab.joints[0].type = physics.ArticulatedJointType.HARD
    name_to_dof = {}
    for joint in prefab.joints:
        if joint.type == physics.ArticulatedJointType.REVOLUTE:
            name_to_dof[joint.name] = len(name_to_dof)
    assert set(name_to_dof) == set(JOINT_NAMES)
    context = robotics.create_context()
    bot = robotics.create_bot(scene, prefab, context)
    actor = bot.get_articulated_actor()
    assert actor.get_num_dofs() == 15
    dtype = np.float64 if physics.uses_double_precision() else np.float32
    pose = np.zeros(15, dtype=dtype)
    velocity = np.zeros(15, dtype=dtype)
    # 2. Contact is disabled for this uncalibrated playback example. The generated
    # watertight collision meshes are stand-ins, not contact-validated hardware.
    layers = []
    scene.enumerate_contact_layer_names(layers.append)
    for a in layers:
        for b in layers:
            scene.enable_layer_contact_symmetric(a, b, False)
    completed = 0
    try:
        physics.get_debug_server().set_coordinate_space(physics.CoordinateSpace(axes=physics.CoordinateSpaceAxes.FLU))
        if not args.headless and not physics.debugger.attach():
            raise RuntimeError("SuperDex debugger did not connect; use --headless for non-GUI verification")
        if not args.headless:
            print("Debugger connected. Select the scene and press Play to start; the debugger starts paused.", flush=True)
        for step in range(args.steps):
            tick = time.monotonic()
            if not args.headless and not physics.debugger.is_attached():
                break
            for name, value in target_positions(step * DT).items():
                pose[name_to_dof[name]] = value
            actor.set_articulated_pose_from_joints(pose)
            actor.set_articulated_joint_velocities(velocity)
            scene.step(DT)
            completed += 1
            if trace.wants(step):
                sampled = physics.DynamicArrayReal(15)
                actor.get_articulated_pose(sampled)
                trace.capture(step, {name: sampled[index] for name, index in name_to_dof.items()})
            if not args.headless:
                time.sleep(max(0, DT - (time.monotonic() - tick)))
        values = physics.DynamicArrayReal(15)
        actor.get_articulated_pose(values)
        trace.save()
        report("superdex", {name: values[index] for name, index in name_to_dof.items()}, completed)
    finally:
        robotics.destroy_bot(scene, bot)
        physics.shutdown()


if __name__ == "__main__":
    main()
