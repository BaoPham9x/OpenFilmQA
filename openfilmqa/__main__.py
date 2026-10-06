"""No API key, account or network call is needed."""
import argparse
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
from .review import digest, markdown, review
from .evaluation import evaluate
from .repair import compare
from .adapters import judge
from .delivery import verify


def run(args):
    result = subprocess.run(args, capture_output=True, text=True, check=True)
    return result.stdout


def prepare(movie, out, timestamps, reference=None, storyboard=None, plan=None):
    movie, out = Path(movie).resolve(), Path(out)
    for binary in ("ffprobe", "ffmpeg"):
        if not shutil.which(binary):
            raise ValueError(f"Install {binary} to prepare movie packets; JSON review itself needs only Python")
    if not movie.is_file():
        raise ValueError("Movie file does not exist")
    probe = json.loads(run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(movie)]))
    duration = float(probe["format"]["duration"])
    if any(not math.isfinite(t) or t < 0 or t >= duration for t in timestamps):
        raise ValueError("Every timestamp must be inside the movie duration")
    if out.exists():
        raise ValueError("Choose a new output folder to avoid overwriting review evidence")
    out.mkdir(parents=True)
    frames = []
    for i, second in enumerate(timestamps):
        name = f"frame-{i+1:03d}.jpg"
        run(["ffmpeg", "-v", "error", "-ss", str(second), "-i", str(movie), "-frames:v", "1", "-vf", "scale=960:-2", "-update", "1", str(out / name)])
        frames.append({"file": name, "time_seconds": second, "sha256": digest(out / name)})
    assets = {}
    for key, source in (("reference", reference), ("storyboard", storyboard), ("plan", plan)):
        if source:
            source = Path(source)
            name = key + source.suffix
            shutil.copyfile(source, out / name)
            assets[key] = {"file": name, "sha256": digest(out / name)}
    packet = {"schema_version": 1, "movie_filename": movie.name, "movie_source": str(movie), "movie_sha256": digest(movie), "duration_seconds": duration,
              "streams": [{k: s.get(k) for k in ("codec_type", "codec_name", "width", "height", "avg_frame_rate", "sample_rate")} for s in probe["streams"]],
              "frames": frames, **assets, "review_status": "unreviewed"}
    (out / "packet.json").write_text(json.dumps(packet, indent=2) + "\n")
    (out / "REVIEW.md").write_text("# Review this exact movie\n\nMovie SHA-256: `" + packet["movie_sha256"] + "`\n\n"
        "Watch and listen to the entire movie at normal speed. Frames alone do not cover motion, story or sound.\n"
        "Compare each shot with the approved scene specification, characters, storyboard and reference.\n"
        "Check identity, wardrobe, props, environment, action, scale and visual artifacts.\n"
        "For each proposed fault, cite a frame/timecode, observed fact, viewer effect, severity, smallest repair and recheck.\n"
        "A second reviewer confirms or rejects each proposal from the actual evidence, including intentional holds and offscreen action.\n"
        "Judge the whole film separately: story clarity, pacing, performance, picture and sound. Rewatch repairs with adjacent shots.\n"
        "Report creative, technical and release decisions separately. Missing review stays unreviewed.\n")
    return packet


def main():
    parser = argparse.ArgumentParser(description="OpenFilmQA: evidence-first QA for AI films")
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("review", help="Check structured observations and adjudications")
    check.add_argument("input", type=Path)
    check.add_argument("--out", type=Path)
    packet = sub.add_parser("prepare", help="Extract real timestamped frames and a model-neutral review packet")
    packet.add_argument("movie", type=Path)
    packet.add_argument("--at", required=True, help="Comma-separated seconds; select meaningful story/shot moments")
    packet.add_argument("--out", required=True, type=Path)
    packet.add_argument("--reference", type=Path)
    packet.add_argument("--storyboard", type=Path)
    packet.add_argument("--plan", type=Path, help="Approved director plan; kept as source material")
    benchmark = sub.add_parser("evaluate", help="Measure reviewers against private owner-labelled held-out cases")
    benchmark.add_argument("dataset", type=Path)
    benchmark.add_argument("predictions", type=Path)
    repair = sub.add_parser("compare", help="Verify repaired observations, new faults and adjacent-shot review")
    repair.add_argument("before", type=Path)
    repair.add_argument("after", type=Path)
    external = sub.add_parser("judge", help="Prepare an open reviewer job; no model call without --run")
    external.add_argument("packet", type=Path)
    external.add_argument("--adapter", required=True, type=Path)
    external.add_argument("--out", required=True, type=Path)
    external.add_argument("--scope", choices=("still", "shot", "scene", "film"), default="still")
    external.add_argument("--run", action="store_true", help="Explicitly execute your configured reviewer; account costs may apply")
    delivery = sub.add_parser("verify", help="Fully decode a real export and compare explicit delivery settings")
    delivery.add_argument("movie", type=Path)
    delivery.add_argument("--width", type=int, required=True)
    delivery.add_argument("--height", type=int, required=True)
    delivery.add_argument("--fps", type=float, required=True)
    delivery.add_argument("--audio", choices=("required", "silent", "optional"), default="required")
    args = parser.parse_args()
    try:
        if args.command == "verify":
            result = verify(args.movie, args.width, args.height, args.fps, args.audio)
            print(json.dumps(result, indent=2)); return 0 if result['technical'] == 'pass' else 1
        if args.command == "evaluate":
            result = evaluate(json.loads(args.dataset.read_text()), json.loads(args.predictions.read_text()), args.dataset.resolve().parent)
            print(json.dumps(result, indent=2)); return 0 if result['status'] == 'measured' else 2
        if args.command == "compare":
            result = compare(json.loads(args.before.read_text()), json.loads(args.after.read_text()), args.before.resolve().parent, args.after.resolve().parent)
            print(json.dumps(result, indent=2)); return 0 if result['status'] == 'reviewed repair' else 1 if result['status'] == 'regression' else 2
        if args.command == "judge":
            result = judge(args.packet, args.adapter, args.out, args.scope, args.run)
            print(json.dumps(result, indent=2)); return 1 if result['status'] == 'revision' else 0 if result['status'] == 'pass' else 2
        if args.command == "prepare":
            result = prepare(args.movie, args.out, [float(t) for t in args.at.split(",")], args.reference, args.storyboard, args.plan)
            print(json.dumps(result, indent=2))
            return 0
        data = json.loads(args.input.read_text())
        result = review(data, args.input.resolve().parent)
        if args.out:
            args.out.mkdir(parents=True, exist_ok=True)
            (args.out / "report.json").write_text(json.dumps(result, indent=2) + "\n")
            (args.out / "report.md").write_text(markdown(result, args.input.resolve().parent, args.out.resolve()))
        print(json.dumps(result, indent=2))
        return 1 if any(f["status"] == "confirmed" for f in result["findings"]) else 2 if result["creative"] == "unreviewed" else 1 if result["creative"] == "revision" else 0
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError, ZeroDivisionError) as error:
        print(f"OpenFilmQA: {error}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
