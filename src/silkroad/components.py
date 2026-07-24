from pathlib import Path


def ensure_default_components(execroot):
    base = Path(execroot) / ".silkroad" / "components"
    base.mkdir(parents=True, exist_ok=True)
    component = base / "document_indexer.py"
    if not component.exists():
        component.write_text("# Silk Road v2 keeps Sherpa behavior in package modules.\n", encoding="utf-8")
    return base
