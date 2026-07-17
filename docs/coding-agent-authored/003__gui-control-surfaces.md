# Silk Road GUI Control Surfaces

Generated: 2026-07-15

## Help Windows

The Tkinter GUI has a Help menu with three separate windows:

- Using Silk Road
- Sherpas
- Waystation Structure

These are ordinary text windows intended to grow as the program becomes more capable.

## Waystation Controls

The Waystations panel supports:

- Install
- Remove
- Open
- Refresh

Install creates or reuses the selected folder as the waystation itself. It does not create a nested waystation folder. It ensures `waystation.json`, `signposts/`, `cache/`, and `bazaar/` directly inside that folder, and persists the enabled waystation record into `.silkroad/config.json`.

Remove disables the selected waystation in `.silkroad/config.json` rather than deleting filesystem data.

Open asks the operating system to open the selected waystation folder using the normal shell behavior.

## Sherpa Controls

The Sherpas panel supports:

- Run
- Edit Code
- Interval
- Logs
- Failures

Edit Code opens the exact component file configured for the selected Sherpa. Saving writes the source file used by the next Sherpa run.

Interval sets how often the selected Sherpa should run. The value is saved in `.silkroad/config.json` as seconds and the next scheduled run is recalculated immediately.

Logs opens `.silkroad/logs/events.jsonl`.

Failures shows persistent `last_failure` values plus malformed document records from each configured waystation's `cache/silk-road/malformed.json`.
