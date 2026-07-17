import json
from pathlib import Path
from time import time

from .jsonio import write_json
from .waypoints import get_enabled_waypoints, get_silk_cache_dir

MD_HEADER_READ_BYTES = 16 * 1024


def scan_documents(config, state):
    ts = int(time())
    candidates = find_candidate_files(config)
    documents = {}
    malformed = []
    warnings = []
    files_examined = 0

    for path in candidates:
        files_examined += 1
        try:
            doc = read_document_header(path)
        except Exception as e:
            malformed.append({
                "path": str(path),
                "error": str(e),
                "ts": ts,
            })
            continue

        if not isinstance(doc, dict):
            continue
        document_id = doc.get("document-id")
        if not document_id:
            warnings.append({
                "path": str(path),
                "warning": "document header has no document-id",
                "ts": ts,
            })
            continue

        entry = make_location_entry(path, doc, ts)
        documents.setdefault(document_id, []).append(entry)

    index = reconcile_index(documents, ts)
    conflicts = find_conflicts(index)
    librarian = make_librarian_registry(index, conflicts)
    output_paths = write_outputs(config, index, malformed, warnings, conflicts, librarian, ts)

    counts = {
        "files_examined": files_examined,
        "valid_documents": sum(len(v) for v in index["documents"].values()),
        "document_ids": len(index["documents"]),
        "duplicate_ids": sum(1 for v in index["documents"].values() if len(v) > 1),
        "conflicting_ids": len(conflicts),
        "warnings": len(warnings),
        "failures": len(malformed),
    }

    return {
        "status": "ok",
        "counts": counts,
        "conflicts": conflicts,
        "warnings": warnings,
        "malformed": malformed,
        "output_paths": output_paths,
        "ts": ts,
    }


def find_candidate_files(config):
    seen = set()
    candidates = []

    if config["discovery"].get("scan_docs_raw", True):
        for territory in config.get("scan_territories", []):
            root = Path(territory).expanduser()
            if root.exists():
                add_docs_raw_candidates(candidates, seen, root)

    for root_text in config.get("document_roots", []):
        root = Path(root_text).expanduser()
        if root.exists():
            add_document_candidates(candidates, seen, root)

    return candidates


def add_docs_raw_candidates(candidates, seen, root):
    for docs_raw in root.rglob("docs/raw"):
        if not docs_raw.is_dir():
            continue
        add_document_candidates(candidates, seen, docs_raw)


def add_document_candidates(candidates, seen, root):
    for pattern in ["*.json", "*.md"]:
        for path in root.rglob(pattern):
            resolved = path.resolve()
            key = str(resolved).lower()
            if key not in seen:
                seen.add(key)
                candidates.append(resolved)


def read_document_header(path):
    suffix = path.suffix.lower()
    if suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        doc = data.get("document") if isinstance(data, dict) else None
        if isinstance(doc, dict):
            doc = dict(doc)
            doc["_source-format"] = "json"
        return doc
    if suffix == ".md":
        return read_markdown_document_header(path)
    return None


def read_markdown_document_header(path):
    text = read_text_prefix(path, MD_HEADER_READ_BYTES)
    if not text.startswith("```"):
        return None
    lines = text.splitlines()
    if not lines:
        return None

    header_lines = []
    for line in lines[1:]:
        if line.strip() == "```":
            break
        header_lines.append(line)
    else:
        return None

    doc = parse_simple_header_lines(header_lines)
    if doc:
        doc["_source-format"] = "md"
    return doc


def read_text_prefix(path, byte_count):
    with path.open("rb") as f:
        data = f.read(byte_count)
    return data.decode("utf-8", errors="replace")


def parse_simple_header_lines(lines):
    doc = {}
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if key == "tags":
            doc[key] = value.split()
        elif key == "type":
            doc[key] = value
        else:
            doc[key] = value
    return doc


def make_location_entry(path, doc, ts):
    stat = path.stat()
    metadata = {
        key: value
        for key, value in doc.items()
        if not key.startswith("_")
    }
    return {
        "path": str(path),
        "modified": stat.st_mtime,
        "size": stat.st_size,
        "discovered-ts": ts,
        "title": doc.get("title"),
        "purpose": doc.get("purpose"),
        "tags": doc.get("tags", []),
        "type": doc.get("type", {}),
        "format": doc.get("_source-format", path.suffix.lower().lstrip(".")),
        "metadata": metadata,
    }


def reconcile_index(documents, ts):
    for locations in documents.values():
        locations.sort(key=lambda item: item["path"].lower())
    return {
        "type": "silk-road-document-index",
        "version": 1,
        "ts": ts,
        "documents": dict(sorted(documents.items())),
    }


def find_conflicts(index):
    conflicts = []
    for document_id, locations in index["documents"].items():
        titles = sorted({loc.get("title") for loc in locations if loc.get("title")})
        purposes = sorted({loc.get("purpose") for loc in locations if loc.get("purpose")})
        if len(titles) > 1 or len(purposes) > 1:
            conflicts.append({
                "document-id": document_id,
                "locations": [loc["path"] for loc in locations],
                "titles": titles,
                "purposes": purposes,
            })
    return conflicts


def make_librarian_registry(index, conflicts):
    conflict_ids = {item["document-id"] for item in conflicts}
    registry = {}
    for document_id, locations in index["documents"].items():
        first = locations[0]
        tags = list(first.get("tags") or [])
        if "silk_road" not in tags:
            tags.append("silk_road")
        if "document" not in tags:
            tags.append("document")
        if document_id in conflict_ids:
            tags.append("conflict")

        registry[document_id] = {
            "id": document_id,
            "title": first.get("title") or document_id,
            "purpose": first.get("purpose") or "Discovered Lion-style JSON document.",
            "location": [{"path": loc["path"]} for loc in locations],
            "tags": tags,
            "type": {
                "logical": {
                    "base": "file",
                    "format": first.get("format") or "json",
                    "encoding": "utf-8",
                },
                "semantic": {
                    "base": "document",
                    "system": "silk-road",
                },
            },
        }

    return {
        "document": {
            "document-id": "silk-road.librarian.document-registry.v1",
            "title": "Silk Road Discovered Documents",
            "purpose": "Librarian2-compatible registry generated by Silk Road's document-indexer Sherpa.",
            "tags": ["silk_road", "librarian", "documents"],
        },
        "registry": registry,
    }


def write_outputs(config, index, malformed, warnings, conflicts, librarian, ts):
    output_paths = []
    for waypoint in get_enabled_waypoints(config):
        cache = get_silk_cache_dir(waypoint)
        files = {
            "document-index.json": index,
            "malformed.json": {
                "type": "malformed-documents",
                "files": malformed,
                "ts": ts,
            },
            "warnings.json": {
                "type": "document-indexer-warnings",
                "warnings": warnings,
                "ts": ts,
            },
            "conflicts.json": {
                "type": "document-id-conflicts",
                "conflicts": conflicts,
                "ts": ts,
            },
            "librarian-registry.json": librarian,
            "last-run.json": {
                "type": "silk-road-sherpa-run",
                "sherpa": "document-indexer",
                "ts": ts,
                "outputs": [
                    "document-index.json",
                    "librarian-registry.json",
                    "malformed.json",
                    "warnings.json",
                    "conflicts.json",
                ],
            },
        }
        for name, data in files.items():
            path = cache / name
            write_json(path, data)
            output_paths.append(str(path))
    return output_paths
