```
title: Silk Road v2 — Waystation and Sherpa Control Panel
date: 2026-07-16
```

# Silk Road v2 — Waystation and Sherpa Control Panel

## Mission

Build the first deliberate version of **Silk Road** as a self-contained Python Tkinter application.

Silk Road supervises small filesystem workers called **Sherpas**. Sherpas are based at explicit folders called **Waystations**. They explore bounded portions of the filesystem, notice selected kinds of files and other Waystations, register discoveries, optionally collect copies, and keep persistent records of their journeys.

This is the **hard Silk Road**: a specific, coherent application for this use case. It should be internally modular, but it is not yet a generalized process runner, plugin framework, or replacement for Bproc.

The primary deliverable is a useful control panel through which the operator can:

* register and discover Waystations
* inspect the Sherpas based at each Waystation
* enable, disable, pause, resume, and dispatch Sherpas
* edit Sherpa specifications and local controls
* observe Sherpas while they are hiking
* control how aggressively Sherpas use the filesystem
* inspect discoveries, statistics, state, warnings, and journals

---

# 1. Core Concepts

## 1.1 Waystation

A Waystation is an explicit directory named `waystation`.

Examples:

```text
C:\lion\waystation
C:\lion\github\waystation
C:\lion\code\waystation
```

A Waystation is recognized by the presence of:

```text
waystation\waystation.json
```

A minimal `waystation.json` looks like:

```json
{
  "type": "waystation",
  "version": "v1",
  "name": "lion-github",
  "notes": "Created by Silk Road."
}
```

The Waystation is a base of operations. It owns local configuration, Sherpa encampments, observations, cached material, libraries, and signposts to other Waystations.

## 1.2 Sherpa

A Sherpa is a small, named filesystem worker based at a Waystation.

A Sherpa has:

* a portable specification
* local operational controls
* transient and persistent execution state
* cumulative statistics
* an optional journey journal
* one current journey at most

Sherpas operate incrementally. They do not scan an entire territory in one blocking run.

## 1.3 Journey

A journey is one bounded traversal undertaken by a Sherpa.

A journey has:

* a starting territory
* a navigation policy
* a queue of directories or locations still to inspect
* a record of locations already visited
* current progress
* discoveries
* warnings and errors
* a beginning and ending time

A journey may remain in progress over many application ticks. It may be paused and resumed.

## 1.4 Discovery

A discovery is something noticed by a Sherpa.

Initial discovery types are:

* another Waystation
* a Lion JSON Document
* a document using Lion’s annotated Markdown format
* a file matching a configured glob pattern

For each discovery type, the Sherpa may be configured to:

* notice it
* register it
* collect a copy
* record it in the journey journal

These actions are distinct.

## 1.5 Library

A Library stores registered document discoveries.

A Sherpa specification should normally refer to:

```json
"library": "waystation"
```

This means:

> Register discoveries in the Library belonging to whichever Waystation currently hosts this Sherpa.

The Sherpa specification should not need a hard-coded absolute Library path.

A Sherpa may alternatively be configured to use an explicit Library file, but the default is the hosting Waystation’s Library.

---

# 2. Waystation Filesystem Structure

Use the following initial structure:

```text
waystation/
    waystation.json

    bazaar/
        requests/
        offers/

    cache/

    signposts/

    libraries/
        library.jsonl

    sherpas/
        specifications/
            document-scout.json
            waypoint-scout.json

        control/
            document-scout.json
            waypoint-scout.json

        state/
            document-scout.json
            waypoint-scout.json

        statistics/
            document-scout.json
            waypoint-scout.json

        journals/
            document-scout/
            waypoint-scout/
```

## 2.1 `waystation.json`

Contains stable descriptive information about the Waystation.

Possible fields:

```json
{
  "type": "waystation",
  "version": "v1",
  "waystation_id": "lion-github",
  "name": "Lion GitHub",
  "notes": "Waystation for projects beneath C:/lion/github.",
  "created_at": "2026-07-16T18:00:00-07:00"
}
```

