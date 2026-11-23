"""Newton SolverSteel contact integration and Newton's native headless OpenGL viewer."""

from importlib.metadata import version
import numpy as np
import warp as wp
import pyglet

pyglet.options["headless"] = True
import newton
from newton.solvers import SolverSteel
from newton.viewer import ViewerGL
from common import Capture, DT, HALF, rgb, xyzw, from_xyzw, read_mesh


def xf(p, q):
    return wp.transform(wp.vec3(*p), wp.quat(*xyzw(q)))


def main():
    c = Capture("steel")
    s = c.s
    wp.set_device("cuda:0")
    b = newton.ModelBuilder()
    cfg = newton.ModelBuilder.ShapeConfig(mu=0.65, restitution=0.0)
    for f in s["fixtures"]:
        kw = dict(xform=xf(f["pos"], f["quat"]), cfg=cfg)
        if f["type"] == "box":
            b.add_shape_box(-1, hx=f["size"][0], hy=f["size"][1], hz=f["size"][2], **kw)
        else:
            b.add_shape_cylinder(
                -1, radius=f["size"][0], half_height=f["size"][1], **kw
            )
    body = b.add_body(xform=xf(c.initial[:3], c.initial[3:]), label="brick")
    brickcfg = newton.ModelBuilder.ShapeConfig(
        density=float(s["mass"] / np.prod(2 * np.array(HALF))), mu=0.65, restitution=0.0
    )
    b.add_shape_box(body, hx=HALF[0], hy=HALF[1], hz=HALF[2], cfg=brickcfg)
    m = b.finalize()
    solver = SolverSteel(m)
    state = m.state()
    next_state = m.state()
    control = m.control()
    contacts = m.contacts()

    def step(force):
        nonlocal state, next_state
        state.clear_forces()
        state.body_f.assign(np.array([[*force, 0, 0, 0]], np.float32))
        m.collide(state, contacts)
        solver.step(state, next_state, control, contacts, DT)
        state, next_state = next_state, state
        v = state.body_q.numpy()[body]
        return [*v[:3], *from_xyzw(v[3:])]

    c.physics(step)
    b = newton.ModelBuilder()
    for j, p in enumerate(c.frames[0]):
        b.add_body(xform=xf(p[:3], p[3:]), is_kinematic=True, label="link" + str(j))
    cfg = newton.ModelBuilder.ShapeConfig(
        has_shape_collision=False, has_particle_collision=False, density=0.0
    )
    for x in s["surfaces"]:
        v, f = read_mesh(c.root / (x["name"] + ".obj"))
        b.add_shape_mesh(
            x["body"],
            mesh=newton.Mesh(v, f.ravel(), compute_inertia=False),
            cfg=cfg,
            color=rgb(x["color"]),
            label=x["name"],
        )
    model = b.finalize()
    display = model.state()
    view = ViewerGL(width=s["width"], height=s["height"], headless=True, vsync=False)
    try:
        view.set_model(model)
        view.show_ui = False
        view.set_camera(wp.vec3(*s["eye"]))
        view.camera.look_at(s["target"])
        view.camera.fov = s["fov"]
        for i in c.draw:
            display.body_q.assign(
                c.frames[i][:, [0, 1, 2, 4, 5, 6, 3]].astype(np.float32)
            )
            view.begin_frame(i / 24)
            view.log_state(display)
            view.end_frame()
            c.save_frame(i, view.get_frame().numpy())
        c.finish(version("newton"), "Newton ViewerGL / SolverSteel")
    finally:
        view.close()


if __name__ == "__main__":
    main()
