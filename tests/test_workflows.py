import copy
import json
import tempfile
import unittest
from pathlib import Path
from openfilmqa.review import digest, CATEGORIES
from openfilmqa.evaluation import evaluate
from openfilmqa.repair import compare
from openfilmqa.adapters import judge


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        (self.base/'source.bin').write_bytes(b'known test source')
        (self.base/'owner.txt').write_text('Human label fixture for engine behavior only')
        self.source = {'file': 'source.bin', 'sha256': digest(self.base/'source.bin')}
        self.case = {'id': 'case-a', 'group': 'film-a/scene-a', 'split': 'test', 'source': self.source,
                     'owner': {'labelled_by': 'human fixture', 'reference': {'file': 'owner.txt', 'sha256': digest(self.base/'owner.txt')},
                               'issues': [{'id': 'missing-action', 'severity': 'major'}], 'preference': 'after', 'repair': 'regressed'}}
        self.prediction = {'case_id': 'case-a', 'source_sha256': self.source['sha256'], 'reviewer': 'fixture', 'completed': True,
                           'issues': [{'id': 'missing-action', 'severity': 'major'}, {'id': 'false-alarm', 'severity': 'minor'}],
                           'preference': 'before', 'repair': 'improved'}

    def tearDown(self):
        self.temp.cleanup()

    def test_real_metrics_include_false_alarms_and_harmful_repair(self):
        r = evaluate({'schema_version': 1, 'cases': [self.case]}, {'predictions': [self.prediction]}, self.base)
        self.assertEqual((r['matched_issues'],r['false_alarms'],r['important_misses']),(1,1,0))
        self.assertEqual(r['precision'],0.5)
        self.assertEqual(r['preference_accuracy'],0)
        self.assertEqual(r['repair_accuracy'],0)

    def test_missing_prediction_stays_in_denominator(self):
        r = evaluate({'schema_version': 1, 'cases': [self.case]}, {'predictions': []}, self.base)
        self.assertEqual((r['coverage'],r['recall'],r['important_misses']),(0,0,1))
        self.assertEqual(r['status'],'incomplete')

    def test_unlabelled_is_never_perfect_accuracy(self):
        del self.case['owner']
        r = evaluate({'schema_version': 1, 'cases': [self.case]}, {'predictions': []}, self.base)
        self.assertIsNone(r['recall']);self.assertEqual(r['unlabelled_cases'],['case-a'])

    def test_group_and_exact_source_split_leakage_rejected(self):
        other = copy.deepcopy(self.case); other.update(id='case-b', split='train')
        with self.assertRaises(ValueError): evaluate({'schema_version':1,'cases':[self.case,other]}, {'predictions':[]}, self.base)
        other['group']='different-group'
        with self.assertRaises(ValueError): evaluate({'schema_version':1,'cases':[self.case,other]}, {'predictions':[]}, self.base)

    def test_changed_owner_provenance_rejected(self):
        (self.base/'owner.txt').write_text('changed')
        with self.assertRaises(ValueError): evaluate({'schema_version':1,'cases':[self.case]}, {'predictions':[]}, self.base)

    def reviews(self):
        evidence = [{'file':'source.bin','time_seconds':0,'sha256':self.source['sha256']}]
        shot = {'id':'s01','expected':{c:'intended' for c in CATEGORIES}, 'observed':{c:'intended' for c in CATEGORIES}, 'evidence':evidence,
                'playback':{'source_sha256':'a'*64,'reviewer':'human','watched_full':True}}
        before = {'schema_version':1,'scope':'shot','movie_sha256':'a'*64,'shots':[shot]}
        shot['observed']['environment']='wrong room'
        shot['adjudications']={'environment':{'status':'confirmed','reviewer':'human','reason':'Changed room'}}
        after=copy.deepcopy(before);after['movie_sha256']='b'*64
        after['shots'][0]['playback']['source_sha256']='b'*64
        after['shots'][0]['observed']['environment']='intended'
        after['repair_review']={'before_sha256':'a'*64,'after_sha256':'b'*64,'reviewer':'human',
                                'watched_before_after':True,'adjacent_shots_checked':True}
        return before,after

    def test_repair_needs_replacement_coverage_and_adjacent_check(self):
        before,after=self.reviews()
        self.assertEqual(compare(before,after,self.base,self.base)['status'],'reviewed repair')
        del after['shots'][0]['observed']['environment']
        self.assertEqual(compare(before,after,self.base,self.base)['unreviewed'],[{'shot':'s01','check':'environment'}])
        before,after=self.reviews();after['repair_review']['adjacent_shots_checked']=False
        self.assertEqual(compare(before,after,self.base,self.base)['status'],'needs review')

    def test_clean_before_still_needs_adjacency_attestation(self):
        before,after=self.reviews()
        before['shots'][0]['observed']['environment']='intended'
        del after['repair_review']
        self.assertEqual(compare(before,after,self.base,self.base)['status'],'needs review')

    def test_looser_spec_does_not_resolve_fault(self):
        before,after=self.reviews();after['shots'][0]['expected']['environment']='wrong room';after['shots'][0]['observed']['environment']='wrong room'
        self.assertEqual(compare(before,after,self.base,self.base)['status'],'needs review')

    def test_new_fault_is_a_regression(self):
        before,after=self.reviews();s=after['shots'][0];s['observed']['identity']='changed'
        s['adjudications']['identity']={'status':'confirmed','reviewer':'human','reason':'Identity changed'}
        self.assertEqual(compare(before,after,self.base,self.base)['status'],'regression')

    def adapter_inputs(self, argv):
        packet={'movie_source':str(self.base/'source.bin'),'movie_sha256':self.source['sha256'],'duration_seconds':1,
                'frames':[{**self.source,'time_seconds':0}]}
        (self.base/'packet.json').write_text(json.dumps(packet))
        (self.base/'adapter.json').write_text(json.dumps({'argv':argv,'capabilities':{'images':True,'video':False,'audio':False}}))
        return self.base/'packet.json',self.base/'adapter.json'

    def test_adapter_is_default_dry_run_and_rejects_motion_claim(self):
        packet,config=self.adapter_inputs(['nonexistent-reviewer'])
        r=judge(packet,config,self.base/'job');self.assertFalse(r['executed']);self.assertEqual(r['status'],'prepared')
        with self.assertRaises(ValueError):judge(packet,config,self.base/'motion',scope='shot')

    def test_failed_transport_never_returns_pass(self):
        packet,config=self.adapter_inputs(['nonexistent-reviewer'])
        with self.assertRaises(ValueError):judge(packet,config,self.base/'job',execute=True)
        receipt=json.loads((self.base/'job/receipt.json').read_text());self.assertEqual(receipt['status'],'unreviewed')

    def test_real_local_subprocess_response_is_validated(self):
        import sys
        worker = self.base / 'worker.py'
        worker.write_text("import sys,json\nrequest=json.loads(sys.stdin.read().split('Request:\\n')[-1])\n"
                         "print(json.dumps({'schema_version':1,'scope':request['scope'],'profile':'director',"
                         "'movie_sha256':request['movie_sha256'],'shots':[{'id':'s01','expected':{},'observed':{},"
                         "'evidence':[e for e in request['evidence'] if 'time_seconds' in e]}]}))\n")
        packet,config=self.adapter_inputs([sys.executable,str(worker)])
        receipt=judge(packet,config,self.base/'valid-job',execute=True)
        self.assertTrue(receipt['executed']);self.assertEqual(receipt['status'],'unreviewed')
        report=json.loads((self.base/'valid-job/report.json').read_text())
        self.assertEqual(report['profile'],'director')
        self.assertTrue(any(c['status']=='unreviewed' for c in report['coverage']))
        self.assertTrue(any(c['status']=='out of scope' for c in report['coverage']))

    def test_movie_change_during_reviewer_call_invalidates_result(self):
        import sys
        worker=self.base/'mutate.py'
        worker.write_text("import sys,json\nfrom pathlib import Path\nr=json.loads(sys.stdin.read().split('Request:\\n')[-1])\n"
                         "Path(r['movie_source']).write_bytes(b'changed during review')\n"
                         "print(json.dumps({'schema_version':1,'scope':r['scope'],'profile':'director',"
                         "'movie_sha256':r['movie_sha256'],'shots':[{'id':'s01'}]}))\n")
        packet,config=self.adapter_inputs([sys.executable,str(worker)])
        with self.assertRaises(ValueError):judge(packet,config,self.base/'changing-job',execute=True)
        receipt=json.loads((self.base/'changing-job/receipt.json').read_text())
        self.assertEqual(receipt['status'],'unreviewed')
        self.assertFalse((self.base/'changing-job/report.json').exists())

    def test_adapter_rejects_changed_attachment(self):
        packet,config=self.adapter_inputs(['nonexistent-reviewer'])
        (self.base/'source.bin').write_bytes(b'changed')
        with self.assertRaises(ValueError):judge(packet,config,self.base/'job')


if __name__=='__main__':unittest.main()
