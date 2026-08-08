# ASTRA Sector-Complete Instrument Module v0.1.0-alpha.1

**Status:** public namespaced GitHub alpha research preview; synthetic methods
only. This
namespaced resource is not ASTRA v0.3.2, does not modify SPPT/ASTRA v1.0.6 or
*Earth Is the Instrument* v0.3.0, and has no GitHub Pages, Zenodo, or DOI
publication.

This package implements the next local milestone proposed in the supplied methods audit:

1. correct the observation equation;
2. define a typed transduction schema;
3. add sector-coverage and identifiability tests;
4. build a frozen four-generator benchmark: reflect, absorb, local transmit, string transmit;
5. require local observations to report their absorb/string equivalence;
6. test whether string/environment/interface observables resolve the equivalence;
7. include broken-duality, detector-noise, finite-boundary, and out-of-set model-mismatch controls;
8. keep all dark-matter interpretations `proposed_only`.

The benchmark is not a simulation of the duality-defect paper. It is an intentionally small calibration of an inference failure: a local null can identify only an equivalence class when two generators place information in unmeasured sectors.

## Reproduce

```bash
python scripts/run_sector_complete_benchmark.py
pytest -q
```

Use a declared Python environment with NumPy, SciPy, Matplotlib, and pytest.
The benchmark forces Matplotlib's `Agg` backend and writes UTF-8 LF-normalized
JSON/CSV. Re-run twice and compare the JSON/CSV/checksum bytes before treating
the result as deterministic. The supplied PDF/DOCX reading editions remain
external review inputs; their original bytes and visual/a11y reports are not
part of this release, so no PDF accessibility result is claimed.

## Core correction

The rejected equation was a trace of a commutator, which vanishes under ordinary finite-dimensional conditions. For an unconditioned channel and a POVM, this package uses

```text
p(d | rho, Gamma, u) = Tr[M_d E_{Gamma,u}(rho)]
```

The product between the POVM element and channel output is intentional. A
comma or commutator in that position is not equivalent notation.

Selected branches require a trace-nonincreasing quantum instrument.

## Interpretation firewall

The dark-matter template is intentionally empty and marked `proposed_only`. No
ontological bridge is claimed from sunlight SPDC, duality defects, photonic
routing, fermium spectroscopy, or levitated-magnet papers to dark-matter
identity, origin, or purpose.

The magnet literature is a certificate-layer comparison only:

- Amaral et al. (published PRL 134, 251001; DOI
  `10.1103/PhysRevLett.134.251001`) report a narrow-band (B-L) null search and
  model-specific upper limit, not particle identification or universal
  exclusion: <https://arxiv.org/abs/2409.03814>.
- Ji et al. report room-temperature LeMaMa field metrology near 32 fT/√Hz,
  not a dark-matter observation or limit: <https://arxiv.org/abs/2504.21524>.
- Tian et al. report model-dependent spin--spin--velocity bounds in an APS
  accepted record, not a dark-matter detection; version-of-record status is not
  asserted here: <https://journals.aps.org/prl/accepted/10.1103/35c1-ylnx>.

Any future adapter must declare an interaction Hamiltonian/effective operator,
distribution and abundance, mediator/coupling normalization, coherence range,
detector response and units, nuisance controls, multi-sector predictions,
preregistration, and a falsifiable null. Force sensitivity must not be relabeled
as field sensitivity or as a planetary energy/latent-heat term.

## Evidence and rights boundary

The attached ZIP was independently hashed as
`B0B9606B3C64C91C97A92E18E4E4A5BDB7519ED4D15664A33F864E420F32C1B6`; the
companion text hash is
`0DC731EAAC8FFADFD9105AFD7AC944A5A98274D8B26462547343BC16D30C3675`. These
identify supplied inputs, not a release identity. The claim and source ledgers
retain source-level versus synthetic evidence classes and duplicate aliases.
On 2026-08-07, the package author authorized original code, scripts, tests, and
schemas under MIT, and original explanatory text, diagrams, synthetic data, and
generated results under CC BY 4.0, to the extent the author holds the relevant
rights. This declaration does not relicense citations, bibliographic metadata,
scientific facts, referenced publications, third-party dependencies, embedded
fonts, raw experimental datasets, or other third-party material. No third-party
article text or figures are redistributed.

ChatGPT/OpenAI assistance is provenance and drafting assistance, not authorship,
endorsement, peer review, or evidence. Jacko T. retains responsibility for the
candidate's claims, code, sources, and publication decisions.
