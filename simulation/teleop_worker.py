"""Private local RPC worker: eight hand joint radians, no hardware/network control."""
import argparse
import json
import math
import os
from pathlib import Path
import socket
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from simulation.common import ROOT, PACKAGE, JOINT_NAMES, HAND_JOINTS, DT, target_positions


class Backend:
    def __init__(self, engine, headless):
        self.engine, self.headless = engine, headless
        self.viewer, self.app, self.robot, self.physics = None, None, None, None
        import numpy as np
        self.np = np
        if engine == "mujoco":
            import mujoco
            self.mj = mujoco
            self.model = mujoco.MjModel.from_xml_path(str(PACKAGE / "openarm_manual_dex.xml"))
            self.data = mujoco.MjData(self.model)
            if not headless:
                import mujoco.viewer
                self.viewer = mujoco.viewer.launch_passive(self.model, self.data)
                self.viewer.cam.lookat[:] = [.12, 0, .35]
                self.viewer.cam.distance = 1.2
                self.viewer.cam.azimuth, self.viewer.cam.elevation = 140, -20
                self.viewer.opt.geomgroup[3] = 0
        elif engine == "genesis":
            import genesis as gs
            self.gs = gs
            gs.init(backend=gs.cpu, logging_level="warning")
            self.scene = gs.Scene(sim_options=gs.options.SimOptions(dt=DT, gravity=(0, 0, 0)),
                viewer_options=gs.options.ViewerOptions(camera_pos=(1.1, -1.1, .85), camera_lookat=(.1, 0, .45)),
                show_viewer=not headless)
            self.robot = self.scene.add_entity(gs.morphs.URDF(file=str(PACKAGE / "openarm_manual_dex.urdf"),
                fixed=True, merge_fixed_links=False, collision=False))
            self.scene.build()
            self.dofs = [self.robot.get_joint(name).dofs_idx_local[0] for name in JOINT_NAMES]
        elif engine == "superdex":
            import superdex.physics as physics
            import superdex.robotics as robotics
            self.physics, self.robotics = physics, robotics
            physics.initialize(num_worker_threads=0)
            self.scene = physics.create_scene("Manual-Dex LeRobot teleoperation")
            self.scene.set_gravity([0, 0, 0])
            prefab = robotics.load_bot_prefab_from_urdf_file(str(PACKAGE / "openarm_manual_dex.urdf"))
            prefab.joints[0].type = physics.ArticulatedJointType.HARD
            self.joints = [j.name for j in prefab.joints if j.type == physics.ArticulatedJointType.REVOLUTE]
            self.context = robotics.create_context()
            self.robot = robotics.create_bot(self.scene, prefab, self.context)
            self.actor = self.robot.get_articulated_actor()
            self.dtype = np.float64 if physics.uses_double_precision() else np.float32
            layers = []
            self.scene.enumerate_contact_layer_names(layers.append)
            for a in layers:
                for b in layers:
                    self.scene.enable_layer_contact_symmetric(a, b, False)
            if not headless:
                physics.get_debug_server().set_coordinate_space(physics.CoordinateSpace(axes=physics.CoordinateSpaceAxes.FLU))
                if not physics.debugger.attach():
                    raise RuntimeError("Debugger did not connect")
                print("Press Play in the SuperDex debugger to allow LeRobot to step.", flush=True)
        else:
            self._init_isaac(headless)
        self.step({name: 0. for name in HAND_JOINTS}, DT)

    def _init_isaac(self, headless):
        from isaacsim import SimulationApp
        self.app = SimulationApp({"headless": headless, "create_new_stage": False, "multi_gpu": False,
            "disable_viewport_updates": headless,
            "extra_args": ["--/app/renderer/enabled=false", "--/exts/omni.kit.viewport.window/startup/disableWindowOnLoad=true"] if headless else []})
        import omni.kit.commands
        import omni.usd
        from pxr import Usd, UsdPhysics
        from isaacsim.core.api import World
        from isaacsim.core.prims import SingleArticulation
        from isaacsim.core.utils.extensions import enable_extension
        from isaacsim.core.utils.stage import add_reference_to_stage
        omni.usd.get_context().new_stage()
        enable_extension("isaacsim.asset.importer.urdf")
        self.app.update()
        ok, config = omni.kit.commands.execute("URDFCreateImportConfig")
        if not ok:
            raise RuntimeError("Cannot configure URDF importer")
        config.set_fix_base(True)
        config.set_make_default_prim(True)
        config.set_merge_fixed_joints(False)
        config.set_self_collision(False)
        config.set_import_inertia_tensor(True)
        config.set_default_drive_strength(0.)
        config.set_default_position_drive_damping(0.)
        destination = ROOT / "build/lerobot/usd" / str(os.getpid()) / "openarm_manual_dex.usd"
        destination.parent.mkdir(parents=True, exist_ok=True)
        ok, _ = omni.kit.commands.execute("URDFParseAndImportFile", urdf_path=str(PACKAGE / "openarm_manual_dex.urdf"),
                                          import_config=config, dest_path=str(destination))
        # Retain the stage while inspecting its prim; a prim from a temporary
        # Stage.Open() becomes invalid as soon as that stage is destroyed.
        asset_stage = Usd.Stage.Open(str(destination)) if ok else None
        if not asset_stage or not asset_stage.GetDefaultPrim():
            raise RuntimeError("URDF import failed")
        self.world = World(stage_units_in_meters=1., physics_dt=DT, rendering_dt=1/60)
        self.world.get_physics_context().set_gravity(0.)
        add_reference_to_stage(str(destination), "/World/ManualDex")
        stage = omni.usd.get_context().get_stage()
        roots = []
        for prim in stage.Traverse():
            if prim.HasAPI(UsdPhysics.CollisionAPI):
                UsdPhysics.CollisionAPI(prim).GetCollisionEnabledAttr().Set(False)
            if str(prim.GetPath()).startswith("/World/ManualDex") and prim.HasAPI(UsdPhysics.ArticulationRootAPI):
                roots.append(str(prim.GetPath()))
        if len(roots) != 1:
            raise RuntimeError(f"Expected one articulation, got {roots}")
        self.robot = self.world.scene.add(SingleArticulation(prim_path=roots[0], name="manual_dex"))
        self.world.reset()
        self.dofs = [self.robot.get_dof_index(name) for name in JOINT_NAMES]

    def step(self, hand, dt):
        if set(hand) != set(HAND_JOINTS) or any(isinstance(v, bool) or not isinstance(v, (float, int)) or not math.isfinite(v) or abs(v) > 1.5 for v in hand.values()):
            raise ValueError("Eight finite hand coordinates within CAD display bounds are required")
        if isinstance(dt, bool) or not isinstance(dt, (int, float)) or not math.isfinite(dt) or not 0 < dt <= .1:
            raise ValueError("Invalid step interval")
        target = target_positions(0)
        target.update(hand)  # The seven arm joints stay at a fixed inspection pose.
        n = max(1, round(dt / DT))
        np = self.np
        for _ in range(n):
            if self.engine == "mujoco":
                for name, value in target.items():
                    self.data.joint(name).qpos[0] = value
                self.data.qvel[:] = 0
                self.mj.mj_step(self.model, self.data)
                self.mj.mj_forward(self.model, self.data)
            elif self.engine == "genesis":
                self.robot.set_dofs_position(np.array([target[name] for name in JOINT_NAMES]), dofs_idx_local=self.dofs, zero_velocity=True)
                self.scene.step()
            elif self.engine == "superdex":
                self.actor.set_articulated_pose_from_joints(np.array([target[name] for name in self.joints], dtype=self.dtype))
                self.actor.set_articulated_joint_velocities(np.zeros(15, dtype=self.dtype))
                self.scene.step(DT)
            else:
                self.robot.set_joint_positions(np.array([target[name] for name in JOINT_NAMES]), joint_indices=self.dofs)
                self.robot.set_joint_velocities(np.zeros(15), joint_indices=self.dofs)
                self.world.step(render=not self.headless)
        if self.viewer is not None:
            if not self.viewer.is_running():
                raise RuntimeError("Simulation viewer closed")
            self.viewer.sync()
        return self.positions()

    def positions(self):
        if self.engine == "mujoco":
            values = {name: float(self.data.joint(name).qpos[0]) for name in HAND_JOINTS}
        else:
            if self.engine == "genesis":
                vector = self.robot.get_dofs_position(dofs_idx_local=self.dofs).cpu().numpy().reshape(-1)
                names = JOINT_NAMES
            elif self.engine == "superdex":
                vector = self.physics.DynamicArrayReal(15)
                self.actor.get_articulated_pose(vector)
                names = self.joints
            else:
                vector = self.robot.get_joint_positions(joint_indices=self.dofs)
                names = JOINT_NAMES
            all_values = dict(zip(names, vector))
            values = {name: float(all_values[name]) for name in HAND_JOINTS}
        if not all(math.isfinite(v) for v in values.values()):
            raise RuntimeError("Non-finite simulator readback")
        return values

    def close(self):
        if self.viewer is not None:
            self.viewer.close()
        if self.engine == "genesis":
            self.gs.destroy()
        elif self.engine == "superdex" and self.physics is not None:
            if self.robot is not None:
                self.robotics.destroy_bot(self.scene, self.robot)
            self.physics.shutdown()
        elif self.app is not None:
            self.app.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", required=True, choices=["mujoco", "genesis", "superdex", "isaacsim"])
    parser.add_argument("--headless", action="store_true")
    args = parser.parse_args()
    connection = socket.socket(fileno=int(os.environ["MANUAL_DEX_RPC_FD"]))
    stream = connection.makefile("rwb")
    backend = None

    def reply(value):
        stream.write((json.dumps(value, allow_nan=False) + "\n").encode())
        stream.flush()

    try:
        backend = Backend(args.engine, args.headless)
        reply({"event": "ready", "engine": args.engine, "positions": backend.positions()})
        while line := stream.readline(65537):
            if len(line) > 65536:
                raise ValueError("Oversized RPC request")
            request = json.loads(line)
            if request["op"] == "close":
                reply({"seq": request["seq"], "closed": True})
                break
            if request["op"] != "step":
                raise ValueError("Unknown operation")
            reply({"seq": request["seq"], "positions": backend.step(request["positions"], request["dt"])})
    except Exception as error:
        try:
            reply({"error": f"{type(error).__name__}: {error}"})
        except (BrokenPipeError, OSError):
            pass
        raise
    finally:
        stream.close()
        connection.close()
        if backend is not None:
            backend.close()


if __name__ == "__main__":
    main()
