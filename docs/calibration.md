# Evaluate the reviewer

Keep owner labels and production footage private. This repository contains no
production case study, human verdict dataset or claimed benchmark result.

Create a local dataset JSON with `schema_version: 1` and `cases`. Each case has:

- `id`: stable case identity; `group`: project/scene/take-family identity.
- `split`: `train` or `test`; related versions must stay in one split.
- `source`: actual local `file` and SHA-256, inside the dataset folder.
- `owner`: `labelled_by`, hashed `reference` to the saved original human verdict,
  and `issues`, each with manually curated unique `id` and `severity`.
- Optional human `preference`: `before`, `after` or `tie`; `repair`: `improved`,
  `regressed` or `unchanged`. Do not turn an AI guess into a human label.

Predictions are a separate JSON object with `predictions`: each contains
`case_id`, exact `source_sha256`, `reviewer`, `completed`, `issues` and optional
`preference`/`repair`. Save raw reviewer outputs before revealing labels. A
curator independently matches equivalent issue claims to stable IDs; the engine
compares those IDs exactly. It does not secretly perform semantic matching.

```sh
python3 -m openfilmqa evaluate /private/cases/dataset.json /private/run/predictions.json
```

The command verifies files and label references, rejects exact-source or group
leakage, and measures test cases only. It reports coverage, false alarms, missed
faults, important misses, precision/recall, preference and repair accuracy.
Missing reviews stay in denominators and count as misses of known faults.
Unlabelled cases are explicitly excluded from accuracy and make status incomplete.
No available observations yields null metrics, never a perfect score.

A `measured` status means the dataset was evaluated completely; it is not PASS.
Report dataset size, split construction, review capability and curation alongside
numbers. Compare old/new prompts on the same frozen held-out inputs. Keep source
and human label provenance, but a hash alone cannot authenticate the human.
Do not claim a few historical cases demonstrate improvement on unseen films.
No feedback is automatically written into a shared skill, production policy or
model weights. Review and authorize such changes separately.
