# Markdown Document Discovery

Generated: 2026-07-15

Silk Road's document-indexer recognizes Markdown files with a simple fenced metadata block at the very start of the file.

Example:

````text
```
document-id: example.document.v1
title: Example Document
tags: alpha beta gamma
type: style-card
```
````

Rules:

- Only the first 16 KiB are read for Markdown header discovery.
- The file must start with a triple-backtick fence.
- Simple `key: value` lines inside the opening fence are parsed.
- `tags` is interpreted as a whitespace-delimited list.
- `document-id` is required for the file to become an indexed document.
- Parsed metadata is stored on the Silk Road index entry under `metadata`.
- The Librarian export records Markdown files with logical format `md`.

The first configured Markdown root is:

```text
C:/lion/github/lions-documents/coding-guidelines/style-cards
```
