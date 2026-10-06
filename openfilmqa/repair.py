"""A disappeared complaint is not sufficient proof of a successful repair."""
from .review import review, meaningful
import re


def compare(before, after, before_base='.', after_base='.'):
    old, new = review(before, before_base), review(after, after_base)
    old_hash, new_hash = old.get('movie_sha256'), new.get('movie_sha256')
    valid = lambda h: isinstance(h, str) and re.fullmatch(r'[0-9a-f]{64}', h) is not None
    if not valid(old_hash) or not valid(new_hash) or old_hash == new_hash:
        raise ValueError('Repair comparison needs distinct exact before/after movie SHA-256 hashes')
    if (old['scope'], old['profile']) != (new['scope'], new['profile']):
        raise ValueError('Compare the same scope and review profile')
    key = lambda f: (f['shot'], f['check'])
    old_faults = {key(f): f for f in old['findings'] if f['status'] == 'confirmed'}
    new_faults = {key(f): f for f in new['findings'] if f['status'] != 'rejected'}
    new_coverage = {key(c): c['status'] for c in new['coverage']}
    witness = after.get('repair_review', {})
    if not isinstance(witness, dict):
        raise ValueError('repair_review must be an object')
    joined = bool(witness.get('before_sha256') == old_hash and witness.get('after_sha256') == new_hash
                  and meaningful(witness.get('reviewer')) and witness.get('watched_before_after') is True
                  and witness.get('adjacent_shots_checked') is True)
    # Same-spec comparisons prevent a looser new expectation from silently resolving a fault.
    new_shots = {s['id']: s for s in after['shots']}
    resolved, unresolved, unreviewed = [], [], []
    for k, fault in old_faults.items():
        row = {'shot': k[0], 'check': k[1]}
        if k in new_faults:
            unresolved.append(row)
        elif new_coverage.get(k) == 'reviewed' and joined and new_shots[k[0]]['expected'].get(k[1]) == fault['expected']:
            resolved.append(row)
        else:
            unreviewed.append(row)
    regressions = [{'shot': f['shot'], 'check': f['check']} for k, f in new_faults.items()
                   if k not in old_faults and f['status'] == 'confirmed']
    return {'schema_version': 1, 'resolved': resolved, 'unresolved': unresolved, 'unreviewed': unreviewed,
            'regressions': regressions, 'adjacent_review_attested': joined,
            'status': 'regression' if regressions else 'needs review' if not joined or unresolved or unreviewed or new['creative'] != 'pass' else 'reviewed repair',
            'notes': ['Confirmed new faults are regressions; pending new claims still keep the review incomplete.',
                      'Repair decisions are based on supplied observations and human playback attestations, not automatic perception.']}
