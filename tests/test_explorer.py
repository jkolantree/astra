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
SIGNALS = ROOT / "docs/understand/signals"


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


def run_signal_model_assertions(assertions: str) -> None:
    """Execute the actual page model in Node, without a browser or DOM."""
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node is required for the optional signal-model calculation diagnostic")
    preamble = "const Model=require(" + json.dumps(str(SIGNALS / "signals.js")) + ");\n"
    preamble += r'''
const assert=require('node:assert/strict');
const near=(actual,expected,rtol=1e-11,atol=0)=>{
 assert.ok(Number.isFinite(actual), `Nonfinite result: ${actual}`);
 assert.ok(Math.abs(actual-expected)<=atol+rtol*Math.abs(expected),
  `${actual} != ${expected}`);
};
'''
    subprocess.run([node], input=preamble + assertions, text=True, check=True)


def test_signal_modulation_reconstructs_real_sidebands_with_correct_phases() -> None:
    run_signal_model_assertions(r'''
assert.equal(Model.yearDays,365.25);
for(const depth of [0,.2,.7,1])for(const phase of [-2.4,0,.8,Math.PI]){
 const components=Model.components(depth,phase).sort((a,b)=>a.frequency-b.frequency);
 assert.equal(components.length,3);
 const [lower,carrier,upper]=components;
 near(carrier.frequency,1);
 near(upper.frequency-carrier.frequency,1/365.25);
 near(carrier.frequency-lower.frequency,1/365.25);
 near(carrier.amplitude,1);
 near(lower.amplitude,depth/2);
 near(upper.amplitude,depth/2);
 near(carrier.phase,0,0,1e-14);
 // The lower sideband has -psi, the upper has +psi for phi = 0.
 near(Math.sin(lower.phase),-Math.sin(phase),1e-11,1e-14);
 near(Math.cos(lower.phase),Math.cos(phase),1e-11,1e-14);
 near(Math.sin(upper.phase),Math.sin(phase),1e-11,1e-14);
 near(Math.cos(upper.phase),Math.cos(phase),1e-11,1e-14);
 for(const days of [0,.125,1,22.7,365.25/4,365.25,700.31]){
  const reconstructed=components.reduce((sum,c)=>
   sum+c.amplitude*Math.cos(2*Math.PI*c.frequency*days+c.phase),0);
  near(Model.am(days,depth,phase),reconstructed,1e-10,2e-12);
 }
}
// Under the stated 365.25-day approximation this is about 23 h 56 min,
// not an independently measured astronomical period.
const siderealHours=24/Model.components(1,0).find(c=>c.frequency>1).frequency;
assert.ok(siderealHours>23.93 && siderealHours<23.94);
''')


def test_passive_sensor_units_scaling_and_transfer_function() -> None:
    run_signal_model_assertions(r'''
const boltzmann=1.380649e-23;
const baseline=Model.sensor(1);
for(const ratio of [.1,.25,1,2]){
 const s=Model.sensor(ratio);
 near(s.kappa,ratio*1e-18);
 near(s.gamma,1e-18);
 near(s.mu,1e-16);
 near(s.kBT,boltzmann*300);
 // Unit-bearing identities: tau in s, cutoff in Hz, variance in rad^2,
 // static gain in rad/T, and input PSD in T^2/Hz.
 near(s.tau*s.kappa,s.gamma);
 near(s.cutoff*s.tau,1/(2*Math.PI));
 near(s.variance*s.kappa,s.kBT);
 near(s.staticGain*s.kappa,s.mu);
 near(s.inputPSD*s.mu*s.mu,4*s.kBT*s.gamma);
 near(s.tau*ratio,baseline.tau);
 near(s.cutoff/ratio,baseline.cutoff);
 near(s.variance*ratio,baseline.variance);
 near(s.staticGain*ratio,baseline.staticGain);
 near(s.inputPSD,baseline.inputPSD);
 for(const frequency of [0,s.cutoff,10*s.cutoff,1e4*s.cutoff]){
  const r=Model.response(frequency,ratio);
  const scaled=frequency/s.cutoff;
  near(r.gain/s.staticGain,1/Math.sqrt(1+scaled*scaled));
  near(r.phase,-Math.atan(scaled),1e-11,1e-14);
  near(Model.outputPSD(frequency,ratio)/(r.gain*r.gain),s.inputPSD);
 }
 near(Model.response(s.cutoff,ratio).gain,s.staticGain/Math.sqrt(2));
 near(Model.response(s.cutoff,ratio).phase,-Math.PI/4);
 near(Model.response(1e5*s.cutoff,ratio).gain*2*Math.PI*1e5*s.cutoff,
  s.mu/s.gamma,1e-9);
}
''')


