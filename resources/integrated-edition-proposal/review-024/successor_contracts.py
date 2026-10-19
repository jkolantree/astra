"""Externally bound local consistency proposals; never grants admission."""
from __future__ import annotations
import argparse, hashlib, json, os, re, stat
from pathlib import Path, PurePosixPath

TAG = 'astra-integrated-core-v1.1.0-alpha.1'
PAGES_EXPECTATIONS_SHA256 = 'e9271980f701dc0902c54b365132a6f8189481e97039b4801964368335cb0be6'
FLAGS = ('source_admitted', 'runtime_admitted', 'pages_admitted', 'publication_authorized')
PREFIX = 'resources/integrated-edition-proposal/'
BOUNDARY_SHA256 = '8fadc3ba44375809aed3fb280ca8e424dbba8b0e85e8803a55525ec439cd4d2f'

def require(condition, guard):
    if not condition:
        raise RuntimeError(guard)

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def relative(name):
    require(isinstance(name, str) and re.fullmatch(r'[A-Za-z0-9_.\-/]+', name) is not None
            and not name.startswith('/') and all(x not in {'', '.', '..'} for x in name.split('/'))
            and PurePosixPath(name).as_posix() == name, 'UNSAFE_PATH')
    return name

def inventory(root):
    require(root.is_dir() and not any(p.is_symlink() for p in [root, *root.parents]), 'SOURCE_LINK')
    rows = {}
    for base, dirs, files in os.walk(root, followlinks=False):
        for name in dirs:
            require(not (Path(base)/name).is_symlink(), 'SOURCE_LINK')
        for name in files:
            p = Path(base)/name
            n = relative(p.relative_to(root).as_posix())
            s = p.lstat()
            require(stat.S_ISREG(s.st_mode) and s.st_nlink == 1, 'NONREGULAR_OR_HARDLINK')
            rows[n] = {'bytes': s.st_size, 'sha256': digest(p)}
    require(len({x.casefold() for x in rows}) == len(rows), 'CASE_COLLISION')
    return dict(sorted(rows.items()))

def load(path, expected_sha256):
    require(not any(p.is_symlink() for p in [path, *path.parents]), 'RECORD_LINK')
    require(path.is_file() and path.stat().st_nlink == 1, 'RECORD_FILE')
    require(re.fullmatch('[a-f0-9]{64}', expected_sha256) is not None
            and digest(path) == expected_sha256, 'EXTERNAL_RECORD_DIGEST')
    def unique(pairs):
        out = {}
        for k, v in pairs:
            require(k not in out, 'DUPLICATE_JSON_KEY')
            out[k] = v
        return out
    return json.loads(path.read_text(), object_pairs_hook=unique)

def boundary(record, kind, tag_context=False):
    require(record.get('schema') == 'astra-integrated-core-'+kind+'-proposal-024'
            and record.get('status') == 'PROPOSED_NOT_ADMITTED', 'PROPOSAL_SCHEMA')
    require(record.get('tag') == TAG, 'CANDIDATE_IDENTITY')
    require(all(record.get(k) is False for k in FLAGS), 'ADMISSION_FORBIDDEN')
    require(not tag_context, 'TAG_CONTEXT_FORBIDDEN')

def file_map(rows):
    require(isinstance(rows, dict) and bool(rows), 'EMPTY_ROSTER')
    for name, row in rows.items():
        relative(name)
        require(isinstance(row, dict) and set(row) == {'bytes', 'sha256'}
                and type(row['bytes']) is int and row['bytes'] >= 0
                and isinstance(row['sha256'], str)
                and re.fullmatch('[a-f0-9]{64}', row['sha256']) is not None, 'FILE_SCHEMA')
    require(len({x.casefold() for x in rows}) == len(rows), 'CASE_COLLISION')
    names=set(rows)
    require(not any(p.as_posix() in names for n in names for p in PurePosixPath(n).parents), 'FILE_DIRECTORY_COLLISION')

