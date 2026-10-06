"""Deterministic checks on observations supplied by a person or vision model.

These rules do not pretend to see pixels. Missing review coverage stays unreviewed.
"""
from pathlib import Path
import hashlib
import json
import math
import os
import re
from urllib.parse import quote

CATEGORIES = ("identity", "wardrobe", "props", "environment", "action", "scale", "artifacts")
DIRECTOR_CHECKS = ("narrative_clarity", "action_completion", "shot_join", "sound_intent")
TEMPORAL_CHECKS = ("action", "action_completion", "shot_join", "sound_intent")
SEVERITIES = ("minor", "major", "blocker")


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest() if hasattr(hashlib, "file_digest") else _digest(stream)


def _digest(stream):
    h = hashlib.sha256()
    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
        h.update(chunk)
    return h.hexdigest()


def evidence_ok(item, base):
    """Time and source identity are required; paths cannot escape the review folder."""
    if not isinstance(item, dict) or not isinstance(item.get("file"), str):
        return False
    second = item.get("time_seconds")
    if isinstance(second, bool) or not isinstance(second, (int, float)) or not math.isfinite(second) or second < 0:
        return False
    path = (base / item["file"]).resolve()
    if not path.is_relative_to(base.resolve()) or not path.is_file():
        return False
    return bool(item.get("sha256")) and digest(path) == item["sha256"]


def meaningful(value):
    """Empty placeholders cannot establish that a visual check was reviewed."""
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, bool):
        return True
    if isinstance(value, (int, float)):
        return math.isfinite(value)
    if isinstance(value, dict):
        return bool(value) and all(meaningful(v) for v in value.values())
    if isinstance(value, list):
        return bool(value) and all(meaningful(v) for v in value)
    return False


def object_field(data, key):
    value = data.get(key, {})
    if not isinstance(value, dict):
        raise ValueError(f"{key} must be an object")
    return value


