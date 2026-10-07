# Design Decisions

## Nothing happens without approval
Every move needs a typed answer. The prompt only accepts `y`, `n`, `a` or `q` and repeats on anything else, so the program never guesses what the user meant. Tests check that `n`, `q` and `--dry-run` leave all files untouched.

## No delete, only archive
There is no delete anywhere in the code. Files move to `.archive` with a timestamp prefix, so any action can be undone and two files with the same name never overwrite each other.

## Dry run
`--dry-run` prints the plan and exits before the approval step, so the tool can be previewed with no risk.

## Everything is logged, including skips
`cleaner_log.jsonl` records each decision with a time. An audit trail that only recorded actions would hide what the user chose not to do.

## Duplicates are found by contents, not names
Files are fingerprinted with SHA-256, read in chunks so large files don't need to fit in memory. The first copy is kept and later copies are flagged.

## The plan is built separately from the action
`build_plan` only reads files and returns a list. Keeping it separate from `archive` makes it safe to test, and it means the thing that decides can later be swapped for an LLM without touching the safety logic.

## Known limitations
- Works on one folder at a time and ignores subfolders.
- "Copy" detection is name-based and will miss unusual naming.
- No undo command yet. Files are restored by moving them back by hand.
- The log is written next to where the tool is run.