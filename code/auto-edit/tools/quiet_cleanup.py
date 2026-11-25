"""Retirer les creux acoustiques courts en conservant les marges de parole."""
import math
import subprocess
import numpy as np


def read_audio(path, sample_rate=16000):
    data = subprocess.check_output([
        'ffmpeg', '-v', 'error', '-nostdin', '-i', str(path), '-vn',
        '-ar', str(sample_rate), '-ac', '1', '-f', 's16le', '-'])
    return np.frombuffer(data, dtype='<i2').astype(np.float64) / 32768, sample_rate


def find_quiet_cuts(audio, sample_rate, words, *, fps=50, threshold_db=-55,
                    minimum=.13, maximum=1.0, pad=.02):
    """Détecter les creux quasi silencieux. Les centres de mots restent protégés.

    La fenêtre RMS mesure 10 ms. Chaque retrait garde 20 ms sur chaque bord.
    La quantification arrondit vers l'intérieur du silence. Les pauses longues
    restent sous le contrôle du VAD et du montage manuel.
    """
    block = round(sample_rate * .01)
    count = len(audio) // block
    if not count:
        return []
    windows = np.asarray(audio[:count * block]).reshape(count, block)
    rms = np.sqrt(np.mean(windows * windows, axis=1))
    quiet = rms <= 10 ** (threshold_db / 20)
    edges = np.flatnonzero(np.diff(np.r_[False, quiet, False])).reshape(-1, 2)
    centers = [(w['start'] + w['end']) / 2 for w in words]
    cuts = []
    for a, b in edges:
        start, end = a * block / sample_rate, b * block / sample_rate
        if not minimum - 1e-9 <= end - start <= maximum + 1e-9:
            continue
        lo = math.ceil((start + pad) * fps - 1e-9)
        hi = math.floor((end - pad) * fps + 1e-9)
        if hi <= lo or any(lo / fps - .025 <= t <= hi / fps + .025 for t in centers):
            continue
        cuts.append([lo, hi])
    return cuts


def subtract_cuts(kept, cuts):
    """Soustraire sans déplacer les bornes manuelles ni fusionner les répétitions."""
    output = []
    for start, end in kept:
        pieces = [[start, end]]
        for lo, hi in cuts:
            next_pieces = []
            for a, b in pieces:
                if hi <= a or lo >= b:
                    next_pieces.append([a, b])
                else:
                    if a < lo:
                        next_pieces.append([a, min(lo, b)])
                    if hi < b:
                        next_pieces.append([max(hi, a), b])
            pieces = next_pieces
        output.extend(pieces)
    return output


def clean_segments(segments, audio, sample_rate, words, fps):
    kept = [[round(a * fps), round(b * fps)] for a, b in segments]
    cuts = find_quiet_cuts(audio, sample_rate, words, fps=fps)
    cleaned = subtract_cuts(kept, cuts)
    return [(a / fps, b / fps) for a, b in cleaned]


def remap_words(words, kept, fps):
    output, cursor = [], 0
    for a,b in kept:
        for word in words:
            if a/fps <= (word['start']+word['end'])/2 < b/fps:
                output.append({**word,'start':cursor/fps+max(0,word['start']-a/fps),
                    'end':cursor/fps+min((b-a)/fps,word['end']-a/fps)})
        cursor += b-a
    return output


def refine_kept(kept, audio, sample_rate, words, *, fps=50):
    """Nettoyer aussi les raccords créés par Resolve jusqu'au contrôle sans retrait."""
    original = [list(pair) for pair in kept]
    cuts = find_quiet_cuts(audio,sample_rate,words,fps=fps)
    clean = subtract_cuts(original,cuts)
    for iteration in range(8):
        composed = np.concatenate([audio[round(a*sample_rate/fps):round(b*sample_rate/fps)]
            for a,b in clean]) if clean else np.array([])
        extra = find_quiet_cuts(composed,sample_rate,remap_words(words,clean,fps),fps=fps)
        if not extra:
            return clean, {'removed_frames':sum(b-a for a,b in original)-sum(b-a for a,b in clean),
                'remaining':0,'iterations':iteration+1,'cuts':cuts}
        cursor = 0
        for a,b in clean:
            for lo,hi in extra:
                x,y = max(cursor,lo),min(cursor+b-a,hi)
                if y > x:
                    cuts.append([a+x-cursor,a+y-cursor])
            cursor += b-a
        clean = subtract_cuts(original,cuts)
    raise RuntimeError('Le nettoyage acoustique ne converge pas.')


def audit_video(video, words, fps=50):
    audio,sample_rate = read_audio(video)
    cuts = find_quiet_cuts(audio,sample_rate,words,fps=fps)
    return {'eligible_quiet_spans':len(cuts),'cuts':cuts,'threshold_db':-55,
        'minimum_seconds':.13,'padding_seconds':.02,'fps':fps}


if __name__ == '__main__':
    import argparse
    import json
    from pathlib import Path
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--video',required=True)
    parser.add_argument('--words',required=True)
    parser.add_argument('--out',required=True)
    parser.add_argument('--fps',type=float,default=50)
    parser.add_argument('--no-open',action='store_true')
    args=parser.parse_args()
    report=audit_video(args.video,json.loads(Path(args.words).read_text()),args.fps)
    Path(args.out).write_text(json.dumps(report,indent=2))
    print(json.dumps(report))
    raise SystemExit(1 if report['eligible_quiet_spans'] else 0)
