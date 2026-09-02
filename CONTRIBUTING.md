# Contributing to ASTRA

The most useful contribution is a specific, reproducible challenge. You do not need to accept the framework’s premises to question its mathematics, sources, code, accessibility, or interpretation.

## Choose the right report

- [Scientific correction](https://github.com/jkolantree/astra/issues/new?template=scientific-correction.yml) — a mathematical error, unsupported inference, missing qualification, source problem, or plausible counterexample.
- [Reproducibility problem](https://github.com/jkolantree/astra/issues/new?template=reproducibility.yml) — a command, environment, checksum, build, test, or archive failure.
- [Accessibility problem](https://github.com/jkolantree/astra/issues/new?template=accessibility.yml) — a reading, navigation, contrast, keyboard, screen-reader, reflow, PDF, or alternative-text barrier.
- [Open question](https://github.com/jkolantree/astra/issues/new/choose) — anything that does not fit the forms above.

A strong report names the publication and version, the exact page, section, claim, file, or command, what you observed, what you expected, and the smallest example that shows the problem. Link a primary source when the issue turns on external evidence.

## Corrections and publication history

Published tags and release assets are historical records. Do not propose replacing them in place. A correction should identify the affected version and recommend one of three visible paths:

1. documentation erratum when the published bytes remain unchanged;
2. source correction for a future version; or
3. new publication identity when scientific or generated artifact bytes change.

Claim identifiers keep their meanings. If a proposition changes materially, it needs a new identifier rather than a recycled one. Negative results, failed gates, and known limitations remain part of the record.

## Source and generated files

Identify the canonical source and producer before editing a generated document, figure, data file, manifest, or checksum. Do not hand-edit a derivative merely to make a check pass. Run generation in an isolated worktree or disposable copy unless the package instructions explicitly authorize another path.

The core and supplemental publications have independent build and evidence boundaries. A passing package test does not promote a Draft, alter the core citation, or authorize a release.

## Privacy and rights

Do not post credentials, private correspondence, local filesystem paths, personal contact data, unpublished third-party material, or source files you do not have the right to redistribute. Prefer a DOI, publisher record, repository, or arXiv link over copying article text or figures.

Contributions are accepted only to the extent their rights are clear. Software contributions are expected to be compatible with the repository’s MIT license; prose, diagrams, and generated scientific materials must be compatible with the file-level mapping in [LICENSE_MAP.md](LICENSE_MAP.md).

## Before proposing code

Read [REPRODUCING.md](REPRODUCING.md), run the narrowest relevant check, and report the exact runtime and result. Keep unrelated working-tree changes out of the patch. If a full canonical environment is unavailable, say so plainly; a careful diagnostic result is still useful when it is not presented as release evidence.

Substantive model assistance may be used, but responsibility stays with the human contributor. Cite sources and tests, not model output.