def source_check(root, record, *, tag_context=False):
    boundary(record, 'source', tag_context)
    file_map(record['files'])
    actual = inventory(root)
    require(set(actual) == set(record['files']), 'SOURCE_ROSTER')
    require(actual == record['files'], 'SOURCE_HASH')
    bound_path = root/PREFIX/'BOUNDARY_EXPECTATIONS.json'
    require(digest(bound_path) == BOUNDARY_SHA256, 'HISTORICAL_BOUNDARY_IDENTITY')
    bound = json.loads(bound_path.read_text())
    require(record.get('base_commit') == bound['base_commit'], 'SOURCE_BASE')
    for field in ('protected_payload', 'historical_authorities', 'claim_bindings'):
        require(record.get(field) == bound[field], 'MANDATORY_PROTECTED_BINDINGS')
        require(all(actual[n]['sha256'] == h for n,h in bound[field].items()), 'PROTECTED_BYTES')
    require(record.get('historical_equivalence') == 'FAIL_UNCHANGED'
            and record.get('linux_baseline') == 'EXISTING_OWNER_APPROVAL_PRESERVED'
            and record.get('claim_status_upgraded') is False, 'SCIENTIFIC_BOUNDARY')
    require(record.get('final_commit') is None and record.get('final_tree') is None, 'UNRELEASED_SOURCE')
    return {'status':'CONSISTENCY_PASS_NOT_ADMISSION', 'files':len(actual)}

def pages_check(root, record, source_contract_sha256, *, tag_context=False):
    boundary(record, 'pages', tag_context)
    require(record.get('source_contract_sha256') == source_contract_sha256, 'SOURCE_CONTRACT_BINDING')
    file_map(record['files'])
    actual=inventory(root)
    require(set(actual) == set(record['files']), 'PAGES_ROSTER')
    require(actual == record['files'], 'PAGES_HASH')
    expectation_path=Path(__file__).with_name('PAGES_EXPECTATIONS.json')
    expected=load(expectation_path,PAGES_EXPECTATIONS_SHA256)
    for field in ('route_groups','specialist_coverage','preserved_stable_files'):
        require(record.get(field) == expected[field], 'MANDATORY_PAGES_BINDINGS')
    partitions=record['route_groups']
    require(set(partitions) == {'gateway_companion_baseline','integrated_additions','historical_reading_and_aliases'}, 'ROUTE_GROUPS')
    flattened=[n for names in partitions.values() for n in names]
    require(len(flattened) == len(set(flattened)) and set(flattened) == set(actual), 'ROUTE_PARTITION')
    require([len(partitions[k]) for k in ('gateway_companion_baseline','integrated_additions','historical_reading_and_aliases')] == [65,51,78], 'ROUTE_COUNTS')
    require(record.get('latest_stable') == 'v1.0.7' and record.get('fresh_production') is False, 'PAGES_SCOPE')
    require(set(record['specialist_coverage'].values()) == {'not-tested'} and len(record['specialist_coverage']) == 6, 'COVERAGE_SCOPE')
    for name, item in record['preserved_stable_files'].items():
        require(actual.get(name) == item, 'STABLE_ROUTE_BYTES')
    return {'status':'RETAINED_PREVIEW_CONSISTENCY_NOT_ADMISSION','files':len(actual)}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--kind',choices=['source','pages'],required=True)
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--record',type=Path,required=True)
    p.add_argument('--record-sha256',required=True)
    p.add_argument('--source-contract-sha256')
    args=p.parse_args()
    record=load(args.record,args.record_sha256)
    tag_context=os.environ.get('GITHUB_REF','').startswith('refs/tags/') or os.environ.get('GITHUB_REF_TYPE')=='tag' or os.environ.get('GITHUB_EVENT_NAME') in {'release','create'}
    if args.kind=='source':result=source_check(args.root,record,tag_context=tag_context)
    else:
        require(args.source_contract_sha256 is not None,'MISSING_SOURCE_CONTRACT_BINDING')
        result=pages_check(args.root,record,args.source_contract_sha256,tag_context=tag_context)
    print(json.dumps(result,sort_keys=True))

if __name__ == '__main__':
    main()
