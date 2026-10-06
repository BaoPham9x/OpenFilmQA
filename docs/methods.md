# Methods and source coverage

OpenFilmQA is our original review workflow and implementation. The following
projects inform its methods; none is bundled as a second production runtime.
Source advice is reference material, not authority over the filmmaker's brief.

| Source snapshot | Method adopted | Limitation avoided |
|---|---|---|
| [director](https://github.com/s1dashu/director/tree/0972f5489740949e0927dc492e3593f385a4f37c) | Current approved source roles, character/set/voice versioning, start/end states, action and camera phases, representative review | Successful jobs do not establish film quality; fixed shot quotas and vendor settings are not universal |
| [ViMax](https://github.com/HKUDS/ViMax/tree/fd4b72e7731be6e5f88486206d25ea59849b0285) | Relevant visual references, cross-angle room geography, camera dependencies, first/end-frame consistency | Relative best candidate is not necessarily acceptable; reject all when necessary |
| [AIComicBuilder](https://github.com/LingyiChen-AI/AIComicBuilder/tree/e01e7dd501131922fb5051ec36926271d394b4d3) | Narrative/event coverage, inter-shot continuity, version staleness and before/after comparison | Reviewer/parse failure cannot become PASS; description-based emotion scores do not prove performed emotion |
| OpenMontage Director/QA and private production audits | Viewer change, prop journeys, evidence freshness, scoped claims, playback/audio separation, claim-by-claim adjudication | Image-open traces do not prove perception; historical score agreement does not prove future artistic accuracy |

The same nine-stage contract holds source roles, directing intent, stills,
motion/joins, full scene/film experience, adjudication, repair, delivery and
reviewer calibration. It separates these stages rather than adding contradictory
rules to every job. Reference selection matches the shot's costume, angle,
room state, time and weather. Voice continuity concerns what is actually heard,
not just voice IDs. Camera motion and subject action have separate phases.

## Targeted source audit, 6 October 2026

Inventoried 67 tracked files in director, 188 in ViMax and 340 in AIComicBuilder.
Read QA-relevant content in 18 files (combined full file lengths 2,337 lines),
plus selected ViMax pipeline excerpts. This is not an audit of every source line,
execution path or finished demo. No vendor runtime or paid model call was run.

- director: `SKILL.md`, `references/community-directing-notes.md`,
  `references/video-generation-prompt-guide.md`, `references/voice-reference-guide.md`,
  and Cinematic Drama's `workflow.md`, `video-prompt-guide.md`,
  `reference-development-guide.md`.
- ViMax: `agents/best_image_selector.py`, `reference_image_selector.py`,
  `storyboard_artist.py`, `camera_image_generator.py`, `utils/image_selection.py`,
  and `pipelines/script2video_pipeline.py` excerpts.
- AIComicBuilder: `src/lib/pipeline/continuity-check.ts`, `video-quality-check.ts`,
  `src/lib/staleness.ts`, `src/components/editor/version-compare.tsx`,
  `src/lib/ai/prompts/shot-split.ts`,
  `src/app/api/projects/[id]/emotion-analysis/route.ts`.

Direct anchors: [director reference authority](https://github.com/s1dashu/director/blob/0972f5489740949e0927dc492e3593f385a4f37c/modes/cinematic-drama/reference-development-guide.md),
[ViMax selection](https://github.com/HKUDS/ViMax/blob/fd4b72e7731be6e5f88486206d25ea59849b0285/agents/best_image_selector.py),
[ComicBuilder quality fallback](https://github.com/LingyiChen-AI/AIComicBuilder/blob/e01e7dd501131922fb5051ec36926271d394b4d3/src/lib/pipeline/video-quality-check.ts).

Upstream licenses: director and ViMax MIT; AIComicBuilder Apache-2.0. This repo
contains newly written methods and code with source links, not copied source or
third-party film assets. Private production feedback is not published. The
removed v0.1 case study remains in historical Git revisions; its removal from
current files is not a claim that previously public media became private.
