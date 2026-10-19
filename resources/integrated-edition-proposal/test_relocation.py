"""Explicit rebind protects linked ancestors and already sealed work."""
import hashlib,importlib.util,json,os,shutil,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('relocate',Path(__file__).with_name('relocate_draft.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class RebindControls(unittest.TestCase):
    def fixture(self,root):
        runtime=root/'runtime';runtime.mkdir();package=root/'package';package.mkdir();expected={}
        for role in ['science','wki']:
            base=runtime/(role+'-base/python/bin');base.mkdir(parents=True);exe=base/'python3.12';exe.write_bytes(b'fixture interpreter');expected[role]={'executable_sha256':hashlib.sha256(exe.read_bytes()).hexdigest()}
            venv=runtime/role;(venv/'bin').mkdir(parents=True);(venv/'pyvenv.cfg').write_text('home = /old/'+role+'-base/python/bin\nrelocatable = true\n');(venv/'bin/python').symlink_to('/old/'+role+'-base/python/bin/python3.12')
        (package/'PORTABLE_INPUTS_DRAFT.json').write_text(json.dumps({'python_expected':expected}));(runtime/'bootstrap-receipt.json').write_text(json.dumps({'status':'CONSTRUCTED_NOT_ADMITTED','runtime_admitted':False}));return runtime,package
    def test_positive_rebind_and_idempotent_second_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,package=self.fixture(Path(tmp))
            with patch.object(m,'PACKAGE',package):
                self.assertEqual(m.rebind(root)['status'],'REBOUND_NOT_ADMITTED');m.rebind(root)
            self.assertEqual(os.readlink(root/'science/bin/python'),'../../science-base/python/bin/python3.12')
            self.assertIn(str(root/'science-base/python/bin'),(root/'science/pyvenv.cfg').read_text())
    def test_symlinked_venv_or_bin_cannot_write_victim(self):
        for target in ['science','science/bin']:
            with self.subTest(target=target),tempfile.TemporaryDirectory() as tmp:
                base=Path(tmp);root,package=self.fixture(base)
                with patch.object(m,'PACKAGE',package):m.rebind(root)
                original=root/target;victim=base/'victim';original.rename(victim);original.symlink_to(victim,target_is_directory=True)
                before={p.relative_to(victim).as_posix():(os.readlink(p) if p.is_symlink() else p.read_bytes()) for p in victim.rglob('*') if p.is_symlink() or p.is_file()}
                with patch.object(m,'PACKAGE',package),self.assertRaisesRegex(RuntimeError,'Unexpected linked runtime'):m.rebind(root)
                after={p.relative_to(victim).as_posix():(os.readlink(p) if p.is_symlink() else p.read_bytes()) for p in victim.rglob('*') if p.is_symlink() or p.is_file()};self.assertEqual(before,after)
    def test_sealed_root_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,package=self.fixture(Path(tmp));(root/'LOCAL_CANDIDATE_IDENTITY.json').write_text('{}')
            with patch.object(m,'PACKAGE',package),self.assertRaisesRegex(RuntimeError,'Sealed evidence'):m.rebind(root)
if __name__=='__main__':unittest.main()
