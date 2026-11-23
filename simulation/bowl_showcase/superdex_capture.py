"""SuperDex rigid contacts and the bundled Polyscope EGL viewer."""

from importlib.metadata import version
import numpy as np
import trimesh
import superdex.physics as ph
from superdex.physics.viewer import Viewer, ViewerCfg
from superdex.physics.viewer.backend import polyscope as ps
from superdex.physics.utils import render_model_registry as registry
from common import Capture, DT, HALF, rgb, xyzw, from_xyzw, read_mesh


def main():
    c = Capture("superdex")
    s = c.s
    ph.initialize(num_worker_threads=3)
    dtype = np.float64 if ph.uses_double_precision() else np.float32

    def pose(p):
        return ph.TransformRT(ph.Quaternion(*xyzw(p[3:])), ph.Real3(*p[:3]))

    def shape(mesh):
        return ph.create_tri_mesh_shape(
            np.asarray(mesh.vertices, dtype=dtype).ravel(),
            np.asarray(mesh.faces, np.int32).ravel(),
        )

    dyn = ph.create_scene("Bowl release")
    dyn.set_gravity([0, 0, -9.81])
    dyn.enable_layer_contact_symmetric("Brick", "Bowl", True)
    contact = ph.ContactParams()
    contact.coulomb_friction_coefficient = 0.65
    for f in s["fixtures"]:
        box = f["type"] == "box"
        mesh = (
            trimesh.creation.box(extents=2 * np.array(f["size"]))
            if box
            else trimesh.creation.cylinder(
                radius=f["size"][0], height=2 * f["size"][1], sections=48
            )
        )
        dyn.create_rigid_actor(
            name=f["name"],
            layer="Bowl",
            shape=shape(mesh),
            is_static=True,
            contact=contact,
            world_from_local=pose(f["pos"] + f["quat"]),
            collider_type=ph.ColliderType.BOX if box else ph.ColliderType.MESH,
        )
    brick = dyn.create_rigid_actor(
        name="brick",
        layer="Brick",
        shape=shape(trimesh.creation.box(extents=2 * np.array(HALF))),
        world_from_local=pose(c.initial),
        is_static=False,
        mass=s["mass"],
        contact=contact,
        collider_type=ph.ColliderType.BOX,
    )

    def step(force):
        brick.set_external_forces_on_dofs(
            np.arange(3, dtype=np.int32), np.asarray(force, dtype=dtype)
        )
        dyn.step(DT)
        p = brick.get_root_transform()
        return [*p.translation, *from_xyzw(list(p.rotation))]

    c.physics(step)
    visual = ph.create_scene("OpenArm MC-Dex")
    visual.set_gravity([0, 0, 0])
    actors = {}
    colors = {}
    proxy = shape(trimesh.creation.box(extents=(0.001,) * 3))
    for x in s["surfaces"]:
        n = x["name"]
        actor = visual.create_rigid_actor(
            name=n,
            shape=proxy,
            layer="Display",
            is_static=True,
            collider_type=ph.ColliderType.NONE,
            world_from_local=pose(c.frames[0, x["body"]]),
        )
        v, f = read_mesh(c.root / (n + ".obj"))
        mesh = trimesh.Trimesh(v, f, process=False)
        mesh.apply_transform(
            trimesh.transformations.rotation_matrix(-np.pi / 2, [1, 0, 0])
        )
        dest = c.out / (n + ".glb")
        mesh.export(dest)
        registry.register(
            visual,
            actor.get_handle(),
            str(dest),
            ph.TRANSFORM_RT_IDENTITY,
            ph.Real3(1, 1, 1),
        )
        actors[n] = actor
        colors[n] = rgb(x["color"])
    viewer = Viewer(
        ViewerCfg(
            backend="openGL3_egl",
            offscreen=True,
            size=(s["width"], s["height"]),
            coordinate_system="ros",
        )
    )
    try:
        viewer.set_scene(visual)
        viewer.set_paused(False)
        viewer.set_enable_follow_camera(False)
        viewer.set_compute_automatic_distance(False)
        viewer.set_camera_view(s["eye"], s["target"], [0, 0, 1])
        ps.set_view_projection_mode("perspective")
        ps.set_vertical_fov_degrees(s["fov"])
        ps.set_background_color((0.84, 0.87, 0.86))
        for renderer in viewer.get_actor_renderers():
            renderer.set_enable_edges(False)
            renderer.set_enable_axes(False)
            renderer.set_front_face_color(
                colors[renderer.get_actor().get_name().rsplit("/", 1)[-1]]
            )
        for i in c.draw:
            for x in s["surfaces"]:
                actors[x["name"]].set_root_transform(pose(c.frames[i, x["body"]]))
            viewer.render()
            c.save_frame(i, viewer.take_screenshot()[:, :, :3])
        c.finish(version("superdex"), "SuperDex SDK / Polyscope EGL")
    finally:
        viewer.close()
        ph.shutdown()


if __name__ == "__main__":
    main()
