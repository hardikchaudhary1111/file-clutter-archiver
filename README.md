# Folder Cleaner

A command-line tool that finds clutter in a folder and archives it **only after you approve each file**. Built as a small, tested example of a human-in-the-loop workflow: scan, plan, ask, act, log.

It never deletes anything. Approved files move to an `.archive` folder, so every action can be undone.

## How it works

1. **Scan:** fingerprints every file in the folder.
2. **Plan:** proposes files that are duplicates (same contents), have copy-style names like `report (1).pdf` or `report_copy.txt`, or are installers (`.exe`, `.msi`).
3. **Ask:** shows each proposal with its reason. You answer `y`, `n`, `a` (approve all) or `q` (quit). Anything else is refused and the question repeats.
4. **Act:** approved files move into `.archive` with a timestamp in the name.
5. **Log:** every decision, including skips, is appended to `cleaner_log.jsonl`.

## Usage

```bash
python cleaner.py path/to/folder --dry-run   # preview only, touches nothing
python cleaner.py path/to/folder             # asks before each move
```

To try it safely, make a throwaway folder with a few fake files and point the tool at that.

## Tests

```bash
pip install -r requirements.txt
python -m pytest -v
```

9 tests cover the plan, the approval prompt and the file moves. The key ones check that answering no, quitting, or running `--dry-run` leaves every file exactly where it was. Tests run in temporary folders, so real files are never touched.

## Design decisions

See [DECISIONS.md](DECISIONS.md).

## Status

Version 1 uses fixed rules to decide what looks like clutter. Next version: an LLM proposes what to archive, with the same approval gate in front of every action.