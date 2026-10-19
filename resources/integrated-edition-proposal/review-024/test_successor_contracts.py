"""Positive-first controls using actual successor and retained preview bytes."""
import copy, importlib.util, json, os, shutil
from contextlib import contextmanager
from pathlib import Path
import pytest

spec=importlib.util.spec_from_file_location('contracts024',Path(__file__).with_name('successor_contracts.py'))
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)

@pytest.fixture(scope='module')
def actual(tmp_path_factory):
    settings=json.loads(Path(os.environ['ASTRA_024_TEST_INPUTS']).read_text())
    tmp=tmp_path_factory.mktemp('actual-contracts')
    source=tmp/'source';site=tmp/'site'
    shutil.copytree(settings['source'],source)
    shutil.copytree(settings['preview'],site)
    sr=v.load(Path(settings['source_record']),settings['source_record_sha256'])
    pr=v.load(Path(settings['pages_record']),settings['pages_record_sha256'])
    v.source_check(source,sr)
    v.pages_check(site,pr,settings['source_record_sha256'])
    return source,site,sr,pr,settings['source_record_sha256']

@contextmanager
def changed(path,data=None):
    old=path.read_bytes() if path.exists() else None
    if data is None:path.unlink()
    else:path.write_bytes(data)
    try:yield
    finally:
        if old is None:path.unlink()
        else:path.write_bytes(old)

def test_actual_positive_source_and_pages(actual):
    source,site,sr,pr,h=actual
    assert v.source_check(source,sr)['files']==len(sr['files'])
    assert v.pages_check(site,pr,h)['files']==194

@pytest.mark.parametrize('kind',['source','pages'])
@pytest.mark.parametrize('mutation,guard',[('changed','SOURCE_HASH'),('missing','SOURCE_ROSTER'),('extra','SOURCE_ROSTER')])
def test_real_byte_and_roster_mutations(actual,kind,mutation,guard):
    source,site,sr,pr,h=actual;root=source if kind=='source' else site
    check=(lambda:v.source_check(source,sr)) if kind=='source' else (lambda:v.pages_check(site,pr,h))
    check();before=v.inventory(root)
    p=root/('README.md' if kind=='source' else 'index.html')
    if mutation=='extra':p=root/'private-unlisted.txt'
    with changed(p,None if mutation=='missing' else b'controlled tamper'):
        tampered=v.inventory(root)
        with pytest.raises(RuntimeError,match='^'+guard.replace('SOURCE','PAGES' if kind=='pages' else 'SOURCE')+'$'):check()
        assert v.inventory(root)==tampered
    assert v.inventory(root)==before;check()

@pytest.mark.parametrize('kind',['source','pages'])
@pytest.mark.parametrize('field',v.FLAGS)
def test_no_admission_flag_can_be_enabled(actual,kind,field):
    source,site,sr,pr,h=actual;record=copy.deepcopy(sr if kind=='source' else pr)
    record[field]=True
    with pytest.raises(RuntimeError,match='^ADMISSION_FORBIDDEN$'):
        if kind=='source':v.source_check(source,record)
        else:v.pages_check(site,record,h)

@pytest.mark.parametrize('field,value,guard',[
 ('tag','v1.1.0-alpha.1','CANDIDATE_IDENTITY'),
 ('protected_payload',{},'MANDATORY_PROTECTED_BINDINGS'),
 ('historical_authorities',{},'MANDATORY_PROTECTED_BINDINGS'),
 ('claim_bindings',{},'MANDATORY_PROTECTED_BINDINGS'),
 ('claim_status_upgraded',True,'SCIENTIFIC_BOUNDARY'),
 ('historical_equivalence','PASS','SCIENTIFIC_BOUNDARY'),
 ('linux_baseline','OWNER_PERMISSION_REQUIRED','SCIENTIFIC_BOUNDARY'),
 ('final_commit','invented','UNRELEASED_SOURCE')])
def test_source_boundary_controls(actual,field,value,guard):
    source,_,sr,_,_=actual;v.source_check(source,sr);bad=copy.deepcopy(sr);bad[field]=value
    with pytest.raises(RuntimeError,match='^'+guard+'$'):v.source_check(source,bad)

