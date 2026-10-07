"""Rebind the two private venv launchers after moving their shared runtime root.

uv makes package entrypoints relocatable; CPython base links/home need this
explicit local rebind. No packages are installed and no admission is granted.
"""
import argparse,hashlib,json,os,re
from pathlib import Path
PACKAGE=Path(__file__).resolve().parent

def rebind(root:Path)->dict:
    if not root.is_absolute() or '..' in root.parts or any(p.is_symlink() for p in [root,*root.parents]):
        raise RuntimeError('Unlinked absolute runtime root required')
    if any((p/'LOCAL_CANDIDATE_IDENTITY.json').exists() for p in [root,*root.parents]):
        raise RuntimeError('Sealed evidence root forbidden')
    receipt=json.loads((root/'bootstrap-receipt.json').read_text())
    if receipt.get('status')!='CONSTRUCTED_NOT_ADMITTED' or receipt.get('runtime_admitted') is not False:
        raise RuntimeError('Constructed private runtime required')
    expected=json.loads((PACKAGE/'PORTABLE_INPUTS_DRAFT.json').read_text())['python_expected'];changes=[]
    for role in ['science','wki']:
        base=root/(role+'-base/python/bin/python3.12');venv=root/role;cfg=venv/'pyvenv.cfg';link=venv/'bin/python'
        if any(p.is_symlink() for p in [cfg,*cfg.parents,*link.parents,base,*base.parents]) or cfg.stat().st_nlink!=1 or not link.is_symlink():
            raise RuntimeError('Unexpected linked runtime configuration')
        if hashlib.sha256(base.read_bytes()).hexdigest()!=expected[role]['executable_sha256']:
            raise RuntimeError('Interpreter identity mismatch')
        original=cfg.read_text();homes=[line for line in original.splitlines() if line.startswith('home = ')]
        if len(homes)!=1 or not homes[0].endswith('/'+role+'-base/python/bin') or 'relocatable = true' not in original:
            raise RuntimeError('Unexpected venv home/configuration')
        if not os.readlink(link).endswith('/'+role+'-base/python/bin/python3.12'):
            raise RuntimeError('Unexpected interpreter link')
        changes.append((cfg,link,base,original,role))
    # Both profiles are preflighted before any write.
    records=[]
    for cfg,link,base,original,role in changes:
        updated=re.sub(r'^home = .*$', 'home = '+str(base.parent), original,flags=re.MULTILINE)
        before=hashlib.sha256(original.encode()).hexdigest();cfg.write_text(updated)
        link.unlink();link.symlink_to('../../'+role+'-base/python/bin/python3.12')
        records.append({'role':role,'configuration_before_sha256':before,'configuration_after_sha256':hashlib.sha256(updated.encode()).hexdigest(),'interpreter_link':'../../'+role+'-base/python/bin/python3.12'})
    return {'status':'REBOUND_NOT_ADMITTED','runtime_admitted':False,'package_installation':False,'changes':records}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True,type=Path);args=parser.parse_args();print(json.dumps(rebind(args.root.absolute()),indent=2))
if __name__=='__main__':main()
