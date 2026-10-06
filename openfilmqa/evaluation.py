"""Measure reviewer reliability against independently labelled, private cases."""
from .review import digest, meaningful
from pathlib import Path
import re


def checked_source(value, base):
    if not isinstance(value, dict) or not isinstance(value.get('file'), str):
        raise ValueError('Every source needs file and SHA-256')
    path = (base / value['file']).resolve()
    if not path.is_relative_to(base.resolve()) or not path.is_file() or digest(path) != value.get('sha256'):
        raise ValueError('Source is missing, changed, or outside the dataset folder')
    return value['sha256']


def issue_map(items):
    if not isinstance(items, list):
        raise ValueError('issues must be a list')
    result = {}
    for issue in items:
        if not isinstance(issue, dict) or not isinstance(issue.get('id'), str) or not issue['id'].strip():
            raise ValueError('Issues need non-empty manually matched IDs')
        if issue['id'] in result or issue.get('severity') not in ('minor', 'major', 'blocker'):
            raise ValueError('Issues need unique IDs and valid severities')
        result[issue['id']] = issue['severity']
    return result


def evaluate(dataset, results, base='.'):
    base = Path(base)
    if not isinstance(dataset, dict) or dataset.get('schema_version') != 1 or not isinstance(dataset.get('cases'), list) or not dataset['cases']:
        raise ValueError('Provide a versioned dataset with non-empty cases')
    if not isinstance(results, dict) or not isinstance(results.get('predictions'), list):
        raise ValueError('Provide predictions in a separate object')
    cases, groups, hashes = {}, {}, {}
    for case in dataset['cases']:
        if not isinstance(case, dict) or not isinstance(case.get('id'), str) or not case['id'].strip() or case['id'] in cases:
            raise ValueError('Every case needs a unique non-empty id')
        group, split = case.get('group'), case.get('split')
        if not isinstance(group, str) or not group.strip() or split not in ('train', 'test'):
            raise ValueError('Group by project/scene/take family; split must be train or test')
        sha = checked_source(case.get('source'), base)
        for table, key in ((groups, group), (hashes, sha)):
            if key in table and table[key] != split:
                raise ValueError('Training/test leakage: group or exact source occurs in both splits')
            table[key] = split
        cases[case['id']] = case
    predictions = {}
    for row in results['predictions']:
        if not isinstance(row, dict) or row.get('case_id') not in cases or row['case_id'] in predictions:
            raise ValueError('Prediction needs a known, unique case_id')
        if row.get('source_sha256') != cases[row['case_id']]['source']['sha256']:
            raise ValueError('Prediction refers to a different source version')
        if row.get('completed') is True and not meaningful(row.get('reviewer')):
            raise ValueError('Completed prediction needs a reviewer')
        issue_map(row.get('issues', []))
        predictions[row['case_id']] = row
    rows = []
    tp = fp = fn = major_misses = labelled = reviewed = preferences = preferred = repairs = correct_repairs = 0
    unlabelled = []
    for key, case in cases.items():
        if case['split'] != 'test':
            continue
        owner = case.get('owner')
        if not isinstance(owner, dict) or not meaningful(owner.get('labelled_by')) or not owner.get('reference'):
            unlabelled.append(key)
            continue
        checked_source(owner['reference'], base)
        truth = issue_map(owner.get('issues'))
        labelled += 1
        prediction = predictions.get(key)
        complete = bool(prediction and prediction.get('completed') is True)
        found = issue_map(prediction.get('issues', [])) if complete else {}
        reviewed += int(complete)
        hits, alarms, misses = truth.keys() & found.keys(), found.keys() - truth.keys(), truth.keys() - found.keys()
        tp += len(hits); fp += len(alarms); fn += len(misses)
        major_misses += sum(truth[i] in ('major', 'blocker') for i in misses)
        for dimension, allowed in (('preference', ('before', 'after', 'tie')), ('repair', ('improved', 'regressed', 'unchanged'))):
            expected = owner.get(dimension)
            if expected is not None and expected not in allowed:
                raise ValueError(f'Unknown owner {dimension}')
            if expected is not None:
                correct = complete and prediction.get(dimension) == expected
                if dimension == 'preference': preferences += 1; preferred += int(correct)
                else: repairs += 1; correct_repairs += int(correct)
        rows.append({'case_id': key, 'status': 'reviewed' if complete else 'missing or abstained',
                     'matched': sorted(hits), 'false_alarms': sorted(alarms), 'missed': sorted(misses)})
    ratio = lambda a, b: a / b if b else None
    return {'schema_version': 1, 'status': 'measured' if labelled and reviewed == labelled and not unlabelled else 'incomplete',
            'test_cases': len(rows) + len(unlabelled), 'labelled_cases': labelled, 'reviewed_cases': reviewed,
            'coverage': ratio(reviewed, labelled), 'unlabelled_cases': unlabelled, 'abstentions_or_missing': labelled - reviewed,
            'matched_issues': tp, 'false_alarms': fp, 'missed_issues': fn, 'important_misses': major_misses,
            'precision': ratio(tp, tp + fp), 'recall': ratio(tp, tp + fn),
            'preference_accuracy': ratio(preferred, preferences), 'preference_cases': preferences,
            'repair_accuracy': ratio(correct_repairs, repairs), 'repair_cases': repairs, 'cases': rows,
            'notes': ['Exact issue IDs are matched by an independent curator; no semantic model is hidden in this command.',
                      'Missing reviews remain in denominators and count as missed known issues.',
                      'Labels are supplied human provenance, not an authentication or film-perception guarantee.',
                      'Do not call a small historical dataset proof of future artistic quality.']}
