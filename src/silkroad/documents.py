import json
from pathlib import Path

from silkroad import constants as C
from silkroad.journey import dispatch_sherpa, step_sherpa
from silkroad.noticing import read_markdown_metadata
from silkroad.persistence import write_json
from silkroad.waypoints import ensure_waystation


def scan_documents(config, state):
    if config.get("scan_territories") or config.get("document_roots"):
        return scan_documents_legacy(config)
    waypoints = config.get("waypoints") or config.get("waystations") or []
    if not waypoints:
        return {"counts": empty_counts(), "warnings": [], "failures": []}
    waypoint = next((w for w in waypoints if w.get("enabled", True)), waypoints[0])
    path = Path(waypoint["path"])
    ensure_waystation(path, waypoint.get("name", "Waystation"))
    record = {
        "sherpa_id": C.SHERPA_DOCUMENT_SCOUT,
        "name": "Document Scout",
    }
    dispatch_sherpa(path, C.SHERPA_DOCUMENT_SCOUT)
    guard = 0
    while step_sherpa(path, C.SHERPA_DOCUMENT_SCOUT):
        guard += 1
        if guard > 10000:
            break
    return {
        "sherpa": record,
        "counts": summarize(path),
        "warnings": [],
        "failures": [],
    }


def summarize(path):
    from silkroad.sherpa_files import load_sherpa
    row = load_sherpa(path, C.SHERPA_DOCUMENT_SCOUT)
    stats = row["statistics"]
    return {
        "files_examined": stats.get("filesystem_entries_examined", 0),
        "valid_documents": stats.get("documents_noticed", 0),
        "warnings": stats.get("warnings", 0),
        "failures": stats.get("journeys_failed", 0),
    }


def empty_counts():
    return {
        "files_examined": 0,
        "valid_documents": 0,
        "warnings": 0,
        "failures": 0,
    }


def scan_documents_legacy(config):
    waypoints = config.get("waypoints") or config.get("waystations") or []
    waypoint = next((w for w in waypoints if w.get("enabled", True)), waypoints[0])
    waypoint_path = Path(waypoint["path"])
    ensure_waystation(waypoint_path, waypoint.get("name", "Waystation"))
    roots = [Path(p) for p in config.get("scan_territories", [])]
    roots.extend(Path(p) for p in config.get("document_roots", []))
    docs = {}
    warnings = []
    failures = []
    files_examined = 0
    for root in roots:
        if not root.exists():
            continue
        for path in iter_document_candidates(root):
            files_examined += 1
            discovery = read_candidate(path)
            if discovery.get("failure"):
                failures.append(discovery)
            elif discovery.get("warning"):
                warnings.append(discovery)
            elif discovery.get("document_id"):
                docs.setdefault(discovery["document_id"], []).append({
                    "path": str(path.resolve()),
                    "format": discovery["format"],
                    "metadata": discovery["metadata"],
                })
    outdir = waypoint_path / "cache" / "silk-road"
    index = {
        "type": "silk-road-document-index",
        "version": "v1",
        "documents": docs,
        "warnings": warnings,
        "failures": failures,
    }
    write_json(outdir / "document-index.json", index)
    write_json(outdir / "librarian-registry.json", legacy_librarian_registry(docs))
    return {
        "counts": {
            "files_examined": files_examined,
            "valid_documents": sum(len(v) for v in docs.values()),
            "warnings": len(warnings),
            "failures": len(failures),
        },
        "warnings": warnings,
        "failures": failures,
    }


def iter_document_candidates(root):
    docs_raw_roots = [p for p in Path(root).rglob("docs/raw") if p.is_dir()]
    if docs_raw_roots:
        for docs_raw in docs_raw_roots:
            for path in docs_raw.rglob("*"):
                if path.is_file() and path.suffix.lower() in (".json", ".md", ".markdown"):
                    yield path
        return
    for path in Path(root).rglob("*"):
        if path.is_file() and path.suffix.lower() in (".json", ".md", ".markdown"):
            yield path


def read_candidate(path):
    if path.suffix.lower() == ".json":
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            return {"failure": True, "path": str(path), "message": str(exc)}
        doc = data.get("document") if isinstance(data, dict) else None
        if not isinstance(doc, dict):
            return {"warning": True, "path": str(path), "message": "No document header."}
        doc_id = doc.get("document-id") or doc.get("document_id")
        if not doc_id:
            return {"warning": True, "path": str(path), "message": "Missing document-id."}
        metadata = dict(doc)
        metadata["document-id"] = doc_id
        return {"document_id": doc_id, "format": "json", "metadata": metadata}
    metadata = read_markdown_metadata(path)
    doc_id = metadata.get("document-id")
    if not doc_id:
        return {"warning": True, "path": str(path), "message": "Missing document-id."}
    return {"document_id": doc_id, "format": "md", "metadata": metadata}


def legacy_librarian_registry(docs):
    registry = {}
    for doc_id, locations in docs.items():
        metadata = locations[0]["metadata"]
        registry[doc_id] = {
            "id": doc_id,
            "title": metadata.get("title") or doc_id,
            "purpose": metadata.get("purpose") or metadata.get("description") or "",
            "tags": normalize_tags(metadata.get("tags")),
            "type": metadata.get("type") if isinstance(metadata.get("type"), dict) else {
                "logical": {"base": "file", "format": locations[0]["format"]}
            },
            "location": [{"path": loc["path"], "metadata": loc["metadata"]} for loc in locations],
        }
    return {
        "document": {
            "document-id": "silk-road.generated.librarian-registry",
            "title": "Silk Road Generated Librarian Registry",
        },
        "registry": registry,
    }


def normalize_tags(tags):
    if isinstance(tags, list):
        return tags
    if isinstance(tags, str):
        return tags.split()
    return []
