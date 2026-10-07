"""Two input-only integrated-core alpha productions, without admission or publication."""
from pathlib import Path
import argparse,importlib.util,json,os,sys,time
P=Path(__file__).resolve().parent;ROOT=P.parents[2]
sys.path.insert(0,str(P))
import verify_successor as gate
helper_path=ROOT/'resources/integrated-edition-proposal/verify_edition.py'
spec=importlib.util.spec_from_file_location('retained_process_helper',helper_path)
helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)

def save(path,record):
    tmp=path.with_suffix('.new');tmp.write_text(json.dumps(record,indent=2,sort_keys=True)+'\n');tmp.replace(path)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['source-record','record-sha256','science-python','wki-python','browser','work','retained-preview']:p.add_argument('--'+n,required=True)
    a=p.parse_args();record=gate.load(Path(a.source_record),a.record_sha256)
    gate.source_check(ROOT,record,os.environ.get('GITHUB_REF','').startswith('refs/tags/') or os.environ.get('GITHUB_REF_TYPE')=='tag' or os.environ.get('GITHUB_EVENT_NAME') in {'release','create'})
    contract=gate.spec();runtime={x:gate.runtime_check(getattr(a,x+'_python'),x) for x in ['science','wki']}
    runtime['browser']=gate.browser_check(a.browser,contract)
    work=Path(a.work);gate.require(work.is_absolute() and not work.exists() and not any(x.is_symlink() for x in [work,*work.parents]),'NEW_WORK_REQUIRED')
    gate.require(not work.is_relative_to(ROOT) and not ROOT.is_relative_to(work),'WORK_OVERLAP');work.mkdir(parents=True)
    inputs=gate.input_map(record['files'],contract);receipt={'status':'INCOMPLETE','candidate_tag':gate.TAG,'source_contract_sha256':a.record_sha256,'source_files':record['files'],'inputs':inputs,'runtime':runtime,**{k:False for k in gate.FLAGS},'passes':[]}
    target=work/'PRODUCTION_RECEIPT.json';save(target,receipt)
    try:
        for number in [1,2]:
            stage=work/f'pass-{number}';gate.prepare(ROOT,stage,inputs,contract['outputs'])
            row={'pass':number,'status':'RUNNING','outputs_present_before':0,'input_files':len(inputs),'commands':[]};receipt['passes'].append(row);save(target,receipt)
            cache=stage/'tmp';cache.mkdir()
            env=dict(os.environ)
            for key in list(env):
                if key.startswith(('PYTHON','PYTEST')) or key in {'VIRTUAL_ENV','MPLCONFIGDIR'}:env.pop(key)
            env.update(PYTHONHASHSEED='0',PYTHONDONTWRITEBYTECODE='1',TZ='UTC',SOURCE_DATE_EPOCH='946684800',OPENBLAS_CORETYPE='HASWELL',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',NPY_DISABLE_CPU_FEATURES='AVX512F,AVX512CD,AVX512_SKX,AVX512_CLX,AVX512_CNL,AVX512_ICL',MPLBACKEND='Agg',MPLCONFIGDIR=str(cache/'mpl'),TMPDIR=str(cache),TMP=str(cache),TEMP=str(cache),XDG_CACHE_HOME=str(cache/'cache'),XDG_CONFIG_HOME=str(cache/'config'),XDG_DATA_HOME=str(cache/'data'),PLAYWRIGHT_BROWSERS_PATH=str(Path(a.browser).parents[2]))
            generated=stage/gate.PREFIX/'generated';generated.mkdir(parents=True)
            commands=[
                ('science','scripts/make_figures.py',['--workers','4']),
                ('science','tools/build_dark_medium_response_atlas_documents.py',['--no-identity','--linux-layout']),
                ('science','src/integrated_case.py',['--case','data/integrated-core/integrated_case.json','--output',str(generated/'integrated-case.json')]),
                ('science','scripts/run_scm_checks.py',['--output',str(generated/'scm-checks.json')]),
                ('wki','scripts/wki_check_algebra.py',['--output',str(generated/'wki-checks.json')]),
                ('science',gate.PREFIX+'validate_release_reports.py',[]),
                ('science',gate.PREFIX+'render_diagrams.py',[]),
                ('science',gate.PREFIX+'build_documents.py',['--browser',a.browser,'--pdf']),
            ]
            for i,(profile,script,arguments) in enumerate(commands,1):
                row['current_command']=script;save(target,receipt);start=time.monotonic()
                helper.child(getattr(a,profile+'_python'),stage,env,script,arguments,work/f'pass-{number}-command-{i}.log')
                row['commands'].append({'profile':profile,'script':script,'exit_code':0,'seconds':round(time.monotonic()-start,3)});save(target,receipt)
            outputs=gate.outputs_check(stage,inputs,contract)
            pages=gate.assemble_pages(ROOT,stage,Path(a.retained_preview),work/f'pages-{number}',json.loads((P/'PAGES_PLAN.json').read_text()),inputs=inputs,contract=contract,output_map=outputs)
            gate.source_check(ROOT,record)
            row.update(status='PASS',outputs=outputs,pages=pages,source_unchanged=True);save(target,receipt)
        gate.require(receipt['passes'][0]['outputs']==receipt['passes'][1]['outputs'],'TWO_PASS_OUTPUT_MISMATCH')
        gate.require(receipt['passes'][0]['pages']==receipt['passes'][1]['pages'],'TWO_PASS_PAGES_MISMATCH')
        for x in ['science','wki']:gate.runtime_check(getattr(a,x+'_python'),x)
        gate.browser_check(a.browser,contract)
        receipt.update(status='PASS_TWO_CLEAN_PRODUCTIONS_NOT_ADMISSION',all_69_outputs_byte_identical=True,pages_194_byte_identical=True,historical_windows_equivalence='FAIL_PRESERVED',historical_57_source_gate='UNCHANGED_REJECTION_NOT_THIS_SUCCESSOR_CONTRACT')
    except BaseException as error:
        receipt.update(status='FAIL',error_type=type(error).__name__,error=str(error));raise
    finally:save(target,receipt)
    print(json.dumps({'status':receipt['status'],'outputs_per_pass':69,'pages_per_pass':194,'source_contract_sha256':a.record_sha256}),flush=True)

if __name__=='__main__':main()
