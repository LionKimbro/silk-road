from pathlib import Path

from . import constants as C
from .jsonio import read_json, write_json


def get_project_path(execroot):
    return Path(execroot) / C.PROJECT_DIR


def make_default_config(execroot):
    waypoint = find_default_waypoint()
    territories = []
    for candidate in [Path("C:/lion/github"), Path("C:/lion/code")]:
        if candidate.exists():
            territories.append(str(candidate))
    document_roots = []
    style_cards = Path("C:/lion/github/lions-documents/coding-guidelines/style-cards")
    if style_cards.exists():
        document_roots.append(str(style_cards))

    return {
        "version": 1,
        "waypoints": [
            {
                "name": "code",
                "path": str(waypoint),
                "enabled": True,
            }
        ],
        "scan_territories": territories,
        "document_roots": document_roots,
        "sherpas": {
            C.SHERPA_DOCUMENT_INDEXER: {
                "enabled": True,
                "interval_seconds": 1800,
                "component": str(get_project_path(execroot) / C.COMPONENT_DIR / C.DOCUMENT_INDEXER_COMPONENT),
            }
        },
        "discovery": {
            "scan_docs_raw": True,
            "json_only": True,
        },
    }


def find_default_waypoint():
    candidates = [
        Path("F:/lion/code/waystation"),
        Path("C:/lion/code/waystation"),
        Path("C:/lion/github/waystation"),
    ]
    for path in candidates:
        if (path / "waystation.json").exists():
            return path
    return Path("F:/lion/code/waystation")


def load_config(execroot):
    project = get_project_path(execroot)
    path = project / C.CONFIG_FILE
    config = read_json(path)
    if config is None:
        config = make_default_config(execroot)
        write_json(path, config)
    elif normalize_config(config):
        write_json(path, config)
    return config


def normalize_config(config):
    changed = False
    config.setdefault("document_roots", [])
    style_cards = Path("C:/lion/github/lions-documents/coding-guidelines/style-cards")
    if style_cards.exists():
        style_cards_text = str(style_cards)
        existing = {str(Path(path).expanduser()).lower() for path in config["document_roots"]}
        if style_cards_text.lower() not in existing:
            config["document_roots"].append(style_cards_text)
            changed = True
    return changed


def save_config(execroot, config):
    write_json(get_project_path(execroot) / C.CONFIG_FILE, config)


def ensure_runtime_dirs(execroot):
    project = get_project_path(execroot)
    (project / C.COMPONENT_DIR).mkdir(parents=True, exist_ok=True)
    (project / "logs").mkdir(parents=True, exist_ok=True)
    return project
