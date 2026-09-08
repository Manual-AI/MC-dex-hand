"""Check the versioned MuJoCo models and, optionally, the paired animation."""
import argparse
import json
import xml.etree.ElementTree as ET

import mujoco
import numpy as np
from PIL import Image

from render import (MODELS, OUT, FPS, FRAMES, SECONDS, WIDTH, HEIGHT, REGISTER_X,
                    ROTATION, world, pose_at, orbit_azimuth)


def check_model(kind, expected_parts):
    directory = MODELS / kind
    parts = json.loads((directory / "parts.json").read_text())
    joints = json.loads((directory / "joints.json").read_text())
    model = mujoco.MjModel.from_xml_path(str(directory / "scene.xml"))
    data = mujoco.MjData(model)
    assert len(parts) == model.ngeom == expected_parts
    assert len(joints) == model.njnt == model.nq == 8
    assert not np.any(model.geom_contype) and not np.any(model.geom_conaffinity)
    assert not np.any(model.opt.gravity)
    tree = ET.parse(directory / "scene.xml")
    files = {mesh.attrib["file"] for mesh in tree.findall("asset/mesh")}
    assert files == {p.name for p in (directory / "meshes").glob("*.stl")}
    assert len(files) == expected_parts

    # The CAD reference pose must preserve every occurrence's assembled placement.
    mujoco.mj_forward(model, data)
    for part in parts:
        assert (directory / part["mesh"]).is_file()
        np.testing.assert_allclose(data.site(f"label_{part['index']}").xpos,
                                   world(part["center"]), atol=1e-8, rtol=0)
    for name, joint in joints.items():
        body_id = model.body(name).id
        assert model.body_parentid[body_id] == model.body(joint["parent"]).id
        np.testing.assert_allclose(model.joint(name).axis, ROTATION @ joint["axis"], atol=1e-8)

    # Joint motion closes at both the five-second flexion cycle and ten-second GIF seam.
    pose_at(data, 0)
    start = data.qpos.copy()
    for t in (5, 10):
        pose_at(data, t)
        np.testing.assert_allclose(data.qpos, start, atol=1e-14)
    pose_at(data, 2.5)
    assert np.all(np.abs(data.qpos - start) > .2), "Every joint should visibly flex"
    mujoco.mj_forward(model, data)
    fixed = [p for p in parts if p["body"] == "frame"]
    for part in fixed:
        np.testing.assert_allclose(data.site(f"label_{part['index']}").xpos,
                                   world(part["center"]), atol=1e-8, rtol=0)
    print(f"{kind}: {expected_parts} meshes loaded; eight joints; CAD placements, hierarchy and periodic motion verified")


def check_animation():
    with Image.open(OUT / "manual-dex-paired-kinematics.gif") as gif:
        assert gif.size == (WIDTH, HEIGHT)
        assert gif.n_frames == FRAMES and gif.info["loop"] == 0
        duration = 0
        legend = None
        for i in range(gif.n_frames):
            gif.seek(i)
            assert gif.info["duration"] == 1000 // FPS
            duration += gif.info["duration"]
            pixels = gif.convert("RGB")
            register = pixels.crop((REGISTER_X, 128, WIDTH, 974)).tobytes()
            if legend is None:
                legend = register
            assert register == legend, f"Register changed in frame {i}"
            # Both views must contain geometry, not an accidentally blank panel.
            for x in (0, 700):
                panel = np.asarray(pixels.crop((x, 150, x + 700, 950)))
                assert np.count_nonzero(panel.mean(axis=2) < 220) > 20000
                edges = np.concatenate((panel[0], panel[-1], panel[:, 0], panel[:, -1]))
                assert not np.any(edges.mean(axis=1) < 245), f"Viewport clipping in frame {i}"
        assert duration == SECONDS * 1000
    assert orbit_azimuth(1) - orbit_azimuth(0) == 36
    assert orbit_azimuth(SECONDS) - orbit_azimuth(0) == 360
    print(f"Animation: {FRAMES} frames, {duration} ms, both devices visible, constant register, half-speed full orbit")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--animation", action="store_true", help="Also check the decoded GIF")
    args = parser.parse_args()
    check_model("glove", 86)
    check_model("hand", 178)
    if args.animation:
        check_animation()
