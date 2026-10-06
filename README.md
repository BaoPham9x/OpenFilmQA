# OpenFilmQA

**An open film-review skill, from director intent to the final watch.**

A good-looking frame can hide an unfinished action, a confusing cut or a poor
ending. OpenFilmQA connects source references, director intent, real media,
independent findings, repair decisions and human feedback in one review workflow.

Made by Bao Ngoc Pham at [Bao Studio / Little Bao House](https://rawdestiny.com/about/).
Code and documentation are [MIT licensed](LICENSE). Production footage and owner
labels stay private; this repository has no production case-study media.

## Use with Claude, Codex or your own reviewer

OpenFilmQA ships a portable **SKILL.md**, a local Python engine and open CLI
adapters. Claude and Codex can read the same skill and evidence contracts; your
agent supplies its permitted media tools. Reviewer identity, capability and
account access remain yours. The tool does not contain a model or API client.

Install the skill into your current project with the NPM-compatible GitHub package:

```sh
npx --yes --package=github:BaoPham9x/OpenFilmQA openfilmqa install
# Claude's project skill directory:
npx --yes --package=github:BaoPham9x/OpenFilmQA openfilmqa install --claude
```

Default: `.agents/skills/openfilmqa`; `--claude`: `.claude/skills/openfilmqa`.
Use `--dry-run` to preview or `--dir PATH` for another agent's skill directory.
Existing folders and symlink destinations are refused. Global installation is
explicit with `--global`. This is a GitHub-distributed NPM package; **npmjs
registry publication is deferred**. No install hooks, generation or model calls.
Requires Node.js 18+ for installation, Python 3.10+ for QA, FFmpeg only for packets.

After installation ask your agent to use OpenFilmQA to review the exact film.
Or run `python3 .agents/skills/openfilmqa/bin/qa.py --help` directly. Agents that
cannot watch/listen may still inspect frames, but cannot approve motion or sound.
See [the compatibility and adapter guide](docs/adapters.md) for verified limits.

## One workflow, nine steps

| Step | Purpose |
|---|---|
| 1. Source lock | Exact references, media versions, approved intent and review scope |
| 2. Director intent | Essential events, prop journey, staging, action, cut and sound plan |
| 3. Still review | Identity, wardrobe, props, environment, scale and artifacts |
| 4. Motion and joins | Continuous action, contact, completion and state across cuts |
| 5. Scene and film | Normal-speed watch/listen, clarity, rhythm and emotional landing |
| 6. Adjudication | Separate proposed errors, confirmed faults and false alarms |
| 7. Repair check | Recheck before/after, original intent and adjacent shots |
| 8. Delivery | Separate technical checks and the owner's release decision |
| 9. Reviewer evaluation | Measure misses, false alarms, preferred cuts and repair harm |

The [skill](SKILL.md) guides the agent through these steps. The
[review contract](docs/review-contract.md) specifies evidence and structured outputs.
These are our own synthesized methods, informed by
[director, ViMax, AIComicBuilder and production lessons](docs/methods.md).
We do not import a vendor's fixed shot length, dialogue requirement or model choice.

## Working commands

Clone the repository or use the bundled installed-skill command:

```sh
git clone https://github.com/BaoPham9x/OpenFilmQA.git
cd OpenFilmQA
python3 -m openfilmqa prepare /path/to/film.mp4 --at 0.5,12,28.5 \
  --out output/packet --reference /path/to/room.jpg --plan /path/to/director-plan.json
python3 -m openfilmqa verify /path/to/film.mp4 --width 1920 --height 1080 --fps 24 --audio required
python3 -m openfilmqa review /private/review.json --out output/review
python3 -m openfilmqa compare /private/before.json /private/after.json
python3 -m openfilmqa evaluate /private/cases/dataset.json /private/run/predictions.json
```

`prepare` extracts real frames and records exact movie/evidence hashes plus a
review brief. It preserves the movie's local source path and never sends media
anywhere. A packet starts unreviewed. Sampled frames are not full playback.

`review` validates reviewer observations, scoped coverage and adjudications.
The director profile adds narrative clarity, action completion, shot joins and
sound intent. Temporal checks require exact-source playback attestations; sound
requires listening. A scoped pass does not release a film. Full-film creative
and technical verdicts remain separate. Unknown applicable checks stay unreviewed; temporal/director checks are labelled
out of scope on still reviews. A still pass is always explicitly scoped.

`verify` fully decodes the exact local export and compares resolution, frame
rate and intended audio presence. A technical pass does not judge sound or story.

`compare` refuses to call a fault fixed when replacement evidence is missing,
the specification changed or adjacent shots were not checked. It reports new
confirmed faults separately as regressions. It does not see pixels itself.

`evaluate` measures independent human-labelled held-out cases. Related versions
cannot occur in both splits. Missing reviewer results stay in denominators.
[Calibration guide](docs/calibration.md). No benchmark scores are claimed here.

Exit codes: **0** completed review/measurement, **1** revision/regression,
**2** incomplete/prepared, **3** invalid input/tool failure. They are not permission
to publish. Reports expose scope, coverage, claims and limitations.

## Open judges

Prepare a Codex CLI job without calling a model:

```sh
python3 -m openfilmqa judge output/packet/packet.json \
  --adapter adapters/codex.json --scope still --out output/codex-job
```

Use `adapters/antigravity.json` for the documented `agy` CLI envelope, or create
an adapter for your own reviewer. Execution requires an explicit `--run`, existing
account access and your authorization for any cost. The included adapters declare
**images only**. They reject scene/film approval rather than pretending to play
video or hear sound. You can configure a capable transport with the same contract.

Timeouts, malformed outputs, unsupported capabilities and changed sources keep
jobs unreviewed. A judge proposes findings; another reviewer or the owner must
adjudicate them. A more confident score cannot erase a located major fault.

## Verification and limits

```sh
python3 -m unittest discover -s tests -v
npm test
npm pack --dry-run
```

v0.2 ships local packet preparation, full-decode delivery verification, scoped observation gates, open reviewer
transport, repair comparison, held-out evaluation and a portable skill installer.
Tests cover false passes, source changes, leakage, missing review coverage,
repair regressions, transport failure and safe installation. Transport is tested
locally without model calls. Codex flags were checked against installed CLI help;
Antigravity configuration follows official documentation. Neither live paid
reviewer performance nor Claude/Codex/Antigravity artistic accuracy is benchmarked.

Current limits: no built-in vision, playback or audio analysis; no automatic
human-label authentication; no semantic issue matching; no trained director model.
Human playback attestations are records, not proof of correct understanding.
Next work should measure real held-out cases and test a genuine motion/audio
adapter before claiming better film judgment, rather than adding more rules.
