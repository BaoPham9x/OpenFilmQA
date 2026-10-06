import copy
import tempfile
import unittest
from pathlib import Path
from openfilmqa.review import CATEGORIES, digest, review


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        (self.base / 'frame.jpg').write_bytes(b'test evidence, not a real film')
        self.evidence = {'file': 'frame.jpg', 'time_seconds': 1, 'sha256': digest(self.base / 'frame.jpg')}
        self.data = {'schema_version': 1, 'shots': [{'id': 's01', 'expected': {}, 'observed': {}, 'evidence': [self.evidence]}]}

    def tearDown(self):
        self.temp.cleanup()

    def test_every_visual_rule_detects_mismatch_but_does_not_claim_confirmation(self):
        for category in CATEGORIES:
            with self.subTest(category=category):
                data = copy.deepcopy(self.data)
                data['shots'][0]['expected'][category] = {'state': 'approved'}
                data['shots'][0]['observed'][category] = {'state': 'different'}
                report = review(data, self.base)
                self.assertEqual(report['findings'][0]['check'], category)
                self.assertEqual(report['findings'][0]['status'], 'pending')
                self.assertEqual(report['creative'], 'unreviewed')

    def test_confirmed_wrong_room_requires_revision(self):
        shot = self.data['shots'][0]
        shot['expected']['environment'] = 'kitchen'
        shot['observed']['environment'] = 'different table'
        shot['adjudications'] = {'environment': {'status': 'confirmed', 'reviewer': 'operator', 'reason': 'Compared real frames'}}
        self.assertEqual(review(self.data, self.base)['creative'], 'revision')

    def test_rejected_false_alarm_is_recorded_but_not_a_confirmed_fault(self):
        shot = self.data['shots'][0]
        shot['expected']['props'] = 'basket held'
        shot['observed']['props'] = 'basket teleported'
        shot['adjudications'] = {'props': {'status': 'rejected', 'reviewer': 'operator', 'reason': 'Paw holding basket is visible'}}
        report = review(self.data, self.base)
        self.assertEqual(report['findings'][0]['status'], 'rejected')
        self.assertNotEqual(report['creative'], 'revision')

    def test_no_observations_cannot_pass(self):
        self.assertEqual(review(self.data, self.base)['creative'], 'unreviewed')

    def test_changed_or_missing_evidence_does_not_cover_a_check(self):
        self.data['shots'][0]['expected']['identity'] = 'Ginger'
        self.data['shots'][0]['observed']['identity'] = 'Ginger'
        (self.base / 'frame.jpg').write_bytes(b'replaced evidence')
        self.assertEqual(review(self.data, self.base)['coverage'][0]['status'], 'unreviewed')

    def test_path_escape_is_not_valid_evidence(self):
        self.evidence['file'] = '../outside.jpg'
        self.assertEqual(review(self.data, self.base)['coverage'][0]['status'], 'unreviewed')

    def test_duplicate_shot_id_rejected(self):
        self.data['shots'].append(copy.deepcopy(self.data['shots'][0]))
        with self.assertRaises(ValueError):
            review(self.data, self.base)

    def test_scores_or_images_alone_cannot_approve_whole_movie(self):
        self.data['shots'][0]['expected'] = {c: 'same' for c in CATEGORIES}
        self.data['shots'][0]['observed'] = {c: 'same' for c in CATEGORIES}
        self.data['film_review'] = {'score': 10, 'watched_full': True, 'listened_full': False}
        self.assertEqual(review(self.data, self.base)['creative'], 'unreviewed')

    def test_full_movie_attestation_must_match_export_and_cover_every_dimension(self):
        shot = self.data['shots'][0]
        shot['expected'] = shot['observed'] = {c: 'same' for c in CATEGORIES}
        self.data['movie_sha256'] = 'a' * 64
        self.data['film_review'] = {'movie_sha256': 'b' * 64, 'reviewer': 'operator', 'watched_full': True, 'listened_full': True,
                                   **{c: 'pass' for c in ('story', 'pacing', 'performance', 'picture', 'sound')}}
        self.assertEqual(review(self.data, self.base)['creative'], 'unreviewed')
        self.data['film_review']['movie_sha256'] = 'a' * 64
        self.assertEqual(review(self.data, self.base)['creative'], 'pass')
        self.assertNotEqual(review(self.data, self.base)['release'], 'ready for owner decision')

    def test_empty_placeholders_never_approve_release(self):
        for empty in (None, "", "   ", [], {}, {"state": None}, [""]):
            with self.subTest(empty=empty):
                data = copy.deepcopy(self.data)
                data['shots'][0]['expected'] = {c: empty for c in CATEGORIES}
                data['shots'][0]['observed'] = {c: empty for c in CATEGORIES}
                data['movie_sha256'] = 'a' * 64
                data['film_review'] = {'movie_sha256': 'a' * 64, 'reviewer': 'operator',
                    'watched_full': True, 'listened_full': True,
                    **{c: 'pass' for c in ('story', 'pacing', 'performance', 'picture', 'sound')}}
                data['technical_review'] = {'movie_sha256': 'a' * 64, 'reviewer': 'operator',
                    'decode_complete': True, 'export_matches_spec': True}
                result = review(data, self.base)
                self.assertEqual(result['creative'], 'unreviewed')
                self.assertNotEqual(result['release'], 'ready for owner decision')

    def test_explicit_false_and_zero_are_meaningful(self):
        shot = self.data['shots'][0]
        shot['expected'] = shot['observed'] = {'artifacts': False, 'props': {'count': 0}}
        covered = {c['check']: c['status'] for c in review(self.data, self.base)['coverage']}
        self.assertEqual(covered['artifacts'], 'reviewed')
        self.assertEqual(covered['props'], 'reviewed')

    def test_malformed_objects_raise_descriptive_value_error(self):
        for data in ([], {**self.data, 'film_review': []}, {**self.data, 'technical_review': []},
                     {**self.data, 'shots': [{'id': 's01', 'expected': []}]},
                     {**self.data, 'shots': [{'id': 's01', 'observed': []}]},
                     {**self.data, 'shots': [{'id': 's01', 'evidence': {}}]},
                     {**self.data, 'shots': [{'id': 's01', 'adjudications': {'props': []}}]}):
            with self.subTest(data=data), self.assertRaises(ValueError):
                review(data, self.base)

    def test_real_before_after_example(self):
        import json
        base = Path(__file__).resolve().parents[1] / 'examples' / 'little-bao-house'
        before = review(json.loads((base / 'before.json').read_text()), base)
        after = review(json.loads((base / 'after.json').read_text()), base)
        self.assertEqual(before['creative'], 'revision')
        self.assertEqual(before['findings'][0]['check'], 'environment')
        self.assertEqual(after['findings'], [])
        self.assertEqual(after['creative'], 'unreviewed')


if __name__ == '__main__':
    unittest.main()
