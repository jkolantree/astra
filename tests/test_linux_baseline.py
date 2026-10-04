"""The Linux baseline cannot silently accept new output bytes or inventory."""
from __future__ import annotations

import pytest

from tools.verify_linux_baseline import check_outputs


@pytest.mark.parametrize("observed", [{"a": "changed"}, {}, {"a": "fixed", "b": "extra"}])
def test_baseline_rejects_changed_missing_and_extra_outputs(observed: dict[str, str]) -> None:
    with pytest.raises(RuntimeError, match="Linux baseline"):
        check_outputs({"a": "fixed"}, observed)


def test_baseline_accepts_only_exact_output_bytes() -> None:
    check_outputs({"a": "fixed"}, {"a": "fixed"})


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