For v1, `waystation_id` may be the same as `name` in machine-friendly form.

## 2.2 `bazaar/`

Reserved for requests and offers of information.

Do not build a full Bazaar protocol in v1. Create and preserve the directories.

## 2.3 `cache/`

Stores collected or temporary material associated with the Waystation.

The cache is not assumed to be authoritative.

## 2.4 `signposts/`

Stores pointers to other known Waystations.

A signpost should be a small JSON file containing at least:

```json
{
  "type": "waystation-signpost",
  "version": "v1",
  "waystation_id": "lion-code",
  "path": "C:/lion/code/waystation",
  "last_observed_at": "2026-07-16T18:10:00-07:00"
}
```

## 2.5 `libraries/`

Contains the Waystation’s local Library.

For v1, use:

```text
libraries/library.jsonl
```

The existing Librarian project and its format must be inspected before finalizing the record format. Prefer compatibility with the existing Librarian format.

## 2.6 `sherpas/specifications/`

Contains portable descriptions of what Sherpas do.

These files should be transferable between Waystations without modification wherever practical.

## 2.7 `sherpas/control/`

Contains local operational choices for each Sherpa instance.

Examples:

* enabled or disabled
* paused or unpaused
* pace
* tick interval
* scheduling interval
* automatic journey start
* local overrides

## 2.8 `sherpas/state/`

Contains current operational state.

Examples:

* resting
* hiking
* paused
* trouble
* current directory
* pending navigation queue
* current journey ID
* last completed step
* last error
* next scheduled journey

State should allow an interrupted journey to resume where practical.

## 2.9 `sherpas/statistics/`

Contains cumulative and historical counts.

Examples:

* lifetime journeys
* completed journeys
* failed journeys
* files examined
* directories entered
* Waystations discovered
* documents noticed
* documents registered
* documents collected
* warnings encountered

Statistics must remain separate from current state.

## 2.10 `sherpas/journals/`

Contains human-readable or structured journey logs.

Each journey should produce a separate journal file when journaling is enabled.

---

# 3. Separation of Responsibilities

Keep these four categories separate.

## 3.1 Specification

The specification describes what kind of Sherpa this is.

It should be portable.

Example:

```json
{
  "type": "sherpa-specification",
  "version": "v1",
  "sherpa_id": "document-scout",
  "name": "Document Scout",

  "navigation": {
    "mode": "peer_directories",
    "peer_depth": 3
  },

  "noticing": {
    "waystations": {
      "enabled": true,
      "write_signpost": true
    },

    "lion_json_documents": {
      "enabled": true,
      "register": true,
      "collect": false,
      "collection_target": "waystation-cache"
    },

    "annotated_markdown_documents": {
      "enabled": true,
      "register": true,
      "collect": false,
      "collection_target": "waystation-cache"
    },

    "file_pattern": {
      "enabled": false,
      "pattern": "*.lsf",
      "register": false,
      "collect": false
    }
  },

  "library": {
    "target": "waystation"
  },

  "journal": {
    "enabled": true,
    "detail": "summary"
  }
}
```

## 3.2 Control

Control describes how this Sherpa instance is currently operated at this Waystation.

Example:

```json
{
  "type": "sherpa-control",
  "version": "v1",
  "sherpa_id": "document-scout",

  "enabled": true,
  "paused": false,

  "pace": {
    "preset": "walking",
    "work_budget_ms": 15,
    "tick_interval_ms": 250
  },

  "schedule": {
    "automatic": true,
    "journey_interval_seconds": 1800
  }
}
```

The named pace is for human readability. Explicit numbers remain authoritative.

## 3.3 State

State describes what the Sherpa is doing now.

Example:

```json
{
  "type": "sherpa-state",
  "version": "v1",
  "sherpa_id": "document-scout",

  "status": "hiking",
  "journey_id": "2026-07-16T18-15-00-document-scout",

  "started_at": "2026-07-16T18:15:00-07:00",
  "last_step_at": "2026-07-16T18:16:42-07:00",

  "current_directory": "C:/lion/github/tkmachina/docs",
  "directories_waiting": 84,
  "directories_visited": 122,
  "filesystem_entries_examined": 1844,

  "last_error": null,
  "next_journey_at": null
}
```

