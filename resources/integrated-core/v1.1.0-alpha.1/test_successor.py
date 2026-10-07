"""Actual source/production positives precede isolated corruption controls."""
import copy,importlib.util,json,os,shutil,subprocess,sys
from pathlib import Path
import pytest
P=Path(__file__).resolve().parent
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
g=module('successor025',P/'verify_successor.py')
b=module('documents025',P/'build_documents.py')

@pytest.fixture(scope='module')
def actual(tmp_path_factory):
    settings=json.loads(Path(os.environ['ASTRA025_INPUTS']).read_text())
    source=Path(settings['source']);production=Path(settings['production'])
    sr=g.load(Path(settings['source_record']),settings['source_record_sha256'])
    receipt=g.load(Path(settings['receipt']),settings['receipt_sha256'])
    g.source_check(source,sr);contract=g.spec();g.verify_production(production,sr,receipt,contract)
    temp=tmp_path_factory.mktemp('successor025');sc=temp/'source';stage=temp/'stage'
    shutil.copytree(source,sc);shutil.copytree(production/'pass-1',stage,ignore=shutil.ignore_patterns('tmp'))
    return settings,source,production,sr,receipt,contract,sc,stage,temp

def test_exact_versioned_plan_and_entrypoint():
    b.validate_plan(b.PLAN)
    result=json.loads(subprocess.check_output([sys.executable,'-I','-B',str(P/'version.py')],text=True))
    assert result['version']=='1.1.0-alpha.1' and result['candidate_tag']==g.TAG
    assert result['publication_authorized'] is False

@pytest.mark.parametrize('field,value',[('release_version',None),('release_version','1x1x0-alphaX1'),('release_tag','v1.1.0-alpha.1'),('status','ADMITTED'),('output_directory','manuscript'),('epoch_is_release_date',True)])
def test_plan_rejects_wrong_version_and_scope(field,value):
    b.validate_plan(b.PLAN);bad=copy.deepcopy(b.PLAN);bad[field]=value
    with pytest.raises(RuntimeError):b.validate_plan(bad)

def test_plan_rejects_swapped_documents_and_titles():
    for field in ['stem','title','source']:
        bad=copy.deepcopy(b.PLAN);a,z=bad['documents'];a[field],z[field]=z[field],a[field]
        with pytest.raises(RuntimeError,match='Exact source'):b.validate_plan(bad)

def test_unversioned_or_historical_output_refused():
    for name in ['ASTRA_integrated_manuscript_draft.pdf','SPPT_ASTRA_preprint_v1.0.7.pdf','document_identity.extra.json']:
        with pytest.raises(RuntimeError,match='exact filename'):b.ensure_safe_output(b.OUTPUT_ROOT/name)

def test_snapshot_empty_partial_duplicate_rejected(tmp_path,monkeypatch):
    shutil.copyfile(b.MANUSCRIPT/'snapshot-roster.json',tmp_path/'snapshot-roster.json')
    original=json.loads((b.MANUSCRIPT/'source-snapshot.json').read_text())
    monkeypatch.setattr(b,'MANUSCRIPT',tmp_path)
    for rows in [[],original['files'][:-1],original['files']+[original['files'][0]]]:
        (tmp_path/'source-snapshot.json').write_text(json.dumps({**original,'files':rows}))
        with pytest.raises(RuntimeError,match='Exact nonempty'):b.validate_source_snapshot()

def test_wki_limitations_and_claims_are_preserved():
    text=(b.MANUSCRIPT/'supplement.md').read_text()
    for phrase in ['CVG-06/07 or reaudit CVG-08–12','A discrete domain may not admit','Marginal sectors, nonlinear integration','transformed-background R6 comparison remain open']:
        assert phrase in text
    assert 'proposed unified successor' not in text
    assert 'no version, tag, clean committed' not in text

def test_actual_source_production_pages_and_runtime(actual):
    settings,source,production,sr,receipt,contract,*_=actual
    assert len(g.verify_production(production,sr,receipt,contract)['status'])>0
    for profile in ['science','wki']:
        assert g.runtime_check(settings[profile+'_python'],profile)['profile']==profile
    assert len(receipt['passes'][0]['outputs'])==69 and len(receipt['passes'][0]['pages'])==194

def test_actual_reading_contracts_and_pdf_inspection(actual):
    _,_,production,_,receipt,_,*_=actual
    rb=module('produced_documents025',production/'pass-1'/g.PREFIX/'build_documents.py')
    rb.validate_plan(rb.PLAN);rb.validate_source_snapshot();rb.validate_figure_declaration()
    for source,html,pdf,title in rb.DOCUMENTS:
        expected=rb.source_contract(source,title)
        assert rb.validate_static_html(html.read_text(),expected)['status']=='PASS'
        result=rb.inspect_draft_pdf(pdf)
        assert result['tagged'] and result['all_pages_have_extractable_text']

