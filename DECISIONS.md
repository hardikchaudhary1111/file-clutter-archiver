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


## Claude can propose, never act
The model has no tool that moves or deletes files. The only write path is `archive()`, called by the program after a human types `y`. Even a confused or manipulated model can only waste a prompt.

## Proposals are validated before they reach the human
Claude's file names are checked against the files actually in the folder. Invented names and path tricks are dropped, and tests feed those cases in directly.

## The loop has a turn cap
`MAX_TURNS` limits how many times the agent can go round, so a confused model cannot run up the bill.

## Tests use a fake model
`FakeClient` returns scripted replies, so the agent logic is tested quickly, repeatably and for free. Real model behaviour is checked by hand with `--dry-run`.

## Known limits of version 2
- The model sees only names, sizes and 300-byte previews, so it can miss subtle duplicates. Version 1's fingerprinting is more exact.
- Model answers vary between runs, and there is no automated evaluation of their quality yet.
- It works on one folder and ignores subfolders.


## Known limitations
- Works on one folder at a time and ignores subfolders.
- "Copy" detection is name-based and will miss unusual naming.
- No undo command yet. Files are restored by moving them back by hand.
- The log is written next to where the tool is run.