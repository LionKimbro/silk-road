import time
from pathlib import Path

from silkroad import constants as C
from silkroad.librarian import register_document
from silkroad.noticing import notice_path, write_signpost
from silkroad.persistence import append_jsonl, read_json, write_json
from silkroad.sherpa_files import load_sherpa, mark_started, save_sherpa_record
from silkroad.timeutil import journey_stamp, now_iso
from silkroad.traversal import initial_queue, should_enter

reg = {
    "waystation": None,
    "record": None,
    "journey": None,
    "journal": None,
}


def dispatch_sherpa(waystation, sherpa_id):
    reg["waystation"] = Path(waystation)
    reg["record"] = load_sherpa(reg["waystation"], sherpa_id)
    if not reg["record"]:
        return
    jid = f"{journey_stamp()}-{sherpa_id}"
    mark_started(reg["record"], jid)
    journey = {
        "type": "sherpa-journey",
        "version": "v1",
        "journey_id": jid,
        "sherpa_id": sherpa_id,
        "started_at": now_iso(),
        "queue": initial_queue(reg["waystation"], reg["record"]["spec"]),
        "visited": [],
        "visited_keys": [],
        "discoveries": [],
        "warnings": [],
        "stop_after_step": False,
    }
    save_journey(journey)
    write_journal({"event": "journey_started", "journey_id": jid})


def step_sherpa(waystation, sherpa_id):
    reg["waystation"] = Path(waystation)
    reg["record"] = load_sherpa(reg["waystation"], sherpa_id)
    if not reg["record"]:
        return False
    control = reg["record"]["control"]
    state = reg["record"]["state"]
    if not control.get("enabled"):
        state["status"] = C.STATUS_DISABLED
        save_sherpa_record(reg["record"])
        return False
    if control.get("paused") or state.get("status") == C.STATUS_PAUSED:
        state["status"] = C.STATUS_PAUSED
        save_sherpa_record(reg["record"])
        return False
    if state.get("status") != C.STATUS_HIKING:
        return False
    reg["journey"] = load_current_journey()
    if not reg["journey"]:
        state["status"] = C.STATUS_TROUBLE
        state["last_error"] = "Missing current journey file."
        save_sherpa_record(reg["record"])
        return False
    pace = control.get("pace", {})
    budget_ms = int(pace.get("work_budget_ms", 15))
    end_time = time.perf_counter() + (budget_ms / 1000.0)
    did_work = False
    while time.perf_counter() < end_time and reg["journey"]["queue"]:
        step_one_directory()
        did_work = True
    update_state_from_journey()
    if not reg["journey"]["queue"]:
        finish_journey()
    else:
        save_journey(reg["journey"])
        save_sherpa_record(reg["record"])
    return did_work


def pause_sherpa(waystation, sherpa_id):
    record = load_sherpa(waystation, sherpa_id)
    if record:
        record["control"]["paused"] = True
        record["state"]["status"] = C.STATUS_PAUSED
        save_sherpa_record(record)


def resume_sherpa(waystation, sherpa_id):
    record = load_sherpa(waystation, sherpa_id)
    if record:
        record["control"]["paused"] = False
        record["state"]["status"] = C.STATUS_HIKING if record["state"].get("journey_id") else C.STATUS_RESTING
        save_sherpa_record(record)


def abandon_sherpa(waystation, sherpa_id):
    record = load_sherpa(waystation, sherpa_id)
    if record:
        record["state"].update({"status": C.STATUS_RESTING, "journey_id": None, "last_error": None})
        record["statistics"]["journeys_cancelled"] += 1
        save_sherpa_record(record)


def step_one_directory():
    item = reg["journey"]["queue"].pop(0)
    path = Path(item["path"])
    key = str(path.resolve())
    if key in reg["journey"]["visited_keys"]:
        return
    reg["journey"]["visited_keys"].append(key)
    reg["journey"]["visited"].append(key)
    state = reg["record"]["state"]
    stats = reg["record"]["statistics"]
    state["current_directory"] = key
    state["directories_visited"] += 1
    stats["directories_visited"] += 1
    try:
        entries = list(path.iterdir())
    except Exception as exc:
        warn(str(exc), key)
        return
    for entry in entries:
        state["filesystem_entries_examined"] += 1
        stats["filesystem_entries_examined"] += 1
        handle_entry(entry)
        if entry.is_dir() and item["depth"] < item["max_depth"] and should_enter(entry):
            reg["journey"]["queue"].append({
                "path": str(entry.resolve()),
                "depth": item["depth"] + 1,
                "max_depth": item["max_depth"],
            })


def handle_entry(entry):
    for discovery in notice_path(entry, reg["record"]["spec"]):
        reg["journey"]["discoveries"].append(discovery)
        reg["record"]["state"]["discoveries"] += 1
        if discovery["type"] == "document":
            reg["record"]["statistics"]["documents_noticed"] += 1
            if should_register_document(discovery):
                register_document(reg["waystation"], discovery)
                reg["record"]["statistics"]["documents_registered"] += 1
                write_journal({"event": "document_registered", "path": discovery["path"], "document_id": discovery["document_id"]})
        elif discovery["type"] == "waystation":
            reg["record"]["statistics"]["waystations_discovered"] += 1
            if reg["record"]["spec"].get("noticing", {}).get("waystations", {}).get("write_signpost"):
                write_signpost(reg["waystation"], discovery)
            write_journal({"event": "waystation_discovered", "path": discovery["path"], "waystation_id": discovery.get("waystation_id")})


def should_register_document(discovery):
    key = "lion_json_documents" if discovery.get("format") == "json" else "annotated_markdown_documents"
    return reg["record"]["spec"].get("noticing", {}).get(key, {}).get("register")


def update_state_from_journey():
    state = reg["record"]["state"]
    state["last_step_at"] = now_iso()
    state["directories_waiting"] = len(reg["journey"]["queue"])
    state["warnings"] = len(reg["journey"]["warnings"])


def finish_journey():
    state = reg["record"]["state"]
    stats = reg["record"]["statistics"]
    state["status"] = C.STATUS_RESTING
    state["journey_id"] = None
    state["next_journey_at"] = None
    stats["journeys_completed"] += 1
    reg["journey"]["completed_at"] = now_iso()
    save_journey(reg["journey"])
    save_sherpa_record(reg["record"])
    write_journal({"event": "journey_completed", "journey_id": reg["journey"]["journey_id"]})


def warn(message, path):
    reg["journey"]["warnings"].append({"at": now_iso(), "path": path, "message": message})
    reg["record"]["state"]["warnings"] += 1
    reg["record"]["statistics"]["warnings"] += 1
    write_journal({"event": "warning", "path": path, "message": message})


def load_current_journey():
    jid = reg["record"]["state"].get("journey_id")
    if not jid:
        return None
    return read_json(journey_path(jid), None)


def save_journey(journey):
    write_json(journey_path(journey["journey_id"]), journey)


def journey_path(journey_id):
    return reg["record"]["paths"]["journal_dir"] / f"{journey_id}.journey.json"


def write_journal(record):
    if not reg["record"]["spec"].get("journal", {}).get("enabled", True):
        return
    row = {"at": now_iso()}
    row.update(record)
    jid = reg["record"]["state"].get("journey_id") or record.get("journey_id") or "unassigned"
    append_jsonl(reg["record"]["paths"]["journal_dir"] / f"{jid}.jsonl", row)
