from pathlib import Path

import lionscliapp as cliapp

from silkroad import app
from silkroad.documents import scan_documents


def cmd_gui():
    from silkroad import ui
    app.init(Path.cwd())
    ui.run()


def cmd_scan():
    app.init(Path.cwd())
    config = {"waypoints": app.g["settings"]["known_waystations"]}
    result = scan_documents(config, {})
    print(result)


def main():
    cliapp.declare_app("silk-road", "0.1.0")
    cliapp.describe_app("Silk Road Waystation and Sherpa control panel.")
    cliapp.declare_projectdir(".silkroad")
    cliapp.set_flag("uses_locking", False)
    cliapp.declare_cmd("", cmd_gui)
    cliapp.describe_cmd("", "Open the Silk Road control panel.")
    cliapp.declare_cmd("scan", cmd_scan)
    cliapp.describe_cmd("scan", "Run the Document Scout once.")
    cliapp.main()


if __name__ == "__main__":
    main()
