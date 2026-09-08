"""Load the assembled native MJCF, move 7 arm + 8 hand joints, and inspect the flange."""
import os
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from simulation.common import arguments, PACKAGE, BUILD, JOINT_NAMES, DT, target_positions, report


def main():
    args = arguments("MuJoCo")
    if args.headless:
        os.environ.setdefault("MUJOCO_GL", "egl")
    import mujoco
    import numpy as np

    # 1. One articulated tree: fixed arm base -> wrist flange -> eight-joint hand.
    model = mujoco.MjModel.from_xml_path(str(PACKAGE / "openarm_manual_dex.xml"))
    data = mujoco.MjData(model)
    assert model.nq == len(JOINT_NAMES) == 15
    options = mujoco.MjvOption()
    options.geomgroup[3] = 0  # Hide upstream collision stand-ins in the viewer.
    viewer = None
    if not args.headless:
        import mujoco.viewer
        viewer = mujoco.viewer.launch_passive(model, data)
        viewer.cam.lookat[:] = [.12, 0, .35]
        viewer.cam.distance, viewer.cam.azimuth, viewer.cam.elevation = 1.2, 140, -20
        viewer.opt.geomgroup[3] = 0
    completed = 0
    try:
        for step in range(args.steps):
            tick = time.monotonic()
            if viewer is not None and not viewer.is_running():
                break
            # 2. Prescribed playback, NOT a torque-controller or grasp benchmark.
            target = target_positions(step * DT)
            for name, value in target.items():
                data.joint(name).qpos[0] = value
            data.qvel[:] = 0
            mujoco.mj_step(model, data)
            mujoco.mj_forward(model, data)
            assert np.isfinite(data.qpos).all()
            completed += 1
            if viewer is not None:
                viewer.sync()
                time.sleep(max(0, DT - (time.monotonic() - tick)))
        # 3. Save evidence for headless users and automation.
        if args.screenshot:
            from PIL import Image, ImageDraw
            camera = mujoco.MjvCamera()
            camera.lookat[:] = [.12, 0, .35]
            camera.distance, camera.azimuth, camera.elevation = 1.2, 140, -20
            with mujoco.Renderer(model, height=960, width=1280) as renderer:
                renderer.update_scene(data, camera=camera, scene_option=options)
                image = Image.fromarray(renderer.render())
                draw = ImageDraw.Draw(image)
                draw.text((24, 24), "OpenArm v1 + Manual-Dex | 7 arm + 8 hand joints | Orange marker: wrist flange", fill="white")
                (BUILD / "results").mkdir(parents=True, exist_ok=True)
                image.save(BUILD / "results/mujoco.png")
        report("mujoco", {name: data.joint(name).qpos[0] for name in JOINT_NAMES}, completed,
               {"mujoco_version": mujoco.__version__})
    finally:
        if viewer is not None:
            viewer.close()


if __name__ == "__main__":
    main()
