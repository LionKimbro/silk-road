```
source: https://chatgpt.com/c/6a567adc-fbcc-83e8-b137-280c178a7243
date: 2026-07-14
```

Codex, I have a special mission for you. You are going to create the first working version of a project called **Silk Road**.

I am going to provide substantial background material: earlier Silk Road ideas, conversations with Wing-Cat, the Battery Runner / Bproc project, project-structure documentation, existing waypoint examples, and the Librarian project. Treat these materials as history and evidence, not as inflexible specifications. Learn from them, but prefer a coherent working system over blindly preserving earlier designs.

## Big-picture concept

Silk Road is a persistent, self-contained Tkinter application that supervises small modular workers called **Sherpas**.

Sherpas travel through selected parts of the filesystem, discover and inspect files, perform narrowly defined tasks, and leave structured records at **waypoints**.

A waypoint is a recognizable filesystem location that serves as:

* a collection point for related information
* a base for Sherpas operating in that territory
* a place to store observations, indexes, state, logs, and configuration
* a location that other Silk Road components can discover and interact with

There may be multiple waypoints. Each waypoint may have its own Sherpas and its own territory.

The Tkinter application is the control panel for this running machine. It should let me observe what the system knows, what each Sherpa is doing, when it last ran, what it found, and whether anything has failed.

## Design philosophy

This is the **hard, specific Silk Road**, not yet a generalized framework.

Build a concrete machine for the immediate mission. Keep the internal design modular, but do not prematurely extract a universal plugin system or recreate Bproc.

The Silk Road may eventually be generalized into independently installable workers, but first we need to discover the correct shape by making one complete system work reliably.

Use simple, inspectable structures. Make state and authority obvious. Prefer files and SQLite where appropriate. Avoid unnecessary classes if the surrounding project conventions prefer functions, globals, and explicit structures.

## First mission

The first mission is to discover and index structured documents stored within my projects.

Likely territories include:

* `C:/lions/GitHub`
* `C:/lions/code`
* the Lions Documents project or document collection

Do not assume these paths are exactly correct. Inspect the filesystem and existing project material before committing them to configuration.

Many projects contain:

```text
docs/raw/
```

These folders contain documents that should be discoverable by Silk Road.

There is also a project called **Librarian**. Inspect it carefully. Determine:

* the Librarian file format
* its required fields
* how records are identified
* how existing JSON-based documents are represented
* whether Librarian itself should become the canonical index or whether Silk Road should generate data for it

For version one, only index documents whose metadata already exists in a supported JSON structure. Do not invent final Markdown or LSF metadata standards yet. You may document recommendations for those formats, but they are outside the first implementation.

## Required first vertical slice

Build one complete working path:

1. Silk Road starts as a Tkinter control-panel application.
2. Its configuration names one or more waypoint roots and scan territories.
3. A document-indexing Sherpa can be dispatched manually.
4. The Sherpa scans only configured, bounded territories.
5. It discovers supported documents beneath `docs/raw/` and any explicitly configured document roots.
6. It reads their existing JSON metadata.
7. It validates and records their document IDs.
8. It updates a local waypoint index and, where compatible, a Librarian-format index.
9. The GUI shows:

   * configured waypoints
   * Sherpas
   * current status
   * last-run time
   * next scheduled run
   * number of files examined
   * number of valid documents found
   * duplicate or conflicting document IDs
   * warnings and failures
10. The indexing Sherpa can run again and reconcile the new observation with the prior index rather than simply appending duplicates.

The first version should default to pointer-based indexing. Record where documents are located; do not automatically copy every document into central storage.

Design the data model so that one document identity can have multiple known filesystem locations. This will allow later replication, caching, archival storage, and target folders without redesigning the core model.

## Waypoint discovery

A waypoint should have a clear identifying marker or manifest.

Inspect existing waypoint examples before designing this marker. Reuse their structure where it is genuinely good.

Do not scan the entire filesystem looking for waypoints.

Waypoint discovery may inspect:

* explicitly configured paths
* nearby sibling directories
* parent directories up to a small configurable depth
* directories encountered naturally during a bounded Sherpa scan

Discovery must be bounded, visible, and configurable.

## Scheduling

Sherpas should support:

* manual dispatch
* enabled or disabled state
* configurable interval
* persistent last-run and next-run information
* a default interval somewhere between 20 and 60 minutes
* failure containment so one Sherpa does not bring down the application

The GUI must remain responsive while a Sherpa is working. Use an appropriate worker process or thread boundary, with results communicated safely back to Tkinter.

Make the scheduling and persistence semantics obvious. It should be clear what lives only in memory and what survives restart.

## Proposed internal modules

You may revise this decomposition after inspecting the existing code, but begin by thinking in terms of:

* application/control panel
* configuration
* waypoints
* Sherpa definitions
* scheduling and dispatch
* filesystem discovery
* document identification
* Librarian integration
* persistence
* reconciliation
* logs and status reporting

Sherpas should be modular inside Silk Road, but they do not yet need to be separately installable packages.

## Safety boundary

Do **not** implement arbitrary attached Python `exec` code in the first version.

Instead, design Sherpas as registered, named operations implemented in the Silk Road codebase. Record a future extension point for configurable or dynamically loaded behavior, but do not create a remote-code-execution mechanism or an unrestricted plugin loader during this mission.

## Inspection before implementation

Before writing the main system:

1. Inspect the supplied background material.
2. Inspect existing waypoint structures.
3. Locate and inspect the Librarian project.
4. Locate the project-structure document in Lions Documents, probably in `docs/raw/` and possibly numbered around 11 or 12.
5. Inspect the actual candidate directory roots.
6. Write a concise findings and decisions document inside the new project.

Resolve ambiguities yourself where possible. Record important assumptions. Do not stop merely because the historical materials disagree.

## Definition of success

Version one succeeds when I can launch Silk Road, see its waypoints and Sherpas, manually dispatch the document-indexing Sherpa, watch it scan a bounded territory, and inspect a persistent index of every supported document it found—including its document ID, metadata, known path, waypoint, timestamps, and conflict status.

It should feel like the first functioning segment of a larger road network: specific, understandable, inspectable, and alive.

This is vibe coding. Use judgment. Make something coherent and surprising—but make the magic rest on a small, reliable, working machine.
