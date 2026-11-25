"""Look A : base recalculée par rush DJI, look A inchangé.

Usage :
  etalonnage.py bases --out DIR --cams DJI_A.MP4 DJI_B.MP4 [--force]
      → DIR/etalonnage.json {look_a, bases{chemin: base}, mesures}
  etalonnage.py grades --out DIR
      → affiche la chaîne caméra complète par rush (base + look A)

Le rendu (source_media, pipeline assemble) applique base + look A à la caméra seule,
après mise à l'échelle. La capture d'écran garde ses couleurs.
Méthode : ~/.claude/skills/etalonnage-look-a/SKILL.md
"""
import argparse, json, subprocess, sys, tempfile
from pathlib import Path

import numpy as np
from PIL import Image

LOOK_A = ('colorchannelmixer=rr=1.0:gg=0.972:bb=0.99,'
          'eq=brightness=0.03:contrast=1.06:saturation=1.12,unsharp=5:5:0.5')
CIBLE = np.array([226, 223, 216])          # mur visé avant look A (point de départ)
CIBLE_FINALE = np.array([220, 218, 212])   # mur après look A, pièce beige (défaut)
CIBLE_MUR_BLANC = np.array([240, 238, 233])  # pièce à mur blanc, choisie par Lucien le 11/10/2026
ECART_MAX = 6                              # tolérance par canal après look A
MUR = (slice(80, 260), slice(780, 1000))   # mur vide entre la tête et le bras du micro (image 1280x720)
SAT_MAX = 15                               # % de pixels saturés tolérés


def base_filter(g):
    return (f'colorchannelmixer=rr={g[0]:.3f}:gg={g[1]:.3f}:bb={g[2]:.3f},'
            'eq=gamma=1.03:contrast=1.05:saturation=1.05')


def frame(src, t, vf, tmp):
    v = 'scale=1280:720' + (',' + vf if vf else '')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(t), '-i', str(src), '-frames:v', '1',
                    '-vf', v, str(tmp)], check=True)
    return np.asarray(Image.open(tmp).convert('RGB')).astype(float)


def mesure(a):
    return a[MUR].reshape(-1, 3).mean(0), (a.max(-1) >= 250).mean() * 100


def boucle(src, tmp, cible=None):
    cible = CIBLE_FINALE if cible is None else np.array(cible, float)
    d = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0',
                              str(src)], capture_output=True, text=True).stdout)
    ts = [d * k for k in (0.1, 0.3, 0.5, 0.7, 0.9)]
    brut = np.mean([mesure(frame(src, t, '', tmp))[0] for t in ts], 0)
    g = CIBLE / brut
    for it in range(20):
        res = [mesure(frame(src, t, f'{base_filter(g)},{LOOK_A}', tmp)) for t in ts]
        mur = np.mean([r[0] for r in res], 0)
        sat = max(r[1] for r in res)
        ok = True
        # Le mur doit tomber sur la cible après look A : un mur à 240 passait le contrôle (AI Advantage, 11/10/2026).
        if np.abs(mur - cible).max() > ECART_MAX:
            g *= cible / mur; ok = False
        if mur[1] > mur[0]:
            g[1] *= 0.99; ok = False
        if mur[2] > mur[1]:
            g[2] *= 0.99; ok = False
        if sat > SAT_MAX:
            g *= 0.97; ok = False
        if ok:
            break
    return {'base': base_filter(g), 'mur_brut': brut.round(1).tolist(), 'mur': mur.round(1).tolist(),
            'sat_max': round(sat, 1), 'iterations': it + 1, 'controle_ok': ok}


def bases(out, cams, force=False, cible=None):
    p = Path(out) / 'etalonnage.json'
    doc = json.loads(p.read_text()) if p.exists() else {}
    # Un look déjà choisi pour la vidéo (ex. 'null' pour Studio A seul) n'est jamais écrasé.
    doc.setdefault('look_a', LOOK_A)
    doc.setdefault('bases', {}); doc.setdefault('mesures', {})
    if cible is not None:
        doc['cible_mur'] = list(cible)
    cible = doc.get('cible_mur')
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / 'f.png'
        for c in cams:
            c = str(Path(c).resolve())
            if c in doc['bases'] and not force:
                continue
            m = boucle(c, tmp, cible)
            doc['bases'][c] = m.pop('base')
            doc['mesures'][c] = m
            print(Path(c).name, doc['bases'][c], m, flush=True)
    p.write_text(json.dumps(doc, ensure_ascii=False, indent=1))
    return doc


def grades(out):
    """{chemin rush: chaîne caméra complète} ou {} sans etalonnage.json."""
    p = Path(out) / 'etalonnage.json'
    if not p.exists():
        return {}
    doc = json.loads(p.read_text())
    look = doc.get('look_a', LOOK_A)
    if look in ('', 'null', None):
        return dict(doc['bases'])
    return {k: f"{v},{look}" for k, v in doc['bases'].items()}


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    b = sub.add_parser('bases'); b.add_argument('--out', required=True)
    b.add_argument('--cams', nargs='+', required=True); b.add_argument('--force', action='store_true')
    b.add_argument('--cible', help='mur visé après look A, ex. 240,238,233 pour une pièce blanche')
    g = sub.add_parser('grades'); g.add_argument('--out', required=True)
    a = ap.parse_args()
    if a.cmd == 'bases':
        bases(a.out, a.cams, a.force, [float(x) for x in a.cible.split(',')] if a.cible else None)
    else:
        print(json.dumps(grades(a.out), indent=1))
