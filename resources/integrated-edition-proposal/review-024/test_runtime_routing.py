import copy,importlib.util,json,os
from pathlib import Path
import pytest
spec=importlib.util.spec_from_file_location('routing024',Path(__file__).with_name('runtime_routing.py'))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)

@pytest.fixture
def bound():
    settings=json.loads(Path(os.environ['ASTRA_024_TEST_INPUTS']).read_text())
    record=json.loads(Path(settings['routing_record']).read_text())
    collected=json.loads(Path(settings['collected_record']).read_text())
    r.validate(record,collected,record['source_contract_sha256'])
    return record,collected

def test_complete_collected_identity_coverage(bound):
    record,collected=bound;counts=r.validate(record,collected,record['source_contract_sha256'])
    assert sum(counts.values())==len(collected)
    assert counts['historical_windows']==1 and counts['current_wki']==14 and counts['historical_science']==193

@pytest.mark.parametrize('fault,guard',[('tag','ROUTING_TAG'),('source','ROUTING_SOURCE_BINDING'),('missing','ROUTING_COVERAGE'),('extra','ROUTING_COVERAGE'),('duplicate','ROUTING_DUPLICATE'),('wki','RUNTIME_OR_FIXTURE_MISROUTED'),('historical','RUNTIME_OR_FIXTURE_MISROUTED'),('windows','RUNTIME_OR_FIXTURE_MISROUTED'),('version','RUNTIME_FIXTURE_CONTRACT'),('admit','ROUTING_ADMISSION_FORBIDDEN'),('exclude','COLLECTION_POLICY')])
def test_real_routing_mutations(bound,fault,guard):
    record,collected=bound;bad=copy.deepcopy(record)
    if fault=='tag':bad['tag']='v1.1.0-alpha.1'
    elif fault=='source':bad['source_contract_sha256']='0'*64
    elif fault=='missing':bad['tests'].pop()
    elif fault=='extra':bad['tests'].append({'nodeid':'tests/test_unreviewed.py::test_extra','route':'current_science'})
    elif fault=='duplicate':bad['tests'].append(bad['tests'][0])
    elif fault in {'wki','historical','windows'}:
        route={'wki':'current_wki','historical':'historical_science','windows':'historical_windows'}[fault]
        next(x for x in bad['tests'] if x['route']==route)['route']='current_science'
    elif fault=='version':bad['profiles_and_fixtures']['current_wki']['python']='3.12.10'
    elif fault=='admit':bad['runtime_admitted']=True
    else:bad['historical_collection_policy']['new_deselections']=['anything']
    with pytest.raises(RuntimeError,match='^'+guard+'$'):r.validate(bad,collected,record['source_contract_sha256'])

def test_results_cannot_omit_duplicate_or_credit_unexecuted_windows(bound):
    record,_=bound
    receipts=[{'route':route,'cases':[{'nodeid':x['nodeid'],'status':'NOT_EXECUTED' if route=='historical_windows' else 'PASS'} for x in record['tests'] if x['route']==route]} for route in r.ROUTES]
    assert r.result_coverage(record,receipts)['NOT_EXECUTED']==1
    bad=copy.deepcopy(receipts);bad[-1]['cases'][0]['status']='PASS'
    with pytest.raises(RuntimeError,match='^WINDOWS_EXECUTION_NOT_AUTHORIZED$'):r.result_coverage(record,bad)
    bad=copy.deepcopy(receipts);bad[0]['cases'].pop()
    with pytest.raises(RuntimeError,match='^RESULT_COVERAGE$'):r.result_coverage(record,bad)
    bad=copy.deepcopy(receipts);bad[0]['cases'].append(bad[0]['cases'][0])
    with pytest.raises(RuntimeError,match='^RESULT_DUPLICATE$'):r.result_coverage(record,bad)
    bad=copy.deepcopy(receipts);bad[0]['cases'][0]['status']='NOT_EXECUTED'
    with pytest.raises(RuntimeError,match='^UNEXPECTED_NONEXECUTION$'):r.result_coverage(record,bad)
