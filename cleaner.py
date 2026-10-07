"""Folder cleaner: scan -> plan -> ask approval -> act -> log."""
import argparse
import hashlib
import json
import re
import shutil
from datetime import datetime
from pathlib import Path

LOG_FILE = Path("cleaner_log.jsonl")
COPY_PATTERN = re.compile(r"(\(\d+\)|[ _-]copy)\.[^.]+$", re.IGNORECASE)
INSTALLERS = {".exe", ".msi"}


def file_hash(path):
    """Return a fingerprint of a file's contents."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def build_plan(folder):
    """Look at the files and propose actions. Changes nothing."""
    plan = []
    seen = {}
    for path in sorted(p for p in folder.iterdir() if p.is_file()):
        digest = file_hash(path)
        if digest in seen:
            reason = f"duplicate of {seen[digest]}"
        else:
            seen[digest] = path.name
            if COPY_PATTERN.search(path.name):
                reason = "name looks like a copy"
            elif path.suffix.lower() in INSTALLERS:
                reason = "installer file"
            else:
                continue
        plan.append({"file": path.name, "reason": reason})
    return plan


def ask(item):
    """The approval gate: nothing proceeds without an answer."""
    while True:
        answer = input(
            f"Archive {item['file']}? ({item['reason']}) [y/n/a=all/q=quit] "
        ).strip().lower()
        if answer in {"y", "n", "a", "q"}:
            return answer


def archive(folder, name):
    """Move a file into .archive (recoverable), never delete it."""
    archive_dir = folder / ".archive"
    archive_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = archive_dir / f"{stamp}_{name}"
    shutil.move(str(folder / name), str(target))
    return target


def log(entry):
    """Append one line to the log file recording what happened."""
    entry["time"] = datetime.now().isoformat(timespec="seconds")
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Archive clutter, with approval.")
    parser.add_argument("folder", help="folder to clean")
    parser.add_argument("--dry-run", action="store_true", help="show the plan only")
    args = parser.parse_args()

    folder = Path(args.folder).resolve()
    if not folder.is_dir():
        raise SystemExit(f"Not a folder: {folder}")

    plan = build_plan(folder)
    if not plan:
        print("Nothing to clean.")
        return

    print(f"Proposed {len(plan)} action(s) in {folder}:")
    for item in plan:
        print(f"  - {item['file']}: {item['reason']}")
    if args.dry_run:
        print("Dry run: no files were touched.")
        return

    approve_all = False
    for item in plan:
        answer = "y" if approve_all else ask(item)
        if answer == "q":
            print("Stopped.")
            break
        if answer == "a":
            approve_all = True
            answer = "y"
        if answer == "y":
            target = archive(folder, item["file"])
            log({"action": "archived", "file": item["file"], "to": str(target)})
            print("  archived", item["file"])
        else:
            log({"action": "skipped", "file": item["file"]})
            print("  skipped", item["file"])


if __name__ == "__main__":
    main()