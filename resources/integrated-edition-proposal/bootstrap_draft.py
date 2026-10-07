"""Offline, relocatable private runtime construction; never runtime admission."""
from __future__ import annotations
import argparse,hashlib,io,json,os,platform,posixpath,re,shutil,signal,stat,subprocess,tarfile,zipfile
from pathlib import Path,PurePosixPath

PACKAGE=Path(__file__).resolve().parent
def require(ok:bool,message:str)->None:
    if not ok:raise RuntimeError(message)
def sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as stream:
        while chunk:=stream.read(1048576):h.update(chunk)
    return h.hexdigest()
def safe_name(name:str)->str:
    p=PurePosixPath(name)
    require(bool(name) and not p.is_absolute() and '..' not in p.parts and '\\' not in name and '\x00' not in name,'unsafe archive member')
    canonical=p.as_posix()
    require(name in {canonical,canonical+'/', './'+canonical, './'+canonical+'/', '.'},'noncanonical archive member')
    return canonical
def inspect_tar(archive:tarfile.TarFile,supplements:dict[str,Path]|None=None)->list[tarfile.TarInfo]:
    members=archive.getmembers();names=[safe_name(m.name) for m in members]
    require(len(names)==len(set(names)),'duplicate archive member')
    require(len(names)<50000 and sum(m.size for m in members)<1024**3,'archive exceeds bounded input size')
    by_name=dict(zip(names,members,strict=True))
    for name,path in (supplements or {}).items():
        require(safe_name(name)==name and name not in by_name and path.is_file() and not path.is_symlink(),'invalid archive supplement')
        m=tarfile.TarInfo(name);m.size=path.stat().st_size;by_name[name]=m
    all_names=set(by_name)
    links={safe_name(m.name) for m in members if m.issym() or m.islnk()}
    for m,name in zip(members,names,strict=True):
        require(m.isdir() or m.isfile() or m.issym() or m.islnk(),'special archive member')
        require(not any(p.as_posix() in links for p in PurePosixPath(name).parents),'archive member beneath link')
        require(not any(q.as_posix() in by_name and not by_name[q.as_posix()].isdir() for q in PurePosixPath(name).parents if q.as_posix()!='.'),'archive file/directory conflict')
        if m.issym() or m.islnk():
            require(not PurePosixPath(m.linkname).is_absolute() and '\\' not in m.linkname,'absolute archive link')
            target=posixpath.normpath(posixpath.join(posixpath.dirname(name) if m.issym() else '',m.linkname))
            require(target in all_names and not target.startswith('../'),'escaping or unresolved archive link')
    for name in links:
        seen=set(); current=name
        while current in links:
            require(current not in seen,'cyclic archive link');seen.add(current);m=by_name[current]
            current=posixpath.normpath(posixpath.join(posixpath.dirname(current) if m.issym() else '',m.linkname))
        require(current in by_name,'unresolved archive link')
    return members
def extract_tar(source:Path|io.BytesIO,destination:Path,supplements:dict[str,Path]|None=None)->None:
    with tarfile.open(source if isinstance(source,Path) else None,fileobj=source if isinstance(source,io.BytesIO) else None,mode='r:*') as archive:
        members=inspect_tar(archive,supplements)
        destination.mkdir(parents=True,exist_ok=False)
        for name,path in (supplements or {}).items():
            target=destination/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target);target.chmod(0o644)
        for m in members:
            if m.issym() or m.islnk():continue
            p=destination/safe_name(m.name)
            if m.isdir():p.mkdir(parents=True,exist_ok=True)
            else:
                p.parent.mkdir(parents=True,exist_ok=True)
                with p.open('xb') as out:shutil.copyfileobj(archive.extractfile(m),out)
                p.chmod(0o755 if m.mode&0o111 else 0o644)
        for m in members:
            if not(m.issym() or m.islnk()):continue
            p=destination/safe_name(m.name);p.parent.mkdir(parents=True,exist_ok=True)
            if m.issym():p.symlink_to(m.linkname)
            else:
                target=destination/safe_name(m.linkname)
                require(target.is_file() and not target.is_symlink(),'unsafe hard-link target')
                shutil.copyfile(target,p);p.chmod(target.stat().st_mode&0o777)
