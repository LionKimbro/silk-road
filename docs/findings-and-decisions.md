# Silk Road v2 Findings and Decisions

Generated: 2026-07-16

## Documents Read Before Implementation

- Lion's Dictionary for LLMs (`lions_dictionary_for_llms`)
- Lion's Python Programming Guidelines (2025) -- Simplified Edition
- Coding Style Card -- Globals
- Coding Style Card -- Function Arguments and Flags
- Coding Style Card -- Machines
- Coding Style Card -- Registers
- Coding Style Card -- Python Rules
- lionscliapp Reference Guide
- Lion's Tkinter Development Conventions
- TkVillage System Manual
- TkVillage System API Reference
- `docs/raw/010__rebuild-declaration.md`

## Evidence Findings

- The previous `src/silkroad` implementation had been removed. Tests and documentation from the earlier slice remained.
- The current Librarian project is `C:/lion/github/librarian2`, not `C:/lion/github/librarian`.
- Librarian2 registry files use a top-level `document` object and a flat `registry` dictionary.
- Librarian2 entries are keyed by resource id and commonly include `id`, `title`, `purpose`, `tags`, `type`, and `location`.
- Librarian2 file entries store filesystem pointers in `location`, usually as a list of objects with `path`.
- Existing Markdown document metadata is a leading fenced metadata block. `document-id` is the required identifier for confident discovery.
- Existing Waystations were found at `C:/lion/waystation`, `C:/lion/code/waystation`, and `C:/lion/github/waystation`.
- Existing Waystations are minimal: `waystation.json`, `bazaar/`, `cache/`, and `signposts/` exist, but v2 Sherpa folders are not yet present.
- Lion's compact project structure guide confirms the `src/`, `tests/`, `docs/raw/`, `zoo-project.json`, and `README.md` layout already used here.

## Implementation Decisions

- Silk Road v2 is implemented as a concrete operations console, not a general plugin or process-runner framework.
- Existing minimal Waystations are upgraded in place by creating missing folders, without deleting or rewriting unrelated content.
- Portable Sherpa specifications live under `sherpas/specifications/`; local operation lives separately under `control/`, `state/`, `statistics/`, and `journals/`.
- The first built-in Sherpas are `document-scout` and `waystation-scout`.
- Document registration writes the hosting Waystation Library at `libraries/library.jsonl`.
- A Librarian2-compatible registry export is also written to `libraries/librarian-registry.json` for compatibility with existing tooling.
- Library records are reconciled by document id and location path. Duplicate locations are not blindly appended.
- Journey work is cooperative and time-budgeted on the Tkinter main loop. v1 steps one Sherpa at a time globally for predictability.
- GUI callbacks post semantic actions into the app machine; they do not perform filesystem traversal directly.
- TkVillage is kept as an architectural reference for the v2 shape, while the first implementation uses a direct Tkinter shell to maintain compatibility with the existing test surface.
