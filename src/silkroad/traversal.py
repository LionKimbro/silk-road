from pathlib import Path

from silkroad import constants as C


def initial_queue(waystation, spec):
    waystation = Path(waystation).resolve()
    nav = spec.get("navigation", {})
    mode = nav.get("mode", "peer_directories")
    if mode == "specific_directory":
        root = Path(nav.get("path") or waystation.parent).expanduser().resolve()
        return [{"path": str(root), "depth": 0, "max_depth": int(nav.get("depth", 3))}]
    if mode == "ancestor_territory":
        levels_up = int(nav.get("levels_up", 1))
        root = waystation.parent
        for _ in range(levels_up):
            root = root.parent
        return [{"path": str(root), "depth": 0, "max_depth": int(nav.get("levels_down", 3))}]
    root = waystation.parent
    return [{"path": str(root), "depth": 0, "max_depth": int(nav.get("peer_depth", 3))}]


def should_enter(path):
    path = Path(path)
    if path.name in C.IGNORED_DIR_NAMES:
        return False
    try:
        if path.is_symlink():
            return False
    except OSError:
        return False
    return True
