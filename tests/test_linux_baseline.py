"""The Linux baseline cannot silently accept new output bytes or inventory."""
from __future__ import annotations

from pathlib import Path

import pytest

from tools.verify_linux import digest
from tools.verify_linux_baseline import check_outputs, check_replay_tree


@pytest.mark.parametrize("observed", [{"a": "changed"}, {}, {"a": "fixed", "b": "extra"}])
def test_baseline_rejects_changed_missing_and_extra_outputs(observed: dict[str, str]) -> None:
    with pytest.raises(RuntimeError, match="Linux baseline"):
        check_outputs({"a": "fixed"}, observed)


def test_baseline_accepts_only_exact_output_bytes() -> None:
    check_outputs({"a": "fixed"}, {"a": "fixed"})


@pytest.mark.parametrize("change", ["extra", "missing", "source", "output"])
def test_replay_tree_rejects_undeclared_changes(tmp_path: Path, change: str) -> None:
    source = tmp_path / "producer.py"
    output = tmp_path / "result.json"
    source.write_text("fixed source")
    output.write_text("historical result")
    original = {p.name: digest(p) for p in (source, output)}
    if change == "extra":
        (tmp_path / "unexpected.json").write_text("undeclared")
    elif change == "missing":
        output.unlink()
    elif change == "source":
        source.write_text("altered producer")
    else:
        output.write_text("new result checked separately by the exact byte gate")
        check_replay_tree(tmp_path, original, {output.name})
        return
    with pytest.raises(RuntimeError, match="Linux replay"):
        check_replay_tree(tmp_path, original, {output.name})


def test_linux_layout_cannot_create_a_publication_identity() -> None:
    import subprocess
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "-I", "-B", str(root / "tools/build_dark_medium_response_atlas_documents.py"),
         "--linux-layout"], capture_output=True, text=True, check=False,
    )
    assert result.returncode == 2
    assert "--linux-layout requires --no-identity" in result.stderr
