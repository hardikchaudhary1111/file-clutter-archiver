from types import SimpleNamespace

import pytest

import agent
import cleaner


def tool_call(file, reason="because", name="propose_archive"):
    """A pretend 'Claude wants to call a tool' block."""
    return SimpleNamespace(
        type="tool_use", id="t1", name=name, input={"file": file, "reason": reason}
    )

def text(words):
    return SimpleNamespace(type="text", text=words)


class FakeClient:
    """Stands in for Anthropic(). Returns scripted turns and never touches the network."""

    def __init__(self, blocks, *later_turns):
        self._turns = iter([blocks, *later_turns])
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **kwargs):
        return SimpleNamespace(content=next(self._turns, []))


@pytest.fixture
def folder(tmp_path, monkeypatch):
    monkeypatch.setattr(cleaner, "LOG_FILE", tmp_path / "log.jsonl")
    box = tmp_path / "box"
    box.mkdir()
    for name in ["notes.txt", "report.txt", "report_copy.txt", "setup.exe"]:
        (box / name).write_text(name)
    return box


def names(folder):
    return sorted(p.name for p in folder.iterdir() if p.is_file())


def run_agent(monkeypatch, folder, blocks, answers, extra_args=()):
    replies = iter(answers)
    monkeypatch.setattr("builtins.input", lambda _prompt: next(replies))
    monkeypatch.setattr("sys.argv", ["agent.py", str(folder), *extra_args])
    monkeypatch.setattr(agent, "Anthropic", lambda: FakeClient(blocks))
    agent.main()


def test_real_files_are_accepted(folder):
    client = FakeClient([tool_call("setup.exe"), tool_call("report_copy.txt")])
    files = [p["file"] for p in agent.get_proposals(client, folder)]
    assert files == ["setup.exe", "report_copy.txt"]


def test_invented_file_names_are_dropped(folder):
    client = FakeClient([tool_call("does_not_exist.txt")])
    assert agent.get_proposals(client, folder) == []


def test_path_tricks_are_dropped(folder):
    client = FakeClient([tool_call("..\\secret.txt"), tool_call("../secret.txt"), tool_call("sub/setup.exe")])
    assert agent.get_proposals(client, folder) == []


def test_other_tools_and_text_are_ignored(folder):
    client = FakeClient([text("hello"), tool_call("setup.exe", name="delete_everything")])
    assert agent.get_proposals(client, folder) == []


def test_claude_proposal_with_no_approval_moves_nothing(monkeypatch, folder):
    before = names(folder)
    run_agent(monkeypatch, folder, [tool_call("setup.exe")], ["n"])
    assert names(folder) == before


def test_quit_moves_nothing(monkeypatch, folder):
    before = names(folder)
    run_agent(monkeypatch, folder, [tool_call("setup.exe")], ["q"])
    assert names(folder) == before


def test_dry_run_never_asks_and_moves_nothing(monkeypatch, folder):
    before = names(folder)
    run_agent(monkeypatch, folder, [tool_call("setup.exe")], [], extra_args=["--dry-run"])
    assert names(folder) == before


def test_approved_proposal_moves_and_is_logged_as_claude(monkeypatch, folder, tmp_path):
    run_agent(monkeypatch, folder, [tool_call("setup.exe")], ["y"])
    assert "setup.exe" not in names(folder)
    assert '"source": "claude"' in (tmp_path / "log.jsonl").read_text()

def test_read_preview_refuses_names_outside_the_folder(folder):
    real = {p.name for p in folder.iterdir() if p.is_file()}
    assert agent.read_preview(folder, real, "../notes.txt") == "No such file."


def test_read_preview_handles_binary_files(folder):
    (folder / "data.bin").write_bytes(b"ab\x00cd")
    real = {p.name for p in folder.iterdir() if p.is_file()}
    assert "binary" in agent.read_preview(folder, real, "data.bin")


def test_loop_reads_then_proposes(folder):
    client = FakeClient(
        [tool_call("report_copy.txt", name="read_preview")],
        [tool_call("report_copy.txt")],
    )
    files = [p["file"] for p in agent.get_proposals(client, folder)]
    assert files == ["report_copy.txt"]


def test_loop_stops_at_the_turn_cap(folder):
    client = FakeClient(
        [tool_call("setup.exe")],
        [tool_call("report_copy.txt")],
        [tool_call("notes.txt")],
    )
    files = [p["file"] for p in agent.get_proposals(client, folder, max_turns=2)]
    assert files == ["setup.exe", "report_copy.txt"]