def extract_zip(source:Path,destination:Path)->None:
    with zipfile.ZipFile(source) as archive:
        members=archive.infolist();names=[safe_name(m.filename) for m in members]
        require(len(names)==len(set(names)),'duplicate ZIP member')
        require(sum(m.file_size for m in members)<1024**3,'ZIP exceeds bounded size')
        by_name=dict(zip(names,members,strict=True))
        for m,name in zip(members,names,strict=True):
            mode=m.external_attr>>16
            require(stat.S_IFMT(mode) in {0,stat.S_IFREG,stat.S_IFDIR},'ZIP special member not supported')
            require(not any(q.as_posix() in by_name and not by_name[q.as_posix()].is_dir() for q in PurePosixPath(name).parents),'ZIP file/directory conflict')
        destination.mkdir(parents=True,exist_ok=False)
        for m,name in zip(members,names,strict=True):
            mode=m.external_attr>>16
            p=destination/name
            if m.is_dir():p.mkdir(parents=True,exist_ok=True)
            else:
                p.parent.mkdir(parents=True,exist_ok=True)
                with p.open('xb') as out:out.write(archive.read(m))
                p.chmod(0o755 if mode&0o111 else 0o644)
def deb_payload(source:Path)->io.BytesIO:
    raw=source.read_bytes();require(raw[:8]==b'!<arch>\n','invalid deb archive');offset=8;data=[]
    while offset<len(raw):
        header=raw[offset:offset+60];require(len(header)==60 and header[58:]==b'`\n','invalid ar member')
        name=header[:16].decode().strip().rstrip('/');length=int(header[48:58]);offset+=60
        require(0<=length and offset+length<=len(raw),'truncated or negative ar member')
        if length%2:require(raw[offset+length:offset+length+1]==b'\n','invalid ar padding')
        if name.startswith('data.tar.'):data.append(raw[offset:offset+length])
        offset+=length+(length%2)
    require(offset==len(raw),'trailing ar bytes')
    require(len(data)==1,'ambiguous deb payload');return io.BytesIO(data[0])
def validate_inputs(store:Path,record:dict)->dict[str,Path]:
    require(record.get('status')=='PROPOSED_NOT_ADMITTED' and record.get('runtime_admitted') is False,'draft status required')
    names=[x['file'] for x in record['items']];require(len(names)==len(set(names)),'duplicate artifact')
    paths={}
    for item in record['items']:
        name=safe_name(item['file']);require('/' not in name,'artifact must be basename')
        p=store/name;require(p.is_file() and not p.is_symlink() and p.stat().st_nlink==1,'unsafe or missing artifact')
        require(p.stat().st_size==item['bytes'] and sha(p)==item['sha256'],'artifact hash mismatch: '+name);paths[name]=p
    return paths
def environment(root:Path)->dict[str,str]:
    env={k:v for k,v in os.environ.items() if k not in {'PYTHONHOME','PYTHONPATH','VIRTUAL_ENV','LD_PRELOAD','LD_LIBRARY_PATH','PYTEST_ADDOPTS','PYTEST_PLUGINS'} and not k.startswith(('UV_','PIP_','GIT_'))}
    env.update(PYTHONDONTWRITEBYTECODE='1',UV_OFFLINE='true',UV_PYTHON_DOWNLOADS='never',UV_NO_CONFIG='true',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',OPENBLAS_CORETYPE='HASWELL',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',NPY_DISABLE_CPU_FEATURES='AVX512F,AVX512CD,AVX512_SKX,AVX512_CLX,AVX512_CNL,AVX512_ICL',XDG_CACHE_HOME=str(root/'cache'),MPLCONFIGDIR=str(root/'cache/mpl'))
    return env
