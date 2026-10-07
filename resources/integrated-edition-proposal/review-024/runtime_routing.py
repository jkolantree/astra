"""Complete test ownership proposal; unavailable Windows execution stays pending."""
from __future__ import annotations
import hashlib,json
from pathlib import Path

HISTORICAL_MODULES=frozenset('tests/'+n+'.py' for n in (
    'test_claim_source_coverage','test_release_integrity','test_pages_admission',
    'test_research_companion_pages','test_linux_companion'))
HISTORICAL_EXPLORER='tests/test_explorer.py::test_production_docs_are_unchanged_and_candidate_is_bounded'
WINDOWS_CASE='tests/test_dark_medium_response_benchmark.py::test_retained_evaluation_reproduces_with_frozen_sources'
ROUTES={
    'current_science':{'profile':'science','python':'3.12.10','fixture':'successor'},
    'current_wki':{'profile':'wki','python':'3.12.14','fixture':'successor'},
    'historical_science':{'profile':'science','python':'3.12.10','fixture':'pinned_main'},
    'historical_windows':{'profile':'historical_windows','python':'3.12.10','fixture':'pinned_main','execution':'NOT_EXECUTED_NO_APPROVED_WINDOWS_RUNTIME'},
}

def require(condition,guard):
    if not condition:raise RuntimeError(guard)

def route_for(node):
    module=node.split('::',1)[0]
    if node==WINDOWS_CASE:return 'historical_windows'
    if module in HISTORICAL_MODULES or node==HISTORICAL_EXPLORER:return 'historical_science'
    if module=='tests/test_wki_successor.py':return 'current_wki'
    return 'current_science'

def validate(record,collected,expected_source_sha256):
    require(record.get('schema')=='astra-integrated-core-runtime-routing-proposal-024','ROUTING_SCHEMA')
    require(record.get('status')=='PROPOSED_NOT_ADMITTED','ROUTING_STATUS')
    require(all(record.get(k) is False for k in ('source_admitted','runtime_admitted','pages_admitted','publication_authorized')),'ROUTING_ADMISSION_FORBIDDEN')
    require(record.get('profiles_and_fixtures')==ROUTES,'RUNTIME_FIXTURE_CONTRACT')
    require(len(collected)==len(set(collected)),'COLLECTION_DUPLICATE')
    require(record.get('tag')=='astra-integrated-core-v1.1.0-alpha.1','ROUTING_TAG')
    require(record.get('source_contract_sha256')==expected_source_sha256,'ROUTING_SOURCE_BINDING')
    rows=record['tests'];nodes=[x['nodeid'] for x in rows]
    require(len(nodes)==len(set(nodes)),'ROUTING_DUPLICATE')
    require(set(nodes)==set(collected),'ROUTING_COVERAGE')
    for row in rows:
        require(set(row)=={'nodeid','route'},'ROUTE_SCHEMA')
        require(row['route']==route_for(row['nodeid']),'RUNTIME_OR_FIXTURE_MISROUTED')
    require(record.get('historical_collection_policy')=={
        'retained_excluded_module':'tests/test_dark_medium_response_atlas_successor_overlay.py',
        'reason':'Existing conftest preserves historical S1 transition as byte evidence; adjacent historical tests remain collected',
        'new_deselections':[]},'COLLECTION_POLICY')
    return {route:sum(x['route']==route for x in rows) for route in ROUTES}

def result_coverage(record,receipts):
    expected={x['nodeid']:x['route'] for x in record['tests']}
    seen={}
    for receipt in receipts:
        for row in receipt['cases']:
            n=row['nodeid'];require(n in expected and expected[n]==receipt['route'],'RESULT_ROUTE')
            require(n not in seen,'RESULT_DUPLICATE')
            require(row['status'] in {'PASS','FAIL','ERROR','SKIP','NOT_EXECUTED'},'RESULT_STATUS')
            if receipt['route']=='historical_windows':require(row['status']=='NOT_EXECUTED','WINDOWS_EXECUTION_NOT_AUTHORIZED')
            if row['status']=='NOT_EXECUTED':require(receipt['route']=='historical_windows','UNEXPECTED_NONEXECUTION')
            seen[n]=row['status']
    require(set(seen)==set(expected),'RESULT_COVERAGE')
    return {status:list(seen.values()).count(status) for status in ('PASS','FAIL','ERROR','SKIP','NOT_EXECUTED')}
