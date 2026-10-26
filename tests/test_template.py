"""Offline structural guard; Godot itself is executed in CI separately."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class TemplateTests(unittest.TestCase):
    def test_project_has_real_main_scene(self):
        project = (ROOT / "project.godot").read_text(encoding="utf-8")
        self.assertIn('run/main_scene="res://scenes/main.tscn"', project)
        self.assertIn('renderer/rendering_method="gl_compatibility"', project)
        self.assertTrue((ROOT / "scenes/main.tscn").is_file())

    def test_scene_has_visible_3d_nodes(self):
        scene = (ROOT / "scenes/main.tscn").read_text(encoding="utf-8")
        for token in ('type="Node3D"', 'type="MeshInstance3D"', 'type="Camera3D"', 'type="DirectionalLight3D"', 'BoxMesh'):
            with self.subTest(token=token):
                self.assertIn(token, scene)

    def test_script_reference_and_node_match(self):
        scene = (ROOT / "scenes/main.tscn").read_text(encoding="utf-8")
        script = (ROOT / "scripts/main.gd").read_text(encoding="utf-8")
        self.assertIn('path="res://scripts/main.gd"', scene)
        self.assertIn('name="RotatingCube"', scene)
        self.assertIn('$RotatingCube', script)
        self.assertIn('extends Node3D', script)

    def test_generated_binaries_not_tracked_by_default(self):
        ignored = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        for item in (".godot/", "*.exe", "*.msix", "*.pck", "build/"):
            with self.subTest(item=item):
                self.assertIn(item, ignored)

    def test_factory_required_godot_smoke_contract(self):
        # 3d-game-factory validates this exact candidate path and test_ entry.
        smoke = (ROOT / "tests/test_smoke.gd").read_text(encoding="utf-8")
        self.assertIn("extends SceneTree", smoke)
        self.assertIn("func test_main_scene()", smoke)
        self.assertIn("get_node_or_null", smoke)
        self.assertIn("quit(1)", smoke)
        workflow = (ROOT / ".github/workflows/godot-smoke.yml").read_text(encoding="utf-8")
        self.assertIn("--script res://tests/test_smoke.gd", workflow)

    def test_real_engine_ci_is_declared(self):
        workflow = (ROOT / ".github/workflows/godot-smoke.yml").read_text(encoding="utf-8")
        self.assertIn("Godot_v4.3-stable_linux.x86_64.zip", workflow)
        self.assertIn("--headless --editor --path . --import", workflow)
        self.assertIn("--headless --path . --quit-after 5", workflow)


if __name__ == "__main__":
    unittest.main()
