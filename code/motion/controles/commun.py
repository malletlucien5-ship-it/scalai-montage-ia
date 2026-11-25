"""Outils partagés des contrôles : lecture vidéo et audio par ffmpeg, résultat normalisé."""
import json, subprocess
from dataclasses import dataclass, field

import numpy as np


@dataclass
class Resultat:
    nom: str
    ok: bool
    bloquant: bool = True
    detail: str = ''
    defauts: list = field(default_factory=list)

    def ligne(self):
        etat = 'OK' if self.ok else ('ÉCHEC' if self.bloquant else 'ALERTE')
        return f"{etat} {self.nom} : {self.detail}"


def sonde(video):
    """Largeur, hauteur, cadence, nombre d'images, durée et présence d'audio."""
    out = subprocess.run(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', video],
                         capture_output=True, text=True, check=True).stdout
    d = json.loads(out)
    v = next(s for s in d['streams'] if s['codec_type'] == 'video')
    num, den = map(int, v.get('avg_frame_rate', '0/1').split('/'))
    fps = num / den if den else 0
    duree = float(d['format'].get('duration') or v.get('duration') or 0)
    n = int(v['nb_frames']) if v.get('nb_frames', '').isdigit() else round(duree * fps)
    return {'w': int(v['width']), 'h': int(v['height']), 'fps': fps, 'images': n, 'duree': duree,
            'audio': any(s['codec_type'] == 'audio' for s in d['streams'])}


def images_gris(video, w, h, fps=None, debut=None, duree=None):
    """Tableau (N, h, w) uint8 en niveaux de gris, réduit à w x h, éventuellement rééchantillonné."""
    vf = ([f'fps={fps}'] if fps else []) + [f'scale={w}:{h}', 'format=gray']
    cmd = ['ffmpeg', '-nostdin', '-v', 'error']
    if debut is not None:
        cmd += ['-ss', f'{debut:.3f}']
    cmd += ['-i', video]
    if duree is not None:
        cmd += ['-t', f'{duree:.3f}']
    cmd += ['-vf', ','.join(vf), '-an', '-f', 'rawvideo', '-']
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w)


def audio_mono(fichier, sr=16000):
    raw = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-i', fichier, '-vn', '-ac', '1', '-ar', str(sr),
                          '-f', 's16le', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768.0


def plages(indices, ecart=1):
    """Regroupe des indices triés en plages [début, fin] contiguës."""
    out = []
    for i in indices:
        if out and i - out[-1][1] <= ecart:
            out[-1][1] = i
        else:
            out.append([i, i])
    return out


def tc(secondes):
    m, s = divmod(max(0.0, secondes), 60)
    return f'{int(m)}:{s:05.2f}'
