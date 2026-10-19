# Reproducing ASTRA publications

Choose the publication identity before choosing a command. The core and each supplemental line have different source archives, runtimes, builders, and claims. A successful check for one line does not verify another.

## Current source and website development

Ordinary pull requests and `main` CI validate the current committed source and
website without recreating historical scientific results:

```sh
python3 -I -B tools/bootstrap_linux.py --current-development
.venv/bin/python -I -B tools/verify_linux_companion.py --current-development
```

The bootstrap flag adds the separately hash-pinned SymPy 1.14.0 and mpmath 1.3.0
wheels in `requirements-development.txt`. It permits no source-build fallback and
does not change the historical dependency lock or runtime records. Current
verification checks these two installed versions as well as the historical lock.

This uses the declared Debian 13 runtime below and the real Git index and commit,
not an external audit inventory. Every indexed regular file must match its Git
blob; the complete source inventory must remain unchanged during checks. A clean
committed worktree is required for a pass. Historical receipts and the old root
manifest remain historical evidence; this mode does not reissue them for changed
source bytes or claim a release archive has been verified.

The suite includes historical identity checks, temporary Git fixtures and website
assembly controls. Only the two retained benchmark reproduction tests and
`ScopedClaimControls::test_CORE08_repeatable_explicit_run` are excluded because
they execute scientific replay. The existing historical S1 collection policy
remains. An empty test result, any skip, failure or error blocks the gate. The
Playwright-bundled Node runtime supplies JavaScript tests.

Maintained source also receives repository-content, Python lint/type, citation,
link, current Pages admission and existing-PDF checks. Exact archived draft files
remain in the full Git inventory but outside maintained-code lint. Results retain
each failed gate in a fresh `tmp/current-development-*/results.json`. Current
Pages admission binds the reviewed current website separately from immutable
release routes. Passing development checks does not publish anything, authorize a
new scientific claim, or establish full historical reproduction.

Tag workflows keep their existing historical release checks. Use the explicit
historical commands below when reproducing their named contracts; there is no
automatic fallback from a failed historical check to current development.

## Retained local successor diagnostics

The local integration successor uses an external, digest-pinned schema-2 inventory.
It anchors the preserved 627-file snapshot and declares every changed or added file;
it does not update historical admission records or `MANIFEST.sha256`.

On the Windows reference runtime, use the existing companion entry point:

```text
python -I -B -X utf8 tools/verify_linux_companion.py --profile local-successor --successor-contract <external-contract.json> --successor-contract-sha256 <reviewed-sha256> --development --work-directory <new-external-directory>
```

The eight reported gates cover runtime, the reviewed root test suite,
maintained Python lint, source types, citation metadata, maintained Markdown links,
the retained external-link observation record, and inspection of existing PDFs.
All 42 root test files are accounted for: the existing historical S1 collection
exclusion is preserved, and the other 41 files run with explicit exclusions for
17 functions that create commits, run scientific replay, or assemble a real site.
Parameterized functions may account for more than 17 deselected cases. The exact
selection and reasons are reported with each result. Safe historical-identity
tests remain included and can fail when the snapshot lacks their committed
history or publication admission; those failures do not become passes here.
Some tests exercise mocked build/replay controllers; no real artifact build or
scientific replay is invoked. External links are not contacted. Scratch output
must be outside the source tree, in a fresh directory.

When Windows cannot create the real symbolic-link fixtures, the same entry point
can run the entire selected test suite on a provisioned WSL Linux host. Add
`--wsl-test-distribution Ubuntu --wsl-test-python <absolute-native-python>` and
`--wsl-test-work-directory <fresh-native-directory>`. The interpreter must be
CPython 3.12.10 with every locked dependency version available. The host must also
supply Git, PowerShell for the workflow controls, and Pandoc for in-memory source
parsing. Provisioning these tools is separate from running the entry point.