def test_one_sided_per_hz_sensor_noise_integrates_to_equilibrium_variance() -> None:
    run_signal_model_assertions(r'''
for(const ratio of [.1,1,2]){
 const s=Model.sensor(ratio);
 near(Model.bandVariance(0,ratio),0,0,0);
 near(Model.bandVariance(s.cutoff,ratio),s.variance/2);
 near(Model.bandVariance(1e9*s.cutoff,ratio),s.variance,1e-8);
 // Independent composite Simpson quadrature of the per-Hz spectrum.
 // An accidental two-sided or per-radian convention fails this integral.
 for(const multiple of [.2,1,5]){
  const end=multiple*s.cutoff, intervals=4096, step=end/intervals;
  let total=Model.outputPSD(0,ratio)+Model.outputPSD(end,ratio);
  for(let i=1;i<intervals;i++)total+=(i%2?4:2)*Model.outputPSD(i*step,ratio);
  const integral=step*total/3;
  near(Model.bandVariance(end,ratio),integral,1e-10);
  near(integral/s.variance,2*Math.atan(multiple)/Math.PI,1e-10);
 }
 // A spectral amplitude density is not the RMS noise in a finite band.
 const band=Model.bandVariance(s.cutoff,ratio);
 assert.ok(Math.abs(band-Model.outputPSD(0,ratio)*s.cutoff)>band*.2);
 assert.ok(Model.bandVariance(2*s.cutoff,ratio)>band);
 assert.ok(Model.bandVariance(2*s.cutoff,ratio)<s.variance);
}
''')


def test_passive_sensor_step_response_has_the_stated_speed_and_static_limit() -> None:
    run_signal_model_assertions(r'''
for(const ratio of [.1,.5,1,2]){
 const s=Model.sensor(ratio);
 for(const field of [0,1e-4,1e-3]){
  near(Model.step(0,ratio,field),0,0,0);
  near(Model.step(s.tau,ratio,field),s.staticGain*field*(1-Math.exp(-1)));
  near(Model.step(40*s.tau,ratio,field),s.staticGain*field);
  near(Model.step(.01*s.tau,ratio,field),
   -Math.expm1(-.01)*s.staticGain*field);
 }
 near(Model.step(s.tau,ratio),Model.step(s.tau,ratio,1e-4));
}
// Softening changes the final response and its settling time together;
// equal elapsed time is not equal equilibration across stiffness settings.
assert.ok(Model.step(1,1)/Model.sensor(1).staticGain>
 Model.step(1,.1)/Model.sensor(.1).staticGain);
''')


def test_signal_models_reject_invalid_parameters_and_remain_finite_at_bounds() -> None:
    run_signal_model_assertions(r'''
const invalid=[NaN,Infinity,-Infinity,undefined,null,'1'];
for(const value of invalid){
 for(const call of [()=>Model.am(value,.5,0),()=>Model.am(1,value,0),
  ()=>Model.am(1,.5,value),()=>Model.components(value,0),
  ()=>Model.components(.5,value),()=>Model.sensor(value),
  ()=>Model.response(value,1),()=>Model.response(0,value),
  ()=>Model.outputPSD(value,1),()=>Model.outputPSD(0,value),
  ()=>Model.bandVariance(value,1),()=>Model.bandVariance(0,value),
  ()=>Model.step(value,1),()=>Model.step(0,value)])assert.throws(call);
 // Omitted field has an explicit default; other invalid field values do not.
 if(value!==undefined)assert.throws(()=>Model.step(1,1,value));
}
for(const value of [-.01,1.01]){
 assert.throws(()=>Model.am(0,value,0));
 assert.throws(()=>Model.components(value,0));
}
for(const value of [-Math.PI-.001,Math.PI+.001]){
 assert.throws(()=>Model.am(0,.5,value));
 assert.throws(()=>Model.components(.5,value));
}
for(const value of [-.01,2*365.25+.01])assert.throws(()=>Model.am(value,.5,0));
for(const value of [0,.099,2.001]){
 for(const call of [()=>Model.sensor(value),()=>Model.response(0,value),
  ()=>Model.outputPSD(0,value),()=>Model.bandVariance(0,value),
  ()=>Model.step(0,value)])assert.throws(call);
}
for(const call of [()=>Model.response(-1,1),()=>Model.outputPSD(-1,1),
 ()=>Model.bandVariance(-1,1),()=>Model.step(-1,1),
 ()=>Model.step(1,1,-1e-6),()=>Model.step(1,1,.00101)])assert.throws(call);
for(const ratio of [.1,2]){
 const s=Model.sensor(ratio);
 for(const value of Object.values(s))assert.ok(Number.isFinite(value));
 for(const value of [0,Number.MAX_VALUE]){
  assert.ok(Number.isFinite(Model.response(value,ratio).gain));
  assert.ok(Number.isFinite(Model.response(value,ratio).phase));
  assert.ok(Number.isFinite(Model.outputPSD(value,ratio)));
  assert.ok(Number.isFinite(Model.bandVariance(value,ratio)));
  assert.ok(Number.isFinite(Model.step(value,ratio)));
 }
}
for(const days of [0,2*365.25])for(const depth of [0,1])for(const phase of [-Math.PI,Math.PI])
 assert.ok(Number.isFinite(Model.am(days,depth,phase)));
''')