def review(data, base="."):
    """Return a report; confirmed faults block creative approval, pending faults need review."""
    base = Path(base)
    if not isinstance(data, dict):
        raise ValueError("Review input must be an object")
    film = object_field(data, "film_review")
    technical = object_field(data, "technical_review")
    if data.get("schema_version") != 1:
        raise ValueError("Expected schema_version 1")
    shots = data.get("shots")
    if not isinstance(shots, list) or not shots:
        raise ValueError("Provide at least one shot")
    ids = [s.get("id") for s in shots if isinstance(s, dict)]
    if len(ids) != len(shots) or not all(isinstance(i, str) and i for i in ids) or len(set(ids)) != len(ids):
        raise ValueError("Every shot needs a unique non-empty id")
    scope = data.get("scope", "film")
    if scope not in ("still", "shot", "scene", "film"):
        raise ValueError("scope must be still, shot, scene, or film")
    profile = data.get("profile", "visual")
    if profile not in ("visual", "director"):
        raise ValueError("profile must be visual or director")
    checks = CATEGORIES + (DIRECTOR_CHECKS if profile == "director" else ())
    movie_hash = data.get("movie_sha256")
    valid_movie_hash = isinstance(movie_hash, str) and re.fullmatch(r"[0-9a-f]{64}", movie_hash) is not None
    findings, coverage = [], []
    for shot in shots:
        expected, observed = object_field(shot, "expected"), object_field(shot, "observed")
        adjudications = object_field(shot, "adjudications")
        if any(not isinstance(a, dict) for a in adjudications.values()):
            raise ValueError("Every adjudication must be an object")
        evidence = shot.get("evidence", [])
        if not isinstance(evidence, list):
            raise ValueError("evidence must be a list")
        valid_evidence = bool(evidence) and all(evidence_ok(e, base) for e in evidence)
        playback = object_field(shot, "playback")
        continuous = bool(scope != "still" and valid_movie_hash and playback.get("source_sha256") == movie_hash
                          and meaningful(playback.get("reviewer")) and playback.get("watched_full") is True)
        for category in checks:
            if scope == "still" and (category in TEMPORAL_CHECKS or category in DIRECTOR_CHECKS):
                coverage.append({"shot": shot["id"], "check": category, "status": "out of scope"})
                continue
            media_covered = continuous if category in TEMPORAL_CHECKS else True
            if category == "sound_intent":
                media_covered = continuous and playback.get("listened_full") is True
            covered = meaningful(expected.get(category)) and meaningful(observed.get(category)) and valid_evidence and media_covered
            coverage.append({"shot": shot["id"], "check": category, "status": "reviewed" if covered else "unreviewed"})
            if not covered or expected[category] == observed[category]:
                continue
            adjudication = adjudications.get(category, {})
            status = adjudication.get("status", "pending")
            if status not in ("confirmed", "rejected", "pending"):
                raise ValueError("Adjudication must be confirmed, rejected, or pending")
            # A model claim is a proposal, not a fact. Record who checked it and why.
            if status != "pending" and not (adjudication.get("reviewer") and adjudication.get("reason")):
                raise ValueError("Confirmed/rejected findings need reviewer and reason")
            severity = adjudication.get("severity", "major")
            if severity not in SEVERITIES:
                raise ValueError("Unknown severity")
            findings.append({"shot": shot["id"], "check": category, "severity": severity, "status": status,
                             "expected": expected[category], "observed": observed[category], "evidence": evidence,
                             "reviewer": adjudication.get("reviewer"), "reason": adjudication.get("reason"),
                             "repair": adjudication.get("repair", "Compare the cited frame with the approved scene specification; repair only if the mismatch is confirmed.")})
    experience = ("story", "pacing", "performance", "picture", "sound")
    # Full-film approval is an explicit reviewer attestation tied to an exact export.
    attested = bool(valid_movie_hash and film.get("movie_sha256") == movie_hash and film.get("reviewer")
                    and film.get("watched_full") is True and film.get("listened_full") is True)
    complete = attested and all(film.get(c) in ("pass", "revision") for c in experience)
    if scope == "film":
        coverage.append({"shot": "whole film", "check": "film_experience", "status": "reviewed" if complete else "unreviewed"})
    confirmed = any(f["status"] == "confirmed" for f in findings)
    pending = any(f["status"] == "pending" for f in findings)
    gaps = any(c["status"] == "unreviewed" for c in coverage)
    creative = "revision" if confirmed or (scope == "film" and complete and any(film[c] == "revision" for c in experience)) else "unreviewed" if pending or gaps else "pass"
    technical_pass = bool(valid_movie_hash and technical.get("movie_sha256") == movie_hash and technical.get("decode_complete") is True
                          and technical.get("export_matches_spec") is True and technical.get("reviewer"))
    return {"schema_version": 1, "title": data.get("title", "Untitled review"), "movie_sha256": movie_hash,
            "scope": scope, "profile": profile, "checks": list(checks) + (["film_experience"] if scope == "film" else []), "coverage": coverage, "findings": findings,
            "creative": creative, "technical": "pass" if technical_pass else "unreviewed",
            "release": "ready for owner decision" if scope == "film" and creative == "pass" and technical_pass else "blocked or incomplete review",
            "notes": ["Observation-based rules; no built-in vision model.", "Matching observations are reviewer evidence, not automatic pixel recognition.",
                      "Playback, full-film watch/listen and technical verdicts are explicit attestations, not inferred from thumbnails.", "A scoped pass does not approve a whole film. Attestations must identify the exact source hash."]}


def markdown(report, source_dir=None, output_dir=None):
    lines = [f"# {report['title']}", "", f"Scope: **{report.get('scope', 'film')}**", "", f"Creative: **{report['creative']}**", f"Technical: **{report['technical']}**",
             f"Release: **{report['release']}**", "", "## Findings", ""]
    if not report["findings"]:
        lines.append("No mismatches in the supplied covered observations. Consult coverage before calling the film clean.")
    for f in report["findings"]:
        lines += [f"### {f['shot']}: {f['check']} ({f['severity']}, {f['status']})", "",
                  f"Expected: `{json.dumps(f['expected'], ensure_ascii=False)}`", f"Observed: `{json.dumps(f['observed'], ensure_ascii=False)}`",
                  f"Reason: {f['reason'] or 'Awaiting adjudication'}", f"Repair: {f['repair']}", ""]
        for e in f["evidence"]:
            link = os.path.relpath(Path(source_dir) / e["file"], output_dir) if source_dir and output_dir else e["file"]
            lines.append(f"Evidence: [{e['file']}]({quote(link)}) at {e['time_seconds']:.3f}s, SHA-256 `{e['sha256']}`")
        lines.append("")
    lines += ["## Coverage", "", "| Shot | Check | Status |", "|---|---|---|"]
    lines += [f"| {c['shot']} | {c['check']} | {c['status']} |" for c in report["coverage"]]
    lines += ["", *report["notes"], ""]
    return "\n".join(lines)
