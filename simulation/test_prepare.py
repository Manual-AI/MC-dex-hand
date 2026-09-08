"""Offline regression tests for pinned vendor checkout setup (builder environment)."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import prepare


class VendorCheckoutTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="manual-dex-checkout-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.upstream = self.root / "upstream"
        self.upstream.mkdir()
        self.git(self.upstream, "init", "-b", "main")
        self.git(self.upstream, "config", "user.name", "Local Test")
        self.git(self.upstream, "config", "user.email", "test@example.invalid")
        (self.upstream / "model.xml").write_text("<mujoco/>\n")
        self.git(self.upstream, "add", "model.xml")
        self.git(self.upstream, "commit", "-m", "test fixture")
        revision = self.git(self.upstream, "rev-parse", "HEAD").strip()
        (self.root / "simulation").mkdir()
        (self.root / "simulation/versions.json").write_text(json.dumps({
            "openarm_repository": str(self.upstream),
            "openarm_commit": revision,
            "openarm_model": "model.xml",
        }))
        self.build = self.root / "build"

    @staticmethod
    def git(path, *args):
        return subprocess.check_output(["git", "-C", str(path), *args], text=True,
                                       stderr=subprocess.DEVNULL)

    def source(self):
        with patch.object(prepare, "ROOT", self.root), patch.object(prepare, "BUILD", self.build):
            return prepare.openarm_source()

    def test_first_clone_and_clean_reuse(self):
        path = self.source()
        self.assertEqual(path.read_text(), "<mujoco/>\n")
        self.assertEqual(self.source(), path)

    def test_modified_checkout_is_preserved(self):
        path = self.source()
        path.write_text("local changes\n")
        with self.assertRaisesRegex(RuntimeError, "Refusing to overwrite modified"):
            self.source()
        self.assertEqual(path.read_text(), "local changes\n")


if __name__ == "__main__":
    unittest.main()
