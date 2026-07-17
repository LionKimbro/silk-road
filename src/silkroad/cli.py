import pathlib
import sys

import lionscliapp as app

from . import constants as C
from .config import ensure_runtime_dirs, load_config
from .components import ensure_default_components
from .sherpas import dispatch_sherpa, ensure_schedules
from .state import load_state, save_state
from .ui import run_gui


def cmd_gui():
    execroot = pathlib.Path.cwd()
    run_gui(execroot)


def cmd_scan():
    execroot = pathlib.Path.cwd()
    ensure_runtime_dirs(execroot)
    ensure_default_components(execroot)
    config = load_config(execroot)
    state = load_state(execroot)
    if ensure_schedules(config, state):
        save_state(execroot, state)
    result = dispatch_sherpa(execroot, config, state, C.SHERPA_DOCUMENT_INDEXER)
    counts = result["counts"]
    print("document-indexer completed")
    print(f"files examined: {counts['files_examined']}")
    print(f"valid documents: {counts['valid_documents']}")
    print(f"document ids: {counts['document_ids']}")
    print(f"duplicates: {counts['duplicate_ids']}")
    print(f"conflicts: {counts['conflicting_ids']}")
    print(f"failures: {counts['failures']}")
    for path in result.get("output_paths", []):
        print(f"output: {path}")


def cmd_init():
    execroot = pathlib.Path.cwd()
    ensure_runtime_dirs(execroot)
    component = ensure_default_components(execroot)
    config = load_config(execroot)
    state = load_state(execroot)
    if ensure_schedules(config, state):
        save_state(execroot, state)
    print(f"initialized {C.PROJECT_DIR}")
    print(f"component: {component}")
    for waypoint in config["waypoints"]:
        print(f"waystation: {waypoint['path']}")


def declare():
    app.declare_app(C.APP_NAME, C.APP_VERSION)
    app.describe_app("Filesystem-native Silk Road control panel for local Sherpas.")
    app.declare_projectdir(C.PROJECT_DIR)
    app.set_flag("search_upwards_for_project_dir", True)
    app.set_flag("uses_locking", True)

    app.declare_cmd("", cmd_gui)
    app.describe_cmd("", "Open the Silk Road Tkinter control panel.")
    app.declare_cmd("gui", cmd_gui)
    app.describe_cmd("gui", "Open the Silk Road Tkinter control panel.")
    app.declare_cmd("scan", cmd_scan)
    app.describe_cmd("scan", "Run the document-indexing Sherpa once.")
    app.set_cmd_flag("scan", "locking", True)
    app.declare_cmd("init", cmd_init)
    app.describe_cmd("init", "Create Silk Road runtime files.")


def main():
    declare()
    app.main()


if __name__ == "__main__":
    main()
