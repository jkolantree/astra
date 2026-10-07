"""Operational local successor validation. Never admits or publishes a release."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, os, re, shutil, stat, subprocess, sys
from pathlib import Path, PurePosixPath

PACKAGE=Path(__file__).resolve().parent
ROOT=PACKAGE.parents[2]
TAG='astra-integrated-core-v1.1.0-alpha.1'
PREFIX='resources/integrated-core/v1.1.0-alpha.1/'
FLAGS=('source_admitted','runtime_admitted','pages_admitted','publication_authorized')

def require(ok,guard):
    if not ok:raise RuntimeError(guard)

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def relative(name):
    require(isinstance(name,str) and bool(name) and not name.startswith('/') and '\\' not in name and ':' not in name and all(x not in {'','.','..'} for x in name.split('/')),'UNSAFE_PATH')
    return name

def safe(root,name):
    p=root/relative(name)
    require(not any(x.is_symlink() for x in [p,*p.parents]),'LINK')
    return p

def inventory(root):
    require(root.is_dir() and not any(x.is_symlink() for x in [root,*root.parents]),'LINK')
    out={}
    for base,dirs,files in os.walk(root,followlinks=False):
        for n in dirs:require(not (Path(base)/n).is_symlink(),'LINK')
        for n in files:
            p=Path(base)/n;name=relative(p.relative_to(root).as_posix());s=p.lstat()
            require(stat.S_ISREG(s.st_mode) and s.st_nlink==1,'NONREGULAR_OR_SHARED')
            out[name]={'bytes':s.st_size,'sha256':sha(p)}
    require(len({n.casefold() for n in out})==len(out),'CASE_COLLISION')
    return dict(sorted(out.items()))

def load(path,expected):
    require(not any(x.is_symlink() for x in [path,*path.parents]) and path.is_file() and path.stat().st_nlink==1,'RECORD_FILE')
    require(sha(path)==expected,'EXTERNAL_IDENTITY')
    def pairs(items):
        result={}
        for k,v in items:require(k not in result,'DUPLICATE_JSON_KEY');result[k]=v
        return result
    return json.loads(path.read_text(),object_pairs_hook=pairs)

def spec():
    s=json.loads((PACKAGE/'RELEASE_SPEC.json').read_text())
    require(s['candidate_tag']==TAG and s['version']=='1.1.0-alpha.1' and all(s[k] is False for k in FLAGS),'SPEC_IDENTITY')
    require(len(s['outputs'])==len(set(s['outputs']))==69 and len(s['scientific_outputs'])==61 and len(s['reading_outputs'])==8,'OUTPUT_CONTRACT')
    require(set(s['outputs'])==set(s['scientific_outputs'])|set(s['reading_outputs']) and set(s['scientific_outputs']).isdisjoint(s['reading_outputs']),'OUTPUT_PARTITION')
    for n in s['outputs']+s['excluded_historical_outputs']:relative(n)
    require(set(s['outputs']).isdisjoint(s['excluded_historical_outputs']),'OUTPUT_EXCLUSION_OVERLAP')
    require(len(s['frozen_linux_31'])==31 and set(s['frozen_linux_31'])<=set(s['outputs']),'LINUX_BASELINE_ROSTER')
    return s

def source_check(root,record,tag_context=False):
    require(record.get('schema')=='astra-integrated-core-source-proposal-025' and record.get('candidate_tag')==TAG,'SOURCE_IDENTITY')
    require(all(record.get(k) is False for k in FLAGS),'ADMISSION_FORBIDDEN')
    require(not tag_context,'TAG_CONTEXT_FORBIDDEN')
    require(inventory(root)==record['files'],'SOURCE_ROSTER_OR_BYTES')
    boundary=root/'resources/integrated-edition-proposal/BOUNDARY_EXPECTATIONS.json'
    require(sha(boundary)=='8fadc3ba44375809aed3fb280ca8e424dbba8b0e85e8803a55525ec439cd4d2f','HISTORICAL_BOUNDARY')
    b=json.loads(boundary.read_text())
    require(record.get('base_commit')==b['base_commit'] and record.get('final_commit') is None and record.get('final_tree') is None and record.get('claim_status_upgraded') is False,'SOURCE_SCOPE')
    for key in ['protected_payload','historical_authorities','claim_bindings']:
        require(record.get(key)==b[key],'MANDATORY_PROTECTED_BINDINGS')
        require(all(record['files'][n]['sha256']==h for n,h in b[key].items()),'PROTECTED_BYTES')
    require(record.get('historical_windows_equivalence') is False and record.get('linux_baseline_approval')=='PRESERVED_EXISTING','SCIENTIFIC_SCOPE')
    return record['files']

def runtime_tree(root,expected):
    require(root.is_dir() and not root.is_symlink(),'RUNTIME_ROOT')
    entries={p.relative_to(root).as_posix():({'link':os.readlink(p)} if p.is_symlink() else {'bytes':p.stat().st_size,'sha256':sha(p)}) for p in sorted(root.rglob('*')) if p.is_file() or p.is_symlink()}
    digest=hashlib.sha256(json.dumps(entries,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    require(digest==expected,'RUNTIME_INSTALLED_BYTES')
    return {'files':len(entries),'inventory_sha256':digest}

def browser_check(browser,contract):
    browser=Path(browser)
    require(sha(browser)==contract['browser_sha256'],'BROWSER_IDENTITY')
    root=browser.parent.parent
    rows=inventory(root)
    tree={n:r['sha256'] for n,r in rows.items()}
    digest=hashlib.sha256(json.dumps(tree,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    expected=json.loads((ROOT/'resources/integrated-edition-proposal/RUNTIME_PROPOSAL.json').read_text())['atlas_browser']
    require(len(rows)==expected['files'] and digest==expected['tree_inventory_sha256'],'BROWSER_INSTALLED_BYTES')
    return {'files':len(rows),'inventory_sha256':digest,'executable_sha256':contract['browser_sha256']}

def runtime_check(python,profile):
    expected=json.loads((ROOT/'resources/integrated-edition-proposal/RUNTIME_PROPOSAL.json').read_text())[profile]
    require(sha(Path(python).resolve())==expected['executable_sha256'],'RUNTIME_EXECUTABLE')
    require(sha(Path(python).resolve().parent.parent/'lib/libpython3.12.so.1.0')==expected['libpython_sha256'],'RUNTIME_LIBRARY')
    code="import json,platform,importlib.metadata as m;print(json.dumps({'python':platform.python_version(),'packages':{x.metadata['Name'].lower().replace('_','-'):x.version for x in m.distributions()}}))"
    actual=json.loads(subprocess.check_output([str(python),'-I','-B','-c',code],text=True))
    normalize=lambda rows:{re.sub(r'[-_.]+','-',k).lower():v for k,v in rows.items()}
    require(actual['python']==expected['python'] and normalize(actual['packages'])==normalize(expected['packages']),'RUNTIME_PROFILE')
    installed=runtime_tree(Path(python).absolute().parent.parent,expected['installed_inventory_sha256'])
    return {'profile':profile,'python':actual['python'],'executable_sha256':expected['executable_sha256'],'packages':actual['packages'],'installed':installed}

def input_map(source,contract):
    omit=set(contract['outputs'])|set(contract['excluded_historical_outputs'])
    result={n:v for n,v in source.items() if n not in omit}
    require(set(result).isdisjoint(contract['outputs']),'INPUT_OUTPUT_OVERLAP')
    return result

def prepare(root,stage,inputs,outputs):
    require(stage.is_absolute() and not stage.exists() and not any(p.is_symlink() for p in [stage,*stage.parents]),'NEW_STAGE_REQUIRED')
    require(not stage.is_relative_to(root) and not root.is_relative_to(stage),'STAGE_OVERLAP')
    stage.mkdir(parents=True)
    for n,row in inputs.items():
        p=safe(stage,n);p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(safe(root,n),p)
    require(inventory(stage)==inputs,'INPUT_COPY')
    require(not any(safe(stage,n).exists() for n in outputs),'STALE_OUTPUT')

def outputs_check(stage,inputs,contract):
    actual=inventory(stage);public={n:v for n,v in actual.items() if not n.startswith('tmp/')}
    require(set(public)==set(inputs)|set(contract['outputs']),'OUTPUT_ROSTER')
    require(all(public[n]==v for n,v in inputs.items()),'INPUT_MUTATION')
    outputs={n:public[n] for n in contract['outputs']}
    require(all(outputs[n]['sha256']==h for n,h in contract['frozen_linux_31'].items()),'FROZEN_LINUX_OUTPUT')
    reading=stage/PREFIX/'reading'
    doc=json.loads((reading/'document_identity.json').read_text());inspection=json.loads((reading/'pdf_inspection.json').read_text())
    require(doc['release_tag']==TAG and doc['release_version']=='1.1.0-alpha.1' and doc['status']=='CANDIDATE_NOT_ADMITTED' and doc['runtime_admitted'] is False,'READING_IDENTITY')
    require(len(doc['records'])==2 and all(x['pdf_status']=='DRAFT_INSPECTION_PASS' and x['browser_status']=='PASS' for x in doc['records']) and inspection['status']=='PASS' and len(inspection['records'])==2,'READING_INSPECTION')
    plan=json.loads((stage/'manuscript/integrated-core-v1.1.0-alpha.1/document-plan.json').read_text())
    require([(x['source'],x['html'],x['pdf'],x['title']) for x in doc['records']]==[(x['source'],x['stem']+'.html',x['stem']+'.pdf',x['title']) for x in plan['documents']],'EXACT_DOCUMENT_RECORDS')
    declaration=json.loads((stage/'manuscript/integrated-core-v1.1.0-alpha.1/figure-inputs.json').read_text())
    require(doc['figure_inputs']==declaration and len(declaration['figures'])==13,'EXACT_FIGURE_RECORDS')
    require([x['file'] for x in inspection['records']]==[x['pdf'] for x in doc['records']],'EXACT_INSPECTION_RECORDS')
    require(all(sha(reading/x['file'])==x['sha256'] and (reading/x['file']).stat().st_size==x['bytes'] for x in inspection['records']),'INSPECTION_HASH')
    for row in doc['records']:
        require(sha(reading/row['html'])==row['html_sha256'] and sha(reading/row['pdf'])==row['pdf_sha256'],'READING_HASH')
    for row in doc['figure_inputs']['figures'].values():require(sha(stage/row['source_path'])==row['sha256'],'OWN_PASS_FIGURES')
    return outputs

def pages_expected(plan,source_map,output_map):
    require(plan['candidate_tag']==TAG and all(plan[k] is False for k in FLAGS),'PAGES_IDENTITY')
    expected=json.loads((PACKAGE/'PAGES_PLAN.json').read_text())
    require(plan==expected,'PAGES_PLAN_BINDING')
    rows=plan['routes'];names=[relative(x['destination']) for x in rows]
    require(len(names)==len(set(n.casefold() for n in names))==194,'PAGES_ROSTER')
    require(not any(p.as_posix() in set(names) for n in names for p in PurePosixPath(n).parents),'PAGES_FILE_DIRECTORY_COLLISION')
    expected_map={}
    for row in rows:
        relative(row['source_path'])
        require(row['family'] in {'source','production','retained'},'PAGES_FAMILY')
        if row['family']=='production':
            require(row['source_path'] in output_map,'PAGES_PRODUCTION_MEMBER')
            value=output_map[row['source_path']]
        else:
            value=row['expected']
            if row['family']=='source':require(source_map.get(row['source_path'])==value,'PAGES_SOURCE_BINDING')
        expected_map[row['destination']]=value
    return dict(sorted(expected_map.items()))

def assemble_pages(source,production,retained,destination,plan,*,inputs,contract,output_map):
    require(outputs_check(production,inputs,contract)==output_map,'PRODUCTION_OUTPUT_IDENTITY')
    expected_map=pages_expected(plan,inventory(source),output_map)
    roots={'source':source,'production':production,'retained':retained}
    rows=plan['routes']
    require(destination.is_absolute(),'ABSOLUTE_PAGES_REQUIRED')
    require(not destination.exists() and not any(p.is_symlink() for p in [destination,*destination.parents]),'NEW_PAGES_REQUIRED')
    require(all(not destination.is_relative_to(root) and not root.is_relative_to(destination) for root in roots.values()),'PAGES_OVERLAP')
    # Validate every source before writing a destination byte.
    incoming={}
    for row in rows:
        p=safe(roots[row['family']],row['source_path']);s=p.stat()
        require(p.is_file() and s.st_nlink==1,'PAGES_INPUT_FILE')
        actual={'bytes':s.st_size,'sha256':sha(p)}
        if row['family']!='production':require(actual==row['expected'],'PAGES_RETAINED_OR_SOURCE_HASH')
        else:require(actual==output_map.get(row['source_path']),'PAGES_PRODUCTION_HASH')
        incoming[row['destination']]=actual
    destination.mkdir(parents=True)
    for row in rows:
        p=safe(destination,row['destination']);p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(safe(roots[row['family']],row['source_path']),p)
    require(inventory(destination)==dict(sorted(incoming.items()))==expected_map,'PAGES_OUTPUT_HASH')
    return incoming

def verify_production(root,source_record,receipt,contract):
    require(receipt.get('status')=='PASS_TWO_CLEAN_PRODUCTIONS_NOT_ADMISSION' and receipt.get('candidate_tag')==TAG,'PRODUCTION_STATUS')
    require(all(receipt.get(k) is False for k in FLAGS),'ADMISSION_FORBIDDEN')
    require(receipt.get('source_files')==source_record['files'] and receipt.get('inputs')==input_map(source_record['files'],contract),'PRODUCTION_SOURCE_BINDING')
    require(len(receipt.get('passes',[]))==2,'TWO_PASSES_REQUIRED')
    observed=[]
    for i,row in enumerate(receipt['passes'],1):
        require(row['pass']==i and row['status']=='PASS' and row['outputs_present_before']==0 and row['source_unchanged'] is True,'PASS_FRESHNESS_STATUS')
        actual=outputs_check(root/f'pass-{i}',receipt['inputs'],contract)
        require(actual==row['outputs'],'PRODUCTION_OUTPUT_IDENTITY')
        expected_pages=pages_expected(json.loads((PACKAGE/'PAGES_PLAN.json').read_text()),source_record['files'],actual)
        require(inventory(root/f'pages-{i}')==row['pages']==expected_pages,'PAGES_RECEIPT_IDENTITY')
        observed.append(actual)
    require(observed[0]==observed[1],'TWO_PASS_OUTPUT_MISMATCH')
    require(receipt['passes'][0]['pages']==receipt['passes'][1]['pages'],'TWO_PASS_PAGES_MISMATCH')
    return {'status':'PRODUCTION_AND_PAGES_VERIFIED_NOT_ADMISSION','outputs_per_pass':69,'pages_per_pass':194}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--record',type=Path,required=True);p.add_argument('--record-sha256',required=True);p.add_argument('--science-python',required=True);p.add_argument('--wki-python',required=True)
    p.add_argument('--browser',required=True);p.add_argument('--production-root',type=Path);p.add_argument('--production-receipt',type=Path);p.add_argument('--production-receipt-sha256')
    args=p.parse_args();record=load(args.record,args.record_sha256)
    require(args.source.resolve()==ROOT.resolve(),'SOURCE_ROOT_MISMATCH')
    source_check(args.source,record,os.environ.get('GITHUB_REF','').startswith('refs/tags/') or os.environ.get('GITHUB_REF_TYPE')=='tag' or os.environ.get('GITHUB_EVENT_NAME') in {'release','create'})
    contract=spec();runtime_check(args.science_python,'science');runtime_check(args.wki_python,'wki');browser_check(args.browser,contract)
    result={'status':'OPERATIONAL_PROPOSAL_CHECK_PASS_NOT_ADMISSION','candidate_tag':TAG,**{k:False for k in FLAGS}}
    supplied=[args.production_root,args.production_receipt,args.production_receipt_sha256]
    require(all(supplied) or not any(supplied),'COMPLETE_PRODUCTION_ARGUMENTS_REQUIRED')
    if all(supplied):
        receipt=load(args.production_receipt,args.production_receipt_sha256)
        require(receipt['source_contract_sha256']==args.record_sha256,'PRODUCTION_SOURCE_RECORD_IDENTITY')
        result['production']=verify_production(args.production_root,record,receipt,contract)
    print(json.dumps(result))

if __name__=='__main__':main()