@pytest.mark.parametrize("ready_state", ["loading", "complete"])
def test_signal_control_callbacks_without_browser(ready_state: str) -> None:
    """Actual callbacks and markup with a DOM stub, not a keyboard/layout test."""
    from html.parser import HTMLParser

    node = shutil.which("node")
    if node is None:
        pytest.skip("Node is required for the optional signal-control callback diagnostic")

    class Elements(HTMLParser):
        def __init__(self) -> None:
            super().__init__()
            self.records: dict[str, dict[str, str | None]] = {}

        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            attributes = dict(attrs)
            if attributes.get("id"):
                self.records[str(attributes["id"])] = attributes

    parser = Elements()
    parser.feed((SIGNALS / "index.html").read_text(encoding="utf-8"))
    preamble = "const records=" + json.dumps(parser.records) + ";\n"
    preamble += "const readyState=" + json.dumps(ready_state) + ";\n"
    preamble += r'''
const assert=require('node:assert/strict');
const nodes={},documentHandlers={};
for(const [id,attrs] of Object.entries(records)){
 nodes[id]={attrs:{...attrs},_value:attrs.value||'',handlers:{},textContent:'',
 disabled:Object.hasOwn(attrs,'disabled'),
 get value(){return this._value;},set value(value){this._value=String(value);},
 setAttribute(key,value){this.attrs[key]=String(value);},
 addEventListener(event,callback){this.handlers[event]=callback;}};
}
globalThis.document={readyState:readyState,
 getElementById(id){return nodes[id]||null;},
 addEventListener(event,callback){documentHandlers[event]=callback;}};
assert.equal(nodes['am-controls'].disabled,true);
assert.equal(nodes['sensor-controls'].disabled,true);
'''
    preamble += "require(" + json.dumps(str(SIGNALS / "signals.js")) + ");\n"
    assertions = r'''
if(readyState==='loading'){
 assert.equal(nodes['am-controls'].disabled,true);
 assert.equal(typeof documentHandlers.DOMContentLoaded,'function');
 documentHandlers.DOMContentLoaded();
}
assert.equal(nodes['am-controls'].disabled,false);
assert.equal(nodes['sensor-controls'].disabled,false);
const update=(id,value)=>{
 nodes[id].value=value;
 assert.equal(typeof nodes[id].handlers.input,'function',id);
 nodes[id].handlers.input();
};
const path=id=>nodes[id].attrs.d;
const value=id=>parseFloat(nodes[id].textContent);
const curves=['annual-envelope','time-signal','time-envelope','time-envelope-negative',
 'step-curve','gain-curve','noise-curve','step-curve-reference',
 'gain-curve-reference','noise-curve-reference'];
// The written default figures must depict the same analytical example before
// and after script initialization; this checks paths, not rendered appearance.
for(const id of curves)assert.equal(path(id),records[id].d,id+' static default');
const finiteCurves=()=>{
 for(const id of curves){
  assert.ok(/^M/.test(path(id)),id);
  assert.ok(!/NaN|Infinity|undefined/.test(path(id)),id);
 }
};
finiteCurves();
assert.deepEqual([0,1,2].map(i=>value('component-amplitude-'+i)),[.3,1,.3]);
assert.deepEqual([0,1,2].map(i=>value('component-phase-'+i)),[0,0,0]);
assert.equal(path('step-curve'),path('step-curve-reference'));
assert.equal(path('gain-curve'),path('gain-curve-reference'));
assert.equal(path('noise-curve'),path('noise-curve-reference'));
for(const depth of [0,1])for(const phase of [-180,180])for(const season of [0,360]){
 update('modulation',depth);update('annual-phase',phase);update('season',season);
 assert.equal(value('component-amplitude-0'),depth/2);
 assert.equal(value('component-amplitude-1'),1);
 assert.equal(value('component-amplitude-2'),depth/2);
 finiteCurves();
}
update('modulation',.6);update('annual-phase',0);update('season',90);
const originalSignal=path('time-signal');
const amplitudes=[0,1,2].map(i=>nodes['component-amplitude-'+i].textContent);
const bars=[0,1,2].map(i=>nodes['component-'+i].attrs.y2);
update('annual-phase',90);
assert.notEqual(path('time-signal'),originalSignal);
assert.deepEqual([0,1,2].map(i=>nodes['component-amplitude-'+i].textContent),amplitudes);
assert.deepEqual([0,1,2].map(i=>nodes['component-'+i].attrs.y2),bars);
assert.ok(value('component-phase-0')<0 && value('component-phase-2')>0);
update('annual-phase',0);
assert.equal(path('time-signal'),originalSignal);

update('stiffness',1);update('duration',5);update('bandwidth',.2);
const inputFloor=nodes['noise-floor'].textContent;
const referenceGain=path('gain-curve-reference'),referenceNoise=path('noise-curve-reference');
const originalGain=value('gain-value'),originalRMS=value('rms-value');
update('stiffness',.1);
assert.ok(value('gain-value')>originalGain && value('rms-value')>originalRMS);
assert.equal(nodes['noise-floor'].textContent,inputFloor);
assert.equal(path('gain-curve-reference'),referenceGain);
assert.equal(path('noise-curve-reference'),referenceNoise);
const responseGain=path('gain-curve'),responseNoise=path('noise-curve');
const shortStep=path('step-curve'),shortEnd=value('step-end');
update('duration',30);
assert.notEqual(path('step-curve'),shortStep);
assert.ok(value('step-end')>shortEnd);
assert.equal(value('step-end'),30); // The x-axis is elapsed seconds, not angle.
assert.equal(path('gain-curve'),responseGain);
assert.equal(path('noise-curve'),responseNoise);
const lowBand=value('band-rms');
update('bandwidth',2);
assert.ok(value('band-rms')>lowBand);
assert.equal(path('gain-curve'),responseGain);
assert.equal(path('noise-curve'),responseNoise);
assert.equal(nodes['noise-floor'].textContent,inputFloor);
for(const ratio of [.1,2])for(const duration of [.2,30])for(const bandwidth of [.01,2]){
 update('stiffness',ratio);update('duration',duration);update('bandwidth',bandwidth);
 const near=(actual,expected)=>assert.ok(Math.abs(actual/expected-1)<.005);
 near(value('gain-value'),100/ratio);
 near(value('rms-value'),Math.sqrt(1.380649e-23*300/(ratio*1e-18)));
 near(value('tau-value'),1/ratio);
 near(value('cutoff-value'),ratio/(2*Math.PI));
 near(value('band-rms'),Math.sqrt(2*1.380649e-23*300/(Math.PI*ratio*1e-18)*
  Math.atan(bandwidth*2*Math.PI/ratio)));
 assert.ok(value('band-rms')<=value('rms-value'));
 assert.equal(nodes['noise-floor'].textContent,inputFloor);
 finiteCurves();
 assert.ok(nodes['am-summary'].textContent.includes('Synthetic analytical signal'));
 assert.ok(nodes['sensor-summary'].textContent.includes('Conditional equilibrium model'));
}
console.log('Signal callbacks passed; actual browser behavior remains untested.');
'''
    subprocess.run([node], input=preamble + assertions, text=True, check=True)


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
    # Keep the legacy node name referenced by retained routing evidence.
    from tools.build_pages_admission import docs_entries

    assert docs_entries(current=True)


