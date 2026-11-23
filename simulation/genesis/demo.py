"""Load the composed URDF as one Genesis articulation, then play named joint targets."""
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from simulation.common import arguments, PACKAGE, BUILD, JOINT_NAMES, DT, target_positions, report
from simulation.common import TraceRecorder


def main():
    args = arguments("Genesis")
    trace = TraceRecorder("genesis", args.trace)
    import genesis as gs
    import numpy as np

    # 1. CPU is the portable default; --backend gpu opts into the installed GPU stack.
    gs.init(backend=gs.cpu if args.backend == "cpu" else gs.gpu, logging_level="warning")
    scene = gs.Scene(
        sim_options=gs.options.SimOptions(dt=DT, gravity=(0, 0, 0)),
        viewer_options=gs.options.ViewerOptions(camera_pos=(1.1, -1.1, .85), camera_lookat=(.1, 0, .45)),
        vis_options=gs.options.VisOptions(ambient_light=(.6, .6, .6)),
        show_viewer=not args.headless,
    )
    robot = scene.add_entity(gs.morphs.URDF(file=str(PACKAGE / "openarm_manual_dex.urdf"),
                                          fixed=True, merge_fixed_links=False, collision=False))
    camera = None
    if args.screenshot:
        camera = scene.add_camera(res=(1280, 960), pos=(1.1, -1.1, .85), lookat=(.1, 0, .45), GUI=False)
    scene.build()
    # 2. Resolve DOFs by name; URDF importer order is not a cross-engine contract.
    dofs = [robot.get_joint(name).dofs_idx_local[0] for name in JOINT_NAMES]
    assert robot.n_dofs == len(JOINT_NAMES) == 15
    for step in range(args.steps):
        tick = time.monotonic()
        target = target_positions(step * DT)
        robot.set_dofs_position(np.array([target[name] for name in JOINT_NAMES]),
                                dofs_idx_local=dofs, zero_velocity=True)
        scene.step()
        if trace.wants(step):
            trace.capture(step, dict(zip(JOINT_NAMES, robot.get_dofs_position(dofs_idx_local=dofs).cpu().numpy().reshape(-1))))
        if not args.headless:
            time.sleep(max(0, DT - (time.monotonic() - tick)))
    if camera is not None:
        from PIL import Image
        rgb, *_ = camera.render(rgb=True)
        (BUILD / "results").mkdir(parents=True, exist_ok=True)
        Image.fromarray(rgb).save(BUILD / "results/genesis.png")
    values = robot.get_dofs_position(dofs_idx_local=dofs).cpu().numpy().reshape(-1)
    trace.save()
    report("genesis", dict(zip(JOINT_NAMES, values)), args.steps,
           {"backend": args.backend, "genesis_version": gs.__version__})
    gs.destroy()


if __name__ == "__main__":
    main()
