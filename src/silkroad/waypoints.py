import re
from pathlib import Path

from silkroad import constants as C
from silkroad.persistence import read_json, write_json
from silkroad.timeutil import now_iso


WAYSTATION_DIRS = [
    "bazaar/requests",
    "bazaar/offers",
    "cache",
    "signposts",
    "libraries",
    "sherpas/specifications",
    "sherpas/control",
    "sherpas/state",
    "sherpas/statistics",
    "sherpas/journals",
]


def ensure_waypoint(path, name="local"):
    return ensure_waystation(path, name)


def ensure_waystation(path, name="local"):
    path = Path(path).expanduser().resolve()
    path.mkdir(parents=True, exist_ok=True)
    for rel in WAYSTATION_DIRS:
        (path / rel).mkdir(parents=True, exist_ok=True)
    marker = read_waypoint_marker(path)
    if not marker:
        marker = make_waystation_marker(name)
        write_json(path / "waystation.json", marker)
    else:
        changed = False
        if "waystation_id" not in marker:
            marker["waystation_id"] = slug(marker.get("name") or name)
            changed = True
        if "created_at" not in marker:
            marker["created_at"] = now_iso()
            changed = True
        if changed:
            write_json(path / "waystation.json", marker)
    ensure_library_files(path)
    return marker


def ensure_library_files(path):
    path = Path(path)
    library = path / "libraries" / "library.jsonl"
    registry = path / "libraries" / "librarian-registry.json"
    library.parent.mkdir(parents=True, exist_ok=True)
    if not library.exists():
        library.write_text("", encoding="utf-8")
    if not registry.exists():
        write_json(registry, {
            "document": {
                "document-id": "silk-road.generated.librarian-registry",
                "title": "Silk Road Generated Library Registry",
                "purpose": "Compatibility export from a Silk Road Waystation Library.",
            },
            "registry": {},
        })


def read_waypoint_marker(path):
    path = Path(path)
    marker = read_json(path / "waystation.json", None)
    if not isinstance(marker, dict):
        return None
    if marker.get("type") != "waystation":
        return None
    return marker


def validate_waystation(path):
    path = Path(path).expanduser()
    marker = read_waypoint_marker(path)
    if not marker:
        return {"ok": False, "path": str(path), "error": "Missing valid waystation.json"}
    missing = []
    for rel in WAYSTATION_DIRS:
        if not (path / rel).exists():
            missing.append(rel)
    return {"ok": not missing, "path": str(path.resolve()), "marker": marker, "missing": missing}


def discover_nearby_waystations(start):
    start = Path(start).expanduser().resolve()
    found = []
    roots = [start]
    if start.name == "waystation":
        roots.append(start.parent)
    else:
        roots.append(start.parent)
    seen = set()
    for root in roots:
        if not root.exists():
            continue
        for candidate in root.glob("*/waystation.json"):
            waystation = candidate.parent.resolve()
            if waystation in seen:
                continue
            seen.add(waystation)
            marker = read_waypoint_marker(waystation)
            if marker:
                found.append({"path": str(waystation), "marker": marker})
    return found


def make_waystation_marker(name):
    return {
        "type": "waystation",
        "version": "v1",
        "waystation_id": slug(name),
        "name": name,
        "notes": "Created by Silk Road.",
        "created_at": now_iso(),
    }


def slug(text):
    value = re.sub(r"[^a-zA-Z0-9]+", "-", str(text).strip().lower()).strip("-")
    return value or "waystation"


def status_text(status):
    return C.STATUS_TEXT.get(status, status.title())
