"""Contrôles voix.

- raccords : un raccord tombe dans un mot si la voix sonne juste avant et juste après
  (mots tranchés les 04, 05, 06, 09 et 10/10). Les coupes de Lucien sont listées, jamais bloquantes.
- phrases : chaque phrase attendue (script tourné) figure dans la transcription du master
  (phrase unique supprimée le 10/10, phrases coupées sur Marvin v4 le 17/10).
- duree : le master a exactement le nombre d'images de la timeline de Lucien (coupes modifiées les 07 et 10/10)."""
import re, unicodedata

import numpy as np

from .commun import Resultat, audio_mono, sonde, tc

SR = 16000


def _energie(x, fen=0.02):
    n = int(SR * fen)
    k = len(x) // n
    return 20 * np.log10(np.sqrt((x[:k * n].reshape(k, n) ** 2).mean(axis=1)) + 1e-9), fen


def raccords(master, temps_auto=(), temps_lucien=(), seuil_db=-38, cote=0.04):
    x = audio_mono(master, SR)
    e, fen = _energie(x)

    def tranche(t):
        i = int(t / fen)
        k = max(1, int(cote / fen))
        av, ap = e[max(0, i - k):i], e[i:i + k]
        return len(av) and len(ap) and av.min() > seuil_db and ap.min() > seuil_db

    auto = [t for t in temps_auto if tranche(t)]
    lucien = [t for t in temps_lucien if tranche(t)]
    detail = f"{len(auto)} raccord(s) automatique(s) dans un mot sur {len(temps_auto)}" + ''.join(f" ; {tc(t)}" for t in auto[:8])
    if temps_lucien:
        detail += f". Coupes de Lucien : {len(lucien)} mot(s) tranché(s) à lister" + ''.join(f" ; {tc(t)}" for t in lucien[:8])
    return Resultat('mots coupés aux raccords', not auto, detail=detail,
                    defauts=[{'temps_s': t, 'source': 'auto'} for t in auto] + [{'temps_s': t, 'source': 'lucien'} for t in lucien])


def _mots(t):
    t = unicodedata.normalize('NFKD', t.lower()).encode('ascii', 'ignore').decode()
    return re.findall(r"[a-z0-9]+", t)


def transcrire(master, modele='small'):
    from faster_whisper import WhisperModel
    m = WhisperModel(modele, device='cpu', compute_type='int8')
    segs, _ = m.transcribe(master, language='fr', vad_filter=True)
    return ' '.join(s.text for s in segs)


def phrases(texte_master, attendues, couverture_min=0.8):
    """Une phrase est présente si 80 % de ses mots apparaissent dans l'ordre, dans une fenêtre proche."""
    mots = _mots(texte_master)
    absentes = []
    for p in attendues:
        cible = _mots(p)
        if not cible:
            continue
        meilleur = 0
        for debut in [i for i, w in enumerate(mots) if w == cible[0]] or [0]:
            j, trouves = debut, 0
            for w in cible:
                fenetre = mots[j:j + 4]
                if w in fenetre:
                    j += fenetre.index(w) + 1
                    trouves += 1
            meilleur = max(meilleur, trouves / len(cible))
        if meilleur < couverture_min:
            absentes.append(p)
    return Resultat('phrases du tournage', not absentes,
                    detail=f"{len(attendues) - len(absentes)}/{len(attendues)} phrase(s) présentes"
                    + ''.join(f" ; manque « {p[:60]} »" for p in absentes[:5]),
                    defauts=absentes)


def duree(master, images_attendues, tolerance=1):
    n = sonde(master)['images']
    return Resultat('durée de la timeline', abs(n - images_attendues) <= tolerance,
                    detail=f"{n} images, timeline de Lucien {images_attendues}")
