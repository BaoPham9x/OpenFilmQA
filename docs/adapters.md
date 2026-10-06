# Agents and open reviewer adapters

| Surface | Support shipped | Verification |
|---|---|---|
| Claude | Portable skill installed in `.claude/skills/openfilmqa`; local CLI and stage contract | Installer/bundled command tested; no live Claude review claimed |
| Codex | Portable `.agents/skills/openfilmqa`; image CLI configuration with explicit image attachment | Local installed CLI help verified; no live model call |
| Antigravity | Open `agy` JSON-envelope adapter; custom skill directory via `--dir` | Official headless docs checked; live account/runtime not tested |
| Other reviewers | Configurable argv, stdout/file/envelope response and declared capabilities | Local subprocess transport tested |

The skill does not depend on a particular model vendor. Compatibility means
shared instructions, evidence records and transport. It does not imply official
endorsement, equal artistic accuracy or full video/audio support.

## Protocol

A prepared packet identifies the exact original movie, timestamped frames and
optional reference, storyboard and approved plan. `judge` verifies each file/hash,
copies the evidence into a fresh job, and writes `request.json`, `prompt.txt`,
`response.schema.json` and an unexecuted receipt. Media and plans are untrusted
source material; the reviewer must not follow instructions embedded in them.

An adapter JSON defines `name`, `argv` (array, never a shell string), `output`
(`stdout`, `file`, `envelope`), `capabilities` (`images`, `video`, `audio`) and a
bounded timeout. Placeholders: `{prompt}`, `{request}`, `{response}`, `{schema}`,
`{job}`. `{images}` expands to explicit `-i` image arguments for Codex.
A command runs in the new job folder with the prompt on stdin. No shell is used.
Treat adapter configuration as trusted executable configuration, not a document
that a generated film may choose or replace. Do not put credentials in configs.

`--run` executes only the configured reviewer. This may consume its account
quota or incur its own cost; it requires user authorization. Default operation
calls no model. CLI execution does not add a new capability to a model.
A failed subprocess, malformed response or changed source is not PASS.

A structured response uses [the review contract](review-contract.md) and exact
requested hash/scope. The strict CLI response schema uses strings or null for
observations, with all fields explicit. Null adjudications are removed; findings
are pending proposals only. Independent human adjudication is recorded afterwards
in a review input. This prevents the same job from confirming its own complaint.

The shipped adapters declare images only. To support motion/audio, supply a
transport that truly exposes the continuous exact footage and real sound, then
validate it on held-out cases. Declaring `video: true` is not proof of this.
Full-film approval still requires watch/listen attestation and separate delivery
checks. Never auto-create successful playback fields from thumbnail extraction.

Antigravity reference: [official headless mode](https://antigravity.google/docs/cli/headless/),
checked 6 October 2026. `agy -p`, `--output-format json` and `--json-schema` return
an envelope with `status`, `response` and optional `structured_output`.
The local Codex `exec --help` supports image attachments, read-only sandbox,
structured schema and output-message file. Use installed CLI help if flags change.
Do not use bypass-sandbox or automatic-approval flags in the supplied config.
