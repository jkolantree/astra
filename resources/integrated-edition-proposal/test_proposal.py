"""Positive-first freshness and report corruption controls for the private proposal."""

import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import verify_edition as gate
import validate_reports as reports


class FreshnessControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.stage = self.root/"stage"
        self.stage.mkdir()
        (self.stage/"input.txt").write_text("fixed input")
        (self.stage/"output.txt").write_text("fresh result")
        self.inputs = {"input.txt":gate.digest(self.stage/"input.txt")}
        self.outputs = {"output.txt"}
        self.assertEqual(gate.audit_stage(self.stage,self.inputs,self.outputs),
                         {"output.txt":gate.digest(self.stage/"output.txt")})

    def test_missing_output(self):
        (self.stage/"output.txt").unlink()
        with self.assertRaises(ValueError): gate.audit_stage(self.stage,self.inputs,self.outputs)

    def test_extra_public_output(self):
        (self.stage/"extra.txt").write_text("unexpected")
        with self.assertRaises(ValueError): gate.audit_stage(self.stage,self.inputs,self.outputs)

    def test_source_mutation(self):
        (self.stage/"input.txt").write_text("changed")
        with self.assertRaises(ValueError): gate.audit_stage(self.stage,self.inputs,self.outputs)

    def test_deleted_input(self):
        (self.stage/"input.txt").unlink()
        with self.assertRaises(ValueError): gate.audit_stage(self.stage,self.inputs,self.outputs)

    def test_output_symlink_and_victim(self):
        target=self.root/"victim";target.write_text("unchanged")
        (self.stage/"output.txt").unlink();(self.stage/"output.txt").symlink_to(target)
        with self.assertRaises(ValueError): gate.audit_stage(self.stage,self.inputs,self.outputs)
        self.assertEqual(target.read_text(),"unchanged")

    def test_hardlinked_output(self):
        target=self.root/"victim";target.write_text("unchanged")
        (self.stage/"output.txt").unlink();os.link(target,self.stage/"output.txt")
        with self.assertRaises(ValueError): gate.audit_stage(self.stage,self.inputs,self.outputs)

    def test_linked_directory(self):
        (self.stage/"linked").symlink_to(self.root,target_is_directory=True)
        with self.assertRaises(ValueError): gate.audit_stage(self.stage,self.inputs,self.outputs)

    def test_directory_is_not_an_output(self):
        (self.stage/"output.txt").unlink();(self.stage/"output.txt").mkdir()
        with self.assertRaises(ValueError): gate.audit_stage(self.stage,self.inputs,self.outputs)

    def test_separate_input_only_trees_and_stale_refusal(self):
        with patch.object(gate,"ROOT",self.stage):
            for name in ["first","second"]:
                dest=self.root/name
                gate.prepare_stage(dest,self.inputs,self.outputs)
                self.assertFalse((dest/"output.txt").exists())
                self.assertEqual(gate.files(dest),self.inputs)
                with self.assertRaises(ValueError):gate.prepare_stage(dest,self.inputs,self.outputs)

    def test_unsafe_paths(self):
        for name in ["../escape","/absolute","a/../b","a//b","./file","a\\b","C:file"]:
            with self.subTest(name=name),self.assertRaises(ValueError):gate.safe_path(self.stage,name)

    def test_receipt_progress_and_link_controls(self):
        gate.save_receipt(self.root,{"status":"INCOMPLETE"})
        gate.save_receipt(self.root,{"status":"PASS"})
        self.assertEqual(json.loads((self.root/"freshness-receipt.json").read_text())["status"],"PASS")
        (self.root/"freshness-receipt.json").unlink()
        victim=self.root/"victim";victim.write_text("unchanged")
        (self.root/"freshness-receipt.json").symlink_to(victim)
        with self.assertRaises(ValueError):gate.save_receipt(self.root,{"status":"FAIL"})
        self.assertEqual(victim.read_text(),"unchanged")

    def test_timeout_kills_descendant_process(self):
        script=self.stage/"spawn.py"
        script.write_text("import subprocess,sys,time\nfrom pathlib import Path\n"
                          "p=subprocess.Popen([sys.executable,'-I','-B','-c','import time;time.sleep(30)'])\n"
                          "Path('descendant.pid').write_text(str(p.pid))\ntime.sleep(30)\n")
        with self.assertRaises(subprocess.TimeoutExpired):
            gate.child(sys.executable,self.stage,dict(os.environ),"spawn.py",[],
                       self.root/"child.log",timeout=1)
        pid=int((self.stage/"descendant.pid").read_text())
        state=Path(f"/proc/{pid}/stat")
        self.assertTrue(not state.exists() or state.read_text().split()[2] in {"Z","X"})


