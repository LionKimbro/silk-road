from pathlib import Path

from .jsonio import read_json, write_json


def normalize_waypoint_record(record):
    path = Path(record["path"]).expanduser().resolve()
    return {
        "name": record["name"],
        "path": str(path),
        "enabled": bool(record.get("enabled", True)),
        "exists": path.exists(),
        "has_marker": (path / "waystation.json").exists(),
    }


def get_enabled_waypoints(config):
    waypoints = []
    for record in config["waypoints"]:
        waypoint = normalize_waypoint_record(record)
        if waypoint["enabled"]:
            waypoints.append(waypoint)
    return waypoints


def ensure_waypoint(path, name="local"):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    marker = path / "waystation.json"
    if not marker.exists():
        write_json(marker, {
            "type": "waystation",
            "version": "v1",
            "name": name,
            "notes": "Created by Silk Road.",
        })
    for dirname in ["signposts", "cache", "bazaar"]:
        (path / dirname).mkdir(parents=True, exist_ok=True)


def read_waypoint_marker(path):
    return read_json(Path(path) / "waystation.json", default={})


def get_silk_cache_dir(waypoint):
    path = Path(waypoint["path"])
    cache = path / "cache" / "silk-road"
    cache.mkdir(parents=True, exist_ok=True)
    return cache
