#!/usr/bin/env python3
"""Associer des pistes audio avec ruptures explicites et mesures vérifiables."""
import argparse
import json
import subprocess
from pathlib import Path

import numpy as np
from scipy import signal


def pcm(path, sr=2000):
    p = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-vn', '-ac', '1',
                        '-ar', str(sr), '-f', 'f32le', '-'], capture_output=True, check=True)
    x = np.frombuffer(p.stdout, np.float32).copy()
    return signal.sosfilt(signal.butter(3, [100, min(850, sr*.44)],
                                      btype='bandpass', fs=sr, output='sos'), x).astype(np.float32)


def match(ref, target, sr=2000):
    if len(ref) < sr or len(target) < len(ref):
        return None
    ref = ref - ref.mean()
    energy = float(np.dot(ref, ref))
    if energy < 1e-9:
        return None
    cross = signal.fftconvolve(target, ref[::-1], mode='valid')
    csum = np.r_[0., np.cumsum(target.astype(np.float64)**2)]
    norms = np.sqrt(np.maximum((csum[len(ref):]-csum[:-len(ref)])*energy, 1e-20))
    scores = np.abs(cross)/norms
    best = int(np.argmax(scores))
    peak = float(scores[best])
    scores[max(0, best-int(.3*sr)):best+int(.3*sr)+1] = 0
    second = float(np.max(scores)) if len(scores) else 0
    return {'position': best/sr, 'correlation': peak, 'peak_ratio': peak/max(second, 1e-9)}


def regions(points, duration, step, window):
    """Aucun pont entre offsets distincts ou longues zones sans preuve."""
    groups = []
    for p in points:
        if not p['accepted']:
            continue
        if (not groups or p['cam_time']-groups[-1][-1]['cam_time'] > step*1.6
                or abs(p['offset']-groups[-1][-1]['offset']) > .08):
            groups.append([])
        groups[-1].append(p)
    out = []
    for g in groups:
        if len(g) < 2:
            continue
        ts = np.array([p['cam_time'] for p in g])
        offsets = np.array([p['offset'] for p in g])
        slope, intercept = np.polyfit(ts, offsets, 1)
        residual = float(np.max(np.abs(offsets-(intercept+slope*ts))))
        if abs(slope) > .001 or residual > .015:
            continue
        out.append({'cam_start': max(0., float(ts[0])-window/2),
                    'cam_end': min(duration, float(ts[-1])+window/2),
                    'offset': float(intercept), 'drift': float(slope),
                    'max_residual_ms': residual*1000, 'anchors': len(g)})
    return out


def analyze(cam_path, screen_path, step=20., window=6.):
    cam, scr = pcm(cam_path), pcm(screen_path)
    sr = 2000
    dur = len(cam)/sr
    points = []
    times = sorted(set([window/2] + list(np.arange(10., dur-window/2, step))
                       + [dur-window/2-.01]))
    for t in times:
        start = max(0., t-window/2)
        m = match(cam[round(start*sr):round((start+window)*sr)], scr, sr)
        if m is None:
            continue
        off = m['position']-start
        accepted = m['correlation'] >= .2 and m['peak_ratio'] >= 1.35
        p = {'cam_time': float(t), 'offset': off, 'accepted': accepted, **m}
        points.append(p)
        print(f'{Path(cam_path).stem} t={t:.1f} offset={off:+.4f} corr={m["correlation"]:.3f} ratio={m["peak_ratio"]:.2f} accepted={accepted}', flush=True)
    # Un refrain peut créer deux pics globaux. Deux voisins fiables permettent
    # de confirmer le pic qui respecte le même offset, sans franchir une coupe.
    for i in range(1, len(points)-1):
        a, p, b = points[i-1:i+2]
        if (not p['accepted'] and a['accepted'] and b['accepted']
                and p['correlation'] >= .5
                and max(abs(p['offset']-q['offset']) for q in (a,b)) < .02):
            p['accepted'] = True
            p['confirmation'] = 'offset cohérent avec deux voisins fiables'
    runs = regions(points, dur, step, window)
    # Fenêtres de validation intercalées, jamais utilisées pour le fit.
    validation = []
    valid_runs = []
    for run in runs:
        passed = True
        for t in np.arange(run['cam_start']+window, run['cam_end']-window, max(15., step)):
            start = t-window/2
            expected = start+run['offset']+run['drift']*start
            s0 = max(0., expected-.15)
            m = match(cam[round(start*sr):round((start+window)*sr)],
                      scr[round(s0*sr):round((expected+window+.15)*sr)], sr)
            delta = (s0+m['position']-expected) if m else None
            ok = bool(m is not None and m['correlation'] >= .2 and abs(delta) <= .015)
            validation.append({'cam_time': float(t), 'delta_ms': delta*1000 if delta is not None else None,
                               'correlation': m['correlation'] if m else 0, 'passed': ok})
            passed = passed and ok
        if passed:
            valid_runs.append(run)
    return {'camera_audio': str(cam_path), 'screen_audio': str(screen_path),
            'cam_duration': dur, 'screen_duration': len(scr)/sr, 'sample_rate': sr,
            'points': points, 'regions': valid_runs, 'validation': validation,
            'covered_seconds': sum(r['cam_end']-r['cam_start'] for r in valid_runs)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cam', required=True)
    p.add_argument('--screen', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--step', type=float, default=20.)
    a = p.parse_args()
    result = analyze(a.cam, a.screen, a.step)
    Path(a.out).write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(json.dumps({k: result[k] for k in ('cam_duration', 'screen_duration', 'regions', 'covered_seconds')}, indent=2))


if __name__ == '__main__':
    main()
