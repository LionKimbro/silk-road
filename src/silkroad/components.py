from pathlib import Path

from . import constants as C
from .config import get_project_path


DEFAULT_DOCUMENT_INDEXER_SOURCE = '''# Editable Silk Road component: document-indexer
#
# Contract:
#   D contains config, state, and api.
#   Set D["result"] to the result dictionary.
#
# The default implementation delegates the careful filesystem work to the
# built-in api. Edit this file if you want to experiment with component logic.

D["result"] = D["api"]["scan_documents"](D["config"], D["state"])
'''


def ensure_default_components(execroot):
    component_dir = get_project_path(execroot) / C.COMPONENT_DIR
    component_dir.mkdir(parents=True, exist_ok=True)
    path = component_dir / C.DOCUMENT_INDEXER_COMPONENT
    if not path.exists():
        path.write_text(DEFAULT_DOCUMENT_INDEXER_SOURCE, encoding="utf-8")
    return path


def execute_component(path, data, api):
    path = Path(path)
    source = path.read_text(encoding="utf-8")
    local_ns = {
        "D": {
            "config": data["config"],
            "state": data["state"],
            "api": api,
        }
    }
    exec(compile(source, str(path), "exec"), {}, local_ns)
    return local_ns["D"].get("result")
