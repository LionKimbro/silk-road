from datetime import datetime, timedelta, timezone

from . import constants as C
from .components import execute_component
from .documents import scan_documents
from .jsonio import append_jsonl
from .state import now_iso, save_state


def dispatch_sherpa(execroot, config, state, sherpa_name):
    if sherpa_name != C.SHERPA_DOCUMENT_INDEXER:
        raise ValueError(f"unknown sherpa: {sherpa_name}")

    sherpa_state = state["sherpas"][sherpa_name]
    sherpa_state["status"] = "running"
    sherpa_state["last_run"] = now_iso()
    sherpa_state["last_failure"] = None
    save_state(execroot, state)

    append_jsonl_event(execroot, {
        "type": "sherpa-started",
        "sherpa": sherpa_name,
        "time": sherpa_state["last_run"],
    })

    try:
        component_path = config["sherpas"][sherpa_name]["component"]
        result = execute_component(component_path, {
            "config": config,
            "state": state,
        }, {
            "scan_documents": scan_documents,
        })
        if not isinstance(result, dict):
            raise ValueError("component did not return a result dictionary")

        sherpa_state["status"] = "idle"
        sherpa_state["last_success"] = now_iso()
        sherpa_state["last_counts"] = result.get("counts", {})
        sherpa_state["next_run"] = compute_next_run(config, sherpa_name)
        save_state(execroot, state)
        append_jsonl_event(execroot, {
            "type": "sherpa-completed",
            "sherpa": sherpa_name,
            "time": sherpa_state["last_success"],
            "counts": sherpa_state["last_counts"],
        })
        return result
    except Exception as e:
        sherpa_state["status"] = "failed"
        sherpa_state["last_failure"] = f"{type(e).__name__}: {e}"
        sherpa_state["next_run"] = compute_next_run(config, sherpa_name)
        save_state(execroot, state)
        append_jsonl_event(execroot, {
            "type": "sherpa-failed",
            "sherpa": sherpa_name,
            "time": now_iso(),
            "error": sherpa_state["last_failure"],
        })
        raise


def compute_next_run(config, sherpa_name):
    seconds = int(config["sherpas"][sherpa_name].get("interval_seconds", 1800))
    when = datetime.now(timezone.utc).astimezone() + timedelta(seconds=seconds)
    return when.isoformat(timespec="seconds")


def ensure_schedules(config, state):
    changed = False
    for sherpa_name, record in config.get("sherpas", {}).items():
        if not record.get("enabled", True):
            continue
        sherpa_state = state["sherpas"].get(sherpa_name)
        if not sherpa_state:
            continue
        if not sherpa_state.get("next_run"):
            sherpa_state["next_run"] = compute_next_run(config, sherpa_name)
            changed = True
    return changed


def due_to_run(config, state, sherpa_name):
    if not config["sherpas"][sherpa_name].get("enabled", True):
        return False
    sherpa_state = state["sherpas"][sherpa_name]
    next_run = sherpa_state.get("next_run")
    if not next_run:
        return False
    try:
        return datetime.fromisoformat(next_run) <= datetime.now(timezone.utc).astimezone()
    except ValueError:
        return False


def append_jsonl_event(execroot, record):
    from . import constants as C
    from .config import get_project_path

    append_jsonl(get_project_path(execroot) / C.EVENT_LOG, record)
