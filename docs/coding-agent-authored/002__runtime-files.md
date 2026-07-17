# Silk Road Runtime Files

Generated: 2026-07-14

## Project Runtime Directory

Silk Road creates `.silkroad/` under the execution root.

Expected files:

- `.silkroad/config.json` - machine-local Silk Road configuration.
- `.silkroad/state.json` - persistent Sherpa status.
- `.silkroad/components/document_indexer.py` - editable local Sherpa component source.
- `.silkroad/logs/events.jsonl` - append-only operational event log.

## Waystation Output

The default waystation is `F:/lion/code/waystation` when that marker exists.

Silk Road writes:

- `cache/silk-road/document-index.json`
- `cache/silk-road/librarian-registry.json`
- `cache/silk-road/last-run.json`

The index is authoritative for Silk Road's observed document locations. The Librarian registry is a compatibility export.

## Component Contract

Editable Sherpa component source is executed with a local variable named `D`.

`D` contains:

- `config`
- `state`
- `api`

The component should set:

- `D['result']`

The `api` object exposes simple helpers for this first mission:

- `scan_documents(config, state)`

This keeps editable code small while leaving filesystem, JSON parsing, reconciliation, and Librarian export in normal Silk Road modules.
