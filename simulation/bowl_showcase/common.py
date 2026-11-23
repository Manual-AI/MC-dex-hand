"""Shared inputs, camera and capture checks. Simulation and pixel generation live in each engine adapter."""

import argparse
import hashlib
import json
import time
from pathlib import Path
import numpy as np
from PIL import Image

DT = 1 / 240
HALF = [0.023460, 0.017940, 0.013800]


def rgb(hex_color):
    return tuple(int(hex_color[i : i + 2], 16) / 255 for i in (1, 3, 5))


def xyzw(q):
    return [*q[1:], q[0]]


def from_xyzw(q):
    return [q[3], *q[:3]]


def read_mesh(path):
    verts, faces = [], []
    for line in path.read_text().splitlines():
        if line.startswith("v "):
            verts.append([float(v) for v in line.split()[1:4]])
        elif line.startswith("f "):
            faces.append([int(v.split("/")[0]) - 1 for v in line.split()[1:]])
    return np.array(verts, np.float32), np.array(faces, np.int32)


class Capture:
    def __init__(self, engine):
        p = argparse.ArgumentParser()
        p.add_argument("--scene", type=Path, default=Path("build/bowl-showcase/scene"))
        p.add_argument(
            "--out", type=Path, default=Path("build/bowl-showcase/captures") / engine
        )
        p.add_argument(
            "--smoke",
            action="store_true",
            help="Render three frames into a separate directory",
        )
        args = p.parse_args()
        self.root = args.scene.resolve()
        self.out = args.out.resolve()
        self.smoke = args.smoke
        if self.smoke:
            self.out = self.out / "smoke"
        self.out.mkdir(exist_ok=True, parents=True)
        self.engine = engine
        self.s = json.loads((self.root / "scene.json").read_text())
        self.release = self.s["release"]
        self.obj = self.s["object"]
        self.frames = np.array(self.s["frames"], dtype=np.float64)
        self.initial = self.frames[0, self.obj].copy()
        self.ticks = (len(self.frames) - 1) * 10
        self.draw = (0, 144, 252) if self.smoke else range(0, len(self.frames), 2)
        self.start = time.monotonic()

    def physics(self, step):
        def rotation(q):
            w, x, y, z = q
            return np.array(
                [
                    [1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
                    [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
                    [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)],
                ]
            )

        poses = [self.initial.copy()]
        wrist = self.frames[:, self.s["wrist"]]
        rot = np.array([rotation(p[3:]) for p in wrist])
        grip = self.s["grip"]
        mass = self.s["mass"]
        spring = []
        local = None
        goal = None
        for k in range(self.ticks):
            i, sub = divmod(k, 10)
            force = np.zeros(3)
            pos = poses[-1][:3]
            if k == grip * 10:
                local = rot[i].T @ (pos - wrist[i, :3])
                if np.linalg.norm(local - self.s["graspPoint"]) > 0.04:
                    raise ValueError("Object outside the programmed grasp aperture")
            if grip <= i < self.release:
                frac = (sub + 1) / 10
                target = (1 - frac) * (wrist[i, :3] + rot[i] @ local) + frac * (
                    wrist[i + 1, :3] + rot[i + 1] @ local
                )
                desired_vel = (target - goal) / DT if goal is not None else np.zeros(3)
                vel = (pos - poses[-2][:3]) / DT
                force = (
                    45 * (target - pos)
                    + 1.7 * (desired_vel - vel)
                    + [0, 0, mass * 9.81]
                )
                force *= min(1.0, 2.0 / max(1e-12, np.linalg.norm(force)))
                goal = target
            spring.append(force.tolist())
            poses.append(np.asarray(step(force), dtype=float))
        path = np.array(poses)
        if path.shape != (self.ticks + 1, 7) or not np.isfinite(path).all():
            raise ValueError("Invalid solver sample")
        self.frames[:, self.obj] = path[::10]
        z = path[:, 2]
        vz = np.gradient(z, DT)
        vz[0] = 0.0
        ids = np.arange(0, len(vz), 10)
        f = mass * (9.81 + np.diff(vz[ids]) / (10 * DT))
        landing = f[self.release : self.release + 24]
        self.trace = dict(
            dt=DT,
            massKg=mass,
            gripTick=grip,
            releaseTick=self.release,
            poses=path.tolist(),
            graspForceN=spring,
            forceWindowSeconds=10 * DT,
            verticalForceN=f.tolist(),
            peakWindowN=float(landing.max()),
            maxGraspN=float(np.linalg.norm(spring, axis=1).max()),
            liftHeightM=float(z[grip * 10 : self.release * 10].max() - z[grip * 10]),
            settledMeanN=float(f[-12:].mean()),
            finalCenter=path[-1, :3].tolist(),
        )
        if (
            self.trace["liftHeightM"] < 0.045
            or np.linalg.norm(path[-1, :2] - [0.451, 0.12]) > 0.063
            or not 0.104 < path[-1, 2] < 0.155
        ):
            raise ValueError(
                f"Programmed lift or deposit failed: lift={self.trace['liftHeightM']} end={path[-1, :3]}"
            )

    def save_frame(self, i, pixels):
        a = np.asarray(pixels)
        if (
            a.dtype != np.uint8
            or a.shape[:2] != (self.s["height"], self.s["width"])
            or a.std() < 3
        ):
            raise ValueError(f"Invalid native frame {i}: {a.shape} {a.dtype}")
        Image.fromarray(np.ascontiguousarray(a[:, :, :3])).save(
            self.out / f"{i:04}.jpg", quality=93
        )

    def finish(self, version, renderer):
        assert all((self.out / f"{i:04}.jpg").exists() for i in self.draw)
        if len(
            {
                hashlib.sha256((self.out / f"{i:04}.jpg").read_bytes()).digest()
                for i in self.draw
            }
        ) < min(10, len(self.draw)):
            raise ValueError("Native camera repeated its frames")
        out = dict(
            engine=self.engine,
            version=str(version),
            renderer=renderer,
            frames=list(self.draw),
            seconds=time.monotonic() - self.start,
            sceneSha256=hashlib.sha256(
                (self.root / "scene.json").read_bytes()
            ).hexdigest(),
            **self.trace,
        )
        (self.out / "capture.json").write_text(json.dumps(out, separators=(",", ":")))
        print(
            self.engine,
            renderer,
            len(self.draw),
            "frames,",
            self.trace["peakWindowN"],
            "N peak",
            flush=True,
        )