def run(command:list[str|Path],root:Path,env:dict[str,str],label:str,timeout:float=300)->str:
    require(re.fullmatch(r'[a-z0-9-]+',label) is not None,'unsafe command label')
    record={'status':'INCOMPLETE','exit_code':None,'timeout':timeout};out='';err='';primary=None;child=None
    path=root/'logs'/f'{label}.json';require(not path.exists(),'refuse existing command receipt')
    path.write_text(json.dumps(record,indent=2)+'\n')
    try:
        child=subprocess.Popen([str(x) for x in command],cwd=root,env=env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
        out,err=child.communicate(timeout=timeout);record.update(status='PASS' if child.returncode==0 else 'FAIL',exit_code=child.returncode)
        if child.returncode:primary=RuntimeError(label+' failed; inspect retained logs; exit '+str(child.returncode))
    except BaseException as error:
        primary=error;record.update(status='FAIL',error_type=type(error).__name__)
        if child is not None:
            try:os.killpg(child.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            try:out,err=child.communicate();record['exit_code']=child.returncode
            except BaseException as cleanup_error:record['cleanup_error_type']=type(cleanup_error).__name__
    finally:
        try:
            (root/'logs'/f'{label}.stdout.txt').write_text(out);(root/'logs'/f'{label}.stderr.txt').write_text(err)
            path.write_text(json.dumps(record,indent=2)+'\n')
        except BaseException as receipt_error:
            if primary is None:raise
            primary.add_note('Secondary evidence write failure: '+type(receipt_error).__name__)
    if primary is not None:raise primary
    require(record['exit_code']==0,label+' failed; inspect retained logs');return out
def no_link_ancestors(path:Path)->Path:
    require(path.is_absolute() and '..' not in path.parts,'absolute canonical path required')
    for item in [path,*path.parents]:
        require(not item.is_symlink(),'symbolic-link path ancestor')
        require(not (item/'LOCAL_CANDIDATE_IDENTITY.json').exists(),'sealed evidence destination forbidden')
    return path
def validate_record(record:dict)->None:
    require(set(record)=={'schema','status','runtime_admitted','expected_packages','items','network_required','new_acquisition_performed','platform','python_expected'},'exact record keys required')
    require(record['network_required'] is False and record['new_acquisition_performed'] is False,'offline existing inputs required')
    require(record['platform']=='Linux x86_64, glibc 2.41 reference; AVX2 and FMA3 required','exact platform required')
    require(record.get('schema')=='astra-portable-inputs-draft-1' and record.get('status')=='PROPOSED_NOT_ADMITTED' and record.get('runtime_admitted') is False,'draft schema/status required')
    expected={re.sub(r'[-_.]+','-',k.lower()):v for k,v in json.loads((PACKAGE/'RUNTIME_PROPOSAL.json').read_text())['wki']['packages'].items()}
    require(record.get('expected_packages')==expected and len(expected)==55,'exact package roster required')
    roles=['python_science','python_wki','installer','browser','git','powershell','git_apache_notice','git_gpl_notice']
    kinds=[x['kind'] for x in record['items']];require(len(kinds)==63 and all(kinds.count(role)==1 for role in roles) and kinds.count('wheel')==55,'exact artifact role roster required')
    wheel_items=[x for x in record['items'] if x['kind']=='wheel'];names=[x['package'] for x in wheel_items]
    require(len(names)==len(set(names)) and {x['package']:x['version'] for x in wheel_items}==expected,'duplicate or incompatible wheel package')
    require(len({x['file'] for x in record['items']})==63,'duplicate artifact filename')
    for item in record['items']:
        require(set(item)==({'bytes','file','kind','provenance','sha256','package','version'} if item['kind']=='wheel' else {'bytes','file','kind','provenance','sha256'}),'exact artifact keys required')
        require(isinstance(item['provenance'],dict),'artifact provenance required')
        require(type(item['bytes']) is int and item['bytes']>0 and re.fullmatch(r'[0-9a-f]{64}',item['sha256']) is not None,'invalid artifact size/hash')
    require(record['python_expected']['science']['version']=='3.12.10' and record['python_expected']['wki']['version']=='3.12.14','split interpreter versions required')
def installed_identity(actual:dict,expected:dict,packages:dict)->None:
    require(len(actual['packages'])==55 and len({x[0] for x in actual['packages']})==55,'duplicate installed package metadata')
    require(actual['python']==expected['version'] and dict(actual['packages'])==packages,'installed runtime identity mismatch')
def finalize_tools(destination:Path)->dict:
    target=destination/'powershell/pwsh'
    require(target.is_file() and not target.is_symlink() and target.stat().st_nlink==1,'unsafe PowerShell launcher')
    before=target.stat().st_mode&0o777;target.chmod(0o755)
    return {'powershell_launcher_mode_before':oct(before),'powershell_launcher_mode_after':'0o755','launcher_sha256':sha(target),'reason':'provider TAR stores pwsh without execution bits; exact launcher only'}
def build(store:Path,destination:Path,record:dict,work_root:Path|None=None)->dict:
    no_link_ancestors(destination)
    require(not destination.exists() and not destination.is_symlink(),'destination must not exist')
    require(work_root is not None,'explicit authorized work root required')
    no_link_ancestors(work_root);no_link_ancestors(store)
    require(work_root.is_dir() and destination.parent==work_root,'destination must be a direct child of the authorized work root')
    source_root=PACKAGE.parents[1]
    require(not(work_root.is_relative_to(source_root) or source_root.is_relative_to(work_root)),'work root overlaps candidate source')
    require(not(work_root.is_relative_to(store) or store.is_relative_to(work_root)),'work root overlaps input store')
    validate_record(record);inputs=validate_inputs(store,record)
    require(platform.system()=='Linux' and platform.machine()=='x86_64','Linux x86_64 required')
    require(platform.libc_ver()==('glibc','2.41'),'reference glibc 2.41 required; other hosts unvalidated')
    flags=Path('/proc/cpuinfo').read_text();require('avx2' in flags and re.search(r'\bfma\b',flags),'AVX2 and FMA3 required')
    destination.mkdir();(destination/'logs').mkdir();(destination/'cache').mkdir();env=environment(destination)
    receipt={'status':'INCOMPLETE','runtime_admitted':False,'network_acquisition':False}
    receipt_path=destination/'bootstrap-receipt.json';receipt_path.write_text(json.dumps(receipt,indent=2)+'\n')
    by_kind={x['kind']:inputs[x['file']] for x in record['items'] if x['kind']!='wheel'}
    primary=None
    try:
        for role in ['science','wki']:
            extract_tar(by_kind['python_'+role],destination/(role+'-base'))
            python=destination/(role+'-base/python/bin/python3.12');expected=record['python_expected'][role]
            require(sha(python)==expected['executable_sha256'],'interpreter executable drift')
            require(sha(python.parent.parent/'lib/libpython3.12.so.1.0')==expected['libpython_sha256'],'libpython drift')
            uv=by_kind['installer'];base=[uv,'--no-config','--offline','--no-python-downloads','--no-cache']
            run([*base,'venv','--relocatable','--python',python,destination/role],destination,env,role+'-venv')
            lock=destination/(role+'.requirements.txt')
            lock.write_text(''.join(f"{x['package']}=={x['version']} --hash=sha256:{x['sha256']}\n" for x in record['items'] if x['kind']=='wheel'))
            run([*base,'pip','install','--python',destination/role/'bin/python','--no-index','--find-links',store,'--no-deps','--require-hashes','--link-mode','copy','-r',lock],destination,env,role+'-install')
            run([*base,'pip','check','--python',destination/role/'bin/python'],destination,env,role+'-metadata')
            probe="import importlib.metadata as m,json,platform,re,sys;print(json.dumps({'python':platform.python_version(),'packages':[[re.sub(r'[-_.]+','-',d.metadata['Name'].lower()),d.version] for d in m.distributions()],'prefix':sys.prefix}))"
            actual=json.loads(run([destination/role/'bin/python','-I','-B','-c',probe],destination,env,role+'-identity'))
            installed_identity(actual,expected,record['expected_packages'])
        extract_zip(by_kind['browser'],destination/'browser')
        extract_tar(deb_payload(by_kind['git']),destination/'git',{'usr/share/common-licenses/Apache-2.0':by_kind['git_apache_notice'],'usr/share/common-licenses/GPL-2':by_kind['git_gpl_notice']})
        extract_tar(by_kind['powershell'],destination/'powershell')
        receipt['tool_finalization']=finalize_tools(destination)
        receipt.update(status='CONSTRUCTED_NOT_ADMITTED',python_versions={'science':'3.12.10','wki':'3.12.14'},packages_per_role=len(record['expected_packages']),relocation_test='NOT_YET_RUN')
    except BaseException as error:
        primary=error;receipt.update(status='FAILED',error_type=type(error).__name__,error=str(error));raise
    finally:
        try:receipt_path.write_text(json.dumps(receipt,indent=2)+'\n')
        except BaseException as receipt_error:
            if primary is None:raise
            primary.add_note('Secondary evidence write failure: '+type(receipt_error).__name__)
    return receipt
def main()->None:
    parser=argparse.ArgumentParser();parser.add_argument('--inputs',required=True,type=Path);parser.add_argument('--destination',required=True,type=Path);parser.add_argument('--work-root',required=True,type=Path);parser.add_argument('--record-sha256',required=True);args=parser.parse_args()
    record_path=PACKAGE/'PORTABLE_INPUTS_DRAFT.json'
    require(sha(record_path)==args.record_sha256,'external portable record digest mismatch')
    record=json.loads(record_path.read_text())
    print(json.dumps(build(args.inputs.absolute(),args.destination.absolute(),record,args.work_root.absolute())))
if __name__=='__main__':main()