@pytest.mark.parametrize('field',g.FLAGS)
def test_admission_flags_refused(actual,field):
    _,source,_,sr,*_=actual;bad=copy.deepcopy(sr);bad[field]=True
    with pytest.raises(RuntimeError,match='ADMISSION_FORBIDDEN'):g.source_check(source,bad)

@pytest.mark.parametrize('field,value,guard',[('protected_payload',{},'MANDATORY_PROTECTED_BINDINGS'),('historical_authorities',{},'MANDATORY_PROTECTED_BINDINGS'),('claim_bindings',{},'MANDATORY_PROTECTED_BINDINGS'),('base_commit','invented','SOURCE_SCOPE'),('final_commit','invented','SOURCE_SCOPE'),('claim_status_upgraded',True,'SOURCE_SCOPE'),('historical_windows_equivalence',True,'SCIENTIFIC_SCOPE')])
def test_protected_source_scope_refused(actual,field,value,guard):
    _,source,_,sr,*_=actual;bad=copy.deepcopy(sr);bad[field]=value
    with pytest.raises(RuntimeError,match=guard):g.source_check(source,bad)

@pytest.mark.parametrize('mutation',['missing','extra','changed','symlink','hardlink'])
def test_real_source_corruption(actual,mutation):
    *_,sc,stage,temp=actual;sr=actual[3];g.source_check(sc,sr)
    p=sc/g.PREFIX/'VERSION.json';old=p.read_bytes();extra=sc/'unlisted.txt';alias=temp/'hardlink'
    try:
        if mutation=='missing':p.unlink()
        elif mutation=='extra':extra.write_text('unlisted')
        elif mutation=='changed':p.write_bytes(old+b' ')
        elif mutation=='symlink':p.unlink();p.symlink_to(actual[1]/g.PREFIX/'VERSION.json')
        else:os.link(p,alias)
        with pytest.raises(RuntimeError):g.source_check(sc,sr)
    finally:
        if p.is_symlink():p.unlink()
        p.write_bytes(old)
        if extra.exists():extra.unlink()
        if alias.exists():alias.unlink()
    g.source_check(sc,sr)

@pytest.mark.parametrize('fault',['missing','extra','input_change','reading_duplicate','empty_figures','inspection_duplicate'])
def test_real_output_and_reading_corruptions(actual,fault):
    settings,source,production,sr,receipt,contract,sc,stage,temp=actual
    inputs=receipt['inputs'];g.outputs_check(stage,inputs,contract)
    png=next(n for n in contract['outputs'] if n.endswith('.png'))
    target=stage/png;restore=None;extra=stage/'extra-public.txt'
    if fault=='input_change':target=stage/g.PREFIX/'VERSION.json'
    if fault in ['reading_duplicate','empty_figures']:target=stage/g.PREFIX/'reading/document_identity.json'
    if fault=='inspection_duplicate':target=stage/g.PREFIX/'reading/pdf_inspection.json'
    restore=target.read_bytes()
    try:
        if fault=='missing':target.unlink()
        elif fault=='extra':extra.write_text('extra')
        elif fault=='input_change':target.write_bytes(restore+b' ')
        else:
            value=json.loads(restore)
            if fault=='empty_figures':value['figure_inputs']['figures']={}
            else:value['records'][1]=value['records'][0]
            target.write_text(json.dumps(value))
        with pytest.raises(RuntimeError):g.outputs_check(stage,inputs,contract)
    finally:
        target.write_bytes(restore)
        if extra.exists():extra.unlink()
    g.outputs_check(stage,inputs,contract)

def test_pages_positive_then_production_tamper_has_zero_writes(actual):
    settings,source,production,sr,receipt,contract,sc,stage,temp=actual
    plan=json.loads((P/'PAGES_PLAN.json').read_text());retained=Path(settings['retained_preview']);positive=temp/'positive-pages'
    g.assemble_pages(source,stage,retained,positive,plan,inputs=receipt['inputs'],contract=contract,output_map=receipt['passes'][0]['outputs'])
    assert g.inventory(positive)==receipt['passes'][0]['pages']
    target=stage/next(n for n in contract['outputs'] if '/generated/' in n and n.endswith('.png'));old=target.read_bytes();destination=temp/'tampered-pages'
    try:
        target.write_bytes(old+b'tamper')
        with pytest.raises(RuntimeError,match='PRODUCTION_OUTPUT_IDENTITY'):
            g.assemble_pages(source,stage,retained,destination,plan,inputs=receipt['inputs'],contract=contract,output_map=receipt['passes'][0]['outputs'])
        assert not destination.exists()
    finally:target.write_bytes(old)