@pytest.mark.parametrize('field',['preserved_stable_files','specialist_coverage','route_groups'])
def test_mandatory_pages_maps_cannot_be_omitted(actual,field):
    _,site,_,pr,h=actual;v.pages_check(site,pr,h);bad=copy.deepcopy(pr);bad[field]={}
    with pytest.raises(RuntimeError,match='^MANDATORY_PAGES_BINDINGS$'):v.pages_check(site,bad,h)

def test_equal_size_route_swap_and_renamed_coverage_rejected(actual):
    _,site,_,pr,h=actual
    bad=copy.deepcopy(pr);a=bad['route_groups']['gateway_companion_baseline'];b=bad['route_groups']['integrated_additions'];a[0],b[0]=b[0],a[0]
    with pytest.raises(RuntimeError,match='^MANDATORY_PAGES_BINDINGS$'):v.pages_check(site,bad,h)
    bad=copy.deepcopy(pr);bad['specialist_coverage']['invented']=bad['specialist_coverage'].pop('assistive_technology')
    with pytest.raises(RuntimeError,match='^MANDATORY_PAGES_BINDINGS$'):v.pages_check(site,bad,h)

def test_source_binding_and_tag_context_rejected(actual):
    source,site,sr,pr,h=actual
    with pytest.raises(RuntimeError,match='^SOURCE_CONTRACT_BINDING$'):v.pages_check(site,pr,'0'*64)
    with pytest.raises(RuntimeError,match='^TAG_CONTEXT_FORBIDDEN$'):v.source_check(source,sr,tag_context=True)
    with pytest.raises(RuntimeError,match='^TAG_CONTEXT_FORBIDDEN$'):v.pages_check(site,pr,h,tag_context=True)

@pytest.mark.parametrize('kind',['source','pages'])
@pytest.mark.parametrize('fault',['file_symlink','directory_symlink','hardlink'])
def test_real_filesystem_aliases_rejected(actual,tmp_path,kind,fault):
    source,site,sr,pr,h=actual;root=source if kind=='source' else site
    check=(lambda:v.source_check(source,sr)) if kind=='source' else (lambda:v.pages_check(site,pr,h))
    check();target=root/('README.md' if kind=='source' else 'index.html');old=target.read_bytes();alias=root/'unlisted-alias'
    victim=tmp_path/'victim';victim.write_bytes(old)
    if fault=='file_symlink':target.unlink();target.symlink_to(victim)
    elif fault=='directory_symlink':alias.symlink_to(tmp_path,target_is_directory=True)
    else:os.link(target,tmp_path/'hardlink')
    try:
        with pytest.raises(RuntimeError,match='^(NONREGULAR_OR_HARDLINK|SOURCE_LINK)$'):check()
        assert victim.read_bytes()==old
    finally:
        if fault=='file_symlink':target.unlink();target.write_bytes(old)
        elif fault=='directory_symlink':alias.unlink()
        else:(tmp_path/'hardlink').unlink()
    check()

@pytest.mark.parametrize('name',['../escape','/absolute','a//b','a/./b','a/../b','C:\\escape'])
def test_unsafe_record_paths_rejected(name):
    with pytest.raises(RuntimeError,match='^UNSAFE_PATH$'):v.relative(name)

def test_external_digest_duplicate_keys_and_bool_size(actual,tmp_path):
    p=tmp_path/'record.json';p.write_text('{"key":1}');h=v.digest(p);assert v.load(p,h)=={'key':1}
    p.write_text('{"key":2}')
    with pytest.raises(RuntimeError,match='^EXTERNAL_RECORD_DIGEST$'):v.load(p,h)
    p.write_text('{"key":1,"key":2}')
    with pytest.raises(RuntimeError,match='^DUPLICATE_JSON_KEY$'):v.load(p,v.digest(p))
    with pytest.raises(RuntimeError,match='^FILE_SCHEMA$'):v.file_map({'x':{'bytes':True,'sha256':'0'*64}})
