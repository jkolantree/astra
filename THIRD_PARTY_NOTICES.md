# Third-party notices

The v1.0.6 reference package redistributes no third-party article text, figure, photograph, dataset, or adapted artwork. Bibliographic records and DOI/arXiv links identify externally published sources; those works remain under their own terms. Separately supplied resources are governed by their explicit entries in `LICENSE_MAP.md`: *Earth Is the Instrument* Working Paper 0.1 retains its narrower distribution-only boundary, while the separately versioned v0.3.0 package declares original text and figures CC BY 4.0 and original code MIT. Neither resource relicenses cited works, names, data, trademarks, or embedded third-party fonts; its companion README and release notices state the applicable boundaries.

The v0.3.0 release asset `FONT_NOTICES.txt` records the upstream license routes
for embedded subsets of Charis SIL, Inter, Asana Math, DejaVu, STIX, Computer
Modern, and AMSFonts. No standalone font binary is added to the repository.

The core SPPT/ASTRA v1.0.6 source archive does not vendor Python packages, Pandoc, Chromium, Git, or a Python runtime. Reproduction installs the exact packages named in `requirements-lock.txt` from their publishers and requires the Git for Windows distribution identified in `RUNTIME.json`. Principal direct dependencies and their upstream licenses are:

| Component | Released version | License |
|---|---:|---|
| CPython | 3.12.10 | Python Software Foundation License 2.0 |
| Git for Windows | 2.55.0.windows.3 | GPL-2.0-only, with bundled components under their own compatible terms |
| NumPy | 2.3.5 | BSD-3-Clause |
| SciPy | 1.18.0 | BSD-3-Clause plus bundled component notices |
| pandas | 3.0.1 | BSD-3-Clause |
| Matplotlib | 3.11.1 | Matplotlib license (PSF-compatible) plus bundled font notices |
| pytest | 9.1.1 | MIT |
| pypandoc-binary | 1.15 | MIT wrapper; bundled Pandoc 3.6.1 is GPL-2.0-or-later |
| pypdf | 6.14.2 | BSD-3-Clause |
| pdfplumber | 0.11.10 | MIT |
| pikepdf | 10.11.0 | MPL-2.0; bundled qpdf components retain their notices |
| Playwright for Python | 1.62.0 | Apache-2.0 |
| Chromium used by Playwright | 151.0.7922.34, revision 1234 | BSD-3-Clause plus Chromium third-party notices |
| cffconvert | 2.0.0 | Apache-2.0 |
| Ruff | 0.16.1 | MIT |
| mypy | 2.3.0 | MIT; bundled typeshed portions Apache-2.0 |

Transitive dependencies retain their own notices and license terms. Their exact versions and hashes are in `requirements-lock.txt`; installed distributions contain the authoritative license texts.

## Fonts

The HTML builder embeds the DejaVu Serif, DejaVu Sans, DejaVu Sans Mono, and STIX General font files distributed with Matplotlib 3.11.1 as data URIs. The PDF builder embeds subsets of those same fonts, including STIX General for MathML and DejaVu Serif for page-margin numbers. Exact source-font identities are recorded in `RUNTIME.json`; no machine-installed font is a document-build input.

DejaVu fonts are based on Bitstream Vera and are distributed under the permissive DejaVu/Bitstream/Arev terms reproduced in [`licenses/DEJAVU-FONTS.txt`](licenses/DEJAVU-FONTS.txt). The Matplotlib-distributed STIX files are modified TTF conversions licensed under the SIL Open Font License 1.1; their complete notice is reproduced in [`licenses/STIX-FONTS.txt`](licenses/STIX-FONTS.txt). Those notices accompany every archived copy of the embedded typefaces. The project does not claim authorship of either font family.

## Tool output

PNG and PDF artifacts are generated with the tools above. Tool use does not transfer ownership of those tools to this repository. Generated scientific content, data, and original figure composition are licensed as stated in `LICENSE_MAP.md`.

The namespaced sector-complete GitHub prerelease does not redistribute article
text, publisher PDFs, supplements, or third-party figures. Its source-level
citations for the Amaral, Ji, and Tian magnet records remain under the authors'
and publishers' terms; see the candidate's own `THIRD_PARTY_NOTICES.md` and
`LICENSE_MAP.md`.