## 3.4 Statistics

Statistics describe what the Sherpa has accomplished over time.

Example:

```json
{
  "type": "sherpa-statistics",
  "version": "v1",
  "sherpa_id": "document-scout",

  "journeys_started": 14,
  "journeys_completed": 13,
  "journeys_failed": 0,
  "journeys_cancelled": 1,

  "directories_visited": 4290,
  "filesystem_entries_examined": 48114,

  "waystations_discovered": 3,
  "documents_noticed": 701,
  "documents_registered": 689,
  "documents_collected": 12,

  "warnings": 9
}
```

---

# 4. Sherpa Status Model

A Sherpa may be in one of these states:

## Disabled

The Sherpa is turned off.

It will not start a journey and will not resume an existing journey.

## Resting

The Sherpa is enabled but not currently on a journey.

It may be waiting for manual dispatch or its next scheduled journey.

## Hiking

The Sherpa is actively progressing through a journey in small time-budgeted steps.

## Paused

The current journey is preserved, but no work steps are taken.

The operator may resume it.

## Trouble

The Sherpa encountered an error that prevents safe progress.

The GUI should display the error and allow the operator to inspect, retry, abandon the journey, or disable the Sherpa.

## Finishing

Optional internal state used while writing final indexes, statistics, or journals after traversal ends.

The GUI may display this as “Returning to camp…” or similar.

---

# 5. Time-Budgeted Work

Sherpas must not process a whole directory tree in one blocking action.

Each active Sherpa receives:

* a `work_budget_ms`
* a `tick_interval_ms`

At each tick, the Sherpa performs filesystem work until the work budget expires, then yields.

Example presets:

```text
Cautious    5 ms
Walking    15 ms
Brisk      30 ms
Expedition 75 ms
```

These are initial defaults only.

The GUI should display both the friendly name and the actual number:

```text
Walking — 15 ms every 250 ms
```

The operator may directly edit the numeric values.

The pace presets should be configurable in the application’s settings.

Example global configuration:

```json
{
  "pace_presets": {
    "cautious": 5,
    "walking": 15,
    "brisk": 30,
    "expedition": 75
  },
  "default_tick_interval_ms": 250
}
```

Use a monotonic high-resolution clock to enforce the time budget.

A single slow filesystem call may exceed the budget. The system should tolerate this and yield immediately afterward.

The Tkinter event loop must remain responsive.

---

# 6. Navigation Modes

Each Sherpa specification selects one primary navigation mode.

## 6.1 Peer Directories

```text
Search N levels deep within peers of the Waystation.
```

The Waystation’s parent directory defines the peer territory.

Example:

```text
C:\lion\github\waystation
```

The peers are directories beneath:

```text
C:\lion\github
```

The Sherpa may search a configurable number of levels inside those peers.

Configuration:

```json
{
  "mode": "peer_directories",
  "peer_depth": 3
}
```

## 6.2 Ancestor Territory

```text
Go upward N levels from the Waystation, then search downward M levels.
```

Configuration:

```json
{
  "mode": "ancestor_territory",
  "levels_up": 2,
  "levels_down": 4
}
```

## 6.3 Specific Directory

Search one explicitly selected directory.

Configuration:

```json
{
  "mode": "specific_directory",
  "path": "C:/lion/documents",
  "depth": 5
}
```

The GUI must provide:

* Browse
* Open in file explorer
* validation of the selected path

## 6.4 Navigation Safety

All navigation must be bounded.

Support:

* maximum depth
* skip lists
* ignored directory names
* optional symbolic-link avoidance
* optional hidden-directory avoidance
* prevention of traversal loops
* inaccessible-directory warnings without terminating the journey

Do not scan entire drives by default.

---

# 7. Noticing and Actions

