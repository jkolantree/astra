"""Positive-first controls for the exact private preview, using only stdlib."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path


SPEC = importlib.util.spec_from_file_location("preview_gateway", Path(__file__).with_name("preview_gateway.py"))
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Could not load local preview module")
preview = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(preview)


class PreviewControls(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="astra-preview-controls-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "source"
        self.retained = self.root / "retained"
        self.source.mkdir()
        self.retained.mkdir()
        (self.source / "page.html").write_bytes(b"<html>Gateway fixture</html>\n")
        (self.source / "LICENSE").write_bytes(b"Notice fixture\n")
        (self.retained / "paper.html").write_bytes(b"<html>Retained 020 fixture</html>\n")
        self.record_path = self.root / "record.json"
        self.record = {
            "schema": "astra-gateway-preview-1", "status": "PROPOSED_NOT_ADMITTED",
            **{flag: False for flag in preview.FLAGS},
            "files": [self.row("source", "page.html", "index.html", "gateway"),
                      self.row("source", "LICENSE", "licenses/NOTICE.txt", "notice"),
                      self.row("retained020", "paper.html", "reading/paper/index.html", "historical_reading")],
        }
        # Every negative test first demonstrates the same real assembler succeeds
        # with the authentic small fixture, before changing one guard input.
        result = self.run_preview(self.record, destination=self.root / "positive")
        self.assertEqual(result["files"], 3)
        self.assertEqual(result["retained020_files"], 1)
        self.assertTrue(all(result[flag] is False for flag in preview.FLAGS))
        self.assertEqual((self.root / "positive/reading/paper/index.html").read_bytes(),
                         (self.retained / "paper.html").read_bytes())

    def row(self, family: str, source: str, destination: str, role: str) -> dict:
        root = self.source if family == "source" else self.retained
        data = (root / source).read_bytes()
        return {"family": family, "source_path": source, "destination": destination,
                "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "role": role}

    def bind(self, record: dict) -> str:
        self.record_path.write_text(json.dumps(record, sort_keys=True) + "\n")
        return hashlib.sha256(self.record_path.read_bytes()).hexdigest()

    def run_preview(self, record: dict, **changes) -> dict:
        arguments = {"source": self.source, "retained": self.retained,
                     "record": self.record_path, "record_sha256": self.bind(record),
                     "destination": self.root / "rejected"}
        arguments.update(changes)
        return preview.assemble(**arguments)

    def snapshot(self) -> dict:
        result = {}
        for path in self.root.rglob("*"):
            relative = path.relative_to(self.root).as_posix()
            if path.is_symlink():
                result[relative] = ("link", os.readlink(path))
            elif path.is_dir():
                result[relative] = ("directory",)
            else:
                result[relative] = ("file", path.read_bytes())
        return result

    def rejected(self, code: str, specification: dict | None = None, **changes) -> None:
        record = copy.deepcopy(self.record) if specification is None else specification
        digest = self.bind(record)
        arguments = {"source": self.source, "retained": self.retained,
                     "record": self.record_path, "record_sha256": digest,
                     "destination": self.root / "rejected"}
        arguments.update(changes)
        before = self.snapshot()
        with self.assertRaisesRegex(preview.PreviewError, "^" + code + "$"):
            preview.assemble(**arguments)
        self.assertEqual(self.snapshot(), before, "Rejection wrote or altered a file")

    def test_positive_exact_roster_and_retained_label(self) -> None:
        site = self.root / "positive"
        self.assertEqual({p.relative_to(site).as_posix() for p in site.rglob("*") if p.is_file()},
                         {row["destination"] for row in self.record["files"]})

    def test_record_identity_is_external(self) -> None:
        self.rejected("RECORD_HASH", record_sha256="0" * 64)

    def test_record_digest_format(self) -> None:
        for value in ("A" * 64, "123", "", None):
            with self.subTest(value=value):
                self.rejected("RECORD_DIGEST_FORMAT", record_sha256=value)

    def test_all_admission_flags_must_be_literal_false(self) -> None:
        for flag in preview.FLAGS:
            for value in (True, 0, None, "false"):
                with self.subTest(flag=flag, value=value):
                    changed = copy.deepcopy(self.record)
                    changed[flag] = value
                    self.rejected("ADMISSION_FLAG", changed)

    def test_schema_status_and_roster_are_exact(self) -> None:
        for field, value, code in (("schema", "other", "RECORD_SCHEMA"),
                                   ("status", "ADMITTED", "RECORD_STATUS"),
                                   ("files", [], "EMPTY_ROSTER"),
                                   ("files", {}, "EMPTY_ROSTER")):
            with self.subTest(field=field):
                changed = copy.deepcopy(self.record)
                changed[field] = value
                self.rejected(code, changed)
        changed = copy.deepcopy(self.record)
        changed["approval"] = True
        self.rejected("RECORD_SCHEMA", changed)

    def test_missing_or_extra_row_keys_are_rejected(self) -> None:
        for mutate in (lambda row: row.pop("role"), lambda row: row.update({"approved": True})):
            changed = copy.deepcopy(self.record)
            mutate(changed["files"][0])
            self.rejected("ROW_SCHEMA", changed)

    def test_family_and_role_are_bounded(self) -> None:
        for field, value, code in (("family", "fresh020", "FAMILY"),
                                   ("family", {}, "FAMILY"),
                                   ("role", "validated_science", "ROLE"),
                                   ("role", None, "ROLE")):
            with self.subTest(field=field, value=value):
                changed = copy.deepcopy(self.record)
                changed["files"][0][field] = value
                self.rejected(code, changed)

    def test_member_paths_cannot_escape_or_alias(self) -> None:
        for field in ("source_path", "destination"):
            for value in ("../victim", "/absolute", "a//b", "a/./b", "a/../b", "a\\b",
                          "C:escape", "a/", "NUL.txt", "a/CON", "a/b.", "a/b ", "a/\nb"):
                with self.subTest(field=field, value=value):
                    changed = copy.deepcopy(self.record)
                    changed["files"][0][field] = value
                    self.rejected("RELATIVE_PATH", changed)

    def test_file_size_and_digest_are_strict(self) -> None:
        for field, value, code in (("bytes", True, "FILE_IDENTITY"),
                                   ("bytes", -1, "FILE_IDENTITY"),
                                   ("sha256", "A" * 64, "FILE_IDENTITY"),
                                   ("bytes", 1, "SOURCE_HASH"),
                                   ("sha256", "0" * 64, "SOURCE_HASH")):
            with self.subTest(field=field, value=value):
                changed = copy.deepcopy(self.record)
                changed["files"][0][field] = value
                self.rejected(code, changed)

    def test_late_bad_row_does_not_write_earlier_valid_rows(self) -> None:
        changed = copy.deepcopy(self.record)
        changed["files"][-1]["sha256"] = "0" * 64
        self.rejected("SOURCE_HASH", changed)

    def test_duplicate_and_casefold_destination(self) -> None:
        for destination in ("index.html", "INDEX.HTML"):
            changed = copy.deepcopy(self.record)
            changed["files"][-1]["destination"] = destination
            self.rejected("DUPLICATE_DESTINATION", changed)

    def test_file_directory_collisions_in_both_orders(self) -> None:
        for first, second in (("a", "A/b"), ("a/b", "A")):
            changed = copy.deepcopy(self.record)
            changed["files"][0]["destination"] = first
            changed["files"][1]["destination"] = second
            self.rejected("DESTINATION_COLLISION", changed)

    def test_shared_directory_case_alias(self) -> None:
        changed = copy.deepcopy(self.record)
        changed["files"][0]["destination"] = "Reading/one.html"
        changed["files"][1]["destination"] = "reading/two.html"
        self.rejected("DIRECTORY_ALIAS", changed)

    def test_existing_destination_empty_and_occupied(self) -> None:
        for name, occupied in (("empty", False), ("occupied", True)):
            target = self.root / name
            target.mkdir()
            if occupied:
                (target / "victim").write_bytes(b"Do not alter")
            self.rejected("DESTINATION_EXISTS", destination=target)

    def test_destination_is_absolute_canonical_and_outside_roots(self) -> None:
        self.rejected("DESTINATION_PATH", destination="relative")
        self.rejected("DESTINATION_PATH", destination=str(self.root) + "/alias/../victim")
        for target in (self.source / "preview", self.retained / "preview", self.root):
            self.rejected("DESTINATION_OVERLAP", destination=target)

    def test_destination_alias_preserves_victim(self) -> None:
        victim = self.root / "victim"
        victim.mkdir()
        (victim / "keep").write_bytes(b"Unchanged")
        alias = self.root / "alias"
        alias.symlink_to(victim, target_is_directory=True)
        self.rejected("PATH_ALIAS", destination=alias / "output")
        self.rejected("PATH_ALIAS", destination=alias)

    def test_source_and_retained_root_aliases(self) -> None:
        for key, target in (("source", self.source), ("retained", self.retained)):
            alias = self.root / (key + "-alias")
            alias.symlink_to(target, target_is_directory=True)
            self.rejected("PATH_ALIAS", **{key: alias})

    def test_roots_must_not_overlap(self) -> None:
        self.rejected("SOURCE_ROOT_OVERLAP", retained=self.source)
        nested = self.source / "nested"
        nested.mkdir()
        self.rejected("SOURCE_ROOT_OVERLAP", retained=nested)

    def test_source_file_and_ancestor_symlinks(self) -> None:
        page = self.source / "page.html"
        data = page.read_bytes()
        page.unlink()
        victim = self.root / "victim.html"
        victim.write_bytes(data)
        page.symlink_to(victim)
        self.rejected("PATH_ALIAS")
        page.unlink()
        page.write_bytes(data)
        alias = self.source / "alias"
        alias.symlink_to(self.retained, target_is_directory=True)
        changed = copy.deepcopy(self.record)
        changed["files"][0]["source_path"] = "alias/paper.html"
        self.rejected("PATH_ALIAS", changed)

    def test_source_hardlink_rejected(self) -> None:
        os.link(self.source / "page.html", self.root / "hardlink-victim")
        self.rejected("REGULAR_UNLINKED_FILE")

    def test_retained_hardlink_rejected(self) -> None:
        os.link(self.retained / "paper.html", self.root / "retained-hardlink-victim")
        self.rejected("REGULAR_UNLINKED_FILE")

    def test_record_alias_and_hardlink_rejected(self) -> None:
        self.bind(self.record)
        alias = self.root / "record-alias.json"
        alias.symlink_to(self.record_path)
        self.rejected("PATH_ALIAS", record=alias)
        os.link(self.record_path, self.root / "record-hardlink.json")
        self.rejected("REGULAR_UNLINKED_FILE")

    def test_record_duplicate_keys_rejected(self) -> None:
        self.record_path.write_text('{"schema":"first","schema":"second"}')
        digest = hashlib.sha256(self.record_path.read_bytes()).hexdigest()
        before = self.snapshot()
        with self.assertRaisesRegex(preview.PreviewError, "^DUPLICATE_JSON_KEY$"):
            preview.assemble(self.source, self.retained, self.record_path, digest, self.root / "rejected")
        self.assertEqual(self.snapshot(), before)

    def test_final_roster_rejects_unlisted_file_and_changed_bytes(self) -> None:
        site = self.root / "positive"
        payloads = {row["destination"]: (site / row["destination"]).read_bytes() for row in self.record["files"]}
        (site / "unexpected").write_bytes(b"Not listed")
        with self.assertRaisesRegex(preview.PreviewError, "^OUTPUT_ROSTER$"):
            preview.verify_output(site, payloads)
        (site / "unexpected").unlink()
        (site / "index.html").write_bytes(b"Changed")
        with self.assertRaisesRegex(preview.PreviewError, "^OUTPUT_HASH$"):
            preview.verify_output(site, payloads)


if __name__ == "__main__":
    unittest.main(verbosity=2)