@pytest.mark.parametrize('fault',['empty_passes','wrong_source','forged_pass','admission','duplicate_pass'])
def test_production_receipt_cannot_forge_success(actual,fault):
    _,_,production,sr,receipt,contract,*_=actual;bad=copy.deepcopy(receipt)
    if fault=='empty_passes':bad['passes']=[]
    elif fault=='wrong_source':bad['source_files']={}
    elif fault=='forged_pass':bad['passes'][0]['outputs_present_before']=1
    elif fault=='admission':bad['pages_admitted']=True
    else:bad['passes'][1]=bad['passes'][0]
    with pytest.raises(RuntimeError):g.verify_production(production,sr,bad,contract)

def test_wrong_runtime_and_tag_rejected(actual):
    settings,source,_,sr,*_=actual
    with pytest.raises(RuntimeError,match='RUNTIME_EXECUTABLE'):g.runtime_check(settings['wki_python'],'science')
    with pytest.raises(RuntimeError,match='TAG_CONTEXT_FORBIDDEN'):g.source_check(source,sr,tag_context=True)

def test_runtime_bytes_not_just_package_versions(tmp_path):
    import hashlib
    file=tmp_path/'package.py';file.write_text('original')
    rows={'package.py':{'bytes':file.stat().st_size,'sha256':g.sha(file)}}
    expected=hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    assert g.runtime_tree(tmp_path,expected)['files']==1
    file.write_text('modified')
    with pytest.raises(RuntimeError,match='RUNTIME_INSTALLED_BYTES'):g.runtime_tree(tmp_path,expected)

def test_pages_disk_and_forged_receipt_cannot_agree_on_wrong_tree(actual):
    _,_,production,sr,receipt,contract,_,_,temp=actual
    g.verify_production(production,sr,receipt,contract)
    private=temp/'forged-production'
    for name in ['pass-1','pass-2','pages-1','pages-2']:
        shutil.copytree(production/name,private/name,ignore=shutil.ignore_patterns('tmp'))
    production=private
    bad=copy.deepcopy(receipt);changed=[]
    name=next(n for n in receipt['passes'][0]['pages'] if n.endswith('.html'))
    try:
        for i in [1,2]:
            p=production/f'pages-{i}'/name;changed.append((p,p.read_bytes()));p.write_bytes(b'forged')
            bad['passes'][i-1]['pages'][name]={'bytes':p.stat().st_size,'sha256':g.sha(p)}
        with pytest.raises(RuntimeError,match='PAGES_RECEIPT_IDENTITY'):g.verify_production(production,sr,bad,contract)
    finally:
        for p,data in changed:p.write_bytes(data)
    g.verify_production(production,sr,receipt,contract)

@pytest.mark.parametrize('fault',['removed_route','source_hash','destination','admitted'])
def test_pinned_pages_plan_cannot_be_weakened(actual,fault):
    _,_,_,sr,receipt,_,*_=actual
    plan=json.loads((P/'PAGES_PLAN.json').read_text());outputs=receipt['passes'][0]['outputs']
    assert len(g.pages_expected(plan,sr['files'],outputs))==194
    if fault=='removed_route':plan['routes'].pop()
    elif fault=='source_hash':next(x for x in plan['routes'] if x['family']=='source')['expected']['sha256']='0'*64
    elif fault=='destination':plan['routes'][1]['destination']=plan['routes'][0]['destination']
    else:plan['pages_admitted']=True
    with pytest.raises(RuntimeError):g.pages_expected(plan,sr['files'],outputs)

def test_input_only_stage_refuses_reuse_and_overlap(actual):
    _,source,_,_,receipt,contract,_,_,temp=actual
    dest=temp/'input-only';g.prepare(source,dest,receipt['inputs'],contract['outputs'])
    assert not any((dest/n).exists() for n in contract['outputs'])
    with pytest.raises(RuntimeError,match='NEW_STAGE_REQUIRED'):g.prepare(source,dest,receipt['inputs'],contract['outputs'])
    with pytest.raises(RuntimeError,match='STAGE_OVERLAP'):g.prepare(source,source/'forbidden',receipt['inputs'],contract['outputs'])


def test_long_versioned_frontmatter_title_is_not_line_wrapped(tmp_path):
    title=b.PLAN['documents'][0]['title']
    assert len(title)>72
    source=tmp_path/'long-title.md'
    source.write_text('---\ntitle: '+json.dumps(title)+'\n---\n\nA bounded test source.\n')
    assert b.source_contract(source,title)=={'tables':0,'figures':0,'formulas':0}
    with pytest.raises(RuntimeError,match='frontmatter'):b.source_contract(source,title+' changed')
