# ASTRA Sector-Complete Instrument Module v0.1.0-alpha.1

This is a namespaced GitHub prerelease research preview. It is not
peer-reviewed, is not ASTRA v0.3.2, does not supersede SPPT/ASTRA v1.0.6 or
*Earth Is the Instrument* v0.3.0, and makes no empirical dark-matter,
planetary-evolution, or hidden-sector claim.

## Contents and reproduction

The release contains the typed instrument schema, original source module,
tests, synthetic data, generated figures, source reading edition, claim/source
ledgers, and verification records. Reproduce the benchmark with:

```text
python scripts/run_sector_complete_benchmark.py
python -m pytest -q
```

The release replay used the frozen CPython 3.12.10 runtime and the locked
NumPy 2.3.5, SciPy 1.18.0, Matplotlib 3.11.1, pytest 9.1.1, and jsonschema
3.2.0 environment.

## Tests actually executed

- Focused resource and integration tests: 34 passed.
- Complete repository suite: 245 passed, 2 skipped.
- Repository contract: 171 public files passed.
- Root manifest verification and `git diff --check`: passed.
- Two deterministic benchmark replays: identical frozen text-output hashes.
- Ruff and mypy checks: passed for the candidate module.

The PNG figures are generated outputs. The supplied PDF/DOCX review inputs are
not release assets; no PDF visual or accessibility result is claimed here.

## Scientific limits

The benchmark is synthetic and candidate-set dependent. It demonstrates an
identifiability distinction under a frozen four-generator model; it is not an
experiment, blinded validation, a global p-value, or proof of a physical hidden
sector. Amaral's levitated-magnet result is retained as a narrow model-specific
B-L null search; Ji's record is magnetometry; Tian's item is an accepted
model-dependent interaction-bound record. None is a dark-matter detection or
an SPPT transport edge.

## Rights and provenance

Original code, scripts, tests, and schemas are authorized under MIT. Original
documentation, diagrams, synthetic data, and generated results are authorized
under CC BY 4.0 to the extent the author holds the relevant rights. External
articles, facts, metadata, dependencies, fonts, and raw experimental datasets
remain under their own terms and are not relicensed. ChatGPT/OpenAI assistance
is credited as provenance and drafting assistance, not authorship, endorsement,
peer review, or evidence.
