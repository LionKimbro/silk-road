import json
import re
from pathlib import Path

from silkroad.persistence import read_json, write_json
from silkroad.timeutil import now_iso


def notice_path(path, spec):
    path = Path(path)
    discoveries = []
    if path.is_dir():
        waystation = notice_waystation(path, spec)
        if waystation:
            discoveries.append(waystation)
        return discoveries
    if path.suffix.lower() == ".json":
        doc = notice_lion_json(path, spec)
        if doc:
            discoveries.append(doc)
    if path.suffix.lower() in (".md", ".markdown"):
        doc = notice_annotated_markdown(path, spec)
        if doc:
            discoveries.append(doc)
    pattern = notice_pattern(path, spec)
    if pattern:
        discoveries.append(pattern)
    return discoveries


def notice_waystation(path, spec):
    cfg = spec.get("noticing", {}).get("waystations", {})
    if not cfg.get("enabled"):
        return None
    marker = read_json(Path(path) / "waystation.json", None)
    if isinstance(marker, dict) and marker.get("type") == "waystation":
        return {
            "type": "waystation",
            "path": str(Path(path).resolve()),
            "waystation_id": marker.get("waystation_id") or marker.get("name"),
            "metadata": marker,
        }
    return None


def notice_lion_json(path, spec):
    cfg = spec.get("noticing", {}).get("lion_json_documents", {})
    if not cfg.get("enabled"):
        return None
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return None
    doc = data.get("document") if isinstance(data, dict) else None
    if not isinstance(doc, dict):
        return None
    doc_id = doc.get("document-id") or doc.get("document_id")
    if not doc_id:
        return None
    metadata = dict(doc)
    metadata["document-id"] = doc_id
    return {
        "type": "document",
        "document_id": doc_id,
        "path": str(Path(path).resolve()),
        "format": "json",
        "metadata": metadata,
    }


def notice_annotated_markdown(path, spec):
    cfg = spec.get("noticing", {}).get("annotated_markdown_documents", {})
    if not cfg.get("enabled"):
        return None
    metadata = read_markdown_metadata(path)
    doc_id = metadata.get("document-id")
    if not doc_id:
        return None
    return {
        "type": "document",
        "document_id": doc_id,
        "path": str(Path(path).resolve()),
        "format": "md",
        "metadata": metadata,
    }


def notice_pattern(path, spec):
    cfg = spec.get("noticing", {}).get("file_pattern", {})
    if not cfg.get("enabled"):
        return None
    pattern = cfg.get("pattern") or ""
    if Path(path).match(pattern):
        return {
            "type": "file-pattern",
            "path": str(Path(path).resolve()),
            "pattern": pattern,
            "metadata": {"title": Path(path).name},
        }
    return None


def read_markdown_metadata(path):
    text = Path(path).read_text(encoding="utf-8")[:16384]
    if not text.startswith("```"):
        return {}
    end = text.find("\n```", 3)
    if end < 0:
        return {}
    block = text[3:end]
    metadata = {}
    for line in block.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if key == "tags":
            metadata[key] = value.split()
        else:
            metadata[key] = value
    return metadata


def write_signpost(waystation, discovery):
    waystation = Path(waystation)
    sid = discovery.get("waystation_id") or safe_name(discovery["path"])
    path = waystation / "signposts" / f"{safe_name(sid)}.json"
    write_json(path, {
        "type": "waystation-signpost",
        "version": "v1",
        "waystation_id": sid,
        "path": discovery["path"],
        "last_observed_at": now_iso(),
    })


def safe_name(text):
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", str(text)).strip(".-") or "waystation"
