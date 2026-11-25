#!/usr/bin/env python3
"""Calage mesuré caméra DJI ↔ enregistrements OBS, par GCC-PHAT sur l'audio. --no-open : n'ouvre rien.

Règle du 08/11/2026 : toute affirmation sur la couverture (quel rush va avec quel OBS,
ce qui manque, ce qui dépasse) vient de ce fichier, jamais des noms ni des dates des fichiers.
L'horloge DJI est fausse et les dates de la carte viennent de cette horloge.
Incident : « 7 min 46 de caméra sans OBS » annoncé à Lucien d'après les noms DJI, faux ;
la prise d'essai (rush 1) n'était calée sur aucune partie de l'OBS principal.

Usage :
  calage_sources.py --obs OBS1.mp4 [OBS2.mp4 ...] --cam DJI_1.MP4 [DJI_2.MP4 ...] --out DIR/calage.json

Calcul léger : décodage audio 8 kHz mono et corrélation numpy, aucun encodage vidéo.
Sortie : pour chaque rush, l'OBS qui le porte, son décalage, la confiance, la part des fenêtres
cohérentes, et la couverture de chaque OBS par la caméra. Code 1 si un rush n'est calé sur aucun OBS.
"""
import argparse, json, os, subprocess, sys, time
import numpy as np

SR = 8000
FEN = 60.0          # fenêtre de mesure, s
CONF_MIN = 50.0     # pic / médiane : en dessous, la fenêtre ne se cale pas
TOL = 0.10          # écart toléré entre fenêtres d'un même rush, s
PART_MIN = 0.6      # part des fenêtres cohérentes pour déclarer un rush calé


def pcm(path):
    r = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-vn', '-ac', '1', '-ar', str(SR),
                        '-f', 'f32le', '-'], capture_output=True, check=True)
    return np.frombuffer(r.stdout, dtype=np.float32)


def gcc(ref, seg):
    """Position de seg dans ref (s) et confiance. Taille FFT ≥ len(ref)+len(seg) : retard repassé en positif."""
    n = 1 << int(np.ceil(np.log2(len(ref) + len(seg))))
    R = np.fft.rfft(ref, n) * np.conj(np.fft.rfft(seg, n))
    R /= np.abs(R) + 1e-12
    c = np.abs(np.fft.irfft(R, n))
    k = int(np.argmax(c))
    conf = float(c[k] / (np.median(c) + 1e-12))
    if k > n - len(seg):          # retard négatif : seg commence avant ref
        k -= n
    return k / SR, conf


def caler(obs_pcm, cam):
    d = len(cam) / SR
    mesures = []
    for t0 in np.arange(0, max(d - FEN / 2, 1), FEN):
        seg = cam[int(t0 * SR):int(min(t0 + FEN, d) * SR)]
        if len(seg) < SR * 10:
            continue
        best = None
        for nom, ref in obs_pcm.items():
            pos, conf = gcc(ref, seg)
            if best is None or conf > best[2]:
                best = (nom, pos - t0, conf)
        mesures.append({'t_cam': round(float(t0), 1), 'obs': best[0], 'offset': round(best[1], 3), 'conf': round(best[2], 1)})
    return mesures, d


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--obs', nargs='+', required=True)
    ap.add_argument('--cam', nargs='+', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--no-open', action='store_true', help='sans effet : rien ne s’ouvre')
    a = ap.parse_args()
    obs_pcm = {os.path.basename(o): pcm(o) for o in a.obs}
    obs_dur = {k: len(v) / SR for k, v in obs_pcm.items()}
    rushs, defaut = [], 0
    for c in a.cam:
        mesures, d = caler(obs_pcm, pcm(c))
        bonnes = [m for m in mesures if m['conf'] >= CONF_MIN]
        rush = {'rush': os.path.basename(c), 'duree': round(d, 3), 'fenetres': len(mesures), 'mesures': mesures}
        if bonnes:
            obs_maj = max({m['obs'] for m in bonnes}, key=lambda o: sum(m['obs'] == o for m in bonnes))
            offs = np.array([m['offset'] for m in bonnes if m['obs'] == obs_maj])
            med = float(np.median(offs))
            coh = int(np.sum(np.abs(offs - med) <= TOL))
            part = coh / max(len(mesures), 1)
            rush.update({'obs': obs_maj, 'offset': round(med, 3), 'part_coherente': round(part, 2),
                         'conf_mediane': round(float(np.median([m['conf'] for m in bonnes])), 1),
                         'debut_obs': round(med, 3), 'fin_obs': round(med + d, 3)})
            rush['statut'] = 'cale' if part >= PART_MIN else 'douteux'
        else:
            rush['statut'] = 'non_cale'
        if rush['statut'] != 'cale':
            defaut = 1
        rushs.append(rush)
    couverture = {}
    for o, dur in obs_dur.items():
        spans = sorted((r['debut_obs'], r['fin_obs']) for r in rushs if r.get('obs') == o and r['statut'] == 'cale')
        trous, t = [], 0.0
        for s, e in spans:
            if s - t > 1.0:
                trous.append([round(t, 2), round(s, 2)])
            t = max(t, e)
        if dur - t > 1.0:
            trous.append([round(t, 2), round(dur, 2)])
        depasse = [r['rush'] for r in rushs if r.get('obs') == o and r['statut'] == 'cale'
                   and (r['debut_obs'] < -1.0 or r['fin_obs'] > dur + 1.0)]
        couverture[o] = {'duree': round(dur, 3), 'rushs': [r['rush'] for r in rushs if r.get('obs') == o and r['statut'] == 'cale'],
                         'sans_camera': trous, 'camera_hors_obs': depasse}
    doc = {'date': time.strftime('%Y-%m-%dT%H:%M:%S'), 'methode': 'GCC-PHAT 8 kHz, fenêtres 60 s',
           'rushs': [{k: v for k, v in r.items() if k != 'mesures'} for r in rushs],
           'couverture': couverture, 'detail': {r['rush']: r['mesures'] for r in rushs}}
    with open(a.out, 'w') as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
    for r in doc['rushs']:
        if r['statut'] == 'non_cale':
            print(f"{r['rush']} ({r['duree']:.0f} s) : NON CALÉ sur aucun OBS")
        else:
            print(f"{r['rush']} ({r['duree']:.0f} s) : {r['statut']} sur {r['obs']} à {r['offset']:+.3f} s, "
                  f"{r['part_coherente']*100:.0f} % des fenêtres, confiance {r['conf_mediane']:.0f}")
    for o, c in couverture.items():
        print(f"{o} ({c['duree']:.0f} s) : rushs {c['rushs'] or 'aucun'} ; sans caméra {c['sans_camera'] or 'aucun'} ; "
              f"caméra hors OBS {c['camera_hors_obs'] or 'aucune'}")
    print(f"calage écrit : {a.out}")
    return defaut


if __name__ == '__main__':
    sys.exit(main())
