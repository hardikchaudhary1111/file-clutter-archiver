# File Clutter Archiver

https://github.com/user-attachments/assets/8b2f43d3-3dde-41ea-85d9-8b250225ee27

A command-line tool that finds clutter in a folder and archives it **only after you approve each file**. It has two modes: fixed rules (version 1) and an AI agent that uses Claude (version 2). In both, the same approval gate decides what actually moves.

It never deletes anything. Approved files move to an `.archive` folder, so every action can be undone.

## Version 1: rules (`cleaner.py`)

Fingerprints every file and proposes duplicates (same contents), copy-style names like `report (1).pdf`, and installers (`.exe`, `.msi`).

```bash
python cleaner.py path/to/folder --dry-run   # preview only
python cleaner.py path/to/folder             # asks before each move
```

## Version 2: Claude as the decision-maker (`agent.py`)

Claude gets two tools and runs in a loop (capped at 6 turns):

- `read_preview`: read-only peek at the first 300 bytes of a file in the folder.
- `propose_archive`: records a suggestion. It cannot move or delete anything.

Claude's proposals go through the same approval prompt as version 1. Only your code, after your typed `y`, moves files.

```bash
python agent.py path/to/folder --dry-run   # Claude proposes, nothing moves
python agent.py path/to/folder             # Claude proposes, you approve each one
```

Setup: `pip install -r requirements.txt`, then copy `.env.example` to `.env` and add your Anthropic API key. The key stays in `.env`, which is git-ignored. Each run makes real API calls, which cost a small amount.

## Safety design

- Every move needs a typed `y`. Anything else is refused and asked again.
- No delete anywhere: files move to `.archive` with a timestamp.
- Claude only proposes. Proposals for names not in the folder (invented names, `..\` paths, subfolders) are dropped.
- File names and contents are passed to Claude as data, with the system prompt telling it not to follow instructions found in them. This reduces prompt-injection risk but does not remove it, which is why Claude cannot act on its own.
- Every decision, including skips, is logged with who suggested it.

## Tests

```bash
python -m pytest -v
```

21 tests, none of which call the API. The agent tests use a fake client with scripted replies, including worst cases like invented file names and path tricks. Key checks: answering no, quitting, or `--dry-run` leaves every file where it was, and the loop stops at its turn cap.

## Design decisions

See [DECISIONS.md](DECISIONS.md).
