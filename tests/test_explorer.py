"""Draft explorer fixture, geometry, and bounded content contracts."""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXPLORER = ROOT / "resources/sppt-scm-research-companion/draft-v0.1.0/explorer"
PAGE = EXPLORER / "index.html"


def script(name: str) -> str:
    text = PAGE.read_text(encoding="utf-8")
    match = re.search(r'<script id="' + name + r'"[^>]*>(.*?)</script>', text, re.S)
    assert match is not None
    return match[1]


def test_retained_fixture_is_exact() -> None:
    import csv

    fixture = json.loads(script("fixture"))
    with (ROOT / "data/two_reservoir_step_response.csv").open() as handle:
        rows = list(csv.DictReader(handle))
    for coupling in (0.05, 0.2, 1.0):
        expected = [
            [float(row[key]) for key in ("time", "surface_state", "deep_state")]
            for row in rows if float(row["conductance"]) == coupling
        ]
        assert fixture[str(coupling)] == expected
        assert len(expected) == 900
    provenance = json.loads((EXPLORER / "provenance.json").read_text())
    assert provenance["modules"][1]["sha256"] == hashlib.sha256(
        (ROOT / "data/two_reservoir_step_response.csv").read_bytes()
    ).hexdigest()


def test_geometry_and_frames() -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node is required for the optional browser-model calculation diagnostic")
    assertions = r'''
const assert = require('node:assert/strict');
const near=(a,b)=>assert.ok(Math.abs(a-b)<1e-12, `${a} != ${b}`);
for(const straight of [false,true]) for(let u=-3.14;u<=3.14;u+=.01){
 const g=Model.geometry(u,straight),P=Model.projector(g.t);
 for(const v of [g.t,g.n,g.b]) near(v.reduce((s,x)=>s+x*x,0),1);
 for(const v of [g.n,g.b]) near(v.reduce((s,x,i)=>s+x*g.t[i],0),0);
 for(let i=0;i<3;i++){
  near(P[i].reduce((s,x,j)=>s+x*g.t[j],0),0);
  for(let j=0;j<3;j++)near(P[i].reduce((s,x,k)=>s+x*P[k][j],0),P[i][j]);
 }
}
for(const time of [0,1,4,30]){
 near(Model.angular(.2,.2,time),0);
 near(Model.angular(.35,.2,time),Model.angular(.35,0,time)-.2*time);
 near(Model.angular(.35,0,2*time),2*Model.angular(.35,0,time));
}
'''
    subprocess.run([node, "-e", script("model-code") + assertions], check=True)


def test_local_fragments_and_no_external_runtime() -> None:
    text = PAGE.read_text()
    ids = re.findall(r'\bid="([^"]+)"', text)
    assert len(ids) == len(set(ids))
    for target in re.findall(r'href="#([^"]+)"', text):
        assert target in ids
    assert '<script src=' not in text
    assert '<link ' not in text
    assert 'requestAnimationFrame' not in text
    assert 'prefers-reduced-motion:reduce' in text
    assert '<noscript>' in text
    assert 'v1.0.7' in text and 'unpromoted' in text
    assert 'not a fitted Saturn simulation' in text


def test_explorer_text_privacy() -> None:
    from tools.check_repository import PRIVATE_PATTERNS

    text = PAGE.read_text()
    for label, pattern in PRIVATE_PATTERNS.items():
        assert not pattern.search(text), label


def test_retained_samples_against_independent_matrix_exponential() -> None:
    import numpy as np
    from scipy.linalg import expm

    fixture = json.loads(script("fixture"))
    for coupling, rows in fixture.items():
        k = float(coupling)
        # Independent affine system in augmented coordinates [Ts, Td, 1].
        augmented = np.array([[-(k + 1), k, 0], [k / 20, -k / 20, 1 / 20], [0, 0, 0]])
        for time, surface, deep in rows:
            expected = expm(augmented * time) @ [0, 0, 1]
            np.testing.assert_allclose([surface, deep], expected[:2], rtol=1e-12, atol=1e-12)
            derivative = augmented @ [surface, deep, 1]
            assert abs(derivative[0] + 20 * derivative[1] - (1 - surface)) < 1e-12
    # The same independently assembled system at zero coupling leaves Ts=0,
    # while the constantly driven deep reservoir grows as t/20.
    zero = np.array([[-1, 0, 0], [0, 0, 0.05], [0, 0, 0]])
    np.testing.assert_allclose(expm(zero * 500) @ [0, 0, 1], [0, 25, 1], atol=1e-12)


