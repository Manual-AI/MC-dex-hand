"""Offline checks for scene/control contracts and genuine native capture publishing."""
import ast
import json
import math
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import native_common as nc


class NativeContracts(unittest.TestCase):
    def test_trajectory_and_timing(self):
        self.assertEqual(nc.STEPS, 1200)
        self.assertEqual(nc.STRIDE, 12)
        self.assertEqual(len(nc.JOINTS), 15)
        samples = [nc.targets(step*nc.DT) for step in range(nc.STEPS)]
        for name in nc.JOINTS:
            values = [s[name] for s in samples]
            self.assertTrue(all(math.isfinite(v) for v in values))
            self.assertGreater(max(values)-min(values), .1)
            self.assertAlmostEqual(nc.targets(0)[name], nc.targets(5)[name])

    def test_no_cross_engine_renderer(self):
        for engine in ("genesis", "superdex", "isaacsim"):
            source = (nc.ROOT / "simulation" / engine / "native.py").read_text()
            modules = []
            for node in ast.walk(ast.parse(source)):
                if isinstance(node, ast.Import):
                    modules.extend(a.name for a in node.names)
                elif isinstance(node, ast.ImportFrom):
                    modules.append(node.module or "")
            self.assertFalse(any(m.startswith("mujoco") for m in modules), engine)
        publisher = (nc.ROOT / "simulation/comparison.py").read_text()
        self.assertNotIn("import mujoco", publisher)
        self.assertNotIn("mj_forward", publisher)

    def test_table_and_initial_cube_geometry(self):
        table = nc.SPEC["table"]
        self.assertAlmostEqual(table["center"][2]+table["size"][2]/2, 0)
        self.assertGreater(nc.SPEC["cube"]["center"][2], .2)
        self.assertEqual(nc.SPEC["gravity_m_s2"], [0, 0, -9.81])
        self.assertEqual(len(list(nc.boxes())), 5)

    def test_evidence_rejects_missing_motion_contact_or_frames(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(nc, "NATIVE", Path(tmp)):
            with patch.dict(os.environ, {"MANUAL_DEX_RUN_ID": "test"}):
                evidence = nc.Evidence("test", "test renderer")
            with self.assertRaises(RuntimeError):
                evidence.finish("test")
            for i in range(nc.STEPS):
                z = .27 if i < 60 else .03
                evidence.record(i, nc.targets(i*nc.DT), [0, 0, z], i >= 60)
            evidence.frames = 100
            evidence.contact_steps = 0
            with self.assertRaisesRegex(RuntimeError, "contact"):
                evidence.finish("test")
            evidence.contact_steps = 1140
            for s in evidence.states:
                s["joints"][nc.JOINTS[0]] = 0
            with self.assertRaisesRegex(RuntimeError, "did not move"):
                evidence.finish("test")
            self.assertFalse((Path(tmp) / "test.json").exists())

    def test_all_published_gifs_meet_byte_and_duration_budgets(self):
        from PIL import Image
        budget = json.loads((nc.ROOT / "docs/assets/gif-size-budget.json").read_text())
        for relative, info in budget["assets"].items():
            path = nc.ROOT / "docs/assets" / relative
            self.assertLessEqual(path.stat().st_size, info["bytes"]*.5, relative)
            with Image.open(path) as gif:
                duration = 0
                for i in range(gif.n_frames):
                    gif.seek(i)
                    duration += gif.info["duration"]
                self.assertEqual(duration, info["duration_ms"], relative)

    def test_compressed_component_register_does_not_flicker(self):
        from PIL import Image, ImageChops
        with Image.open(nc.ROOT / "docs/assets/manual-dex-paired-kinematics.gif") as gif:
            # The original fixed right-hand register begins at x=1440/2000.
            # Leave a margin clear of resampling at the moving-panel boundary.
            box = (round(gif.width*.735), 0, gif.width, gif.height)
            first = gif.convert("RGB").crop(box)
            for i in range(gif.n_frames):
                gif.seek(i)
                self.assertIsNone(ImageChops.difference(first, gif.convert("RGB").crop(box)).getbbox(), i)


if __name__ == "__main__":
    unittest.main()
