import hashlib
from pathlib import Path

from silkroad.persistence import read_json, read_jsonl, write_json, write_text
from silkroad.timeutil import now_iso


def register_document(waystation, discovery):
    waystation = Path(waystation)
    library_path = waystation / "libraries" / "library.jsonl"
    registry_path = waystation / "libraries" / "librarian-registry.json"
    records = read_jsonl(library_path)
    doc_id = discovery["document_id"]
    record = find_record(records, doc_id)
    if not record:
        record = {
            "type": "silk-road-library-record",
            "version": "v1",
            "document_id": doc_id,
            "metadata": discovery.get("metadata", {}),
            "locations": [],
            "first_observed_at": now_iso(),
            "last_observed_at": now_iso(),
        }
        records.append(record)
    record["metadata"] = merge_metadata(record.get("metadata", {}), discovery.get("metadata", {}))
    record["last_observed_at"] = now_iso()
    add_location(record, discovery)
    write_library(library_path, records)
    write_librarian_registry(registry_path, records)


def find_record(records, doc_id):
    for record in records:
        if record.get("document_id") == doc_id:
            return record
    return None


def add_location(record, discovery):
    path = str(Path(discovery["path"]).resolve())
    content_hash = file_hash(path)
    for loc in record["locations"]:
        if loc.get("path") == path:
            loc["last_observed_at"] = now_iso()
            loc["content_hash"] = content_hash
            loc["format"] = discovery.get("format")
            return
    record["locations"].append({
        "path": path,
        "format": discovery.get("format"),
        "content_hash": content_hash,
        "first_observed_at": now_iso(),
        "last_observed_at": now_iso(),
    })


def merge_metadata(old, new):
    merged = dict(old)
    for key, value in new.items():
        if value not in (None, "", []):
            merged[key] = value
    return merged


def write_library(path, records):
    lines = []
    import json
    for record in sorted(records, key=lambda item: item.get("document_id", "")):
        lines.append(json.dumps(record, ensure_ascii=False))
    write_text(path, "\n".join(lines) + ("\n" if lines else ""))


def write_librarian_registry(path, records):
    registry = {}
    for record in records:
        doc_id = record["document_id"]
        metadata = record.get("metadata", {})
        registry[doc_id] = {
            "id": doc_id,
            "title": metadata.get("title") or doc_id,
            "purpose": metadata.get("purpose") or metadata.get("description") or "",
            "tags": normalize_tags(metadata.get("tags")),
            "type": metadata.get("type") or default_type(record),
            "location": [{"path": loc["path"]} for loc in record.get("locations", [])],
        }
    write_json(path, {
        "document": {
            "document-id": "silk-road.generated.librarian-registry",
            "title": "Silk Road Generated Library Registry",
            "purpose": "Compatibility export from a Silk Road Waystation Library.",
        },
        "registry": registry,
    })


def normalize_tags(tags):
    if isinstance(tags, list):
        return tags
    if isinstance(tags, str):
        return tags.split()
    return []


def default_type(record):
    locations = record.get("locations") or []
    fmt = locations[0].get("format") if locations else ""
    return {"logical": {"base": "file", "format": fmt or "unknown"}}


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        while True:
            chunk = f.read(1024 * 64)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()
