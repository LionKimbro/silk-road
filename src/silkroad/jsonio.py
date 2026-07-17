import json
import os
import tempfile
from pathlib import Path


def read_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    text = path.read_text(encoding="utf-8")
    return json.loads(text)


def write_json(path, data, indent=2):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    indent_arg = indent if indent > 0 else None
    separators = (",", ":") if indent == 0 else None
    text = json.dumps(data, indent=indent_arg, separators=separators, ensure_ascii=False)
    text += "\n"

    fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp", text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def append_jsonl(path, record):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
    with path.open("a", encoding="utf-8") as f:
        f.write(line)