For each discovery type, represent these separately:

## Notice

Recognize and inspect the item.

## Register

Write a structured record into a Library.

## Collect

Copy the underlying file into a target location.

## Journal

Record the discovery in the journey log.

The GUI should make these relationships clear.

Example:

```text
[x] Lion JSON Documents
    [x] Register discoveries
        Destination: This Waystation’s Library
    [ ] Collect copies
        Destination: This Waystation’s Cache
    [x] Mention in journey journal
```

## 7.1 Other Waystations

When another valid Waystation is discovered:

* validate its `waystation.json`
* display it as discovered
* optionally add it to the application’s known Waystation list
* optionally write a signpost into the observing Waystation
* do not modify the discovered Waystation without an explicit operation

## 7.2 Lion JSON Documents

Inspect the existing Lion JSON document format and the Librarian project.

For v1:

* only register documents confidently recognized as valid
* record validation failures as warnings
* detect duplicate document IDs
* allow one document ID to have multiple known locations
* distinguish same-ID same-content from same-ID conflicting-content where possible

## 7.3 Annotated Markdown Documents

Inspect the existing Markdown annotation convention before implementing final parsing.

For v1, support only clearly established metadata.

Do not silently invent missing required identifiers.

## 7.4 Matching Files

Support glob patterns such as:

```text
*.lsf
project-*.json
**/*.md
```

Keep pattern handling bounded by the selected navigation territory.

---

# 8. Library Behavior

The default destination is:

```json
{
  "target": "waystation"
}
```

This resolves at runtime to the hosting Waystation’s Library.

The same Sherpa specification should therefore work unchanged in multiple Waystations.

Alternative target:

```json
{
  "target": "explicit",
  "path": "C:/lion/documents/librarian/library.jsonl"
}
```

The GUI should show:

```text
Discovery Library

(●) This Waystation’s Library
( ) Another Library file: [........................] [Browse] [Open]
( ) Do not register discoveries
```

The Library should record documents and their locations separately.

Conceptually:

```json
{
  "document_id": "DOC-123",
  "metadata": {
    "title": "Example"
  },
  "locations": [
    {
      "path": "C:/lion/github/project/docs/raw/example.json",
      "waystation_id": "lion-github",
      "content_hash": "..."
    }
  ]
}
```

The exact representation should follow the existing Librarian format where possible.

Updates must reconcile with existing records rather than blindly append duplicates.

---

# 9. Main GUI

Use a three-pane control-panel layout.

```text
┌─────────────────────┬──────────────────────┬───────────────────────────────┐
│ WAYSTATIONS         │ SHERPAS              │ SELECTED SHERPA               │
│                     │                      │                               │
│ Lion GitHub         │ [x] Document Scout   │ Identity and Status           │
│ Lion Code           │ [x] Waypoint Scout   │ Navigation                    │
│ Lion Documents      │ [ ] LSF Scout        │ Noticing                      │
│                     │                      │ Library and Collection        │
│                     │                      │ Journal                       │
│                     │                      │ Pace and Schedule             │
│                     │                      │ Current Journey               │
├─────────────────────┼──────────────────────┼───────────────────────────────┤
│ Add / Discover      │ New / Copy / Delete  │ Save / Reload / Run / Pause   │
└─────────────────────┴──────────────────────┴───────────────────────────────┘
```

## 9.1 Waystation Pane

Display:

* Waystation name
* path
* availability
* whether manually added or discovered
* number of Sherpas
* number currently hiking
* warnings

Actions:

* Add Waystation
* Remove from control panel
* Discover nearby Waystations
* Open Waystation folder
* Create new Waystation
* Refresh
* Validate structure

Removing a Waystation from the control panel must not delete its directory.

## 9.2 Sherpa Pane

List Sherpas for the selected Waystation.

Each row should include:

```text
[x] Document Scout        Hiking the mountains…
    C:\lion\github\tkMachina\docs
```

The checkbox controls `enabled`.

Use recognizable status text:

* Disabled
* Resting
* Hiking the mountains…
* Paused on the trail
* Returning to camp…
* Trouble

Also show a compact activity indicator.

Actions:

* New Sherpa
* Copy Sherpa
* Delete Sherpa
* Open specification JSON
* Reload files
* Run now
* Pause
* Resume
* Abandon journey

Deleting a Sherpa requires confirmation and should offer to retain journals and statistics.

## 9.3 Selected Sherpa Pane

Use clearly separated sections.

### Identity and Status

Show:

* name
* Sherpa ID
* hosting Waystation
* enabled
* current status
* last journey
* next journey
* last result

### Navigation

Provide the three radio-button navigation modes:

```text
(●) Search peers of this Waystation
    [ 3 ] levels deep
    [Open territory]

( ) Search from an ancestor
    Go up [ 2 ] levels
    Then down [ 4 ] levels
    [Open territory]

( ) Search a specific directory
    [ C:\................................. ] [Browse] [Open]
    [ 5 ] levels deep
```

### Noticing

Provide controls for:

* other Waystations
* Lion JSON Documents
* annotated Markdown Documents
* custom file pattern

For each supported document type, include registration, collection, and journaling options.

### Library

Provide:

```text
(●) This Waystation’s Library
( ) Another Library file
( ) Do not register discoveries
```

### Collection

Provide symbolic local targets:

* This Waystation’s Cache
* explicit directory
* do not collect

### Journal

Provide:

* enable journey journal
* summary or detailed level
* open journals directory
* view latest journal

### Pace

Provide:

```text
Pace: [Walking ▼]  [15] ms of work every [250] ms
```

Changing the friendly preset updates the work budget.

Changing the number directly should either set the preset to “Custom” or preserve the nearest label only as a display hint.

### Schedule

Provide:

* automatic journeys enabled
* journey interval
* next journey time
* manual run button

### Current Journey

While hiking, show:

* journey start
* elapsed time
* current directory
* queued directories
* directories visited
* filesystem entries examined
* discoveries
* registrations
* collections
* warnings
* most recent activity

Include:

* Pause
* Resume
* Stop after current step
* Abandon journey
* Open current directory

---

# 10. Application-Level Configuration

Store application settings outside individual Waystations.

Include:

* known Waystation paths
* manually added versus discovered status
* pace preset definitions
* default tick interval
* ignored directory names
* default navigation depth limits
* recent GUI selection
* window geometry
* logging level

Do not store Sherpa-specific operational facts only in the application settings. Those belong at the Waystation.

---

# 11. Processing Architecture

Tkinter must remain responsive.

Use a cooperative stepping model or a worker-thread model with strict communication boundaries.

Preferred conceptual flow:

```text
Tkinter scheduler
    ↓
dispatch due Sherpa step
    ↓
Sherpa performs work within time budget
    ↓
Sherpa returns events or observations
    ↓
main thread updates GUI and persists state
```

Do not manipulate Tkinter widgets from worker threads.

The system should support multiple Sherpas being enabled, but v1 may execute one filesystem work step at a time globally if that significantly simplifies safety and predictability.

If only one Sherpa step runs at a time:

* rotate fairly among hiking Sherpas
* do not let one Sherpa monopolize all ticks
* show queued activity clearly

---

# 12. Persistence and Atomicity

All important state must survive application restart.

Use atomic file replacement when writing JSON:

1. write a temporary file
2. flush and close it
3. replace the previous file

Do not leave partially written JSON files.

Persist state after meaningful progress, but avoid rewriting large files after every filesystem entry.

Possible checkpoint conditions:

* after a time interval
* after a number of steps
* after entering a new directory
* when pausing
* when closing
* when a journey finishes
* when an error occurs

Library writes should also be safe against interruption.

---

# 13. Journaling

When enabled, each journey gets a journal file.

Example:

```text
sherpas/journals/document-scout/
    2026-07-16T18-15-00.jsonl
```

Each record may include:

