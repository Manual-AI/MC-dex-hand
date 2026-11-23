"""Build native render meshes in link frames from the browser's MJCF and CAD palette."""

import json
import tarfile
from pathlib import Path
import numpy as np
import trimesh
import mujoco

SRC = Path(__file__).resolve().parent
BROWSER = SRC.parent / "browser"
OUT = Path("build/bowl-showcase")


def main():
    out = OUT / "scene"
    out.mkdir(parents=True, exist_ok=True)
    work = OUT / "mjcf"
    work.mkdir(exist_ok=True)
    with tarfile.open(BROWSER / "assets/meshes.tar.gz") as archive:
        archive.extractall(work, filter="data")
    item = next(
        x
        for x in json.loads((BROWSER / "bowl/objects.json").read_text())
        if x["id"] == "building-brick"
    )
    xml = (
        (BROWSER / "bowl/scene.xml")
        .read_text()
        .replace("<!--OBJECT_GEOMETRY-->", "\n".join(item["geoms"]))
    )
    (work / "scene.xml").write_text(xml)
    m = mujoco.MjModel.from_xml_path(str(work / "scene.xml"))
    d = mujoco.MjData(m)
    a = json.loads((BROWSER / "assets/appearance.json").read_text())
    rows = json.loads((OUT / "reference.json").read_text())
    frames = []
    release = next(i for i, r in enumerate(rows) if r["carried"] and not r["hand"])
    bodies = [m.body(i).name for i in range(m.nbody)]
    for row in rows:
        d.qpos[:] = row["q"]
        mujoco.mj_forward(m, d)
        frames.append(np.column_stack((d.xpos, d.xquat)).round(9).tolist())
    assets = {}
    fixtures = []
    for g in range(m.ngeom):
        if m.geom_group[g] == 3:
            continue
        geom = m.geom(g)
        name, body = geom.name, int(m.geom_bodyid[g])
        color = "#" + "".join(
            f"{v:02x}" for v in (m.geom_rgba[g, :3] * 255).round().astype(int)
        )
        if m.geom_type[g] == mujoco.mjtGeom.mjGEOM_MESH:
            meshid = m.geom_dataid[g]
            f, v = m.mesh_faceadr[meshid], m.mesh_vertadr[meshid]
            mesh = trimesh.Trimesh(
                m.mesh_vert[v : v + m.mesh_vertnum[meshid]],
                m.mesh_face[f : f + m.mesh_facenum[meshid]],
                process=False,
            )
        elif m.geom_type[g] == mujoco.mjtGeom.mjGEOM_BOX:
            mesh = trimesh.creation.box(extents=2 * m.geom_size[g])
        elif m.geom_type[g] == mujoco.mjtGeom.mjGEOM_CYLINDER:
            mesh = trimesh.creation.cylinder(
                radius=m.geom_size[g, 0], height=2 * m.geom_size[g, 1], sections=32
            )
        else:
            raise ValueError(name)
        colors = np.full(len(mesh.faces), color, dtype="U7")
        for material, ranges in a["faces"].get(name, {}).items():
            for start, n in ranges:
                colors[start : start + n] = a["palette"][material]
                if material == "quest_shell":
                    centers = mesh.triangles_center[start : start + n]
                    plane = a["questFacePlane"]
                    colors[start : start + n][centers @ plane[:3] + plane[3] > 0] = a[
                        "palette"
                    ]["quest_face"]
        mat = trimesh.transformations.quaternion_matrix(m.geom_quat[g])
        mat[:3, 3] = m.geom_pos[g]
        mesh.apply_transform(mat)
        if name.startswith("bowl_") or name == "bench":
            fixtures.append(
                dict(
                    name=name,
                    type="box" if m.geom_type[g] == 6 else "cylinder",
                    pos=m.geom_pos[g].tolist(),
                    quat=m.geom_quat[g].tolist(),
                    size=m.geom_size[g].tolist(),
                )
            )
        for c in np.unique(colors):
            part = mesh.submesh(
                [np.flatnonzero(colors == c)], append=True, repair=False
            )
            assets.setdefault((body, str(c)), []).append(part)
    surfaces = []
    for n, ((body, color), parts) in enumerate(assets.items()):
        mesh = trimesh.util.concatenate(parts)
        name = f"surface_{n:03}"
        mesh.export(out / (name + ".obj"))
        surfaces.append(dict(name=name, body=body, color=color))
    brick = int(m.body("object").id)
    wrist = bodies.index("openarm_link7")
    grip = 96
    pose = np.array(frames[grip][wrist])
    basis = trimesh.transformations.quaternion_matrix(pose[3:])[:3, :3]
    grasp_point = basis.T @ (np.array(frames[grip][brick][:3]) - pose[:3])
    # The engine adapters receive a single initial object state. All later object poses come from their own solver.
    for frame in frames[1:]:
        frame[brick] = frames[0][brick]
    spec = dict(
        bodies=bodies,
        object=brick,
        surfaces=surfaces,
        fixtures=fixtures,
        frames=frames,
        mass=float(m.body_mass[brick]),
        grip=grip,
        wrist=wrist,
        graspPoint=grasp_point.tolist(),
        release=release,
        rate=24,
        frameStride=2,
        eye=[1.02, -0.72, 0.57],
        target=[0.33, -0.01, 0.175],
        fov=45,
        width=640,
        height=432,
        source="MC-Dex bowl scene, programmed building-brick pickup, seed 3200017",
    )
    (out / "scene.json").write_text(json.dumps(spec, separators=(",", ":")))
    print(
        len(surfaces),
        "surfaces,",
        len(frames),
        "poses;",
        spec["mass"],
        "kg, release tick",
        release,
    )


if __name__ == "__main__":
    main()
