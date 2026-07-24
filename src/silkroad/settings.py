from pathlib import Path

from silkroad import constants as C
from silkroad.persistence import read_json, write_json


def ensure_runtime_dirs(execroot):
    execroot = Path(execroot)
    project = execroot / C.PROJECT_DIR
    project.mkdir(parents=True, exist_ok=True)
    (project / "logs").mkdir(exist_ok=True)
    return project


def settings_path(execroot):
    return ensure_runtime_dirs(execroot) / "settings.json"


def load_settings(execroot):
    path = settings_path(execroot)
    data = read_json(path, None)
    if not isinstance(data, dict):
        data = default_settings(execroot)
        write_json(path, data)
    normalize_settings(data, execroot)
    return data


def save_settings(execroot, data):
    normalize_settings(data, execroot)
    write_json(settings_path(execroot), data)


def default_settings(execroot):
    default_waystation = Path(execroot) / C.PROJECT_DIR / "waystations" / "home" / "waystation"
    return {
        "type": "silk-road-settings",
        "version": "v1",
        "known_waystations": [
            {
                "name": "Silk Road Home",
                "path": str(default_waystation),
                "source": "created",
                "enabled": True,
            }
        ],
        "pace_presets": dict(C.PACE_PRESETS),
        "default_tick_interval_ms": 250,
        "ignored_directory_names": sorted(C.IGNORED_DIR_NAMES),
        "default_navigation_depth_limits": {
            "peer_depth": 3,
            "levels_up": 1,
            "levels_down": 3,
            "specific_depth": 3,
        },
        "recent_gui_selection": {
            "waystation_path": str(default_waystation),
            "sherpa_id": C.SHERPA_DOCUMENT_SCOUT,
        },
        "window_geometry": "1280x760",
        "logging_level": "info",
    }


def normalize_settings(data, execroot):
    data.setdefault("type", "silk-road-settings")
    data.setdefault("version", "v1")
    data.setdefault("known_waystations", [])
    data.setdefault("pace_presets", dict(C.PACE_PRESETS))
    data.setdefault("default_tick_interval_ms", 250)
    data.setdefault("recent_gui_selection", {})
    if not data["known_waystations"]:
        data["known_waystations"].append(default_settings(execroot)["known_waystations"][0])


def add_known_waystation(settings, path, name=None, source="manual"):
    path = str(Path(path).expanduser().resolve())
    for record in settings["known_waystations"]:
        if str(Path(record["path"]).expanduser().resolve()) == path:
            record["enabled"] = True
            record["source"] = record.get("source") or source
            if name:
                record["name"] = name
            return record
    record = {
        "name": name or Path(path).parent.name or "Waystation",
        "path": path,
        "source": source,
        "enabled": True,
    }
    settings["known_waystations"].append(record)
    return record
