# ASTRA SPPT SCM research draft and visual atlas

**Public research draft — 5 October 2026. Unpromoted and not peer reviewed.**

This bundle accompanies *Physics Synthesis and Research Priorities for ASTRA SPPT and SCM*. It keeps conditional mathematics, literature-reported findings, proposed experiments and conceptual art distinct. It does not promote or replace the stable SPPT and ASTRA v1.0.7 science authority.

## Read and view

- [Physics synthesis PDF](research/Physics_Synthesis_ASTRA_SPPT_SCM_Public_Draft_2026-10-05.pdf): the 35-page research draft, including the planetary synthesis and source-access limits.
- [Editable research draft](research/Physics_Synthesis_ASTRA_SPPT_SCM_Public_Draft_2026-10-05.docx).
- [Visual atlas PDF](visuals/ASTRA_SPPT_SCM_Visual_Atlas_2026-10-05.pdf): 12 pages with all six scientific figures, two animation previews and three generated illustrations.
- [Scientific captions and sources](visuals/scientific/CAPTIONS_AND_SOURCES.md): full assumptions, limitations and primary-source links.
- [Scientific asset manifest](visuals/scientific/manifest.json): formulas, parameter choices, units and file hashes.
- [Illustration provenance](visuals/illustrations/provenance.json): exact text prompts, captions, alt text and AI-generation provenance.
- [Visual catalog](visuals/catalog.json): concise captions and bundle-relative filenames.

## Animations

These are actual animated assets, with motion-free poster alternatives. Their motion is analytically prescribed; no physical evolution equation or spacecraft dataset is being simulated.

1. Pattern versus material motion: [GIF](visuals/scientific/animations/A1_pattern_vs_material_motion.gif), [MP4](visuals/scientific/animations/A1_pattern_vs_material_motion.mp4), [poster](visuals/scientific/animations/A1_pattern_vs_material_motion_poster.png). Ten-second loop, 10 frames per second. Display rates and radii are arbitrary.
2. Bending graph and normal plane: [GIF](visuals/scientific/animations/A2_bending_graph_normal_frame.gif), [MP4](visuals/scientific/animations/A2_bending_graph_normal_frame.mp4), [poster](visuals/scientific/animations/A2_bending_graph_normal_frame_poster.png). Eight-second loop, 10 frames per second. Display time is a geometric interpolation parameter.

## Generated illustrations

Keep these classifications and captions with the images.

- [Saturn ring dust](visuals/illustrations/images/01-saturn-ring-dust-illustration.png): AI-generated conceptual illustration. Off-plane dust visibility, particle sizes and spatial distribution are artistically enhanced and unmeasured. This is not a spacecraft image or a ring-age determination.
- [Enceladus plume](visuals/illustrations/images/02-enceladus-plume-illustration.png): AI-generated conceptual illustration. Terrain, jets, viewing geometry and scale are invented for the illustration. It does not reveal ocean chemistry, freezing history or biology.
- [Bent filament](visuals/illustrations/images/03-bent-filament-concept.png): AI-generated speculative concept art. The filament and plane fragments are artistic motifs. Their proximity to the separate Saturn-like form establishes no physical connection.

All three are original text-only generations with no input photographs or copied source images. Their original C2PA content-origin credentials remain embedded in the PNG files. The atlas reproduces their pixels with visible conceptual-art labels; the standalone PNGs retain the original credentials.

## Scientific scope

- The WKI plot is an exact linearized model calculation with synthetic parameters. Absence of exponential growth is not proof of nonlinear stability. The older transformed-background literature comparison remains unresolved.
- The two-qubit plot reproduces an established conditional spectrum and credits its prior literature. It is not a gravity experiment or a new formula claim.
- The ring inventory curve is a deliberately restricted toy model, not a Saturn age fit or the complete published evolution model.
- The normal-plane drawing and animation show geometric distinctions, without deriving spin, charge, matter or gravity.
- The observational diagrams propose measurement and calibration disciplines; they do not supply missing data or establish shared physical dynamics.
- Source-access limitations remain in the research report and captions, including incomplete Enceladus methods, supplement and event membership, and preliminary conference evidence.

The public report retains the research edition's scientific text, equations and citations. Its two private-review status passages have been replaced with explicit public-draft status. Publication does not turn conditional calculations into experimental validation or establish literature priority.

## Reproduce and verify

The [scientific README](visuals/scientific/README.md) gives dependency versions and reproduction instructions for the original [figure generator](visuals/scientific/generate_scientific_atlas.py). The dense quantum map is raster-embedded inside its SVG; labels and axes remain editable, and the formula can be regenerated from code.

`MANIFEST.sha256` records the exact bytes of the bundle's other files. The scientific manifest additionally records each figure and animation hash. The archive includes no downloaded third-party paper, source-paper image or earlier research archive. Referenced scientific manuscripts and external publications are cited, not redistributed as source packages.

## Rights and attribution

This bundle assigns no new license and does not override any applicable repository terms or third-party rights. No third-party paper figure was copied or traced. Citations and AI-generation labels should remain with their associated claims and images. Scientific accuracy checks and content-origin metadata are not external peer review or a guarantee of physical validity.
