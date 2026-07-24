from pathlib import Path

from silkroad import constants as C
from silkroad.persistence import read_json, write_json
from silkroad.timeutil import now_iso


def ensure_builtin_sherpas(waystation):
    waystation = Path(waystation)
    ensure_sherpa(waystation, document_scout_spec())
    ensure_sherpa(waystation, waystation_scout_spec())


def ensure_sherpa(waystation, spec):
    sid = spec["sherpa_id"]
    paths = sherpa_paths(waystation, sid)
    paths["journal_dir"].mkdir(parents=True, exist_ok=True)
    if not paths["spec"].exists():
        write_json(paths["spec"], spec)
    if not paths["control"].exists():
        write_json(paths["control"], default_control(sid))
    if not paths["state"].exists():
        write_json(paths["state"], default_state(sid))
    if not paths["statistics"].exists():
        write_json(paths["statistics"], default_statistics(sid))


def load_sherpas(waystation):
    waystation = Path(waystation)
    ensure_builtin_sherpas(waystation)
    rows = []
    for spec_path in sorted((waystation / "sherpas" / "specifications").glob("*.json")):
        spec = read_json(spec_path, {})
        sid = spec.get("sherpa_id") or spec_path.stem
        paths = sherpa_paths(waystation, sid)
        rows.append({
            "sherpa_id": sid,
            "spec": spec,
            "control": read_json(paths["control"], default_control(sid)),
            "state": read_json(paths["state"], default_state(sid)),
            "statistics": read_json(paths["statistics"], default_statistics(sid)),
            "paths": paths,
        })
    return rows


def load_sherpa(waystation, sherpa_id):
    for row in load_sherpas(waystation):
        if row["sherpa_id"] == sherpa_id:
            return row
    return None


def save_sherpa_record(record):
    write_json(record["paths"]["spec"], record["spec"])
    write_json(record["paths"]["control"], record["control"])
    write_json(record["paths"]["state"], record["state"])
    write_json(record["paths"]["statistics"], record["statistics"])


def sherpa_paths(waystation, sherpa_id):
    base = Path(waystation) / "sherpas"
    return {
        "spec": base / "specifications" / f"{sherpa_id}.json",
        "control": base / "control" / f"{sherpa_id}.json",
        "state": base / "state" / f"{sherpa_id}.json",
        "statistics": base / "statistics" / f"{sherpa_id}.json",
        "journal_dir": base / "journals" / sherpa_id,
    }


def default_control(sherpa_id):
    return {
        "type": "sherpa-control",
        "version": "v1",
        "sherpa_id": sherpa_id,
        "enabled": True,
        "paused": False,
        "pace": {
            "preset": "walking",
            "work_budget_ms": 15,
            "tick_interval_ms": 250,
        },
        "schedule": {
            "automatic": False,
            "journey_interval_seconds": 1800,
        },
    }


def default_state(sherpa_id):
    return {
        "type": "sherpa-state",
        "version": "v1",
        "sherpa_id": sherpa_id,
        "status": C.STATUS_RESTING,
        "journey_id": None,
        "started_at": None,
        "last_step_at": None,
        "current_directory": None,
        "directories_waiting": 0,
        "directories_visited": 0,
        "filesystem_entries_examined": 0,
        "discoveries": 0,
        "warnings": 0,
        "last_error": None,
        "next_journey_at": None,
    }


def default_statistics(sherpa_id):
    return {
        "type": "sherpa-statistics",
        "version": "v1",
        "sherpa_id": sherpa_id,
        "journeys_started": 0,
        "journeys_completed": 0,
        "journeys_failed": 0,
        "journeys_cancelled": 0,
        "directories_visited": 0,
        "filesystem_entries_examined": 0,
        "waystations_discovered": 0,
        "documents_noticed": 0,
        "documents_registered": 0,
        "documents_collected": 0,
        "warnings": 0,
    }


def document_scout_spec():
    return {
        "type": "sherpa-specification",
        "version": "v1",
        "sherpa_id": C.SHERPA_DOCUMENT_SCOUT,
        "name": "Document Scout",
        "navigation": {"mode": "peer_directories", "peer_depth": 3},
        "noticing": {
            "waystations": {"enabled": False, "write_signpost": False},
            "lion_json_documents": {"enabled": True, "register": True, "collect": False, "journal": True},
            "annotated_markdown_documents": {"enabled": True, "register": True, "collect": False, "journal": True},
            "file_pattern": {"enabled": False, "pattern": "*.lsf", "register": False, "collect": False, "journal": True},
        },
        "library": {"target": "waystation"},
        "journal": {"enabled": True, "detail": "summary"},
    }


def waystation_scout_spec():
    return {
        "type": "sherpa-specification",
        "version": "v1",
        "sherpa_id": C.SHERPA_WAYSTATION_SCOUT,
        "name": "Waystation Scout",
        "navigation": {"mode": "peer_directories", "peer_depth": 2},
        "noticing": {
            "waystations": {"enabled": True, "write_signpost": True, "journal": True},
            "lion_json_documents": {"enabled": False, "register": False, "collect": False},
            "annotated_markdown_documents": {"enabled": False, "register": False, "collect": False},
            "file_pattern": {"enabled": False, "pattern": "*.json", "register": False, "collect": False},
        },
        "library": {"target": "waystation"},
        "journal": {"enabled": True, "detail": "summary"},
    }


def mark_started(record, journey_id):
    state = record["state"]
    stats = record["statistics"]
    state.update({
        "status": C.STATUS_HIKING,
        "journey_id": journey_id,
        "started_at": now_iso(),
        "last_step_at": None,
        "current_directory": None,
        "directories_waiting": 0,
        "directories_visited": 0,
        "filesystem_entries_examined": 0,
        "discoveries": 0,
        "warnings": 0,
        "last_error": None,
    })
    stats["journeys_started"] += 1
    save_sherpa_record(record)
