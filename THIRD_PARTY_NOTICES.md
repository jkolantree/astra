# Third-party notices

No third-party article text, figure, photograph, dataset, or adapted artwork is redistributed. Bibliographic records and DOI/arXiv links identify externally published sources; those works remain under their own terms.

The source archive does not vendor Python packages, Pandoc, Chromium, Git, or a Python runtime. Reproduction installs the exact packages named in `requirements-lock.txt` from their publishers and requires the Git for Windows distribution identified in `RUNTIME.json`. Principal direct dependencies and their upstream licenses are:

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

The HTML builder embeds the DejaVu Serif, DejaVu Sans, and DejaVu Sans Mono font files distributed with Matplotlib 3.11.1 as data URIs. The PDF builder embeds subsets of those fonts. DejaVu fonts are based on Bitstream Vera and are distributed under the permissive DejaVu/Bitstream/Arev terms reproduced in [`licenses/DEJAVU-FONTS.txt`](licenses/DEJAVU-FONTS.txt). Those notices accompany every archived copy of the embedded typefaces. The terms permit redistribution and embedding, subject to their reserved-name and trademark conditions. The project does not claim authorship of those fonts.

Chromium uses Windows-supplied Cambria Math and Times New Roman subsets for mathematical glyphs that require its native MathML fallback. The build gate directly checks both source fonts' OpenType `OS/2.fsType` value is `8` (editable document embedding) and that only embedded subsets appear in the PDFs. Microsoft documents document-font embedding as an allowed special case when the application follows the OpenType/TrueType embedding flags, and states that documents containing permitted embedded Windows fonts generally have no special distribution restriction. The font files themselves are not shipped separately or hosted as web fonts. See Microsoft's official [Font redistribution FAQ](https://learn.microsoft.com/en-us/typography/fonts/font-faq).

## Tool output

PNG and PDF artifacts are generated with the tools above. Tool use does not transfer ownership of those tools to this repository. Generated scientific content, data, and original figure composition are licensed as stated in `LICENSE_MAP.md`.
