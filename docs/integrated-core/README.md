# Integrated ASTRA core — development proposal

This is one repository-level core integration: existing SPPT/reservoir calculations feed typed transport, capture/reset, boundary response, discrete coupling memory, observation and archive interfaces. A synthetic end-to-end case joins them. It is not a new empirical planetary or quantum theory. SCM and WKI remain explicitly bounded mathematical research sections within the same source/test structure.

Start with [the model contract](model-contract.md), [scientific boundaries](scientific-boundaries.md), [all 93 scoped claims](claims.json), [claim/test mapping](claim-test-map.json) and [module scope](scope.json). The synthetic fixture is `data/integrated-core/integrated_case.json`. The eight bridge records are proposals only; their fifteen citation identities now have bounded source/version assessments in `source-references.json`; full-text, artifact and support gaps remain explicit, and calibration/empirical flags stay false.

Use `python src/integrated_case.py --case data/integrated-core/integrated_case.json --output NEW_REPORT.json` from the repository root. Existing output files are refused. `python scripts/run_scm_checks.py --output NEW_SCM_REPORT.json` and `python scripts/wki_check_algebra.py --output NEW_WKI_REPORT.json` run the bounded research checks. The new-edition proposal routes this fixture and SCM to the existing Python 3.12.10 environment, and WKI to the existing Python 3.12.14 environment with SymPy/mpmath; neither runtime route is admitted. Do not infer a full release gate from an isolated script pass.

The current published citation/release metadata still describes historical v1.0.7. Cite the exact future integration commit when available; do not claim that v1.0.7 validates these additions. No version/tag is selected by this proposal. The existing v1.0.8 candidate is already ancestral to main and remains unpromoted; it is not an unmerged branch.

Before a v-tag release, prepare and review an explicit successor core release/runtime/source-admission contract, exact asset list, citation/version metadata and reproducibility evidence. Current v* tag automation invokes the historical Windows contract. Do not bypass it or overwrite v1.0.7 authority by tagging main. Linux two-pass results for earlier sources are retained history, not results for this file set.

Authorship: Jacko T., with disclosed ChatGPT/Codex assistance. The exact file license map, preserved notices and outside-rights boundaries are in [licenses](licenses.md). The source-family labels Layers, Gamma, Xi, October, SCM and WKI identify scientific lineage; private conversation/intake filenames, raw audit records and approval messages are not included.

No new joint-wave result is claimed. The separate Superfluid–ASTRA analytical brief is deferred pending its own public-file and rights decision. See scope.json for every deferred module and the reason; absence is not refutation.

The [Linux and release migration proposal](migration-proposal.md) links the version-neutral new-edition source/runtime/Pages proposal and preserves the historical gate boundary. It grants no runtime or publication admission.

The version-neutral [manuscript and supplement drafts](../../manuscript/integrated-draft/README.md) assemble the reviewed scope and corrections. Their builder uses separate output/metadata paths and does not admit a release runtime.

The [distinct new-edition proposal](../../resources/integrated-edition-proposal/README.md) adds source-bound explanatory diagrams and an explicit fresh-output experiment. Its 61-output result does not replace the historical 57-output gate or failed Windows comparison.
