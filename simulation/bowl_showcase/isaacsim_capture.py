"""Isaac Sim PhysX programmed grasp and release with native RTX/Replicator camera capture."""

from importlib.metadata import version
from common import Capture, DT, HALF, rgb, read_mesh
import numpy as np
from isaacsim import SimulationApp

c = Capture("isaacsim")
s = c.s
app = SimulationApp(
    dict(
        headless=True,
        width=s["width"],
        height=s["height"],
        renderer="RayTracedLighting",
        multi_gpu=False,
        extra_args=[
            "--/app/renderer/enabled=true",
            "--/exts/isaacsim.core.throttling/enable_async=false",
            "--/rtx/post/aa/op=4",
        ],
    )
)


def main():
    import omni.usd
    from pxr import UsdGeom, UsdPhysics, UsdLux, Gf, Vt
    from isaacsim.core.api import World
    from isaacsim.core.api.objects import DynamicCuboid, FixedCuboid
    import omni.replicator.core as rep

    omni.usd.get_context().new_stage()
    world = World(stage_units_in_meters=1.0, physics_dt=DT, rendering_dt=DT)
    stage = omni.usd.get_context().get_stage()

    def transform(prim, pos, q):
        xf = UsdGeom.Xformable(prim)
        xf.AddTranslateOp().Set(Gf.Vec3d(*pos))
        xf.AddOrientOp().Set(Gf.Quatf(float(q[0]), Gf.Vec3f(*q[1:])))

    for f in s["fixtures"]:
        path = "/World/" + f["name"]
        if f["type"] == "box":
            world.scene.add(
                FixedCuboid(
                    prim_path=path,
                    name=f["name"],
                    size=1.0,
                    scale=2 * np.array(f["size"]),
                    position=np.array(f["pos"]),
                    orientation=np.array(f["quat"]),
                )
            )
        else:
            floor = UsdGeom.Cylinder.Define(stage, path)
            floor.CreateRadiusAttr(f["size"][0])
            floor.CreateHeightAttr(2 * f["size"][1])
            floor.CreateAxisAttr("Z")
            transform(floor.GetPrim(), f["pos"], f["quat"])
            UsdPhysics.CollisionAPI.Apply(floor.GetPrim())
    obj = world.scene.add(
        DynamicCuboid(
            prim_path="/World/Brick",
            name="brick",
            size=1.0,
            scale=2 * np.array(HALF),
            mass=s["mass"],
            position=c.initial[:3],
            orientation=c.initial[3:],
        )
    )
    world.reset()
    from isaacsim.core.prims import RigidPrim

    force_view = RigidPrim("/World/Brick")
    force_view.initialize()

    def step(force):
        force_view.apply_forces(forces=force.reshape(1, 3), is_global=True)
        world.step(render=False)
        p, q = obj.get_world_pose()
        return np.r_[p, q]

    c.physics(step)
    print("Verified native PhysX lift and deposit", c.trace["peakWindowN"], flush=True)
    world.stop()
    omni.usd.get_context().new_stage()
    stage = omni.usd.get_context().get_stage()
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    groups = []
    for j in range(len(s["bodies"])):
        x = UsdGeom.Xform.Define(stage, "/World/B" + str(j))
        groups.append((x.AddTranslateOp(), x.AddOrientOp()))
    for x in s["surfaces"]:
        v, f = read_mesh(c.root / (x["name"] + ".obj"))
        mesh = UsdGeom.Mesh.Define(stage, "/World/B" + str(x["body"]) + "/" + x["name"])
        mesh.CreatePointsAttr(Vt.Vec3fArray.FromNumpy(v))
        mesh.CreateFaceVertexCountsAttr(
            Vt.IntArray.FromNumpy(np.full(len(f), 3, np.int32))
        )
        mesh.CreateFaceVertexIndicesAttr(Vt.IntArray.FromNumpy(f.ravel()))
        mesh.CreateSubdivisionSchemeAttr("none")
        mesh.CreateDisplayColorAttr([Gf.Vec3f(*(np.array(rgb(x["color"])) ** 2.2))])
    UsdLux.DomeLight.Define(stage, "/World/Sky").CreateIntensityAttr(420.0)
    key = UsdLux.DistantLight.Define(stage, "/World/Key")
    key.CreateIntensityAttr(950.0)
    UsdGeom.Xformable(key).AddRotateXYZOp().Set(Gf.Vec3f(26, -32, -22))
    cam = UsdGeom.Camera.Define(stage, "/World/Camera")
    xform = (
        Gf.Matrix4d()
        .SetLookAt(Gf.Vec3d(*s["eye"]), Gf.Vec3d(*s["target"]), Gf.Vec3d(0, 0, 1))
        .GetInverse()
    )
    UsdGeom.Xformable(cam).AddTransformOp().Set(xform)
    cam.CreateFocalLengthAttr(18.0)
    h = 36 * np.tan(np.deg2rad(s["fov"]) / 2)
    cam.CreateVerticalApertureAttr(h)
    cam.CreateHorizontalApertureAttr(h * s["width"] / s["height"])
    cam.CreateClippingRangeAttr(Gf.Vec2f(0.01, 20))
    prod = rep.create.render_product("/World/Camera", (s["width"], s["height"]))
    annot = rep.AnnotatorRegistry.get_annotator("rgb")
    annot.attach(prod)
    for i in c.draw:
        for (t, r), pose in zip(groups, c.frames[i]):
            t.Set(Gf.Vec3d(*pose[:3]))
            r.Set(Gf.Quatf(float(pose[3]), Gf.Vec3f(*pose[4:])))
        rep.orchestrator.step(delta_time=0.0, rt_subframes=3 if i == 0 else 1)
        c.save_frame(i, annot.get_data())
    c.finish(version("isaacsim"), "Isaac Sim RTX / Replicator")


try:
    main()
except BaseException:
    import traceback, sys

    traceback.print_exc()
    sys.stderr.flush()
    app.close(exit_code=1)
    raise
else:
    app.close()