def test_candidate_explorer_has_exact_bounded_roster() -> None:
    from tools.check_repository import RESEARCH_EXPLORER_FILES, RESEARCH_EXPLORER_ROOT

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
            elif url.path in {
                "../../../../assets/astra-midnight-occultation.png",
                "../../../../assets/midnight-occultation-provenance.json",
            }:
                target = ROOT / "docs/assets" / Path(url.path).name
                assert target.is_file()
                assert tag == ("img" if target.suffix == ".png" else "a")
            elif url.path == "../../../../library/":
                assert tag == "a" and key == "href"
                assert (ROOT / "docs/library/index.html").is_file()
            elif url.path in {
                "../../../../understand/",
                "../../../../understand/worlds/",
                "../../../../understand/geometry/",
            }:
                from tools.link_audit_common import parse_html

                assert tag == "a" and key == "href"
                target = ROOT / "docs" / url.path.removeprefix("../../../../") / "index.html"
                assert target.is_file()
                if url.fragment:
                    assert unquote(url.fragment) in parse_html(target).ids
            elif url.path:
                resolved = (EXPLORER / unquote(url.path)).resolve()
                assert resolved.is_relative_to(EXPLORER.parent)
                assert resolved.is_file(), attrs[key]
                if tag in ("img", "source"):
                    assert not resolved.name.endswith(".gif"), "GIF motion must be opt-in"
