"""Import the composed URDF to USD and move the full articulation in Isaac Sim 5.1."""
from pathlib import Path
import sys
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from simulation.common import arguments, PACKAGE, BUILD, JOINT_NAMES, DT, target_positions, report
from simulation.common import TraceRecorder


def main():
    args = arguments("Isaac Sim")
    trace = TraceRecorder("isaacsim", args.trace)
    # Isaac Sim must bootstrap Kit BEFORE importing omni, pxr or its core APIs.
    # EULA acceptance is the launcher's explicit user choice, never set here.
    from isaacsim import SimulationApp
    app = SimulationApp({"headless": args.headless, "width": 1280, "height": 960,
                         "create_new_stage": False, "multi_gpu": False,
                         "disable_viewport_updates": args.headless and not args.screenshot,
                         "extra_args": ["--/app/renderer/enabled=false",
                                        "--/exts/omni.kit.viewport.window/startup/disableWindowOnLoad=true"]
                         if args.headless and not args.screenshot else []})
    try:
        import numpy as np
        import omni.kit.commands
        import omni.usd
        from pxr import Usd, UsdPhysics, UsdLux
        from isaacsim.core.api import World
        from isaacsim.core.prims import SingleArticulation
        from isaacsim.core.utils.extensions import enable_extension
        from isaacsim.core.utils.stage import add_reference_to_stage
        from isaacsim.core.utils.viewports import set_camera_view

        # 1. Convert one already-attached URDF, not two independent articulations.
        omni.usd.get_context().new_stage()
        enable_extension("isaacsim.asset.importer.urdf")
        app.update()
        ok, config = omni.kit.commands.execute("URDFCreateImportConfig")
        if not ok:
            raise RuntimeError("URDF importer could not create its configuration")
        config.set_fix_base(True)
        config.set_make_default_prim(True)
        config.set_merge_fixed_joints(False)
        config.set_self_collision(False)
        config.set_import_inertia_tensor(True)
        config.set_default_drive_strength(0.0)
        config.set_default_position_drive_damping(0.0)
        usd_path = PACKAGE / "openarm_manual_dex.usd"
        ok, root_path = omni.kit.commands.execute("URDFParseAndImportFile",
                                                urdf_path=str(PACKAGE / "openarm_manual_dex.urdf"),
                                                import_config=config, dest_path=str(usd_path))
        if not ok:
            raise RuntimeError("URDF -> USD conversion failed; inspect the importer log")
        asset_stage = Usd.Stage.Open(str(usd_path))
        if not asset_stage or not asset_stage.GetDefaultPrim():
            raise RuntimeError(f"Imported USD has no default prim: {usd_path}")
        world = World(stage_units_in_meters=1.0, physics_dt=DT, rendering_dt=1 / 60)
        world.get_physics_context().set_gravity(0.0)
        add_reference_to_stage(str(usd_path), "/World/OpenArmManualDex")
        stage = omni.usd.get_context().get_stage()
        UsdLux.DomeLight.Define(stage, "/World/InspectionLight").CreateIntensityAttr(1000.0)
        # Explicitly disable every generated proxy collider in this playback demo.
        for prim in stage.Traverse():
            if prim.HasAPI(UsdPhysics.CollisionAPI):
                UsdPhysics.CollisionAPI(prim).GetCollisionEnabledAttr().Set(False)
        roots = [str(prim.GetPath()) for prim in stage.Traverse()
                 if str(prim.GetPath()).startswith("/World/OpenArmManualDex")
                 and prim.HasAPI(UsdPhysics.ArticulationRootAPI)]
        if len(roots) != 1:
            raise RuntimeError(f"Expected one articulation root, found {roots}")
        robot = world.scene.add(SingleArticulation(prim_path=roots[0], name="manual_dex"))
        if not args.headless or args.screenshot:
            set_camera_view(eye=np.array([1.1, -1.1, .85]), target=np.array([.1, 0, .45]))
        world.reset()
        # 2. Resolve by name after initialization; no assumption about PhysX ordering.
        dofs = [robot.get_dof_index(name) for name in JOINT_NAMES]
        assert robot.num_dof == 15
        for step in range(args.steps):
            target = target_positions(step * DT)
            robot.set_joint_positions(np.array([target[name] for name in JOINT_NAMES]), joint_indices=dofs)
            robot.set_joint_velocities(np.zeros(15), joint_indices=dofs)
            world.step(render=not args.headless or args.screenshot)
            if trace.wants(step):
                trace.capture(step, dict(zip(JOINT_NAMES, robot.get_joint_positions(joint_indices=dofs))))
        if args.screenshot:
            from omni.kit.viewport.utility import get_active_viewport, capture_viewport_to_file
            (BUILD / "results").mkdir(parents=True, exist_ok=True)
            capture_viewport_to_file(get_active_viewport(), str(BUILD / "results/isaacsim.png"))
            for _ in range(20):
                app.update()
        positions = robot.get_joint_positions(joint_indices=dofs)
        trace.save()
        report("isaacsim", dict(zip(JOINT_NAMES, positions)), args.steps,
               {"usd": str(usd_path), "importer_root": root_path})
    except Exception:
        # Kit's fast shutdown can exit the process before Python prints an active
        # exception. Preserve the traceback; run.py also requires a fresh run-ID result.
        traceback.print_exc()
        sys.stderr.flush()
        raise
    finally:
        app.close()


if __name__ == "__main__":
    main()
