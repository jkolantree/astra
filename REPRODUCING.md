# Reproducing ASTRA publications

Choose the publication identity before choosing a command. The core and each supplemental line have different source archives, runtimes, builders, and claims. A successful check for one line does not verify another.

## Current core: SPPT/ASTRA v1.0.7

The canonical core environment is recorded in [RUNTIME.json](RUNTIME.json) and [.python-version](.python-version). It requires:

- CPython **3.12.10** exactly;
- the Git for Windows executable identity recorded in `RUNTIME.json`;
- dependencies installed from [requirements-lock.txt](requirements-lock.txt) with hashes;
- the recorded NumPy and SciPy OpenBLAS kernel conditions;
- the recorded Playwright Chromium revision for document generation; and
- the Matplotlib-distributed DejaVu and STIX font bytes named in the runtime record.

From Windows PowerShell:

```powershell
py -3.12 -c "import platform; assert platform.python_version() == '3.12.10', platform.python_version()"
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --require-hashes -r requirements-lock.txt
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe -I -B tools\verify.py --all --workers 4
```

The `-I -B` flags belong before the script path. The verifier checks the runtime, full test discovery, scientific replay, generated figures and documents, accessibility structure, privacy and rights boundaries, metadata, manifests, and release-integrity negative controls. Read its final classification: a diagnostic run under a different Python microrelease is not canonical publication evidence.

Use the [v1.0.7 tagged release](https://github.com/jkolantree/astra/releases/tag/v1.0.7) when the goal is to reproduce the published core. The default branch can contain later draft sources and maintenance work.

## Dark-Medium Response Atlas v0.1.0

Start from the [tagged Atlas release](https://github.com/jkolantree/astra/releases/tag/dark-medium-response-atlas-v0.1.0). Verify `SHA256SUMS`, extract the deterministic source archive into a new directory, and follow the package-local build and verification commands included in that archive. The versioned HTML, PDF, source archive, checksums, and detached release identity should agree byte for byte with the release record.

The Atlas builder is namespaced to its package. It does not rebuild or replace the SPPT/ASTRA v1.0.7 documents. Reproduction establishes the declared document and package contracts; it is not independent scientific validation of the paper’s proposed dark-sector models.

Future Atlas publication tags use two separate GitHub authorities. A dedicated GitHub App, installed only on this repository with repository **Administration: read**, supplies a short-lived token solely for checking that immutable releases are explicitly enabled. The ordinary Actions token retains **Contents: write** for release creation and verification; it is never used as a fallback for the settings check. Repository operators must configure the App client ID as `ATLAS_RELEASE_APP_CLIENT_ID` and its private key as `ATLAS_RELEASE_APP_PRIVATE_KEY`. Until both values exist, the namespaced Atlas workflow stops as `BLOCKED_EXTERNAL_CONFIGURATION` before publication. Before creating a future Atlas tag, its candidate must update and verify every version-bound workflow input and evidence gate, including the artifact controller, successor verifier, release title and notes path, asset names and output paths, and allowlist. The wildcard trigger does not weaken those fail-closed package checks.

## *Earth Is the Instrument* v0.3.0

Use the [versioned resource guide](resources/earth-is-the-instrument/v0.3.0/README.md) and [tagged release](https://github.com/jkolantree/astra/releases/tag/earth-instrument-framework-v0.3.0). That package retains its own source archive, checksum roster, environment disclosure, 90-check package gate, and known accessibility limits.

## Drafts and archives

Drafts may change on the default branch. For a fixed technical comparison, record the exact commit and file hash. Archived publications should be reproduced from their tagged release or versioned route, never by substituting current-branch files with similar names.

## Interpreting a result

- **Reproduced bytes** means the exercised builder produced the recorded artifact bytes under the declared environment.
- **Mechanically verified** means the named checker passed its stated contracts.
- **Environment limited** means a required runtime identity differed or was unavailable.
- **Not checked** means the relevant surface or gate was not exercised.

None of these phrases means peer review, empirical validation, novelty, or proof outside the stated mathematical assumptions. A harness failure invalidates the run; it does not make the underlying scientific claim true or false.

If reproduction fails, [open a reproducibility issue](https://github.com/jkolantree/astra/issues/new?template=reproducibility.yml) with the publication version, operating system, exact command, runtime versions, first failing output, and any changed files. Remove secrets and local personal paths before posting.
