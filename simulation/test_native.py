"""Offline checks for scene/control contracts and genuine native capture publishing."""
import ast
import copy
import importlib.util
import json
import math
import os
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET
from unittest.mock import patch

import native_common as nc


class NativeContracts(unittest.TestCase):
    def test_mujoco_shadow_map_is_focused_without_changing_physics(self):
        spec = importlib.util.spec_from_file_location("manual_dex_mujoco_native", nc.ROOT / "simulation/mujoco/native.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        tree = ET.fromstring('<mujoco><statistic meaninertia="3"/><option timestep="0.0041666666667"/>'
                             '<worldbody><geom type="plane" size="100 100 .1"/></worldbody></mujoco>')
        before = [ET.tostring(tree.find(tag)) for tag in ("option", "worldbody")]
        module.configure_visuals(tree)
        module.configure_visuals(tree)
        self.assertEqual(before, [ET.tostring(tree.find(tag)) for tag in ("option", "worldbody")])
        self.assertEqual(len(tree.findall("statistic")), 1)
        self.assertEqual(tree.find("statistic").get("meaninertia"), "3")
        self.assertEqual(len(tree.findall("visual/quality")), 1)
        quality = tree.find("visual/quality")
        self.assertEqual(int(quality.get("shadowsize")), 8192)
        self.assertEqual(int(quality.get("offsamples")), 8)
        width = 2*float(tree.find("statistic").get("extent"))*float(tree.find("visual/map").get("shadowclip"))
        self.assertLess(width/int(quality.get("shadowsize")), .0004)

    def test_trajectory_and_timing(self):
        self.assertEqual(nc.STEPS, 1200)
        self.assertEqual(nc.STRIDE, 12)
        self.assertEqual(len(nc.JOINTS), 15)
        samples = [nc.targets(step*nc.DT) for step in range(nc.STEPS)]
        for name in nc.JOINTS:
            values = [s[name] for s in samples]
            self.assertTrue(all(math.isfinite(v) for v in values))
        self.assertGreater(max(s["md_middle_distal"] for s in samples), .8)
        self.assertEqual(nc.targets(-1), nc.targets(0))
        self.assertEqual(nc.targets(6), nc.targets(5))
        self.assertEqual(nc.phase(1.5), "close")
        self.assertEqual(nc.phase(2.6), "transport")
        self.assertEqual(nc.phase(4.1), "release")
        for point in nc.POLICY["waypoints"]:
            self.assertEqual(len(point["q_rad"]), 15)
            for n, q in zip(nc.JOINTS, point["q_rad"]):
                self.assertAlmostEqual(nc.targets(point["t_s"])[n], q)

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
        self.assertLess(abs(nc.SPEC["cube"]["center"][2]-nc.SPEC["cube"]["size"][2]/2), .001)
        self.assertEqual(nc.SPEC["gravity_m_s2"], [0, 0, -9.81])
        self.assertEqual(len(list(nc.boxes())), 13)

    def test_evidence_rejects_missing_motion_contact_or_frames(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(nc, "NATIVE", Path(tmp)):
            with patch.dict(os.environ, {"MANUAL_DEX_RUN_ID": "test"}):
                evidence = nc.Evidence("test", "test renderer")
            with self.assertRaises(RuntimeError):
                evidence.finish("test")
            for i in range(nc.STEPS):
                z = .27 if i < 60 else .03
                evidence.record(i, nc.targets(i*nc.DT), [0, 0, z], {"table": .8} if i >= 60 else {})
            evidence.frames = 100
            evidence.contact_steps = 0
            with self.assertRaisesRegex(RuntimeError, "start at rest"):
                evidence.finish("test")
            evidence.contact_steps = 1140
            for s in evidence.states:
                for name in nc.JOINTS:
                    s["joints"][name] = 0
            with self.assertRaisesRegex(RuntimeError, "did not move"):
                evidence.finish("test")
            self.assertFalse((Path(tmp) / "test.json").exists())

    def pick_place_fixture(self):
        samples = []
        for step in range(nc.STEPS):
            t = (step+1)*nc.DT
            u = min(1., max(0., (t-2.4)/.85))
            z = .025 + .12*min(1., max(0., (t-1.8)/.6), max(0., (3.9-t)/.65))
            contacts = ({"md_middle_distal": 2., "md_thumb_distal": 2.} if 1.5 < t < 4.3 else {})
            if z <= .025001:
                contacts["table"] = .8
            samples.append({"step": step, "joints": nc.targets(t), "cube_xyz_m": [.43, -.1+.2*u, z],
                            "cube_contacts_N": contacts, "phase": nc.phase(t)})
        return samples

    def test_pick_place_requires_opposing_finger_contact_and_transport(self):
        good = self.pick_place_fixture()
        self.assertTrue(nc.validate_pick_place(good)["passed"])
        drop = copy.deepcopy(good)
        for s in drop:
            s["cube_xyz_m"] = [.43, -.1, .025]
            s["cube_contacts_N"] = {"table": .8}
        with self.assertRaisesRegex(RuntimeError, "grasp not sustained"):
            nc.validate_pick_place(drop)
        unsupported = copy.deepcopy(good)
        for s in unsupported:
            s["cube_contacts_N"].pop("md_thumb_distal", None)
        with self.assertRaisesRegex(RuntimeError, "grasp not sustained"):
            nc.validate_pick_place(unsupported)
        no_transport = copy.deepcopy(good)
        for s in no_transport:
            s["cube_xyz_m"][1] = -.1
        with self.assertRaisesRegex(RuntimeError, "not transported"):
            nc.validate_pick_place(no_transport)

    def test_pick_place_requires_target_placement_and_release(self):
        for case in ("wrong_target", "unreleased", "moving"):
            samples = self.pick_place_fixture()
            for s in samples[1116:]:
                if case == "wrong_target":
                    s["cube_xyz_m"][0] += .05
                elif case == "unreleased":
                    s["cube_contacts_N"]["md_middle_distal"] = .5
                else:
                    s["cube_xyz_m"][0] += .001*(s["step"] % 2)
            with self.subTest(case=case), self.assertRaises(RuntimeError):
                nc.validate_pick_place(samples)

    def test_protocol_digest_changes_with_scene_or_policy(self):
        before = nc.protocol_hash()
        with patch.dict(nc.SPEC, {"contact_friction": 2.}):
            self.assertNotEqual(nc.protocol_hash(), before)
        with patch.dict(nc.POLICY, {"controller": "modified"}):
            self.assertNotEqual(nc.protocol_hash(), before)

    def test_pick_place_rejects_nonfinite_readbacks(self):
        for field, key in (("cube_xyz_m", 0), ("joints", nc.JOINTS[0]), ("cube_contacts_N", "table")):
            samples = self.pick_place_fixture()
            samples[0][field][key] = float("nan")
            with self.subTest(field=field), self.assertRaisesRegex(RuntimeError, "Invalid"):
                nc.validate_pick_place(samples)

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
