"""Genesis rigid solver and rasterizer. Visual entities replay the programmed link transforms."""

import os

os.environ.setdefault("PYOPENGL_PLATFORM", "egl")
import genesis as gs
import numpy as np
from common import Capture, DT, HALF, rgb


def main():
    c = Capture("genesis")
    s = c.s
    gs.init(backend=gs.cpu, logging_level="warning")

    def scene():
        return gs.Scene(
            sim_options=gs.options.SimOptions(dt=DT),
            show_viewer=False,
            vis_options=gs.options.VisOptions(
                ambient_light=(0.52, 0.52, 0.52), background_color=(0.85, 0.88, 0.87)
            ),
        )

    dynamics = scene()
    for f in s["fixtures"]:
        props = dict(pos=tuple(f["pos"]), quat=tuple(f["quat"]), fixed=True)
        morph = (
            gs.morphs.Box(size=tuple(2 * np.array(f["size"])), **props)
            if f["type"] == "box"
            else gs.morphs.Cylinder(
                radius=f["size"][0], height=2 * f["size"][1], **props
            )
        )
        dynamics.add_entity(morph, material=gs.materials.Rigid(friction=0.65))
    obj = dynamics.add_entity(
        gs.morphs.Box(
            pos=tuple(c.initial[:3]),
            quat=tuple(c.initial[3:]),
            size=tuple(2 * np.array(HALF)),
        ),
        material=gs.materials.Rigid(
            rho=s["mass"] / np.prod(2 * np.array(HALF)), friction=0.65
        ),
    )
    dynamics.build()

    def step(force):
        obj.control_dofs_force(force, dofs_idx_local=[0, 1, 2])
        dynamics.step()
        return np.r_[obj.get_pos().cpu().numpy(), obj.get_quat().cpu().numpy()]

    c.physics(step)
    visual = scene()
    parts = []
    for x in s["surfaces"]:
        parts.append(
            visual.add_entity(
                gs.morphs.Mesh(
                    file=str(c.root / (x["name"] + ".obj")),
                    fixed=False,
                    collision=False,
                    decimate=False,
                    convexify=False,
                ),
                surface=gs.surfaces.Default(color=rgb(x["color"]), smooth=False),
            )
        )
    camera = visual.add_camera(
        res=(s["width"], s["height"]),
        pos=tuple(s["eye"]),
        lookat=tuple(s["target"]),
        fov=s["fov"],
        GUI=False,
    )
    visual.build()
    for i in c.draw:
        visual.step()
        for x, p in zip(s["surfaces"], parts):
            pose = c.frames[i, x["body"]]
            p.set_pos(pose[:3])
            p.set_quat(pose[3:])
        img, *_ = camera.render(rgb=True)
        c.save_frame(i, img)
    c.finish(gs.__version__, "Genesis rasterizer")
    gs.destroy()


if __name__ == "__main__":
    main()
