"""Positive-first destination controls using the unchanged admitted shell bytes.

ASTRA_PAGES_HISTORICAL_SOURCE names a separate retained source fixture.
Actual bytes are checked against the unchanged historical manifest before the
production destination helpers run. No admission record or guard is replaced.
The real successor rejection is checked separately and remains required.
"""
import hashlib
import importlib.util
import json
import os
import shutil
from pathlib import Path

import pytest

from tools import assemble_pages as assembly
from tools import build_pages_admission as builder
from tools import check_pages_admission as checker

ROOT = Path(__file__).resolve().parents[3]


def snapshot(root):
    return {p.relative_to(root).as_posix(): (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mtime_ns)
            for p in root.rglob('*') if p.is_file()}


@pytest.fixture
def admitted(tmp_path, monkeypatch):
    value = os.environ.get('ASTRA_PAGES_HISTORICAL_SOURCE')
    if not value:
        pytest.fail('Set ASTRA_PAGES_HISTORICAL_SOURCE to the retained historical source fixture')
    historical = Path(value)
    if not historical.is_absolute() or historical.resolve() == ROOT.resolve():
        pytest.fail('Historical source fixture must be separate and absolute')
    # Read only to locate the old roster; load_manifest below validates every
    # real companion/support byte through the unchanged production function.
    raw = json.loads(checker.MANIFEST.read_text())
    docs = tmp_path / 'admitted-docs'
    for row in raw['head_shell']['files']:
        source = historical / 'docs' / row['path']
        if source.is_symlink() or source.stat().st_size != row['bytes'] or checker.sha256(source) != row['sha256']:
            pytest.fail('Historical shell fixture does not match its admitted bytes')
        destination = docs / row['path']
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    monkeypatch.setattr(builder, 'ROOT', historical)
    monkeypatch.setattr(checker, 'DOCS', docs)
    record = checker.load_manifest()
    assert checker.check_pages_admission() == record
    return record


def test_actual_successor_docs_still_fail_admission():
    assert builder.ROOT == ROOT and checker.DOCS == ROOT / 'docs'
    with pytest.raises(RuntimeError, match='^Research companion Pages admission differs from exact source bytes$'):
        checker.check_pages_admission()


def test_historical_fixture_rejects_changed_companion_bytes(admitted, tmp_path, monkeypatch):
    changed = tmp_path / 'changed-historical-input'
    paths = [builder.COMPANION_ROOT + '/' + x['path'] for x in admitted['research_companion']['files']]
    paths += [x['path'] for x in admitted['research_companion']['support_files']]
    for name in paths:
        target = changed / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(builder.ROOT / name, target)
    altered = changed / builder.COMPANION_ROOT / 'explorer/README.md'
    altered.write_bytes(altered.read_bytes() + b'\nfixture mutation\n')
    monkeypatch.setattr(builder, 'ROOT', changed)
    with pytest.raises(RuntimeError, match='^Research companion Pages admission differs from exact source bytes$'):
        checker.load_manifest()


@pytest.mark.parametrize('fault', ['direct', 'ancestor', 'late_file', 'late_hardlink', 'late_directory', 'parent_file'])
def test_copy_rejects_alias_or_shared_target_before_writing(admitted, tmp_path, fault):
    good = tmp_path / 'positive'
    checker.copy_admitted_shell(good)
    assert len(snapshot(good)) == 11
    victim = tmp_path / 'victim'
    victim.mkdir()
    (victim / 'sentinel').write_text('preserve external bytes')
    site = tmp_path / 'site'
    site.mkdir()
    if fault == 'direct':
        site.rmdir(); site.symlink_to(victim, target_is_directory=True)
    elif fault == 'ancestor':
        site.rmdir(); site.symlink_to(victim, target_is_directory=True); site = site / 'nested'
    elif fault in {'late_file', 'late_hardlink', 'late_directory'}:
        target = site / admitted['head_shell']['files'][-1]['path']
        target.parent.mkdir(parents=True, exist_ok=True)
        if fault == 'late_file': target.symlink_to(victim / 'sentinel')
        elif fault == 'late_hardlink': os.link(victim / 'sentinel', target)
        else: target.mkdir()
    else:
        (site / 'resources').write_text('preserve parent collision')
    before_site = snapshot(site) if site.exists() else {}
    before_victim = snapshot(victim)
    guard = 'link or junction' if fault in {'direct', 'ancestor', 'late_file'} else 'regular unshared|parent must be a directory|unexpected file'
    with pytest.raises(RuntimeError, match=guard): checker.copy_admitted_shell(site)
    assert snapshot(victim) == before_victim
    assert (snapshot(site) if site.exists() else {}) == before_site


@pytest.mark.parametrize('fault', ['extra', 'different'])
def test_existing_roster_and_bytes_are_checked_before_copy(admitted, tmp_path, fault):
    positive = tmp_path / 'positive'; checker.copy_admitted_shell(positive)
    before = snapshot(positive); checker.copy_admitted_shell(positive)
    assert snapshot(positive) == before
    site = tmp_path / 'site'; site.mkdir()
    if fault == 'extra': (site / 'sentinel').write_text('preserve')
    else: (site / 'index.html').write_text('preserve different index')
    before = snapshot(site)
    with pytest.raises(RuntimeError, match='unexpected file|differing file'):
        checker.copy_admitted_shell(site)
    assert snapshot(site) == before


def atlas_fixture(tmp_path):
    spec = importlib.util.spec_from_file_location('historical_pages_fixture', ROOT / 'tests/test_pages_admission.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module._atlas_fixture(tmp_path)


@pytest.mark.parametrize('entrypoint', ['assemble', 'assemble_atlas_routes'])
def test_assembly_entrypoints_preserve_lexical_alias(admitted, tmp_path, entrypoint):
    assets, source = atlas_fixture(tmp_path)
    positive = tmp_path / 'positive'
    assembly.assemble(positive, assets, source)
    assert (positive / 'resources/dark-medium-response-atlas/v0.1.0/index.html').is_file()
    victim = tmp_path / 'victim'
    victim.mkdir()
    if entrypoint == 'assemble_atlas_routes': checker.copy_admitted_shell(victim)
    alias = tmp_path / 'alias'; alias.symlink_to(victim, target_is_directory=True)
    before = snapshot(victim)
    with pytest.raises(RuntimeError, match='link or junction'):
        getattr(assembly, entrypoint)(alias, assets, source)
    assert snapshot(victim) == before


def test_atlas_route_ancestor_alias_is_rejected_before_writing(admitted, tmp_path):
    assets, source = atlas_fixture(tmp_path)
    positive = tmp_path / 'positive'
    assembly.assemble(positive, assets, source)
    site = tmp_path / 'site'; checker.copy_admitted_shell(site)
    victim = tmp_path / 'victim'; victim.mkdir()
    (victim / 'sentinel').write_text('preserve')
    (site / 'resources/dark-medium-response-atlas').symlink_to(victim, target_is_directory=True)
    before_site, before_victim = snapshot(site), snapshot(victim)
    with pytest.raises(RuntimeError, match='link or junction'):
        assembly.assemble_atlas_routes(site, assets, source)
    assert snapshot(site) == before_site
    assert snapshot(victim) == before_victim
