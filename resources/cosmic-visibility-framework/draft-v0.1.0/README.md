# ASTRA cosmic visibility and transformed-archive framework

Status: repository-visible, unpromoted research draft. This folder is a
methods framework, not a new SPPT equation, a dark-matter detection, or a
replacement cosmology. It is deliberately separate from the immutable
SPPT/ASTRA v1.0.6 release, the Earth Is the Instrument line, and the
Sector-Complete Instrument alpha.

## Purpose

The supplied reports describe two very different observations:

* a proposed search in which magnetised cosmic filaments can transduce a
  hidden carrier into photons before a gamma-ray detector sees it; and
* a Martian meteorite whose age helps show that a gap in recovered samples is
  not automatically a gap in the planet's history.

The common, testable contribution is an inference discipline:

> Treat visibility as a chain from source to certificate, and model the
> operators that convert, erase, select, archive, recover, and measure a
> signal before assigning force to either a detection or an absence.

This draft calls that chain a **visibility kernel**. It can be used for
cosmological messengers, planetary samples, laboratory sensors, or any other
case where the observed record is a transformed and selected view of a hidden
state.

## The framework record

`example_visibility_record.json` is a canonical, machine-checkable example.
`visibility_framework.schema.json` specifies its fields. The record separates:

1. a source or residue model;
2. transduction and propagation operators;
3. archive, recovery, and detector selection;
4. controls and observation operators;
5. predeclared predictions and falsifiers; and
6. a bounded certificate and promotion decision.

The example deliberately keeps the filament-conversion and Martian-archive
chains separate with explicit `chain_id` values. Their shared abstraction is
operator bookkeeping, not a shared physical process. Its kernel factors cover
production, conversion, propagation, archive, sampling, recovery, and
detector stages; unresolved factors are represented as `unknown` rather than
silently assigned unit visibility.

The factors are not assumed to be known. Each carries a value, interval, or
explicit unknown marker, plus units, evidence class, source IDs, and an
identifiability status. Unknown or partially identified factors remain visible
in the record rather than being silently set to one.

## Scientific boundary

The filaments-to-gamma-ray mechanism is represented as a conditional model
whose outcome depends on magnetic-field, coherence-length, filling-fraction,
background, and propagation assumptions. It is not a detection of dark
matter, gravitons, or graviton--photon conversion. The Martian case is
represented as a sampling and archive problem; it does not by itself establish
the number or identity of Martian mantle reservoirs.

The proposed cross-domain result is methodological and falsifiable. A useful
record must support a held-out test such as:

* a signal scales with independently measured converter strength and follows
  the predicted spectrum, while matched low-converter controls do not; or
* a purported historical gap shrinks when the recovery and selection process
  is modelled and a new sample is found in the predicted region.

Failure to distinguish source absence from low visibility is a reason to defer
the conclusion, not evidence for either hypothesis.

## Files and provenance

* `CORE_FRAMEWORK.md`, the accompanying HTML/PDF, and
  `pdf_build_identity.json` are explanatory/build-identity documents;
  they do not promote the claims in the ledgers.
* `visibility_framework.schema.json` and `example_visibility_record.json` are
  the protocol and canonical example.
* `claim_ledger.csv`, `source_ledger.csv`, and `novelty_ledger.csv` separate
  claim status, source identity, and possible contribution. Source rows are
  citation-level records; article bytes, figures, and raw data are not
  redistributed.
* `draft_metadata.json` binds the draft to the immutable v1.0.6 commit and the
  two supplied input hashes. It contains no dynamic `HEAD` lookup.
* `VISIBILITY_MANIFEST.sha256` binds the local payload bytes. It is not a
  release manifest and does not alter `MANIFEST.sha256` or any v1.0.6 asset.

Original draft prose is offered under CC BY 4.0 only to the extent the project
author holds the relevant rights. Cited studies, publisher records, datasets,
figures, and dependencies retain their own terms.

## Promotion gate

Before this framework could become a promoted edition, freeze a new candidate
tree and resolve every `needs_primary_review` source; add claim-local page,
equation, or table locators; archive only permitted input bytes; quantify
converter and recovery uncertainty; preregister controls; and score a
held-out result against a declared baseline. No result should be promoted
from this draft solely because the schema validates.
