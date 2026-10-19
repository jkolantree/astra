"""Expose an internal Playwright registry alias for existing portable bytes."""
import argparse,json,os
from pathlib import Path

def prepare(root:Path)->dict:
    if not root.is_absolute() or '..' in root.parts or any(p.is_symlink() for p in [root,*root.parents]):raise RuntimeError('Unlinked absolute runtime root required')
    if any((p/'LOCAL_CANDIDATE_IDENTITY.json').exists() for p in [root,*root.parents]):raise RuntimeError('Sealed root forbidden')
    registry=root/'chromium_headless_shell-1234';browser=root/'browser/chrome-headless-shell-linux64/chrome-headless-shell'
    if not browser.is_file() or any(p.is_symlink() for p in [browser,*browser.parents]):raise RuntimeError('Unexpected browser path')
    if registry.is_symlink():
        if os.readlink(registry)!='browser':raise RuntimeError('Unexpected browser alias')
    elif registry.exists():raise RuntimeError('Occupied browser alias')
    else:registry.symlink_to('browser',target_is_directory=True)
    return {'status':'LOCAL_PATHS_PREPARED_NOT_ADMITTED','registry_alias':'chromium_headless_shell-1234','target':'browser','environment':'Set PLAYWRIGHT_BROWSERS_PATH to the shared runtime root; all cache/config/data paths to a writable work directory.','runtime_admitted':False}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True,type=Path);a=p.parse_args();print(json.dumps(prepare(a.root.absolute()),indent=2))
