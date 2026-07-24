from pathlib import Path

from silkroad import constants as C
from silkroad.persistence import read_json, write_json


def state_path(execroot):
    return Path(execroot) / C.PROJECT_DIR / "state.json"


def load_state(execroot):
    path = state_path(execroot)
    data = read_json(path, None)
    if not isinstance(data, dict):
        data = {
            "type": "silk-road-app-state",
            "version": "v1",
            "selected_waystation_path": None,
            "selected_sherpa_id": C.SHERPA_DOCUMENT_SCOUT,
            "sherpas": {},
            "last_result": None,
        }
        save_state(execroot, data)
    return data


def save_state(execroot, data):
    write_json(state_path(execroot), data)