def test_render_callbacks_without_browser() -> None:
    """Pure JS callbacks with a DOM stub; not a browser/keyboard/layout test."""
    from html.parser import HTMLParser

    node = shutil.which("node")
    if node is None:
        pytest.skip("Node is required for the optional rendering-callback diagnostic")

    class Elements(HTMLParser):
        def __init__(self) -> None:
            super().__init__()
            self.records: dict[str, dict[str, str]] = {}
            self.select: str | None = None

        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            attributes = {key: value or "" for key, value in attrs}
            if "id" in attributes:
                self.records[attributes["id"]] = attributes
            if tag == "select":
                self.select = attributes["id"]
            elif tag == "option" and self.select:
                record = self.records[self.select]
                if "value" not in record or "selected" in attributes:
                    record["value"] = attributes["value"]

        def handle_endtag(self, tag: str) -> None:
            if tag == "select":
                self.select = None

    parser = Elements()
    parser.feed(PAGE.read_text())
    preamble = "const records=" + json.dumps(parser.records) + ";\n"
    preamble += "const fixtureText=" + json.dumps(script("fixture")) + ";\n"
    preamble += r'''
const assert=require('node:assert/strict');
const nodes={};
for(const [id,attrs] of Object.entries(records)){
 nodes[id]={attrs:{...attrs},_value:attrs.value||'',handlers:{},
 get value(){return this._value;},set value(v){this._value=String(v);},
 textContent:id==='fixture'?fixtureText:'',
 setAttribute(k,v){this.attrs[k]=String(v);},
 addEventListener(k,fn){this.handlers[k]=fn;}};
}
const document={getElementById(id){assert.ok(nodes[id],id);return nodes[id];}};
'''
    assertions = r'''
const update=(id,value)=>{nodes[id].value=value;nodes[id].handlers.input();};
const attr=(id,key)=>nodes[id].attrs[key];
const near=(a,b)=>assert.ok(Math.abs(a-b)<1e-10,`${a} != ${b}`);
update('sat-time',7.3);
near(+attr('tracer-a','cx'),310+110*Math.cos(.35*7.3));
const at73=attr('pattern','d');
update('sat-time',22);update('sat-time',7.3);assert.equal(attr('pattern','d'),at73);
update('frame','pattern');const fixed=attr('pattern','d');
update('sat-time',18.2);assert.equal(attr('pattern','d'),fixed);
near(+attr('tracer-b','cy'),175+145*Math.sin((.15-.2)*18.2));
update('speed',-.3);
near(+attr('tracer-a','cy'),175+110*Math.sin((.35+.3)*18.2));
nodes['sat-reset'].onclick();assert.equal(nodes['sat-time'].value,'0');
assert.equal(nodes.frame.value,'inertial');assert.equal(nodes.speed.value,'0.2');
for(const coupling of ['0.05','0.2','1.0']){
 update('coupling',coupling);
 for(const i of [0,417,899]){
  update('sample',i);const row=JSON.parse(fixtureText)[coupling][i];
  assert.equal(nodes.surface.value,row[1].toFixed(3));
  assert.equal(nodes.deep.value,row[2].toFixed(3));
  assert.equal(nodes['sample-time'].value,row[0].toFixed(2));
  assert.ok(!/NaN|Infinity/.test(attr('curve-deep','d')));
 }
}
nodes['res-reset'].onclick();assert.equal(nodes.coupling.value,'0.2');
assert.equal(nodes.sample.value,'0');assert.equal(nodes.surface.value,'0.000');
for(const shape of ['helix','straight'])for(const u of [-3.14,0,3.14]){
 update('shape',shape);update('position',u);
 for(const id of ['helix','normal-plane','tangent'])assert.ok(!/NaN|Infinity/.test(attr(id,'d')));
}
nodes['geo-reset'].onclick();assert.equal(nodes.shape.value,'helix');
assert.equal(nodes.position.value,'0');
console.log('Callbacks passed; actual browser behavior remains untested.');
'''
    subprocess.run(
        [node], input=preamble + script("model-code") + script("render-code") + assertions,
        text=True, check=True,
    )


