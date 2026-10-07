"""Successor draft isolation, content contracts and failure controls."""

import copy
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("draft_builder", ROOT / "tools/build_integrated_documents.py")
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Draft builder missing")
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


class IntegratedDocumentTests(unittest.TestCase):
    def test_failed_rerun_replaces_old_success_receipt_with_incomplete(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            out = root / "tmp/integrated-document-draft"
            out.mkdir(parents=True)
            receipt = out / "draft_document_identity.json"
            receipt.write_text('{"status":"PASS"}')
            documents = ((root / "manuscript.md", out / "ASTRA_integrated_manuscript_draft.html",
                          out / "ASTRA_integrated_manuscript_draft.pdf", "Draft"),)
            with patch.multiple(builder, ROOT=root, OUTPUT_ROOT=out,
                                TEMP_ROOT=root / "tmp/build", DOCUMENTS=documents), \
                    patch.object(sys, "argv", ["builder"]), \
                    patch.object(builder, "validate_source_snapshot", return_value={}), \
                    patch.object(builder, "source_contract", return_value={}), \
                    patch.object(builder, "build_html", side_effect=RuntimeError("test failure")), \
                    self.assertRaisesRegex(RuntimeError, "test failure"):
                builder.main()
            self.assertEqual(json.loads(receipt.read_text())["status"], "INCOMPLETE")
            tempfile.tempdir = None

    def test_output_hard_link_cannot_overwrite_historical_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            out = root / "tmp/integrated-document-draft"
            out.mkdir(parents=True)
            victim = root / "historical.txt"
            victim.write_text("preserve")
            target = out / "ASTRA_integrated_manuscript_draft.html"
            os.link(victim, target)
            with patch.multiple(builder, ROOT=root, OUTPUT_ROOT=out):
                with self.assertRaisesRegex(RuntimeError, "Hard-linked"):
                    builder.ensure_safe_output(target)
            self.assertEqual(victim.read_text(), "preserve")

    def test_snapshot_rejects_changed_dependency(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            source = root / "input.txt"
            source.write_text("original")
            snapshot = {"status": "DRAFT_SOURCE_SNAPSHOT_NOT_ADMISSION", "files": [
                {"path": "input.txt", "sha256": builder.sha256(source)}]}
            (root / "source-snapshot.json").write_text(json.dumps(snapshot))
            with patch.multiple(builder, ROOT=root, MANUSCRIPT=root):
                builder.validate_source_snapshot()
                source.write_text("altered")
                with self.assertRaisesRegex(RuntimeError, "snapshot mismatch"):
                    builder.validate_source_snapshot()

    def test_plan_refuses_release_or_historical_output(self):
        for field, value in [("release_version", "1.1.0"), ("release_tag", "v1.1.0"),
                             ("status", "ADMITTED"), ("output_directory", "manuscript"),
                             ("epoch_is_release_date", True)]:
            with self.subTest(field=field):
                plan = copy.deepcopy(builder.PLAN)
                plan[field] = value
                with self.assertRaises(RuntimeError):
                    builder.validate_plan(plan)

    def test_plan_refuses_traversal_and_duplicate_names(self):
        for field, value in [("source", "../manuscript.md"), ("stem", "../../historical")]:
            plan = copy.deepcopy(builder.PLAN)
            plan["documents"][0][field] = value
            with self.assertRaises(RuntimeError):
                builder.validate_plan(plan)
        plan = copy.deepcopy(builder.PLAN)
        plan["documents"][1]["stem"] = plan["documents"][0]["stem"]
        with self.assertRaises(RuntimeError):
            builder.validate_plan(plan)

    def test_output_cannot_target_historical_edition(self):
        with self.assertRaises(RuntimeError):
            builder.ensure_safe_output(ROOT / "manuscript/SPPT_ASTRA_preprint_v1.0.7.html")

    def test_output_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            out = root / "tmp/integrated-document-draft"
            out.mkdir(parents=True)
            victim = root / "historical.txt"
            victim.write_text("preserve")
            target = out / "ASTRA_integrated_manuscript_draft.html"
            target.symlink_to(victim)
            with patch.multiple(builder, ROOT=root, OUTPUT_ROOT=out):
                with self.assertRaises(RuntimeError):
                    builder.ensure_safe_output(target)
            self.assertEqual(victim.read_text(), "preserve")

    def test_output_directory_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "elsewhere").mkdir()
            (root / "tmp").symlink_to(root / "elsewhere", target_is_directory=True)
            out = root / "tmp/integrated-document-draft"
            with patch.multiple(builder, ROOT=root, OUTPUT_ROOT=out):
                with self.assertRaises(RuntimeError):
                    builder.ensure_safe_output(out / "ASTRA_integrated_manuscript_draft.html")

    def test_titles_are_checked_against_sources(self):
        source = builder.MANUSCRIPT / "manuscript.md"
        with self.assertRaisesRegex(RuntimeError, "title disagrees"):
            builder.source_contract(source, "Historical title that does not match")

    def test_table_counts_follow_source_ast_not_legacy_constants(self):
        with tempfile.TemporaryDirectory() as d:
            source = Path(d) / "test.md"
            text = '---\ntitle: "Draft"\n---\n\n# Section\n\n'
            source.write_text(text)
            self.assertEqual(builder.source_contract(source, "Draft")["tables"], 0)
            source.write_text(text + '| Key | Value |\n|---|---|\n| A | B |\n\nTable: Caption.\n')
            self.assertEqual(builder.source_contract(source, "Draft")["tables"], 1)

    def test_caption_and_count_checks_remain_mandatory(self):
        html = '<table><thead><tr><th>A</th></tr></thead><tbody><tr><td>B</td></tr></tbody></table>'
        with self.assertRaisesRegex(RuntimeError, "caption"):
            builder.postprocess_tables(html, expected_count=1)
        with self.assertRaisesRegex(RuntimeError, "Expected 2"):
            builder.postprocess_tables(html, expected_count=2)

    def test_headers_remain_accessible(self):
        html = '<table><caption>Caption</caption><thead><tr><th>A</th></tr></thead><tbody><tr><td>B</td></tr></tbody></table>'
        result = builder.postprocess_tables(html, expected_count=1)
        self.assertIn('scope="col"', result)
        self.assertIn('scope="row"', result)

    def test_raw_content_and_remote_images_are_refused_before_embedding(self):
        with tempfile.TemporaryDirectory() as d:
            source = Path(d) / "test.md"
            for content in ['<script>alert(1)</script>', '![x](https://example.invalid/a.png)',
                            '[local](file:///private.txt)']:
                source.write_text('---\ntitle: "Draft"\n---\n\n# Section\n\n' + content)
                with self.subTest(content=content), self.assertRaises(RuntimeError):
                    builder.source_contract(source, "Draft")

    def test_html_static_controls_reject_paths_resources_and_broken_fragments(self):
        expected = {"tables": 0, "figures": 0, "formulas": 0}
        for html in ['<script>x</script>', '<a href="file:///private">x</a>',
                     '<p>/workspace/private</p>', '<a href="#absent">x</a>',
                     '<p id="a"></p><p id="a"></p>',
                     '<style>x {background:url(https://example.invalid/x)}</style>']:
            with self.subTest(html=html), self.assertRaises(RuntimeError):
                builder.validate_static_html(html, expected)

    def test_html_missing_formula_or_table_fails(self):
        with self.assertRaisesRegex(RuntimeError, "counts disagree"):
            builder.validate_static_html('<h1 id="a">Draft</h1>',
                                         {"tables": 1, "figures": 0, "formulas": 1})

    def test_current_sources_have_nonhistorical_table_counts(self):
        # This test counts Markdown constructs; separate fixtures and real builds validate image bytes.
        with patch.object(builder, "declared_figure", return_value={}):
            counts = [builder.source_contract(source, title) for source, _, _, title in builder.DOCUMENTS]
        self.assertEqual([r["tables"] for r in counts], [2, 2])
        self.assertTrue(all(r["formulas"] > 0 for r in counts))
        self.assertEqual([r["figures"] for r in counts], [1, 14])

    def test_declared_figure_positive_then_hash_link_active_and_unused_mutations(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); manuscript=root/'manuscript/integrated-draft';manuscript.mkdir(parents=True)
            declaration={'status':'DECLARED_FIGURE_INPUTS_NOT_ADMISSION','figures':{}}
            for i in range(13):
                relative=f'resources/integrated-edition-proposal/generated/{i+1:02}_test.svg';target=root/relative;target.parent.mkdir(parents=True,exist_ok=True)
                target.write_text('<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0"/></svg>')
                declaration['figures']['../../'+relative]={'source_path':relative,'sha256':builder.sha256(target),'title':'Test','scope':'Fixture'}
            url=next(iter(declaration['figures']));target=root/declaration['figures'][url]['source_path'];original=target.read_text()
            record=manuscript/'figure-inputs.json';record.write_text(json.dumps(declaration))
            with patch.multiple(builder,ROOT=root,MANUSCRIPT=manuscript):
                builder.declared_figure(manuscript/'source.md',url)
                unused=list(declaration['figures'])[-1];bad=copy.deepcopy(declaration);bad['figures'][unused]={};record.write_text(json.dumps(bad))
                with self.assertRaisesRegex(RuntimeError,'Malformed figure'):builder.declared_figure(manuscript/'source.md',url)
                bad=copy.deepcopy(declaration);bad['figures'].pop(unused);record.write_text(json.dumps(bad))
                with self.assertRaisesRegex(RuntimeError,'Exact thirteen'):builder.declared_figure(manuscript/'source.md',url)
                record.write_text('{"figures":{},"figures":{}}')
                with self.assertRaisesRegex(RuntimeError,'Duplicate figure'):builder.declared_figure(manuscript/'source.md',url)
                record.write_text(json.dumps(declaration));target.write_text('<svg/>')
                with self.assertRaisesRegex(RuntimeError,'bytes mismatch'):builder.declared_figure(manuscript/'source.md',url)
                target.write_text('<svg><script>bad()</script></svg>');declaration['figures'][url]['sha256']=builder.sha256(target);record.write_text(json.dumps(declaration))
                with self.assertRaisesRegex(RuntimeError,'Active declared SVG'):builder.declared_figure(manuscript/'source.md',url)
                target.unlink();target.symlink_to(root/'missing')
                with self.assertRaisesRegex(RuntimeError,'Linked or missing'):builder.declared_figure(manuscript/'source.md',url)
                target.unlink();target.write_text(original);declaration['figures'][url]['sha256']=builder.sha256(target);record.write_text(json.dumps(declaration))
                with self.assertRaisesRegex(RuntimeError,'Only local declared'):builder.declared_figure(manuscript/'source.md','https://invalid/image.svg')

    def test_citation_bounds_and_bc008_classification(self):
        references = json.loads((ROOT / "docs/integrated-core/source-references.json").read_text())["references"]
        self.assertEqual(len(references), 15)
        self.assertTrue(all(r["empirical_support_for_core"] is False and r["artifact_bytes_hashed"] is False for r in references))
        self.assertTrue(all(r["relation_to_core"] == "source-version-tracing-test-case" for r in references[-3:]))
        bridges = json.loads((ROOT / "data/integrated-core/bridge_contracts.json").read_text())
        self.assertEqual(bridges[-1]["relation_type"], "source-version-tracing-test-case")
        self.assertTrue(all(b["framework_validation"] == "not-empirically-validated" for b in bridges))

    def test_explicit_browser_required_without_auto_install(self):
        with patch.object(builder, "BROWSER", None), self.assertRaises(RuntimeError):
            builder.launch_browser(None)


if __name__ == "__main__":
    unittest.main()
