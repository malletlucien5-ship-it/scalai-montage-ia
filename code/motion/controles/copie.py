"""Copie d'une référence : écart image par image toutes les 0,2 s, planche des pires instants.

Cause : trois versions livrées sur des scores, sans regard sur la superposition (18-19/10) ;
logos placés au jugé (30/09) ; éléments ajoutés hors référence (01, 14/10).
La planche (référence à gauche, copie à droite, différence en dessous) accompagne chaque livraison."""
import json, os, subprocess

import numpy as np

from .commun import Resultat, images_gris, plages, tc


def ecarts(master, reference, pas=0.2, w=135, h=240):
    a = images_gris(master, w, h, fps=1 / pas)
    b = images_gris(reference, w, h, fps=1 / pas)
    n = min(len(a), len(b))
    return np.abs(a[:n].astype(np.int16) - b[:n].astype(np.int16)).reshape(n, -1).mean(axis=1) / 255.0, n


def superposition(master, reference, seuil=0.08, pas=0.2, min_suite=3, planche=None, valides=()):
    e, n = ecarts(master, reference, pas)
    hauts = [i for i in np.nonzero(e > seuil)[0].tolist() if not any(x <= i * pas <= y for x, y in valides)]
    suites = [(a, b) for a, b in plages(hauts) if b - a + 1 >= min_suite]
    if planche:
        pires = sorted(np.argsort(-e)[:12].tolist())
        fabriquer_planche(master, reference, [i * pas for i in pires], planche)
    return Resultat('superposition avec la référence', not suites,
                    detail=f"écart moyen {e.mean() * 100:.1f} %, max {e.max() * 100:.1f} % (seuil {seuil * 100:.0f} %), "
                    f"{len(suites)} passage(s) au-dessus" + ''.join(f" ; {tc(a * pas)}-{tc((b + 1) * pas)}" for a, b in suites[:6]),
                    defauts=[{'debut_s': a * pas, 'fin_s': (b + 1) * pas} for a, b in suites])


def fabriquer_planche(master, reference, temps, sortie, w=270, h=480):
    """Une colonne par instant : référence en haut, copie au milieu, différence en bas."""
    cols = []
    for t in temps:
        im = []
        for v in (reference, master):
            raw = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-ss', f'{t:.2f}', '-i', v, '-frames:v', '1',
                                  '-vf', f'scale={w}:{h}', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
            im.append(np.frombuffer(raw, np.uint8).reshape(h, w, 3) if len(raw) == w * h * 3 else np.zeros((h, w, 3), np.uint8))
        d = np.clip(np.abs(im[0].astype(np.int16) - im[1].astype(np.int16)) * 3, 0, 255).astype(np.uint8)
        cols.append(np.vstack(im + [d]))
    grille = np.hstack(cols) if cols else np.zeros((h * 3, w, 3), np.uint8)
    subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                    '-s', f'{grille.shape[1]}x{grille.shape[0]}', '-i', '-', '-q:v', '3', sortie],
                   input=grille.tobytes(), check=True)


# 26/10/2026 : motion copié de Yas posé sur la timeline de Lucien, livré sans comparaison.
# Les deux timelines diffèrent : on compare chaque placement à sa plage de la référence.

def charger_correspondance(corr):
    """Liste [{id, mode, ref: [a, b] s, copie: [a, b] s, boite_ref: [x, y, w, h] px de la référence}] ou chemin JSON."""
    return json.load(open(corr)) if isinstance(corr, str) else list(corr)


def _image(video, t, w, h, crop=None):
    vf = (f'crop={crop},' if crop else '') + f'scale={w}:{h}'
    raw = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-ss', f'{t:.3f}', '-i', video, '-frames:v', '1',
                          '-vf', vf, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(h, w, 3) if len(raw) == w * h * 3 else np.zeros((h, w, 3), np.uint8)


def par_placement(master, reference, corr, seuil=0.14, points=(0.3, 0.6, 0.9), dossier=None, valides=()):
    """Plein écran : écart couleur 160x90 à trois instants, médiane comparée au seuil.
    Chaque placement reçoit sa planche (référence à gauche, copie à droite) dans `dossier`, calques compris."""
    mauvais, notes = [], {}
    if dossier:
        os.makedirs(dossier, exist_ok=True)
    for p in charger_correspondance(corr):
        e, paires = [], []
        for q in points:
            tr = p['ref'][0] + (p['ref'][1] - p['ref'][0]) * q
            tc_ = p['copie'][0] + (p['copie'][1] - p['copie'][0]) * q
            a, b = _image(reference, tr, 160, 90), _image(master, tc_, 160, 90)
            e.append(float(np.abs(a.astype(np.int16) - b.astype(np.int16)).mean() / 255))
            if dossier:
                paires.append(np.hstack([_image(reference, tr, 480, 270), np.full((270, 8, 3), 255, np.uint8),
                                         _image(master, tc_, 480, 270)]))
        notes[p['id']] = round(float(np.median(e)), 3)
        if dossier and paires:
            g = np.vstack(paires)
            subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                            '-s', f'{g.shape[1]}x{g.shape[0]}', '-i', '-', '-q:v', '3', os.path.join(dossier, f"{p['id']}.jpg")],
                           input=g.tobytes(), check=True)
        if p.get('mode') == 'plein' and notes[p['id']] > seuil and p['id'] not in valides:
            mauvais.append(p['id'])
    # Écart chiffré indicatif : un site ou un b-roll personnalisé diffère légitimement. La revue de chaque planche
    # (copie.revue dans chantier.json) bloque la livraison finale.
    return Resultat('copie par placement', not mauvais, bloquant=False,
                    detail=f"{len(notes)} placements, {len(mauvais)} plein(s) écran(s) au-dessus de {seuil * 100:.0f} %"
                    + ''.join(f" ; {i} {notes[i] * 100:.0f} %" for i in mauvais[:8]),
                    defauts=[{'id': i, 'ecart': notes[i]} for i in mauvais])


def halo_sombre(master, plaque, corr, seuil=0.01, ecart=45, points=(0.5, 0.85), valides=()):
    """Calques : part de l'image que le motion assombrit de plus de `ecart` niveaux par rapport au sobre (image entière 320x180).
    Le texte de la référence s'éclaire (lueur claire) ; un halo noir sous le texte est le défaut du 26/10/2026.
    Un panneau sombre voulu de la référence s'exempte par son id dans valides.halo."""
    mauvais, notes = [], {}
    for p in charger_correspondance(corr):
        if p.get('mode') != 'calque' or p['id'] in valides:
            continue
        parts = []
        for q in points:
            t = p['copie'][0] + (p['copie'][1] - p['copie'][0]) * q
            m = _image(master, t, 320, 180).astype(np.int16).mean(axis=2)
            s = _image(plaque, t, 320, 180).astype(np.int16).mean(axis=2)
            parts.append(float(((s - m) > ecart).mean()))
        notes[p['id']] = round(max(parts), 3)
        if notes[p['id']] > seuil:
            mauvais.append(p['id'])
    return Resultat('halo sombre sous les calques', not mauvais,
                    detail=f"{len(notes)} calques, {len(mauvais)} assombri(s) (seuil {seuil * 100:.0f} %)"
                    + ''.join(f" ; {i} {notes[i] * 100:.1f} %" for i in mauvais[:10]),
                    defauts=[{'id': i, 'part': notes[i]} for i in mauvais])
