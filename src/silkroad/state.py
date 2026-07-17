from datetime import datetime, timezone

from . import constants as C
from .config import get_project_path
from .jsonio import read_json, write_json


def now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def make_default_state():
    return {
        "version": 1,
        "sherpas": {
            C.SHERPA_DOCUMENT_INDEXER: {
                "enabled": True,
                "status": "idle",
                "last_run": None,
                "next_run": None,
                "last_success": None,
                "last_failure": None,
                "last_counts": {
                    "files_examined": 0,
                    "valid_documents": 0,
                    "duplicate_ids": 0,
                    "conflicting_ids": 0,
                    "warnings": 0,
                    "failures": 0,
                },
            }
        },
    }


def load_state(execroot):
    path = get_project_path(execroot) / C.STATE_FILE
    state = read_json(path)
    if state is None:
        state = make_default_state()
        save_state(execroot, state)
    ensure_state_shape(state)
    return state


def save_state(execroot, state):
    write_json(get_project_path(execroot) / C.STATE_FILE, state)


def ensure_state_shape(state):
    default = make_default_state()
    state.setdefault("version", 1)
    state.setdefault("sherpas", {})
    for name, sherpa in default["sherpas"].items():
        state["sherpas"].setdefault(name, sherpa)
        for key, value in sherpa.items():
            state["sherpas"][name].setdefault(key, value)
