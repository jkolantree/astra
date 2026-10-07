"""Check private proposal consistency and assemble a local additive preview.

This tool cannot admit a source, runtime or site; historical validators and
workflows remain authoritative. Exact record digests are supplied externally.
"""
from __future__ import annotations
import argparse,hashlib,json,os,re,shutil,stat
from pathlib import Path,PurePosixPath
PREFIX='resources/integrated-edition-proposal/'
NAMESPACE='research/integrated-edition-proposal/'
FLAGS=['source_admitted','runtime_admitted','pages_admitted','publication_authorized']

def require(ok:bool,guard:str)->None:
    if not ok:raise RuntimeError(guard)
def digest(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
def relative(value:str)->str:
    require(isinstance(value,str) and re.fullmatch(r'[A-Za-z0-9_.\-/]+',value) is not None and PurePosixPath(value).as_posix()==value and not value.startswith('/') and all(x not in {'.','..',''} for x in value.split('/')),'PATH')
    return value
def safe(root:Path,name:str)->Path:
    p=root/relative(name)
    require(not any(q.is_symlink() for q in [p,*p.parents]),'LINK')
    return p
def inventory(root:Path,repository:bool=False)->dict:
    require(not any(p.is_symlink() for p in [root,*root.parents]),'LINK')
    result={}
    for base,dirs,names in os.walk(root,followlinks=False):
        if repository and Path(base)==root:dirs[:]=[d for d in dirs if d!='.git']
        for name in dirs:require(not (Path(base)/name).is_symlink(),'LINK')
        for name in names:
            p=Path(base)/name;n=p.relative_to(root).as_posix();s=p.lstat();relative(n)
            require(stat.S_ISREG(s.st_mode) and s.st_nlink==1,'NONREGULAR_OR_HARDLINK')
            result[n]={'bytes':s.st_size,'sha256':digest(p)}
    return dict(sorted(result.items()))
def flags(record:dict,kind:str)->None:
    require(record.get('schema')=='astra-'+kind+'-admission-draft-1' and record.get('status')=='PROPOSED_NOT_ADMITTED','STATUS')
    require(all(record.get(k) is False for k in FLAGS),'ADMISSION_FORBIDDEN')
def file_record(root:Path,name:str,record:dict)->None:
    require(set(record)=={'bytes','sha256'} and type(record['bytes']) is int and record['bytes']>=0 and re.fullmatch('[0-9a-f]{64}',record['sha256']) is not None,'FILE_SCHEMA')
    p=safe(root,name);require(p.is_file() and p.stat().st_nlink==1,'MISSING_OR_HARDLINK')
    require(p.stat().st_size==record['bytes'] and digest(p)==record['sha256'],'HASH')
def expectations()->dict:
    path=Path(__file__).with_name('BOUNDARY_EXPECTATIONS.json')
    require(digest(path)=='8fadc3ba44375809aed3fb280ca8e424dbba8b0e85e8803a55525ec439cd4d2f','BOUNDARY_EXPECTATION_DIGEST')
    return json.loads(path.read_text())
def source_check(root:Path,record:dict,*,tag_context:bool=False)->None:
    flags(record,'source');require(not tag_context,'TAG_CONTEXT_FORBIDDEN')
    bound=expectations()
    require(record.get('base_commit')==bound['base_commit'],'SOURCE_BASE')
    for key in ['operational_pin_changes','protected_payload','historical_authorities','claim_bindings']:
        require(record.get(key)==bound[key],'MANDATORY_SOURCE_BINDINGS')
    excluded=['MANIFEST.sha256',PREFIX+'SOURCE_ADMISSION_DRAFT.json']
    require(record['excluded_from_projection']==excluded,'PROJECTION_EXCLUSIONS')
    actual=inventory(root,repository=True)
    require(set(actual)==set(record['files'])|set(excluded),'SOURCE_ROSTER')
    require({n:v for n,v in actual.items() if n not in excluded}==record['files'],'SOURCE_HASH')
    manifest={}
    for line in (root/'MANIFEST.sha256').read_text().splitlines():
        h,n=line.split('  ',1);relative(n);require(n not in manifest,'MANIFEST_DUPLICATE');manifest[n]=h
    require(manifest=={n:v['sha256'] for n,v in actual.items() if n!='MANIFEST.sha256'},'MANIFEST_HASH')
    require(record['historical_authority_changed'] is False and record['claim_status_upgraded'] is False,'SOURCE_BOUNDARY')
    for n,pin in record['operational_pin_changes'].items():require(actual[n]['sha256']==pin['new_sha256'],'OPERATIONAL_PIN')
    for n,h in record['protected_payload'].items():require(actual[n]['sha256']==h,'PAYLOAD_PIN')
    for key in ['historical_authorities','claim_bindings']:
        for n,h in bound[key].items():require(actual[n]['sha256']==h,'HISTORICAL_OR_CLAIM_PIN')
def runtime_check(root:Path,record:dict)->None:
    flags(record,'runtime')
    require(record['profiles']=={'science':'3.12.10','wki':'3.12.14'},'SPLIT_PROFILE')
    require(record['routes']=={'retained_science_atlas':'science','integrated_case':'science','scm':'science','new_diagrams':'science','reading_documents':'science','wki':'wki'},'RUNTIME_ROUTES')
    require(record['historical_windows_equivalence'] is False and record['new_acquisition'] is False,'RUNTIME_BOUNDARY')
    bound=expectations();require(set(record['source_bindings'])==set(bound['runtime_source_paths']),'MANDATORY_RUNTIME_BINDINGS')
    for n,binding in record['source_bindings'].items():file_record(root,n,binding)
    evidence=json.loads((root/PREFIX/'PORTABLE_VALIDATION_DRAFT.json').read_text())
    require(evidence['evidence_hashes']==bound['runtime_evidence_hashes'] and evidence['construction']['exit_code']==0 and evidence['relocation']['status']=='PASS_EXPLICIT_REBIND_REQUIRED' and evidence['runtime_admitted'] is False,'RUNTIME_PHASE_BINDINGS')
    require(evidence['bootstrap_current_sha256']==digest(root/PREFIX/'bootstrap_draft.py') and evidence['relocate_current_sha256']==digest(root/PREFIX/'relocate_draft.py') and evidence['prepare_paths_sha256']==digest(root/PREFIX/'prepare_runtime_paths.py'),'RUNTIME_TOOL_BINDINGS')
    require(record['construction_status']=='CONSTRUCTED_NOT_ADMITTED' and record['relocation_status']=='PASS_EXPLICIT_REBIND_REQUIRED','RUNTIME_EVIDENCE')
def pages_check(roots:dict[str,Path],record:dict)->None:
    flags(record,'pages');require(record['namespace']==NAMESPACE and record['latest_stable_unchanged'] is True,'PAGES_BOUNDARY')
    definitions=[{k:row[k] for k in ['family','source_path','destination','content_role']} for row in record['routes']]
    destinations=[]
    for row in record['routes']:
        require(set(row)=={'family','source_path','destination','bytes','sha256','content_role'},'ROUTE_SCHEMA')
        name=relative(row['destination']);require(name.startswith(NAMESPACE),'ROUTE_NAMESPACE')
        require(row['family'] in roots and row['content_role'] in {'diagram','report','gallery','source_download','reading_html','reading_pdf','font_notice'},'ROUTE_ROLE')
        file_record(roots[row['family']],row['source_path'],{k:row[k] for k in ['bytes','sha256']});destinations.append(name)
    require(len({n.casefold() for n in destinations})==len(destinations),'DUPLICATE_ROUTE')
    names=set(destinations)
    require(not any(p.as_posix() in names for n in names for p in PurePosixPath(n).parents),'ROUTE_FILE_DIRECTORY')
    require(sorted(definitions,key=lambda x:x['destination'])==expectations()['pages_route_definitions'],'MANDATORY_PAGES_ROSTER')
    require(record['gateway']==expectations()['gateway'],'GATEWAY_BOUNDARY')
def assemble(roots:dict[str,Path],destination:Path,record:dict)->dict:
    pages_check(roots,record)
    require(destination.is_absolute() and '..' not in destination.parts and not any(p.is_symlink() for p in [destination,*destination.parents]),'DESTINATION_LINK')
    require(destination.is_dir(),'DESTINATION_MISSING')
    require(not any(destination.is_relative_to(root) or root.is_relative_to(destination) for root in roots.values()),'DESTINATION_OVERLAP')
    before=inventory(destination)
    require(before==record['baseline_fixture'],'BASELINE_ROSTER_OR_HASH')
    # Preflight all destinations before the first write; no overwrite, even identical.
    for row in record['routes']:
        p=safe(destination,row['destination'])
        require(not p.exists(),'COLLISION')
        require(not any(q.is_file() for q in p.parents),'ANCESTOR_FILE_COLLISION')
    for row in record['routes']:
        p=safe(destination,row['destination']);p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as stream:stream.write(safe(roots[row['family']],row['source_path']).read_bytes())
    after=inventory(destination);expected=dict(before)
    expected.update({x['destination']:{k:x[k] for k in ['bytes','sha256']} for x in record['routes']})
    require(after==dict(sorted(expected.items())),'ASSEMBLY_HASH')
    return {'status':'LOCAL_ADDITIVE_PREVIEW_NOT_ADMISSION','preserved_files':len(before),'added_files':len(after)-len(before),'pages_admitted':False,'gateway_reconciled':record['gateway'].get('reconciliation')=='LOCAL_CONTENT_RECONCILED_NOT_ADMITTED'}
def load_record(path:Path,expected:str)->dict:
    require(digest(path)==expected,'EXTERNAL_RECORD_DIGEST')
    def pairs(items):
        result={}
        for k,v in items:require(k not in result,'DUPLICATE_JSON_KEY');result[k]=v
        return result
    return json.loads(path.read_text(),object_pairs_hook=pairs)
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source',required=True,type=Path);parser.add_argument('--kind',required=True,choices=['source','runtime']);parser.add_argument('--record-sha256',required=True);args=parser.parse_args()
    record=load_record(args.source/PREFIX/(args.kind.upper()+'_ADMISSION_DRAFT.json'),args.record_sha256)
    if args.kind=='source':source_check(args.source,record,tag_context=os.environ.get('GITHUB_REF','').startswith('refs/tags/') or os.environ.get('GITHUB_REF_TYPE')=='tag' or os.environ.get('GITHUB_EVENT_NAME') in {'release','create'})
    else:runtime_check(args.source,record)
    print(json.dumps({'status':'CONSISTENCY_PASS_NOT_ADMISSION','kind':args.kind}))
if __name__=='__main__':main()
