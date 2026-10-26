import tempfile
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import launcher

class PortableLauncherTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / "resources"
        (self.source / "resources").mkdir(parents=True)
        (self.source / "resources" / "SKILL.md").write_text("test", encoding="utf-8")
        (self.source / "addon" / "FreeCADMCP").mkdir(parents=True)
        (self.source / "addon" / "FreeCADMCP" / "Init.py").write_text("test", encoding="utf-8")
        self.exe = self.root / "freecad-mcp.exe"
        self.exe.write_text("fake", encoding="utf-8")
        patch.object(launcher.Path, "home", return_value=self.root).start()
        patch.object(launcher, "resource", side_effect=lambda x: self.source / x).start()
        patch.object(launcher, "exe_path", return_value=str(self.exe)).start()
        patch.dict("os.environ", {"APPDATA": str(self.root / "AppData" / "Roaming")}).start()
        self.addCleanup(patch.stopall)

    def test_roundtrip(self):
        p = launcher.paths()
        launcher.write_json(p["config"], {"mcpServers": {"other": {"command": "x"}}, "custom": True})
        launcher.write_text(p["instructions"], "Existing guidance\n")
        self.assertEqual(launcher.install(), 0)
        self.assertEqual(launcher.install(), 0)
        self.assertEqual(launcher.check(), 0)
        self.assertTrue((p["cli_skill"] / "SKILL.md").is_file())
        self.assertEqual(launcher.uninstall(), 0)
        self.assertEqual(launcher.check(), 1)
        self.assertFalse(p["cli_skill"].exists())
        self.assertEqual(launcher.read_json(p["config"]),
                         {"mcpServers": {"other": {"command": "x"}}, "custom": True})
        self.assertIn("Existing guidance", p["instructions"].read_text(encoding="utf-8"))

    def test_empty_json_files_are_initialized(self):
        p = launcher.paths()
        launcher.write_text(p["config"], "")
        launcher.write_text(p["state"], "   \n")
        self.assertEqual(launcher.install(), 0)
        self.assertEqual(launcher.check(), 0)
        self.assertEqual(launcher.read_json(p["config"])["mcpServers"]["freecad"]["command"],
                         str(self.exe))

    def test_malformed_nonempty_json_is_never_overwritten(self):
        p = launcher.paths()
        launcher.write_text(p["config"], "{broken")
        with self.assertRaisesRegex(ValueError, "Invalid JSON in"):
            launcher.install()
        self.assertEqual(p["config"].read_text(encoding="utf-8"), "{broken")

    def test_subcommand_help(self):
        with patch.object(sys, "argv", ["freecad-mcp.exe", "install", "--help"]):
            self.assertEqual(launcher.main(), 0)

    def test_existing_server_not_overwritten(self):
        p = launcher.paths()
        launcher.write_json(p["config"], {"mcpServers": {"freecad": {"command": "other.exe"}}})
        with self.assertRaisesRegex(RuntimeError, "non-managed"):
            launcher.install()

    def test_modified_entry_is_not_deleted(self):
        p = launcher.paths()
        launcher.install()
        conf = launcher.read_json(p["config"])
        conf["mcpServers"]["freecad"]["args"] = ["--host", "127.0.0.1"]
        launcher.write_json(p["config"], conf)
        launcher.uninstall()
        self.assertIn("freecad", launcher.read_json(p["config"])["mcpServers"])

    def test_foreign_addon_preserved(self):
        addon = launcher.paths()["addon"]
        addon.mkdir(parents=True)
        (addon / "keep.txt").write_text("keep", encoding="utf-8")
        launcher.install()
        launcher.uninstall()
        self.assertTrue((addon / "keep.txt").exists())

if __name__ == "__main__":
    unittest.main()