The adapter verifies the helper identity before import and the complete source
inventory before and after testing. It uses native Linux scratch files and the
same explicit test targets and deferrals; it does not substitute mocks for the
real symbolic links. The two existing browser-layout tests run on Windows, using
its installed Chromium, and are excluded only from the Linux portion. Pure
JavaScript tests use the existing Playwright Node executable. Both portions must
report positive counts and zero failures, errors, or skips for the combined test
gate to pass. A new unreviewed test file also blocks the declared scope.
Windows reference-runtime and other development checks still run on Windows.
The host report distinguishes this functional test environment
from the canonical Debian environment and from scientific replay admission.

Pages builder tests use complete exact-roster fixtures. The production default
still rejects unadmitted documentation and changed bytes. Passing these tests
does not admit the local reading-room additions for publication.

The 88 retained local-only draft files remain byte-identical to the preserved
snapshot. They are historical inputs, not maintained or executed code in this
profile. Their whole-tree lint findings remain separate diagnostics; the Ruff
configuration and historical suite are unchanged. This scope grants no source,
runtime, Pages, scientific, or publication admission. A local development pass is
not a full repository or release pass. Linux identity, the complete applicable
suite, committed successor identity, clean/archive checks, builds, and replay
remain separate requirements. Repository-specific Git helpers reject a plain
nested snapshot instead of discovering its enclosing repository.

## Linux runtime and historical reproduction

The Linux runtime is defined by [RUNTIME-linux.json](RUNTIME-linux.json). The supported host
is Debian 13 x86-64 with glibc 2.41 and AVX2/FMA3. The local bootstrap downloads
hash-pinned Astral CPython 3.12.10 and Debian Git 2.47.3 archives into ignored `tmp/`,
downloads hash-pinned Microsoft PowerShell 7.5.4 for the workflow guard tests,
creates `.venv`, installs the existing hash-locked dependencies, and installs the
Playwright-pinned Chromium. It does not change host packages or security settings.
The host must already supply `python3` (3.12 or later), `dpkg-deb`, Chromium's
Linux shared libraries, and Debian's `fonts-liberation` package for the SVG cover's
Arial-compatible fallback. CI declares these prerequisites explicitly. The cover's
measured label-clearance test remains unchanged; missing fallback fonts must not be
worked around by relaxing that test.

```sh
python3 -I -B tools/bootstrap_linux.py
.venv/bin/python -I -B tools/verify.py --runtime-only
.venv/bin/python -I -B tools/verify_linux_companion.py --all --workers 4
```

The Linux verifier checks the Python executable and shared-library hashes, exact
Git executable, lockfile, installed distribution versions, numerical-library hashes,
Haswell single-thread execution, CPU-feature restrictions, font bytes, Chromium
revision/version and headless executable, plus the test-shell executable and version. It uses repository-local browser and tool
paths rather than the shell's default Python or Git. No credentials are needed.
Hash pins identify the retrieved upstream archives; they are not a claim of an
independent signature audit. Host distribution and libc are checked, but the entire
OS image and all browser-linked system-library bytes are not yet frozen.

The separately versioned [Linux research v1 baseline](evidence/linux-research-v1.md)
fixes the existing experimental methods, fresh Linux refits, four-worker execution,
and all 57 expected output hashes in `evidence/linux-research-v1.json`. The baseline
controller never updates expected hashes. It requires two matching builds and an
exact match to that versioned record. The Atlas uses an opt-in print-only Linux
layout; historical HTML, CSS, PDFs and publication identity remain unchanged.

The companion branch uses a separate [operational-source admission](evidence/linux-companion-sources-v1.md)
for exactly three reviewed Pages/repository helpers and the additional verification
files. It preserves the original baseline record and controller, restores the
original `pyproject.toml`, and inherits all runtime, scientific and 57 output pins.
The explicit historical command invokes `verify_linux_companion.py` without
`--current-development`; it never falls back after a v1 failure. The historical v1 command remains strict and rejects this extended tree.

