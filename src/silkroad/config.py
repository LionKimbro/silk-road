from silkroad.settings import ensure_runtime_dirs, load_settings, save_settings


def load_config(execroot):
    settings = load_settings(execroot)
    return {
        "waypoints": settings["known_waystations"],
        "waystations": settings["known_waystations"],
        "sherpas": {},
        "settings": settings,
    }


def save_config(execroot, config):
    settings = config.get("settings") or {}
    settings["known_waystations"] = config.get("waystations") or config.get("waypoints") or []
    save_settings(execroot, settings)
