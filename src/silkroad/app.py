from pathlib import Path

from silkroad import constants as C
from silkroad.journey import abandon_sherpa, dispatch_sherpa, pause_sherpa, resume_sherpa, step_sherpa
from silkroad.settings import add_known_waystation, load_settings, save_settings
from silkroad.sherpa_files import load_sherpa, load_sherpas, save_sherpa_record
from silkroad.waypoints import discover_nearby_waystations, ensure_waystation

g = {
    "execroot": None,
    "settings": None,
    "selected_waystation": None,
    "selected_sherpa": None,
    "status": "Ready.",
}


def init(execroot):
    g["execroot"] = Path(execroot).resolve()
    g["settings"] = load_settings(g["execroot"])
    ensure_configured_waystations()
    select_initial_waystation()


def ensure_configured_waystations():
    for record in g["settings"]["known_waystations"]:
        if record.get("enabled", True):
            ensure_waystation(record["path"], record.get("name", "Waystation"))


def select_initial_waystation():
    enabled = [w for w in g["settings"]["known_waystations"] if w.get("enabled", True)]
    if enabled:
        g["selected_waystation"] = enabled[0]["path"]
        sherpas = load_sherpas(g["selected_waystation"])
        g["selected_sherpa"] = sherpas[0]["sherpa_id"] if sherpas else None


def waystation_rows():
    rows = []
    for record in g["settings"]["known_waystations"]:
        if not record.get("enabled", True):
            continue
        ensure_waystation(record["path"], record.get("name", "Waystation"))
        sherpas = load_sherpas(record["path"])
        hiking = sum(1 for row in sherpas if row["state"].get("status") == C.STATUS_HIKING)
        rows.append({
            "name": record.get("name", "Waystation"),
            "path": str(Path(record["path"]).resolve()),
            "source": record.get("source", "manual"),
            "sherpa_count": len(sherpas),
            "hiking_count": hiking,
            "warnings": sum(row["state"].get("warnings", 0) for row in sherpas),
        })
    return rows


def sherpa_rows():
    if not g["selected_waystation"]:
        return []
    return load_sherpas(g["selected_waystation"])


def selected_sherpa_record():
    if not g["selected_waystation"] or not g["selected_sherpa"]:
        return None
    return load_sherpa(g["selected_waystation"], g["selected_sherpa"])


def select_waystation(path):
    g["selected_waystation"] = str(Path(path).resolve())
    sherpas = load_sherpas(path)
    g["selected_sherpa"] = sherpas[0]["sherpa_id"] if sherpas else None


def select_sherpa(sherpa_id):
    g["selected_sherpa"] = sherpa_id


def create_waystation(path, name):
    marker = ensure_waystation(path, name)
    add_known_waystation(g["settings"], path, name, "created")
    save_settings(g["execroot"], g["settings"])
    g["status"] = f"Created Waystation: {marker['name']}"


def add_waystation(path, name=None):
    marker = ensure_waystation(path, name or "Waystation")
    add_known_waystation(g["settings"], path, name or marker.get("name"), "manual")
    save_settings(g["execroot"], g["settings"])
    g["status"] = f"Added Waystation: {marker.get('name')}"


def remove_waystation(path):
    target = str(Path(path).resolve())
    for record in g["settings"]["known_waystations"]:
        if str(Path(record["path"]).resolve()) == target:
            record["enabled"] = False
    save_settings(g["execroot"], g["settings"])
    select_initial_waystation()


def discover_waystations():
    if not g["selected_waystation"]:
        return []
    found = discover_nearby_waystations(g["selected_waystation"])
    for row in found:
        add_known_waystation(g["settings"], row["path"], row["marker"].get("name"), "discovered")
    save_settings(g["execroot"], g["settings"])
    g["status"] = f"Discovered {len(found)} Waystations."
    return found


def run_selected_sherpa():
    record = selected_sherpa_record()
    if not record:
        return
    dispatch_sherpa(g["selected_waystation"], record["sherpa_id"])
    g["status"] = f"Dispatched {record['spec'].get('name', record['sherpa_id'])}."


def pause_selected_sherpa():
    if g["selected_sherpa"]:
        pause_sherpa(g["selected_waystation"], g["selected_sherpa"])


def resume_selected_sherpa():
    if g["selected_sherpa"]:
        resume_sherpa(g["selected_waystation"], g["selected_sherpa"])


def abandon_selected_sherpa():
    if g["selected_sherpa"]:
        abandon_sherpa(g["selected_waystation"], g["selected_sherpa"])


def update_control_enabled(sherpa_id, enabled):
    record = load_sherpa(g["selected_waystation"], sherpa_id)
    if record:
        record["control"]["enabled"] = bool(enabled)
        if not enabled:
            record["state"]["status"] = C.STATUS_DISABLED
        elif record["state"]["status"] == C.STATUS_DISABLED:
            record["state"]["status"] = C.STATUS_RESTING
        save_sherpa_record(record)


def tick_sherpas():
    for row in waystation_rows():
        for sherpa in load_sherpas(row["path"]):
            state = sherpa["state"]
            if state.get("status") == C.STATUS_HIKING:
                step_sherpa(row["path"], sherpa["sherpa_id"])
                return True
    return False
