# Silk Road

Silk Road is a filesystem-native control panel for small local workers called Sherpas.

The first working slice indexes Lion-style JSON documents under bounded project territories. It discovers JSON files with `document.document-id`, records their known filesystem locations at a waystation, and exports a Librarian2-compatible registry.

## Run

Install locally:

```powershell
python -m pip install -e .
```

Open the Tkinter control panel:

```powershell
silk-road
```

The control panel can:

- run the document-indexing Sherpa
- install, remove, refresh, and open waystations
- edit the local code used by the document-indexer Sherpa
- show Sherpa run logs and failure records
- open help windows for using Silk Road, Sherpas, and waystation structure

Run the document-indexing Sherpa once from the CLI:

```powershell
silk-road scan
```

Runtime state is stored in `.silkroad/`. Waystation output defaults to `F:/lion/code/waystation/cache/silk-road/` when the surviving waystation is present.
