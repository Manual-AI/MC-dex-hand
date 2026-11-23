"""Alloy rigid simulation followed by the Alloy path-traced camera reading native mesh instances."""

from importlib.metadata import version
from types import SimpleNamespace
import numpy as np
import warp as wp
import alloy
from alloy.camera.scene import SceneData, MeshGeom, IDENTITY_XF
from common import Capture, DT, HALF, rgb, read_mesh


def main():
    c = Capture("alloy")
    s = c.s
    scene = alloy.Scene(dt=DT)
    for f in s["fixtures"]:
        kw = dict(
            pos=f["pos"],
            quat_wxyz=f["quat"],
            static=True,
            friction=0.65,
            restitution=0.0,
        )
        if f["type"] == "box":
            scene.add_box(f["name"], half_extents=f["size"], **kw)
        else:
            scene.add_cylinder(f["name"], f["size"][0], 2 * f["size"][1], **kw)
    scene.add_box(
        "brick",
        half_extents=HALF,
        pos=c.initial[:3],
        quat_wxyz=c.initial[3:],
        mass=s["mass"],
        friction=0.65,
        restitution=0.0,
        rigid=True,
    )
    sim = alloy.build(scene, device="cuda:0")

    def step(force):
        sim.apply_wrench("brick", force=force)
        sim.step(1)
        state = sim.state(names=["brick"], world=0)
        return np.r_[state["brick.pos"], state["brick.quat_wxyz"]]

    c.physics(step)
    meshes = []
    parts = s["surfaces"]
    n = len(parts)
    for x in parts:
        v, f = read_mesh(c.root / (x["name"] + ".obj"))
        meshes.append(MeshGeom(x["name"], v, f))
    data = SceneData(
        meshes,
        np.arange(n),
        np.zeros(n, np.int32),
        [x["body"] for x in parts],
        np.tile(IDENTITY_XF, (n, 1)),
        np.array([rgb(x["color"]) for x in parts]) ** 2.2,
    )
    cam = alloy.Camera(
        "bowl",
        look_at=(s["eye"], s["target"]),
        width=s["width"],
        height=s["height"],
        fov=s["fov"],
        spp=12,
    )
    with wp.ScopedDevice("cuda:0"):
        body = wp.empty(len(s["bodies"]), dtype=wp.transform, device="cuda:0")
        state = SimpleNamespace(body_q=body)
        for i in c.draw:
            body.assign(c.frames[i][:, [0, 1, 2, 4, 5, 6, 3]].astype(np.float32))
            frame = cam.render(data, state)
            pixels = frame.numpy() if hasattr(frame, "numpy") else np.asarray(frame)
            c.save_frame(i, pixels[0] if pixels.ndim == 4 else pixels)
    c.finish(version("alloy-engine"), "Alloy path-traced camera")


if __name__ == "__main__":
    main()