def test_production_docs_are_unchanged_and_candidate_is_bounded() -> None:
    from tools.build_pages_admission import docs_entries
    from tools.check_repository import RESEARCH_EXPLORER_FILES, RESEARCH_EXPLORER_ROOT

    assert docs_entries()
    assert RESEARCH_EXPLORER_ROOT == EXPLORER.relative_to(ROOT).as_posix()
    assert {path.name for path in EXPLORER.iterdir()} == set(RESEARCH_EXPLORER_FILES)


def test_approved_collection_is_complete_and_byte_pinned() -> None:
    from pypdf import PdfReader

    from tools.check_repository import check_research_companion

    check_research_companion()
    package = EXPLORER.parent / "package"
    assert len(list(package.rglob("*.pdf"))) == 2
    assert len(PdfReader(next((package / "research").glob("*.pdf"))).pages) == 35
    assert len(PdfReader(next((package / "visuals").glob("*.pdf"))).pages) == 12
    assert len(list(package.rglob("*.svg"))) == 6
    assert len(list(package.rglob("*.png"))) == 11
    assert len(list(package.rglob("*.gif"))) == 2
    assert len(list(package.rglob("*.mp4"))) == 2
    assert not list(package.rglob("*.zip"))


def test_collection_rejects_changed_or_unreviewed_payload(tmp_path: Path, monkeypatch) -> None:
    from tools import check_repository as contract

    destination = tmp_path / contract.RESEARCH_COMPANION_ROOT
    shutil.copytree(EXPLORER.parent, destination)
    monkeypatch.setattr(contract, "ROOT", tmp_path)
    package = destination / "package"
    original = package / "README.md"
    original.write_bytes(original.read_bytes() + b"\nUnreviewed addition.\n")
    with pytest.raises(RuntimeError, match="approved bytes changed"):
        contract.check_research_companion()
    original.write_bytes((EXPLORER.parent / "package/README.md").read_bytes())
    (package / "extra.txt").write_text("Unreviewed file")
    with pytest.raises(RuntimeError, match="roster drift"):
        contract.check_research_companion()
    generator = tmp_path / contract.RESEARCH_GENERATOR_PATH
    contract.check_text_privacy([generator])
    generator.write_bytes(generator.read_bytes() + b"\n# Changed source\n")
    with pytest.raises(RuntimeError, match="local Windows path"):
        contract.check_text_privacy([generator])


def test_media_links_and_motion_defaults() -> None:
    from html.parser import HTMLParser
    from urllib.parse import unquote, urlsplit

    class Elements(HTMLParser):
        def __init__(self):
            super().__init__()
            self.elements = []

        def handle_starttag(self, tag, attrs):
            self.elements.append((tag, dict(attrs)))

    parser = Elements()
    parser.feed(PAGE.read_text())
    images = [attrs for tag, attrs in parser.elements if tag == "img"]
    videos = [attrs for tag, attrs in parser.elements if tag == "video"]
    assert len(images) == 9
    assert len(videos) == 2
    for attrs in images:
        assert attrs["alt"].strip()
        assert int(attrs["width"]) > 0 and int(attrs["height"]) > 0
    for attrs in videos:
        assert "controls" in attrs and "playsinline" in attrs
        assert "autoplay" not in attrs and "loop" not in attrs
        assert attrs["preload"] == "none"
        assert attrs["poster"].endswith("_poster.png")
        assert attrs["aria-describedby"]
    for tag, attrs in parser.elements:
        for key in ("href", "src", "poster"):
            if key not in attrs:
                continue
            url = urlsplit(attrs[key])
            if url.scheme:
                assert url.scheme == "https"
                assert tag == "a", "External resources must be links, not runtime requests"
            elif url.path:
                resolved = (EXPLORER / unquote(url.path)).resolve()
                assert resolved.is_relative_to(EXPLORER.parent)
                assert resolved.is_file(), attrs[key]
                if tag in ("img", "source"):
                    assert not resolved.name.endswith(".gif"), "GIF motion must be opt-in"
