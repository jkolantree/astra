"""Positive-first draft guards, with exact rejection stages and zero-write checks."""
import copy,hashlib,importlib.util,json,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('proposal_checks',Path(__file__).with_name('check_proposals.py'));v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)

def flags(kind):return {'schema':'astra-'+kind+'-admission-draft-1','status':'PROPOSED_NOT_ADMITTED',**{k:False for k in v.FLAGS}}
class ProposalControls(unittest.TestCase):
    def source_fixture(self,root):
        (root/'input.txt').write_text('bound source');expected={'base_commit':'fixture','operational_pin_changes':{},'protected_payload':{},'historical_authorities':{},'claim_bindings':{}}
        active=patch.object(v,'expectations',return_value=expected);active.start();self.addCleanup(active.stop)
        record={**flags('source'),'excluded_from_projection':['MANIFEST.sha256',v.PREFIX+'SOURCE_ADMISSION_DRAFT.json'],'files':v.inventory(root),'historical_authority_changed':False,'claim_status_upgraded':False,'operational_pin_changes':{},'protected_payload':{},'historical_authorities':{},'claim_bindings':{},'base_commit':'fixture'}
        p=root/v.PREFIX/'SOURCE_ADMISSION_DRAFT.json';p.parent.mkdir(parents=True);p.write_text(json.dumps(record));(root/'MANIFEST.sha256').write_text(''.join(x['sha256']+'  '+n+'\n' for n,x in v.inventory(root).items()));v.source_check(root,record);return record
    def test_source_missing_extra_changed_and_wrong_exclusions(self):
        for mutation,guard in [('missing','SOURCE_ROSTER'),('extra','SOURCE_ROSTER'),('changed','SOURCE_HASH'),('exclude','PROJECTION_EXCLUSIONS')]:
            with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);record=self.source_fixture(root)
                if mutation=='missing':(root/'input.txt').unlink()
                elif mutation=='extra':(root/'extra.txt').write_text('extra')
                elif mutation=='changed':(root/'input.txt').write_text('tamper')
                else:record['excluded_from_projection'].append('input.txt')
                with self.assertRaisesRegex(RuntimeError,'^'+guard+'$'):v.source_check(root,record)
    def test_tag_context_is_specific_after_valid_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);record=self.source_fixture(root)
            with self.assertRaisesRegex(RuntimeError,'^TAG_CONTEXT_FORBIDDEN$'):v.source_check(root,record,tag_context=True)
    def test_admission_and_claim_upgrade_are_refused(self):
        for field,guard in [('source_admitted','ADMISSION_FORBIDDEN'),('claim_status_upgraded','SOURCE_BOUNDARY')]:
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);record=self.source_fixture(root);record[field]=True
                with self.assertRaisesRegex(RuntimeError,'^'+guard+'$'):v.source_check(root,record)
    def test_manifest_tamper_is_specific_after_positive(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);record=self.source_fixture(root);p=root/'MANIFEST.sha256';p.write_text(p.read_text().replace('  input.txt','  wrong.txt'))
            with self.assertRaisesRegex(RuntimeError,'^MANIFEST_HASH$'):v.source_check(root,record)
    def test_external_digest_and_duplicate_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'record.json';p.write_text('{"key":1}');h=v.digest(p);self.assertEqual(v.load_record(p,h),{'key':1});p.write_text('{"key":2}')
            with self.assertRaisesRegex(RuntimeError,'^EXTERNAL_RECORD_DIGEST$'):v.load_record(p,h)
            p.write_text('{"key":1,"key":2}')
            with self.assertRaisesRegex(RuntimeError,'^DUPLICATE_JSON_KEY$'):v.load_record(p,v.digest(p))
    def pages_fixture(self,root):
        source=root/'source';source.mkdir();(source/'reading.html').write_text('<h1 id="a">Private draft</h1>');dest=root/'site';dest.mkdir();(dest/'index.html').write_text('historical home');(dest/'explore').mkdir();(dest/'explore/index.html').write_text('approved explorer')
        item=v.inventory(source)['reading.html'];record={**flags('pages'),'namespace':v.NAMESPACE,'latest_stable_unchanged':True,'gateway':{'source_available':False,'reconciliation':'BLOCKED_MISSING_SELECTED_SOURCE'},'baseline_fixture':v.inventory(dest),'routes':[{'family':'reading','source_path':'reading.html','destination':v.NAMESPACE+'reading.html','content_role':'reading_html',**item}]};roots={'reading':source};expected={'gateway':record['gateway'],'pages_route_definitions':[{k:row[k] for k in ['family','source_path','destination','content_role']} for row in record['routes']]}
        active=patch.object(v,'expectations',return_value=expected);active.start();self.addCleanup(active.stop)
        v.pages_check(roots,record);return roots,dest,record
    def test_pages_positive_preserves_existing_bytes_and_mtimes(self):
        with tempfile.TemporaryDirectory() as tmp:
            roots,dest,record=self.pages_fixture(Path(tmp));mtime=(dest/'index.html').stat().st_mtime_ns;result=v.assemble(roots,dest,record);self.assertEqual(result['added_files'],1);self.assertEqual((dest/'index.html').stat().st_mtime_ns,mtime);self.assertEqual((dest/'explore/index.html').read_text(),'approved explorer')
    def test_pages_mutations_fail_before_any_destination_write(self):
        for mutation,guard in [('hash','HASH'),('duplicate','DUPLICATE_ROUTE'),('traversal','PATH'),('namespace','ROUTE_NAMESPACE'),('admit','ADMISSION_FORBIDDEN'),('boolean_size','FILE_SCHEMA'),('missing_source','MISSING_OR_HARDLINK')]:
            with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as tmp:
                roots,dest,record=self.pages_fixture(Path(tmp));before=v.inventory(dest)
                if mutation=='hash':record['routes'][0]['sha256']='0'*64
                elif mutation=='duplicate':record['routes']*=2
                elif mutation=='traversal':record['routes'][0]['destination']=v.NAMESPACE+'../escape'
                elif mutation=='namespace':record['routes'][0]['destination']='latest/index.html'
                elif mutation=='admit':record['pages_admitted']=True
                elif mutation=='boolean_size':record['routes'][0]['bytes']=True
                else:(roots['reading']/'reading.html').unlink()
                with self.assertRaisesRegex(RuntimeError,'^'+guard+'$'):v.assemble(roots,dest,record)
                self.assertEqual(v.inventory(dest),before)
    def test_pages_collision_reaches_intended_guard_with_valid_baseline(self):
        with tempfile.TemporaryDirectory() as tmp:
            roots,dest,record=self.pages_fixture(Path(tmp));target=dest/record['routes'][0]['destination'];target.parent.mkdir(parents=True);target.write_text('preserve collision');record['baseline_fixture']=v.inventory(dest);before=v.inventory(dest)
            with self.assertRaisesRegex(RuntimeError,'^COLLISION$'):v.assemble(roots,dest,record)
            self.assertEqual(v.inventory(dest),before)
    def test_pages_missing_or_extra_baseline(self):
        for extra in [False,True]:
            with self.subTest(extra=extra),tempfile.TemporaryDirectory() as tmp:
                roots,dest,record=self.pages_fixture(Path(tmp))
                if extra:(dest/'private.txt').write_text('not in allowed shell')
                else:(dest/'index.html').unlink()
                before=v.inventory(dest)
                with self.assertRaisesRegex(RuntimeError,'^BASELINE_ROSTER_OR_HASH$'):v.assemble(roots,dest,record)
                self.assertEqual(v.inventory(dest),before)
    def test_pages_linked_ancestor_and_inside_source_destinations(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);roots,dest,record=self.pages_fixture(root);(root/'linked').symlink_to(dest,target_is_directory=True)
            with self.assertRaisesRegex(RuntimeError,'^DESTINATION_LINK$'):v.assemble(roots,root/'linked',record)
            inside=roots['reading']/'site';inside.mkdir()
            with self.assertRaisesRegex(RuntimeError,'^DESTINATION_OVERLAP$'):v.assemble(roots,inside,record)
            self.assertEqual(list(inside.iterdir()),[])
    def test_pages_hardlinked_victim_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);roots,dest,record=self.pages_fixture(root);os.link(dest/'index.html',root/'victim')
            with self.assertRaisesRegex(RuntimeError,'^NONREGULAR_OR_HARDLINK$'):v.assemble(roots,dest,record)
            self.assertEqual((root/'victim').read_text(),'historical home')
    def test_runtime_positive_then_wrong_profile_route_or_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);package=root/v.PREFIX;package.mkdir(parents=True)
            for name in ['bootstrap_draft.py','relocate_draft.py','prepare_runtime_paths.py']:(package/name).write_text('fixture tool')
            evidence={'evidence_hashes':{'fixture':'0'*64},'construction':{'exit_code':0},'relocation':{'status':'PASS_EXPLICIT_REBIND_REQUIRED'},'runtime_admitted':False,'bootstrap_current_sha256':v.digest(package/'bootstrap_draft.py'),'relocate_current_sha256':v.digest(package/'relocate_draft.py'),'prepare_paths_sha256':v.digest(package/'prepare_runtime_paths.py')};(package/'PORTABLE_VALIDATION_DRAFT.json').write_text(json.dumps(evidence))
            expected={'runtime_source_paths':list(v.inventory(root)),'runtime_evidence_hashes':evidence['evidence_hashes']}
            record={**flags('runtime'),'profiles':{'science':'3.12.10','wki':'3.12.14'},'routes':{'retained_science_atlas':'science','integrated_case':'science','scm':'science','new_diagrams':'science','reading_documents':'science','wki':'wki'},'historical_windows_equivalence':False,'new_acquisition':False,'source_bindings':v.inventory(root),'construction_status':'CONSTRUCTED_NOT_ADMITTED','relocation_status':'PASS_EXPLICIT_REBIND_REQUIRED'}
            with patch.object(v,'expectations',return_value=expected):
                v.runtime_check(root,record)
                for field,value,guard in [('profiles',{'science':'3.12.14','wki':'3.12.14'},'SPLIT_PROFILE'),('routes',{},'RUNTIME_ROUTES'),('historical_windows_equivalence',True,'RUNTIME_BOUNDARY'),('source_bindings',{},'MANDATORY_RUNTIME_BINDINGS')]:
                    bad=copy.deepcopy(record);bad[field]=value
                    with self.assertRaisesRegex(RuntimeError,'^'+guard+'$'):v.runtime_check(root,bad)
                (package/'bootstrap_draft.py').write_text('changed')
                with self.assertRaisesRegex(RuntimeError,'^HASH$'):v.runtime_check(root,record)
    def test_missing_mandatory_source_binding_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);record=self.source_fixture(root);record.pop('protected_payload')
            with self.assertRaisesRegex(RuntimeError,'^MANDATORY_SOURCE_BINDINGS$'):v.source_check(root,record)
    def test_empty_route_roster_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            roots,dest,record=self.pages_fixture(Path(tmp));record['routes']=[]
            with self.assertRaisesRegex(RuntimeError,'^MANDATORY_PAGES_ROSTER$'):v.assemble(roots,dest,record)
if __name__=='__main__':unittest.main()
