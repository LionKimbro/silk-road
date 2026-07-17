import queue
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import tkinter as tk

from silkroad import ui
from silkroad.config import ensure_runtime_dirs, load_config
from silkroad.components import ensure_default_components
from silkroad.state import load_state
from silkroad import constants as C


class GuiSmokeTests(unittest.TestCase):
    def test_control_panel_builds_required_widgets(self):
        with tempfile.TemporaryDirectory() as tmp:
            execroot = Path(tmp)
            ensure_runtime_dirs(execroot)
            ensure_default_components(execroot)
            ui.g.clear()
            ui.g["execroot"] = execroot
            ui.g["config"] = load_config(execroot)
            ui.g["state"] = load_state(execroot)
            ui.g["queue"] = queue.Queue()
            ui.g["worker"] = None
            ui.g["widgets"] = {}

            root = tk.Tk()
            root.withdraw()
            try:
                ui.g["root"] = root
                ui.build_ui(root)
                ui.refresh_all()
                self.assertIn("waypoints", ui.g["widgets"])
                self.assertIn("waystations", ui.g["widgets"])
                self.assertIn("sherpas", ui.g["widgets"])
                self.assertIn("result", ui.g["widgets"])
                self.assertGreaterEqual(len(ui.g["widgets"]["waypoints"].get_children()), 1)
                self.assertGreaterEqual(len(ui.g["widgets"]["sherpas"].get_children()), 1)
            finally:
                root.destroy()

    def test_open_path_uses_windows_shell(self):
        with mock.patch("platform.system", return_value="Windows"):
            with mock.patch("os.startfile", create=True) as startfile:
                ui.open_path("C:/example")
        startfile.assert_called_once_with("C:/example")

    def test_add_and_remove_waypoint_updates_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            execroot = Path(tmp) / "app"
            waypoint = Path(tmp) / "new-waypoint"
            ensure_runtime_dirs(execroot)
            ensure_default_components(execroot)
            ui.g.clear()
            ui.g["execroot"] = execroot
            ui.g["config"] = load_config(execroot)
            ui.g["state"] = load_state(execroot)
            ui.g["queue"] = queue.Queue()
            ui.g["worker"] = None
            ui.g["widgets"] = {}

            root = tk.Tk()
            root.withdraw()
            try:
                ui.g["root"] = root
                ui.build_ui(root)
                ui.refresh_all()

                class FakeWindow:
                    def destroy(self):
                        self.destroyed = True

                name_var = tk.StringVar(value="new")
                path_var = tk.StringVar(value=str(waypoint))
                ui.install_waypoint_from_window(FakeWindow(), name_var, path_var)

                enabled = [w for w in ui.g["config"]["waypoints"] if w.get("enabled")]
                self.assertTrue(any(Path(w["path"]) == waypoint.resolve() for w in enabled))
                self.assertTrue((waypoint / "waystation.json").exists())

                tree = ui.g["widgets"]["waypoints"]
                for item in tree.get_children():
                    values = tree.item(item, "values")
                    if Path(values[2]) == waypoint.resolve():
                        tree.selection_set(item)
                        break
                with mock.patch("tkinter.messagebox.askyesno", return_value=True):
                    ui.remove_selected_waypoint()
                disabled = [
                    w for w in ui.g["config"]["waypoints"]
                    if Path(w["path"]).expanduser().resolve() == waypoint.resolve()
                ]
                self.assertFalse(disabled[0]["enabled"])
            finally:
                root.destroy()

    def test_save_sherpa_code_writes_component_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            component = Path(tmp) / "component.py"
            component.write_text("old", encoding="utf-8")

            class FakeText:
                def get(self, start, end):
                    return "new source"

            ui.g.clear()
            ui.g["widgets"] = {"status": mock.Mock()}
            ui.save_sherpa_code(component, FakeText())
            self.assertEqual(component.read_text(encoding="utf-8"), "new source")

    def test_tree_selection_survives_refresh(self):
        with tempfile.TemporaryDirectory() as tmp:
            execroot = Path(tmp)
            ensure_runtime_dirs(execroot)
            ensure_default_components(execroot)
            ui.g.clear()
            ui.g["execroot"] = execroot
            ui.g["config"] = load_config(execroot)
            ui.g["state"] = load_state(execroot)
            ui.g["queue"] = queue.Queue()
            ui.g["worker"] = None
            ui.g["widgets"] = {}

            root = tk.Tk()
            root.withdraw()
            try:
                ui.g["root"] = root
                ui.build_ui(root)
                ui.refresh_all()
                tree = ui.g["widgets"]["waystations"]
                selected = tree.get_children()[0]
                tree.selection_set(selected)
                tree.focus(selected)
                ui.refresh_all()
                self.assertEqual(tree.selection(), (selected,))

                sherpas = ui.g["widgets"]["sherpas"]
                selected_sherpa = sherpas.get_children()[0]
                sherpas.selection_set(selected_sherpa)
                sherpas.focus(selected_sherpa)
                ui.refresh_all()
                self.assertEqual(sherpas.selection(), (selected_sherpa,))
            finally:
                root.destroy()

    def test_save_sherpa_interval_updates_config_and_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            execroot = Path(tmp)
            ensure_runtime_dirs(execroot)
            ensure_default_components(execroot)
            ui.g.clear()
            ui.g["execroot"] = execroot
            ui.g["config"] = load_config(execroot)
            ui.g["state"] = load_state(execroot)
            ui.g["widgets"] = {"status": mock.Mock()}

            class FakeWindow:
                def destroy(self):
                    self.destroyed = True

            minutes_var = mock.Mock()
            minutes_var.get.return_value = "7"
            ui.save_sherpa_interval(FakeWindow(), C.SHERPA_DOCUMENT_INDEXER, minutes_var)

            self.assertEqual(ui.g["config"]["sherpas"][C.SHERPA_DOCUMENT_INDEXER]["interval_seconds"], 420)
            self.assertTrue(ui.g["state"]["sherpas"][C.SHERPA_DOCUMENT_INDEXER]["next_run"])


if __name__ == "__main__":
    unittest.main()
