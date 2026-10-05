# Linux research companion operational-source admission v1

The companion integration changed four files whose bytes are pinned by the
historical Linux research v1 source contract. CI correctly rejected the first
mismatch, `pyproject.toml`. Restoring that file alone would leave three failures.

This separate admission preserves `linux-research-v1.json` and
`tools/verify_linux_baseline.py` byte-for-byte. It identifies the full predecessor
record by SHA-256, restores the original project configuration, and replaces
exactly three operational source pins:

- `tools/build_pages_admission.py`: the reviewed bounded companion admission v2.
- `tools/check_pages_admission.py`: its exact inventory and integrity enforcement.
- `tools/check_repository.py`: the companion resource inventory, supplier-byte
  check, and explicit admission of the separate `ruff.toml` configuration.

The other 43 original source/configuration pins remain mandatory, including both
runtime records, the dependency lock, scientific generators, numerical methods,
the existing verification controllers, and release-integrity checks. The new
controller reads all 57 expected output hashes directly from the unchanged v1
record. It does not generate new expected values, skip hashes, retry with a weaker
profile, or claim that the extended tree satisfies v1's original source roster.

`ruff.toml` extends the original `pyproject.toml` and retains the same nine
exceptions for one exact supplier generator path. The supplier file remains
byte-pinned; no scientific source or dependency is edited to satisfy lint.
The additional operational inputs are independently listed and hashed in
`linux-companion-sources-v1.json`, including this document, controller, lint
configuration, workflow, tests, reproduction guide and license mapping.

CI explicitly invokes:

```sh
.venv/bin/python -I -B tools/verify_linux_companion.py --all --workers 4
```

The controller runs the unchanged runtime and full development checks, including
the clean-worktree and archive gates, before replay. It then reuses the original
two-pass isolated replay, copied-source/inventory checks, and exact v1 output
comparison. Reports identify this operational admission separately in
`tmp/linux-companion-verification.json`. The historical numerical comparison
remains separate and keeps its existing tolerances and documented v1 failure.

The historical command remains available on its original source tree. On the
companion tree it continues to reject the three changed operational files. This
admission does not authorize a release, merge, Pages dispatch or deployment.
Successful exact-head CI and the separately bound Pages publication approval
remain independent requirements. No runtime or historical output claim follows
from source-only validation in an incomplete local environment.
