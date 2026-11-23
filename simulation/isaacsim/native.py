"""Native PhysX articulation drives and Isaac Sim RTX/Replicator camera capture."""
from pathlib import Path
import sys
import traceback
import faulthandler
from importlib.metadata import version

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from native_common import NATIVE, SPEC, JOINTS, DT, STEPS, STRIDE, targets, arguments, Evidence, boxes


def main():
    args = arguments("Isaac Sim")
    if not version("isaacsim").startswith("6."):
        raise SystemExit("Native capture requires the Isaac Sim 6.0.1 profile; use simulation/run.py isaacsim --native")
    from isaacsim import SimulationApp
    extra = ["--/crashreporter/enabled=false", "--/exts/isaacsim.core.throttling/enable_async=false",
             "--/rtx/post/aa/op=4"]  # Native-resolution DLAA, not half-resolution DLSS.
    if args.no_render:
        extra += ["--/app/renderer/enabled=false", "--/exts/omni.kit.viewport.window/startup/disableWindowOnLoad=true"]
    else:
        extra.append("--/app/renderer/enabled=true")
    app = SimulationApp({"headless": True, "width": 580, "height": 460, "anti_aliasing": 4,
        "multi_gpu": False, "active_gpu": 0, "physics_gpu": 0,
        "renderer": "RayTracedLighting", "extra_args": extra})
    try:
        faulthandler.dump_traceback_later(120, repeat=True)
        import numpy as np
        import carb.settings
        import omni.usd
        from pxr import Usd, UsdPhysics, UsdLux, UsdGeom, UsdShade, Gf, PhysxSchema
        from isaacsim.core.api import World
        from isaacsim.core.api.objects import FixedCuboid, DynamicCuboid
        from isaacsim.core.api.materials import PhysicsMaterial
        from isaacsim.core.prims import SingleArticulation, RigidPrim
        from isaacsim.core.utils.extensions import enable_extension
        from isaacsim.core.utils.stage import add_reference_to_stage
        from isaacsim.core.utils.types import ArticulationAction

        omni.usd.get_context().new_stage()
        enable_extension("isaacsim.asset.importer.urdf")
        app.update()
        from isaacsim.asset.importer.urdf import URDFImporter, URDFImporterConfig
        config = URDFImporterConfig(urdf_path=str(NATIVE / "robot.urdf"),
            usd_path=str(NATIVE / "isaac-usd"), fix_base=True, merge_fixed_joints=False,
            collision_from_visuals=False, allow_self_collision=False,
            joint_drive_type="force", joint_target_type="position",
            override_joint_stiffness={"openarm_.*": SPEC["arm_kp"], "md_.*": SPEC["hand_kp"]},
            override_joint_damping={"openarm_.*": SPEC["arm_kd"], "md_.*": SPEC["hand_kd"]})
        print("Isaac native: importing URDF", flush=True)
        usd_path = URDFImporter(config).import_urdf()
        print(f"Isaac native: imported {usd_path}", flush=True)
        if not usd_path:
            raise RuntimeError("Native URDF -> USD import returned no asset")
        asset_stage = Usd.Stage.Open(str(usd_path))
        if not asset_stage or not asset_stage.GetDefaultPrim():
            raise RuntimeError("Native URDF -> USD import failed")
        # The 6.x converter opens intermediate stages. Start a clean scene so its
        # conversion-stage robot is not left alongside the final referenced asset.
        omni.usd.get_context().new_stage()
        world = World(stage_units_in_meters=1., physics_dt=DT, rendering_dt=DT)
        world.get_physics_context().set_gravity(-9.81)
        add_reference_to_stage(str(usd_path), "/World/Robot")
        stage = omni.usd.get_context().get_stage()
        roots = [str(p.GetPath()) for p in stage.Traverse() if str(p.GetPath()).startswith("/World/Robot")
                 and p.HasAPI(UsdPhysics.ArticulationRootAPI)]
        if len(roots) != 1:
            raise RuntimeError(f"Expected one articulation root: {roots}")
        physics_root = PhysxSchema.PhysxArticulationAPI.Apply(stage.GetPrimAtPath(roots[0]))
        physics_root.CreateSolverPositionIterationCountAttr(16)
        physics_root.CreateSolverVelocityIterationCountAttr(4)
        physics_root.CreateEnabledSelfCollisionsAttr(False)
        robot = world.scene.add(SingleArticulation(prim_path=roots[0], name="manual_dex"))
        # Force drives have physical torque saturation, rather than acceleration drives.
        for prim in stage.Traverse():
            if prim.IsA(UsdPhysics.RevoluteJoint):
                drive = UsdPhysics.DriveAPI.Get(prim, "angular")
                drive.CreateTypeAttr("force")
                drive.CreateMaxForceAttr(5. if prim.GetName().startswith("md_") else 150.)
        material = PhysicsMaterial("/World/Friction", static_friction=SPEC["contact_friction"],
                                   dynamic_friction=SPEC["contact_friction"], restitution=0.)
        contact_prims = {}
        for prim in stage.Traverse():
            if str(prim.GetPath()).startswith("/World/Robot"):
                if prim.HasAPI(UsdPhysics.RigidBodyAPI):
                    contact_prims[prim.GetName()] = str(prim.GetPath())
                if prim.HasAPI(UsdPhysics.CollisionAPI):
                    UsdShade.MaterialBindingAPI.Apply(prim).Bind(UsdShade.Material(stage.GetPrimAtPath("/World/Friction")),
                                                               materialPurpose="physics")
        for name, pos, size, color in [("floor", [0, 0, -.82], [200, 200, .1], [.78, .81, .85]), *boxes()]:
            world.scene.add(FixedCuboid(prim_path=f"/World/{name}", name=name, position=np.array(pos),
                scale=np.array(size), size=1., color=np.array(color)**2.2, physics_material=material))
            contact_prims[name] = f"/World/{name}"
        c = SPEC["cube"]
        world.scene.add(DynamicCuboid(prim_path="/World/cube", name="cube", position=np.array(c["center"]),
            scale=np.array(c["size"]), size=1., color=np.array(c["color"])**2.2, mass=c["mass_kg"], physics_material=material))
        cube = world.scene.add(RigidPrim(prim_paths_expr="/World/cube", name="cube_contact", track_contact_forces=True,
            contact_filter_prim_paths_expr=list(contact_prims.values()), max_contact_count=256))
        # USD materials use linear color. Approximate sRGB decoding above and
        # moderate lighting keep the shared gray table / orange cube recognizable.
        UsdLux.DomeLight.Define(stage, "/World/Ambient").CreateIntensityAttr(300.)
        light = UsdLux.DistantLight.Define(stage, "/World/Key")
        light.CreateIntensityAttr(750.)
        UsdGeom.Xformable(light).AddRotateXYZOp().Set(Gf.Vec3f(-30, -35, -20))
        camera = UsdGeom.Camera.Define(stage, "/World/Camera")
        cs = SPEC["camera"]
        transform = Gf.Matrix4d().SetLookAt(Gf.Vec3d(*cs["eye"]), Gf.Vec3d(*cs["target"]), Gf.Vec3d(0, 0, 1)).GetInverse()
        UsdGeom.Xformable(camera).AddTransformOp().Set(transform)
        aperture = 2 * 18 * np.tan(np.deg2rad(cs["fov_deg"])/2)
        camera.CreateFocalLengthAttr(18.)
        camera.CreateVerticalApertureAttr(aperture)
        camera.CreateHorizontalApertureAttr(aperture * 580/460)
        camera.CreateClippingRangeAttr(Gf.Vec2f(.01, 500))
        rgb = None
        if not args.no_render:
            import omni.replicator.core as rep
            rep.orchestrator.set_capture_on_play(False)
            product = rep.create.render_product(str(camera.GetPath()), (580, 460))
            rgb = rep.AnnotatorRegistry.get_annotator("rgb")
            rgb.attach([product])
        print("Isaac native: initializing PhysX scene", flush=True)
        world.reset()
        print("Isaac native: PhysX initialized", flush=True)
        dofs = np.array([robot.get_dof_index(n) for n in JOINTS])
        assert robot.num_dof == 15
        control = robot.get_articulation_controller()
        kp, kd = np.zeros(15), np.zeros(15)
        kp[dofs] = [SPEC["arm_kp"]]*7 + [SPEC["hand_kp"]]*8
        kd[dofs] = [SPEC["arm_kd"]]*7 + [SPEC["hand_kd"]]*8
        control.set_gains(kp, kd)
        # Set initial conditions once; subsequent motion is exclusively PhysX drives.
        robot.set_joint_positions(np.array(list(targets(0).values())), joint_indices=dofs)
        robot.set_joint_velocities(np.zeros(15), joint_indices=dofs)
        if rgb:
            print("Isaac native: warming RTX camera", flush=True)
            rep.orchestrator.step(delta_time=0., pause_timeline=False)
            if carb.settings.get_settings().get("/rtx/post/aa/op") != 4:
                raise RuntimeError("Native-resolution antialiasing was overridden")
            print("Isaac native: RTX camera ready", flush=True)
        initial_sim_time = world.current_time
        evidence = Evidence("isaacsim", "Isaac Sim RTX / Replicator RGB")
        for step in range(1 if args.preview else STEPS):
            control.apply_action(ArticulationAction(joint_positions=np.array(list(targets(step*DT).values())), joint_indices=dofs))
            world.step(render=False)
            pos, _ = cube.get_world_poses()
            forces = cube.get_contact_force_matrix(dt=DT)[0]
            contacts = {name: float(np.linalg.norm(force)) for name, force in zip(contact_prims, forces)}
            evidence.record(step, dict(zip(JOINTS, robot.get_joint_positions(joint_indices=dofs))), pos[0], contacts)
            if args.preview or step % STRIDE == STRIDE - 1:
                if rgb:
                    world.render()
                    rep.orchestrator.step(delta_time=0., pause_timeline=False)
                    pixels = rgb.get_data()
                    if pixels.shape != (460, 580, 4):
                        raise RuntimeError(f"Invalid native camera output: {pixels.shape}")
                    evidence.frame(pixels[:, :, :3])
                if step % 240 == STRIDE-1:
                    print(f"Isaac native: {step+1}/{STEPS} physics steps", flush=True)
        simulated = world.current_time - initial_sim_time
        expected = DT if args.preview else SPEC["duration_s"]
        if not np.isclose(simulated, expected, atol=1e-5):
            raise RuntimeError(f"Rendering changed the physics clock: {simulated} != {expected}")
        evidence.finish(version("isaacsim"), preview=args.preview, rendered=not args.no_render,
            extra={"simulated_time_s": simulated, "anti_aliasing": "DLAA (native resolution)"})
    except Exception:
        traceback.print_exc()
        sys.stderr.flush()
        raise
    finally:
        faulthandler.cancel_dump_traceback_later()
        app.close()


if __name__ == "__main__":
    main()
