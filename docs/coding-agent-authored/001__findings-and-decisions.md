# Silk Road Findings and Decisions

Generated: 2026-07-14

## Findings

- The Silk Road repository was a small shell with `README.md`, `docs/raw/`, and an empty `src/silkroad`.
- The surviving waystation at `F:/lion/code/waystation` has a clear marker file named `waystation.json`.
- That waystation uses:
  - `signposts/` for neighboring waystations
  - `cache/` for discovered knowledge
  - `bazaar/` for requests and fulfilled items
- Existing document discovery data already lives under `cache/discovered-documents/`.
- Librarian2 registries are JSON documents with a top-level `document` object and a flat `registry` dictionary.
- Librarian entries are keyed by resource id and include `id`, `title`, `purpose`, `location`, `tags`, and `type`.
- Lion's project structure guide confirms that `docs/raw/` is an append-oriented source stream and should be preserved as source material.
- Candidate default territories on this machine are `C:/lion/github` and `C:/lion/code`.

## Decisions

- Version one is a concrete Silk Road machine, not a generalized framework.
- The first implemented Sherpa is `document-indexer`.
- The app uses `lionscliapp` and provides a `silk-road` command.
- The default command opens a Tkinter control panel.
- `silk-road scan` runs the document-indexing Sherpa once from the CLI.
- Persistent Silk Road state lives in `.silkroad/` under the execution root.
- Waystation output defaults to the surviving waystation when present: `F:/lion/code/waystation`.
- The indexer scans only configured territories and explicit document roots.
- Version one indexes JSON documents only when they contain a top-level `document.document-id`.
- The index is pointer-based: document identities can have multiple known filesystem locations.
- Silk Road writes its own index and also writes a Librarian2-compatible registry.
- Sherpa implementation is local and inspectable. The default document-indexer source is saved into `.silkroad/components/document_indexer.py` and executed from there, so it can be edited at runtime.

## Important Boundaries

- Component source execution is local filesystem execution, not remote loading.
- Component code receives a small API dictionary and returns structured results through `D['result']`.
- GUI work stays on the Tk thread. Sherpa work runs on a worker thread and reports back through a queue.
- The GUI is intentionally utilitarian: observe waystations, Sherpas, status, run counts, warnings, failures, and output paths.
