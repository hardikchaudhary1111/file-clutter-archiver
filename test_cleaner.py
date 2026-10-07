import pytest
import cleaner


@pytest.fixture
def folder(tmp_path, monkeypatch):
    """A fresh temporary folder for every test, so your real files are never touched."""
    monkeypatch.setattr(cleaner, "LOG_FILE", tmp_path / "log.jsonl")
    box = tmp_path / "box"
    box.mkdir()
    (box / "notes.txt").write_text("notes")
    (box / "report.txt").write_text("report")
    (box / "report_copy.txt").write_text("report")
    (box / "invoice (1).pdf").write_text("inv")
    (box / "setup.exe").write_text("exe")
    return box


def run_cleaner(monkeypatch, folder, answers, extra_args=()):
    """Run the whole program with pretend keyboard answers."""
    replies = iter(answers)
    monkeypatch.setattr("builtins.input", lambda _prompt: next(replies))
    monkeypatch.setattr("sys.argv", ["cleaner.py", str(folder), *extra_args])
    cleaner.main()


def names(folder):
    return sorted(p.name for p in folder.iterdir() if p.is_file())


def test_plan_flags_the_right_files(folder):
    flagged = [item["file"] for item in cleaner.build_plan(folder)]
    assert flagged == ["invoice (1).pdf", "report_copy.txt", "setup.exe"]


def test_original_is_not_flagged_as_duplicate(folder):
    flagged = [item["file"] for item in cleaner.build_plan(folder)]
    assert "report.txt" not in flagged


def test_building_the_plan_changes_nothing(folder):
    before = names(folder)
    cleaner.build_plan(folder)
    assert names(folder) == before


def test_archive_moves_and_keeps_contents(folder):
    target = cleaner.archive(folder, "setup.exe")
    assert "setup.exe" not in names(folder)
    assert target.read_text() == "exe"


def test_ask_rejects_bad_input_then_accepts(monkeypatch):
    replies = iter(["maybe", "", "y"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(replies))
    assert cleaner.ask({"file": "x", "reason": "y"}) == "y"


def test_saying_no_moves_nothing(monkeypatch, folder):
    before = names(folder)
    run_cleaner(monkeypatch, folder, ["n", "n", "n"])
    assert names(folder) == before


def test_quit_moves_nothing(monkeypatch, folder):
    before = names(folder)
    run_cleaner(monkeypatch, folder, ["q"])
    assert names(folder) == before


def test_yes_moves_only_approved_files(monkeypatch, folder):
    run_cleaner(monkeypatch, folder, ["y", "n", "y"])
    assert "invoice (1).pdf" not in names(folder)
    assert "setup.exe" not in names(folder)
    assert "report_copy.txt" in names(folder)
    assert (folder / ".archive").exists()


def test_dry_run_never_asks_and_moves_nothing(monkeypatch, folder):
    before = names(folder)
    run_cleaner(monkeypatch, folder, [], extra_args=["--dry-run"])
    assert names(folder) == before
    