```json
{
  "at": "2026-07-16T18:16:22-07:00",
  "event": "document_registered",
  "path": "C:/lion/github/project/docs/raw/012-example.json",
  "document_id": "DOC-012"
}
```

The GUI should provide a human-readable summary of the latest journey even if the underlying journal is structured JSONL.

---

# 14. First Built-In Sherpas

Implement at least these two Sherpas.

## 14.1 Document Scout

Notices and registers:

* Lion JSON Documents
* supported annotated Markdown Documents
* optional configured patterns

## 14.2 Waystation Scout

Notices:

* valid Waystations
* their identity
* their location

It may:

* add discovered Waystations to the control panel
* write signposts at the hosting Waystation

These may share traversal machinery, but should remain visibly distinct Sherpas.

---

# 15. First-Version Boundaries

Do not implement these in v1:

* arbitrary Python `exec`
* unrestricted dynamic plugins
* remote execution
* network synchronization
* automatic two-way file synchronization
* automatic editing of discovered documents
* full Bazaar request-and-offer exchange
* complete distributed conflict resolution
* scanning entire drives by default
* making collected copies authoritative
* generalized Bproc compatibility

Create explicit extension notes for future work instead.

---

# 16. Project Structure

A reasonable starting decomposition is:

```text
silk_road/
    app.py
    main.py
    settings.py

    gui/
        main_window.py
        waystation_panel.py
        sherpa_list_panel.py
        sherpa_editor_panel.py
        journey_panel.py

    waystations/
        discovery.py
        validation.py
        storage.py
        signposts.py

    sherpas/
        definitions.py
        loader.py
        control.py
        state.py
        statistics.py
        scheduler.py
        journey.py
        traversal.py

    noticing/
        waystations.py
        lion_json.py
        markdown.py
        patterns.py

    librarian/
        adapter.py
        reconciliation.py

    persistence/
        json_files.py
        jsonl_files.py
        atomic_write.py

    models/
        records.py

    logs/

tests/
```

Revise this as needed, but preserve the conceptual separations.

---

# 17. Inspection Tasks Before Coding

Before finalizing formats:

1. Inspect the existing Librarian project.
2. Identify the actual Librarian record format.
3. Inspect examples of Lion JSON Documents.
4. Inspect the current Markdown annotation convention.
5. Inspect existing Waystation folders.
6. Locate the project-structure documentation in Lions Documents.
7. Record findings and implementation decisions in:

```text
docs/findings-and-decisions.md
```

Do not merely reproduce historical designs. Use them as evidence.

---

# 18. Acceptance Criteria

Silk Road v1 is successful when all of the following are true:

1. The application opens as a substantial three-pane Tkinter control panel.
2. The operator can manually add an existing Waystation.
3. The operator can create a new Waystation with the required folder structure.
4. Nearby Waystations can be discovered through bounded exploration.
5. Selecting a Waystation lists the Sherpas based there.
6. Each Sherpa has an enable checkbox in the list.
7. Selecting a Sherpa opens its full configuration panel.
8. Specifications, controls, state, and statistics are stored separately.
9. The same portable Sherpa specification can be used at different Waystations.
10. A Sherpa can be manually dispatched.
11. A Sherpa can remain visibly in a hiking state over time.
12. Work is performed in time-budgeted steps.
13. The GUI remains responsive during a journey.
14. A journey can be paused and resumed.
15. Current progress is displayed while hiking.
16. A Document Scout can discover and register supported documents.
17. A Waystation Scout can discover another Waystation.
18. Discoveries can be registered in the hosting Waystation’s Library without an absolute path in the Sherpa specification.
19. Current state survives application restart where practical.
20. Cumulative statistics remain separate from current state.
21. Errors are visible without crashing the whole application.
22. The operator can open relevant directories, JSON files, Libraries, and journals from the GUI.

The result should feel like an actual operations console for a small network of filesystem travelers—not a static list or a one-button scanner.

The Waystations should feel inhabited. The Sherpas should feel active, observable, and controllable. The system should be concrete enough to use now, while revealing the shapes that may later be extracted into a broader modular architecture.