The test suite and repository, lint, type, citation, link, PDF and manifest gates run
before replay. `--all` builds scientific outputs and Atlas documents twice in a
fresh ignored copy. Consecutive Linux bytes must agree. For historical equivalence, scientific JSON/CSV
values must also agree with the historical outputs at relative and absolute tolerance
1e-12 (tighter than the Draft benchmark's 1e-11 algebra gate); integer counts,
classification outcomes, keys and identities remain exact. Rendered byte differences
are reported separately and never treated as proof of scientific equivalence.
The strict historical route remains `.venv/bin/python -I -B tools/verify.py --all
--workers 4`; a failed historical comparison remains a failed gate. The separate
Linux baseline route records that historical failure explicitly in
`tmp/linux-baseline-verification.json` while judging Linux bytes against Linux v1.
A Linux baseline pass is not a Windows equivalence claim. The companion controller
writes its separately identified report to `tmp/linux-companion-verification.json`.

The Draft benchmark has a separate Linux byte fixture in
[evidence/linux-benchmark-results.json](evidence/linux-benchmark-results.json),
checked both against a fresh Linux evaluation and the original scientific values.
The Linux suite explicitly deselects only the original Windows byte-equality test
`test_retained_evaluation_reproduces_with_frozen_sources`, whose source is itself
frozen. Its Linux replacement runs the same frozen-input gate, exact Linux byte
comparison, all original outcome assertions, and scientific equivalence. Every
other collected test remains admitted. No historical result or test is replaced. The current core manuscript is an unpromoted
source revision; its release-bound reading copies stay frozen. Atlas replay omits
release-identity generation. Linux replay does **not** authorize publication or
assert equality with historical Windows PDFs/figures. A future release needs a new
publication identity and a reviewed Linux artifact baseline.

The migration review and remaining blockers are recorded in
[evidence/linux-migration.md](evidence/linux-migration.md).

## Historical Windows core: SPPT/ASTRA v1.0.7

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

### Nonpublishing authority check for repository operators

The [Atlas release authority preflight](.github/workflows/atlas-release-preflight.yml) can be manually dispatched from `main` in `jkolantree/astra`, repository ID `1319077150`. It takes no inputs, uses **Contents: read**, and calls the same immutable-settings guard as publication. The App token is restricted to this repository and **Administration: read**. Token creation and revocation are handled by the pinned GitHub action; the settings check only reads the repository setting. The workflow contains no tag, release, asset, or repository-setting mutation step.

If the configuration names are absent, the owner must complete this separately authorized checklist:

1. Register a dedicated GitHub App with repository **Administration: read** and no additional requested permissions or webhooks. GitHub supplies the mandatory metadata access.
2. Install that App for **Only select repositories**, selecting only `jkolantree/astra`.
3. Store the App client ID in the repository Actions variable `ATLAS_RELEASE_APP_CLIENT_ID`.
4. Generate the App private key and store it directly in the repository Actions secret `ATLAS_RELEASE_APP_PRIVATE_KEY` using GitHub's secure settings interface. Keep the key out of chat, source files, logs, reports, and artifacts.
5. In Actions, select **Atlas release authority preflight**, choose **Run workflow** on `main`, and inspect the run summary and settings step. Do not create a tag or rerun the historical publication workflow to test authority.

These steps follow [GitHub's App authentication guidance](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/making-authenticated-api-requests-with-a-github-app-in-a-github-actions-workflow) and the [immutable-settings API permission contract](https://docs.github.com/en/rest/repos/repos#check-if-immutable-releases-are-enabled-for-a-repository). Creating or installing the App and changing its configuration require separate owner authorization. If the guard reports disabled immutability, any settings change also requires separate authorization; the preflight cannot enable it.

The summary distinguishes configuration presence, token creation, and the settings guard result. Only a successful settings step establishes authenticated settings access and literal Boolean `enabled: true`. Configuration names alone and mocked tests do not establish operational readiness. Actual publication remains **UNEXERCISED**, even after a successful preflight. The existing controller accepts only v0.1.0, whose published release already exists; a future version requires the explicit version-bound preparation above and fresh publication authorization. A green preflight does not authorize or exercise publication.

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
