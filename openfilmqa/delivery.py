"""Actual full decode and explicit export-spec checks, separate from creative review."""
from pathlib import Path
from fractions import Fraction
import json
import math
import shutil
import subprocess
from .review import digest


def verify(movie, width, height, fps, audio='required', timeout=180):
    movie = Path(movie).resolve()
    if not movie.is_file(): raise ValueError('Movie does not exist')
    if any(type(n) is not int or n <= 0 for n in (width, height)) or isinstance(fps, bool) or not math.isfinite(fps) or fps <= 0:
        raise ValueError('Positive width, height and FPS are required')
    if audio not in ('required', 'silent', 'optional'): raise ValueError('Unknown audio specification')
    if any(not shutil.which(binary) for binary in ('ffmpeg', 'ffprobe')): raise ValueError('FFmpeg and ffprobe are required')
    original_hash = digest(movie)
    probe = subprocess.run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(movie)],
                           capture_output=True,text=True,check=True,timeout=timeout)
    data = json.loads(probe.stdout)
    streams = data.get('streams', [])
    videos = [s for s in streams if s.get('codec_type') == 'video' and not s.get('disposition',{}).get('attached_pic')]
    if len(videos) != 1: raise ValueError('Specify a single actual video stream; cover art is not a film')
    v = videos[0]; actual_fps = float(Fraction(v.get('avg_frame_rate','0')))
    has_audio = any(s.get('codec_type') == 'audio' for s in streams)
    subprocess.run(['ffmpeg','-nostdin','-v','error','-xerror','-i',str(movie),'-map',f"0:{v['index']}",'-map','0:a?',
                    '-f','null','-'],capture_output=True,text=True,check=True,timeout=timeout)
    if digest(movie) != original_hash: raise ValueError('Movie changed while verification was running')
    issues = []
    if v.get('width') != width or v.get('height') != height: issues.append('Resolution does not match delivery specification')
    if not math.isclose(actual_fps, fps, rel_tol=0, abs_tol=.01): issues.append('Frame rate does not match delivery specification')
    if audio == 'required' and not has_audio: issues.append('Required audio stream is missing')
    if audio == 'silent' and has_audio: issues.append('Audio exists in an export specified as silent')
    return {'schema_version':1,'movie_sha256':original_hash,'technical':'revision' if issues else 'pass','creative':'unreviewed',
            'actual':{'width':v['width'],'height':v['height'],'fps':actual_fps,'duration_seconds':float(data['format']['duration']),'audio':has_audio},
            'specification':{'width':width,'height':height,'fps':fps,'audio':audio},'issues':issues,
            'technical_review':{'movie_sha256':original_hash,'reviewer':'FFmpeg local export verifier',
                                'decode_complete':True,'export_matches_spec':not issues},
            'notes':['Full decode checks data integrity and declared export settings, not story or sound quality.',
                     'An audio stream is not proof of correct foley, speech or mixing. Creative review and owner release remain separate.']}
