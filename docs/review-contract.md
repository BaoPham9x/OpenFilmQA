# Review contract

A complete workflow connects the director's intent with the viewer's experience.
Software validates records and evidence; a human or capable model supplies
observations. Neither a high score nor a successful tool call proves good film.

| Stage | Evidence | Outcome |
|---|---|---|
| Source lock | Exact hashes, approved versions, relevant references | Stable input; changed sources invalidate old decisions |
| Director intent | Essential events, opening/turn/ending, prop journey, staging and sound plan | A plan to compare against, never an artistic approval |
| Still | Original image and references | Character, wardrobe, props, environment, scale, artifacts |
| Shot | Continuous exact take, action plan, start/end state | Complete action, contact, support, screen direction |
| Scene | Continuous assembled scene with audio and adjacent shots | Cut logic, prop state, rhythm, sound and viewer change |
| Film | Full normal-speed watch/listen, phone-sized view | Story, pacing, performance, picture, sound and emotional ending |
| Adjudication | Exact cited frame/time, source and observed fact | Pending, confirmed or rejected finding with viewer impact |
| Repair | Before/after exports, original specification, neighboring shots | Resolved, unresolved, unreviewed or new regression |
| Delivery | Full decode and delivery specification | Separate technical attestation and owner release decision |
| Calibration | Frozen predictions plus independent private human labels | Reviewer reliability, not an automatic film verdict |

Source selection uses approved current references relevant to the actual shot's
angle, costume, room state, time and weather, with an assigned role. Resolve
reference-versus-old-text conflicts first. Track camera motion independently of
subject action; completed movements must not restart across cuts unless intended.
For spoken films, listen for actual character identity and distinct speakers,
exact intended words and pronunciation, natural pace, lip/sound timing and audio
glitches at cut ends. Voice IDs alone do not establish audible continuity.

## Structured review

The JSON root has `schema_version: 1`, `scope` (`still`, `shot`, `scene`, `film`),
`profile` (`visual`, `director`), `movie_sha256` and a non-empty `shots` list.
Each shot has a unique `id`, `expected`, `observed`, `evidence` and optional
`adjudications` and `playback`. Evidence has `file`, `time_seconds`, `sha256`;
files must stay within the input folder. All paths refer to actual inspected
media. Never manufacture a hash or use a producer's text as visual evidence.

Visual checks: `identity`, `wardrobe`, `props`, `environment`, `action`, `scale`,
`artifacts`. Director profile additionally requires `narrative_clarity`,
`action_completion`, `shot_join`, `sound_intent`. Expected and observed values
are meaningful JSON observations. Missing, null, blank and empty values stay
unreviewed; explicit `false` and `{"count": 0}` can express an absence.

Action, completion and join observations require shot playback containing
`source_sha256` matching the root, named `reviewer`, `watched_full: true`.
Temporal and narrative director checks are explicitly out of scope for a still
review. This permits a scoped image pass while leaving full-film release blocked.
Sound intent additionally needs `listened_full: true`. These are attestations
of the exact scoped media, not cryptographic proof that a reviewer perceived it
correctly. Stills cannot cover moving action even if playback fields say true.

A mismatch starts pending. Confirmed/rejected adjudications require `reviewer`
and `reason`. Severity is `minor`, `major` or `blocker`. Record viewer impact in
the reason and the smallest proposed change in `repair`. Confirmed faults cannot
be averaged away by higher scores; rejected false alarms remain an audit trail.

Film review requires its matching `movie_sha256`, named `reviewer`, full watch
and listen, plus `pass`/`revision` on `story`, `pacing`, `performance`, `picture`,
`sound`. Technical review separately records matching movie hash, named reviewer,
`decode_complete: true`, `export_matches_spec: true`. A scoped pass cannot release
a full film. A fully reviewed film still needs the owner's publication decision.

## Repair comparison

`compare before.json after.json` needs distinct movie hashes, the same scope and
profile, matching shot/check identities and unchanged expected intent. The after
input's `repair_review` attests exact `before_sha256`, `after_sha256`, named
`reviewer`, `watched_before_after: true`, `adjacent_shots_checked: true`. An old
fault counts resolved only with reviewed matching replacement evidence and this
adjacent-shot attestation. Missing checks remain unreviewed. New confirmed faults
are regressions; pending claims keep the review incomplete.