class PayloadControls(unittest.TestCase):
    def setUp(self):
        root=Path(os.environ["EDITION_REPORT_DIRECTORY"])
        self.payloads=[json.loads((root/n).read_text()) for n in
                       ["integrated-case.json","scm-checks.json","wki-checks.json"]]
        reports.validate(*self.payloads)

    def corrupt(self,index,key,value):
        payloads=copy.deepcopy(self.payloads)
        payloads[index][key]=value
        with self.assertRaises(ValueError):reports.validate(*payloads)

    def test_integration_cannot_claim_empirical_or_release_admission(self):
        for key in ["empirical_admission","core_release_promoted"]:
            with self.subTest(key=key):self.corrupt(0,key,True)

    def test_integration_wrong_fixture(self):self.corrupt(0,"case_sha256","0"*64)

    def test_integration_bad_mass_ledger(self):
        value=copy.deepcopy(self.payloads[0]["transport"]);value["mass_closure_residual_kg"]=1
        self.corrupt(0,"transport",value)

    def test_integration_bad_record_ledger(self):
        value=copy.deepcopy(self.payloads[0]["archive"]);value["balance_residual"]=1
        self.corrupt(0,"archive",value)

    def test_empty_or_missing_observation_bin(self):
        self.corrupt(0,"observations",[])
        self.corrupt(0,"observations",self.payloads[0]["observations"][:-1])

    def test_nonfinite_archive_or_observation(self):
        for bad in [float("inf"),float("nan"),float("-inf")]:
            value=copy.deepcopy(self.payloads[0]["archive"]);value["expected_input_records"]=bad
            with self.subTest(bad=bad):self.corrupt(0,"archive",value)
        value=copy.deepcopy(self.payloads[0]["observations"]);value[0]["expected_counts"][0]=float("inf")
        self.corrupt(0,"observations",value)

    def test_observation_record_disagreement(self):
        value=copy.deepcopy(self.payloads[0]["observations"]);value[0]["expected_counts"][0]+=1
        self.corrupt(0,"observations",value)

    def test_expected_count_sum_overflow(self):
        value=copy.deepcopy(self.payloads[0]["observations"])
        for record in value:record["expected_counts"][0]=1e308
        self.corrupt(0,"observations",value)

    def test_scm_wrong_source(self):self.corrupt(1,"script_sha256","0"*64)

    def test_scm_wrong_runtime(self):
        value=copy.deepcopy(self.payloads[1]["runtime"]);value["python"]="3.12.14"
        self.corrupt(1,"runtime",value)

    def test_scm_empirical_claim(self):self.corrupt(1,"empirical_data",True)

    def test_scm_missing_case(self):self.corrupt(1,"checks",self.payloads[1]["checks"][:-1])

    def test_scm_wrong_case(self):
        value=copy.deepcopy(self.payloads[1]["checks"]);value[0]["name"]="unreviewed"
        self.corrupt(1,"checks",value)

    def test_scm_failed_case(self):
        value=copy.deepcopy(self.payloads[1]["checks"]);value[0]["passed"]=False
        self.corrupt(1,"checks",value)

    def test_wki_wrong_runtime(self):self.corrupt(2,"python","3.12.10")

    def test_wki_nonzero_residual(self):
        value=copy.deepcopy(self.payloads[2]["checks"])
        value["normalized_maximum_growth"]["residuals"][0]="1"
        self.corrupt(2,"checks",value)


if __name__ == "__main__":
    unittest.main()
