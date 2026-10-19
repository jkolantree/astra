"""Positive-first corruption controls for the offline extraction boundary."""
import copy,hashlib,importlib.util,io,json,os,sys,subprocess,tarfile,tempfile,time,unittest
from unittest.mock import patch
from pathlib import Path
spec=importlib.util.spec_from_file_location('draft_bootstrap',Path(__file__).with_name('bootstrap_draft.py'))
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
class BootstrapControls(unittest.TestCase):
    def artifact_fixture(self,root):
        p=root/'wheel.whl';p.write_bytes(b'approved');return {'status':'PROPOSED_NOT_ADMITTED','runtime_admitted':False,'items':[{'file':p.name,'bytes':8,'sha256':hashlib.sha256(b'approved').hexdigest()}]}
    def test_artifact_corruption_is_detected_after_positive_control(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);record=self.artifact_fixture(root);self.assertEqual(len(b.validate_inputs(root,record)),1)
            (root/'wheel.whl').write_bytes(b'changed!')
            with self.assertRaisesRegex(RuntimeError,'artifact hash mismatch'):b.validate_inputs(root,record)
    def test_missing_artifact_is_detected_after_positive_control(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);record=self.artifact_fixture(root);b.validate_inputs(root,record);(root/'wheel.whl').unlink()
            with self.assertRaisesRegex(RuntimeError,'missing artifact'):b.validate_inputs(root,record)
    def test_linked_artifact_is_rejected(self):
        for hard in [False,True]:
            with self.subTest(hard=hard),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);record=self.artifact_fixture(root);b.validate_inputs(root,record);p=root/'wheel.whl';q=root/'original';p.rename(q)
                os.link(q,p) if hard else p.symlink_to(q)
                with self.assertRaisesRegex(RuntimeError,'unsafe or missing artifact'):b.validate_inputs(root,record)
    def test_admission_label_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);record=self.artifact_fixture(root);b.validate_inputs(root,record);record['runtime_admitted']=True
            with self.assertRaisesRegex(RuntimeError,'draft status required'):b.validate_inputs(root,record)
    def test_duplicate_artifact_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);record=self.artifact_fixture(root);b.validate_inputs(root,record);record['items']*=2
            with self.assertRaisesRegex(RuntimeError,'duplicate artifact'):b.validate_inputs(root,record)
    def archive(self,items):
        buffer=io.BytesIO()
        with tarfile.open(fileobj=buffer,mode='w') as tar:
            for name,kind,target in items:
                m=tarfile.TarInfo(name);m.type=kind
                if kind==tarfile.REGTYPE:m.size=4;tar.addfile(m,io.BytesIO(b'data'))
                else:m.linkname=target;tar.addfile(m)
        buffer.seek(0);return buffer
    def test_positive_archive_extracts_regular_file_and_internal_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)/'out';b.extract_tar(self.archive([('python/file',tarfile.REGTYPE,''),('python/link',tarfile.SYMTYPE,'file')]),dest)
            self.assertEqual((dest/'python/link').read_bytes(),b'data')
    def test_traversal_and_absolute_members_fail_before_extraction(self):
        for name in ['../outside','/outside','a/../../b']:
            with self.subTest(name=name),self.assertRaisesRegex(RuntimeError,'unsafe archive member'):
                with tarfile.open(fileobj=self.archive([(name,tarfile.REGTYPE,'')])) as tar:b.inspect_tar(tar)
    def test_escaping_link_fails_at_link_guard(self):
        with self.assertRaisesRegex(RuntimeError,'escaping or unresolved'):
            with tarfile.open(fileobj=self.archive([('python/file',tarfile.REGTYPE,''),('python/link',tarfile.SYMTYPE,'../../outside')])) as tar:b.inspect_tar(tar)
    def test_member_beneath_link_fails_at_link_parent_guard(self):
        with self.assertRaisesRegex(RuntimeError,'beneath link'):
            with tarfile.open(fileobj=self.archive([('target',tarfile.DIRTYPE,''),('link',tarfile.SYMTYPE,'target'),('link/file',tarfile.REGTYPE,'')])) as tar:b.inspect_tar(tar)
    def test_duplicate_tar_member_is_refused(self):
        with self.assertRaisesRegex(RuntimeError,'duplicate archive member'):
            with tarfile.open(fileobj=self.archive([('file',tarfile.REGTYPE,''),('file',tarfile.REGTYPE,'')])) as tar:b.inspect_tar(tar)
    def test_device_member_is_refused(self):
        with self.assertRaisesRegex(RuntimeError,'special archive member'):
            with tarfile.open(fileobj=self.archive([('device',tarfile.CHRTYPE,'')])) as tar:b.inspect_tar(tar)
    def test_existing_destination_is_never_reused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);record=self.artifact_fixture(root);b.validate_inputs(root,record);dest=root/'existing';dest.mkdir();(dest/'keep').write_text('unchanged')
            with self.assertRaisesRegex(RuntimeError,'destination must not exist'):b.build(root,dest,record)
            self.assertEqual((dest/'keep').read_text(),'unchanged')
    def record_fixture(self):
        record=json.loads((b.PACKAGE/'PORTABLE_INPUTS_DRAFT.json').read_text());b.validate_record(record);return record
    def test_exact_record_roles_keys_versions_and_package_roster(self):
        base=self.record_fixture()
        mutations=[('exact record keys',lambda r:r.update(extra=True)),('draft schema',lambda r:r.update(schema='wrong')),('exact artifact role',lambda r:r['items'].pop()),('exact artifact role',lambda r:r['items'][-1].update(kind='installer')),('exact package roster',lambda r:r['expected_packages'].pop('numpy')),('duplicate or incompatible wheel',lambda r:r['items'][1].update(package=r['items'][0]['package'])),('invalid artifact size',lambda r:r['items'][0].update(bytes=True)),('exact artifact keys',lambda r:r['items'][0].update(extra=True)),('split interpreter',lambda r:r['python_expected']['science'].update(version='3.12.14'))]
        for guard,mutate in mutations:
            with self.subTest(guard=guard):
                r=copy.deepcopy(base);mutate(r)
                with self.assertRaisesRegex(RuntimeError,guard):b.validate_record(r)
    def test_installed_metadata_duplicates_and_wrong_interpreter(self):
        r=self.record_fixture();actual={'python':'3.12.10','packages':list(r['expected_packages'].items())};b.installed_identity(actual,r['python_expected']['science'],r['expected_packages'])
        bad=copy.deepcopy(actual);bad['packages'][-1]=bad['packages'][0]
        with self.assertRaisesRegex(RuntimeError,'duplicate installed'):b.installed_identity(bad,r['python_expected']['science'],r['expected_packages'])
        actual['python']='3.12.14'
        with self.assertRaisesRegex(RuntimeError,'installed runtime identity'):b.installed_identity(actual,r['python_expected']['science'],r['expected_packages'])
    def test_all_link_ancestors_and_sealed_roots_rejected_without_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);real=root/'real';real.mkdir();(real/'sub').mkdir();b.no_link_ancestors(real/'sub/new')
            link=root/'link';link.symlink_to(real,target_is_directory=True)
            with self.assertRaisesRegex(RuntimeError,'symbolic-link path ancestor'):b.no_link_ancestors(link/'sub/new')
            self.assertFalse((real/'sub/new').exists());(real/'LOCAL_CANDIDATE_IDENTITY.json').write_text('{}')
            with self.assertRaisesRegex(RuntimeError,'sealed evidence'):b.no_link_ancestors(real/'sub/new')
    def test_work_root_candidate_and_input_overlap_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'candidate';package=source/'resources/package';package.mkdir(parents=True);store=root/'inputs';store.mkdir()
            with patch.object(b,'PACKAGE',package):
                with self.assertRaisesRegex(RuntimeError,'overlaps candidate'):b.build(store,source/'new',{},source)
                with self.assertRaisesRegex(RuntimeError,'overlaps input'):b.build(store,store/'new',{},store)
            self.assertFalse((source/'new').exists());self.assertFalse((store/'new').exists())
    def test_supervisor_positive_then_nonzero_retains_partial_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'logs').mkdir();env=b.environment(root)
            self.assertIn('positive',b.run([sys.executable,'-I','-B','-c',"print('positive')"],root,env,'positive'))
            with self.assertRaisesRegex(RuntimeError,'failed; inspect retained logs'):b.run([sys.executable,'-I','-B','-c',"import sys;print('partial');sys.exit(7)"],root,env,'nonzero')
            self.assertEqual(json.loads((root/'logs/nonzero.json').read_text())['exit_code'],7);self.assertIn('partial',(root/'logs/nonzero.stdout.txt').read_text())
    def test_timeout_kills_handshaken_descendant_and_preserves_logs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'logs').mkdir();env=b.environment(root)
            code="import subprocess,sys,time,pathlib; p=subprocess.Popen([sys.executable,'-I','-B','-c',\"import pathlib,os,time;pathlib.Path('child.pid').write_text(str(os.getpid()));print('child-started',flush=True);time.sleep(60)\"]);\nwhile not pathlib.Path('child.pid').exists():time.sleep(.01)\nprint('handshake',flush=True);time.sleep(60)"
            with self.assertRaises(subprocess.TimeoutExpired):b.run([sys.executable,'-I','-B','-c',code],root,env,'timeout',timeout=1)
            self.assertIn('handshake',(root/'logs/timeout.stdout.txt').read_text());pid=int((root/'child.pid').read_text());statpath=Path(f'/proc/{pid}/stat')
            for _ in range(100):
                if not statpath.exists() or statpath.read_text().split()[2]=='Z':break
                time.sleep(.01)
            self.assertTrue(not statpath.exists() or statpath.read_text().split()[2]=='Z');self.assertEqual(json.loads((root/'logs/timeout.json').read_text())['error_type'],'TimeoutExpired')
    def test_link_cycle_and_file_ancestor_fail_before_output_creation(self):
        for items,guard in [([('a',tarfile.SYMTYPE,'b'),('b',tarfile.SYMTYPE,'a')],'cyclic'),([('a',tarfile.REGTYPE,''),('a/b',tarfile.REGTYPE,'')],'file/directory')]:
            with tempfile.TemporaryDirectory() as tmp:
                dest=Path(tmp)/'out'
                with self.assertRaisesRegex(RuntimeError,guard):b.extract_tar(self.archive(items),dest)
                self.assertFalse(dest.exists())
if __name__=='__main__':unittest.main()
