# ASTRA explorer — unpromoted draft

This static field guide is staged in the research-companion
namespace. The root route `/` contains the explorer; `/explore/` redirects to it.
The existing versioned draft destination remains available. The Research
library is at `/library/`; all historical publication routes are unchanged.
`tools/build_explorer_gateway.py` derives `docs/index.html` from the explorer
source and rebases relative assets without changing the model code or fixture. Admission v2 explicitly enumerates
the companion; it does not change the frozen release routes.
Open `index.html` with a standards-compliant browser or serve this directory
through an approved local preview. The previous appearance approval applies only to the earlier delivered
preview. The root gateway and selected hero require a new review. No install, build step, external font,
analytics, WebGL, or runtime dependency is required. Controls start stationary;
static SVG diagrams, text and equations remain available without JavaScript.

The `model-code` script contains calculations, `render-code` updates the SVG
views, and the JSON `fixture` contains exact pinned reservoir samples. The
[provenance record](provenance.json) identifies source bytes and scientific scope.
The reservoir view is a sample browser, not a live differential-equation solver.
The sample copy is intentional: the interactive models need only the HTML page.
The complete media collection requires its sibling `package/` directory and
the companion review and rights records.
The regression test requires equality with the repository CSV.

## Scientific boundary

- Saturn-inspired view: independently prescribed pattern and tracer kinematics,
  not an observation, fluid solver, or fitted Saturn simulation.
- Reservoir view: retained dimensionless synthetic samples from the existing
  audited repository model; no browser fitting or planetary data.
- Filament view: analytic helix/straight-line geometry and normal-plane projector;
  no WKI dynamics or transported material-frame claim.
- The supplied planetary synthesis and original media are linked with their
  assumptions and source-access limits intact. Native video controls start
  paused; motion-free posters and written motion descriptions are provided.
- The sixfold interactive kinematics and supplied ten-lobed animation are
  separately prescribed teaching examples.
- Quantum recurrence numerical work and experimental data replay remain
  unexecuted; the sourced integration chapter states the distinction.

Publication status is Draft and unpromoted. Physics statuses are stated beside
individual figures. Stable SPPT/ASTRA v1.0.7 and historical editions retain their
independent identities. Passing software checks is not empirical validation.

## Validation and publication

Run the targeted repository tests with the declared Python environment:

```text
python -I -B -m pytest tests/test_explorer.py tests/test_astra_reservoir.py
```

The optional JavaScript calculation diagnostic uses Node when available; no
Node package installation is required. This is a development check, not a site
runtime dependency. Visual acceptance and final publication approval are pending for the
root-gateway redesign. Detailed keyboard, mobile, reduced-motion, media,
console and screen-reader coverage remains separately recorded as not tested. This is not accessibility
certification, and private screenshots are not required for publication.

The Pages workflow remains manual and main-only. Its companion assembly step
requires exact-byte integrity, manual visual acceptance and explicit final
publication approval. The prior acceptance does not authorize the changed page bytes. Successful exact-head CI and the owner's merge remain separate
requirements. Source-only assembly neither deploys nor certifies the result.
The admission and original release asset checks run independently.

Supplied media retain the package distribution status and component terms
recorded in [the companion rights notice](../RIGHTS_AND_NOTICES.md).
Original embedded JavaScript is MIT; original prose, SVG diagrams and retained
synthetic fixture content are CC BY 4.0, to the extent the project author holds
the relevant rights, as mapped in the root LICENSE_MAP.md. External works retain
their own terms. No third-party license grant is asserted, and no third-party
article or figure is bundled.
