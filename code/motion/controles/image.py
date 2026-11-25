"""Contrôles image sur le master décodé en entier.

- noires : suites d'images noires (13 images à 20 min le 20/10, 16 panneaux vides le 15/10).
- flashs : plans d'une à quatre images isolées (84 plans d'une image le 09/10).
- saturation : part de pixels brûlés sur la plaque caméra (15 à 20 % le 02/10).
- visage : élément posé sur le visage, mesuré contre la plaque sobre (01, 02, 14, 15/10).
- visage_panneau : format à panneau gauche et zooms (podcast), visage cherché sur le master lui-même (21/11).
- cadrage : hauteur des yeux sur la plaque (tête trop basse le 17/10)."""
import numpy as np

from .commun import Resultat, images_gris, plages, sonde, tc


def noires(video, seuil=24, min_images=2, valides=()):
    s = sonde(video)
    f = images_gris(video, 64, 36)
    moy = f.reshape(len(f), -1).mean(axis=1)
    bas = np.nonzero(moy < seuil)[0]
    defauts = []
    for a, b in plages(bas.tolist()):
        if b - a + 1 >= min_images and not any(x <= a and b <= y for x, y in valides):
            defauts.append((a, b))
    fps = s['fps'] or 30
    return Resultat('images noires', not defauts,
                    detail=f"{len(defauts)} suite(s) sur {len(f)} images" +
                    ''.join(f" ; {tc(a / fps)} ({b - a + 1} im.)" for a, b in defauts[:6]),
                    defauts=[{'debut_s': a / fps, 'images': b - a + 1} for a, b in defauts])


def flashs(video, valides=()):
    s = sonde(video)
    f = images_gris(video, 96, 54).astype(np.int16)
    ev = []
    for i in range(2, len(f) - 6):
        a = f[i - 1]
        if np.abs(f[i] - a).mean() < 2:
            continue
        for k in range(1, 5):
            if np.abs(f[i + k] - a).mean() < 0.35 and np.abs(f[i - 2] - a).mean() < 0.35:
                if not any(x <= i <= y for x, y in valides):
                    ev.append((i, k))
                break
    fps = s['fps'] or 30
    return Resultat('images isolées', not ev,
                    detail=f"{len(ev)} plan(s) de 1 à 4 images" + ''.join(f" ; {tc(i / fps)}" for i, _ in ev[:8]),
                    defauts=[{'temps_s': i / fps, 'images': k} for i, k in ev])


def _dans(t, valides, fps=None):
    """t (secondes) tombe dans une plage validée par Lucien [debut_s, fin_s].
    fps : l'échantillon i du filtre fps de ffmpeg garde une image prise entre (i - 0,5)/fps et (i + 0,5)/fps.
    La plage couvre donc tout l'échantillon qui la chevauche (10:19.00 refusé pour Jev qui commence à 619,3 s, 25/10/2026)."""
    m = 0.5 / fps if fps else 0
    return any(x - m <= t <= y + m for x, y in valides)


def saturation(plaque, max_part=0.15, fps=1, valides=()):
    """valides : plages en secondes où l'image n'est pas la caméra (écran blanc voulu), 25/10/2026."""
    f = images_gris(plaque, 320, 180, fps=fps)
    part = (f >= 250).reshape(len(f), -1).mean(axis=1)
    mauvais = [i for i in np.nonzero(part > max_part)[0] if not _dans(i / fps, valides, fps)]
    return Resultat('pixels brûlés', len(mauvais) == 0,
                    detail=f"max {part.max() * 100:.1f} % (seuil {max_part * 100:.0f} %), {len(mauvais)} seconde(s) au-dessus"
                    + (f", {len(valides)} plage(s) validée(s) exclue(s)" if valides else "")
                    + ''.join(f" ; {tc(i / fps)}" for i in mauvais[:6]),
                    defauts=[{'temps_s': i / fps, 'part': float(part[i])} for i in mauvais])


def _visages(plaque, fps, w=480):
    import cv2
    s = sonde(plaque)
    h = round(w * s['h'] / s['w'] / 2) * 2
    f = images_gris(plaque, w, h, fps=fps)
    casc = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    boites = []
    for im in f:
        v = casc.detectMultiScale(im, 1.1, 5, minSize=(w // 12, w // 12))
        boites.append(max(v, key=lambda b: b[2] * b[3]) if len(v) else None)
    return f, boites, (w, h)


def visage(master, plaque, fps=2, part_max=0.2, min_suite=3, valides=()):
    """Pixels du visage changés entre motion et sobre : un élément couvre le visage.
    valides : plages en secondes des pleins écrans voulus (placements « plein »), exclues du contrôle, 25/10/2026."""
    f, boites, (w, h) = _visages(plaque, fps)
    m = images_gris(master, w, h, fps=fps)
    n = min(len(f), len(m))
    couverts = []
    for i in range(n):
        b = boites[i]
        if b is None:
            continue
        x, y, bw, bh = b
        diff = np.abs(m[i, y:y + bh, x:x + bw].astype(np.int16) - f[i, y:y + bh, x:x + bw].astype(np.int16))
        if (diff > 40).mean() > part_max and not _dans(i / fps, valides, fps):
            couverts.append(i)
    suites = [(a, b) for a, b in plages(couverts) if b - a + 1 >= min_suite]
    vus = sum(b is not None for b in boites[:n])
    return Resultat('visage couvert', not suites,
                    detail=f"visage vu sur {vus}/{n} échantillons, {len(suites)} passage(s) couvert(s)"
                    + ''.join(f" ; {tc(a / fps)}-{tc((b + 1) / fps)}" for a, b in suites[:6]),
                    defauts=[{'debut_s': a / fps, 'fin_s': (b + 1) / fps} for a, b in suites])


def _panneau_visible(g, luma=28, ecart=10, part=0.9):
    """Panneau gris #1c1c1e à l'écran : marge gauche (2 % de la largeur) uniforme, luma 28 ± 10.
    21/11/2026 : la borne du panneau s'appliquait aux 12 plans seuls, panneau absent, 12 faux refus."""
    bande = g[:, :max(2, g.shape[1] // 50)]
    return float((np.abs(bande.astype(int) - luma) <= ecart).mean()) >= part


def visage_panneau(master, plaque, panneau_px, fps=2, min_suite=3, valides=()):
    """Format à panneau gauche (montage-podcast) : Lucien est recadré à droite et zoomé, sa place sur la plaque ne compte plus.
    Échantillon couvert : visage vu sur la plaque, mais absent du master ou entamé par le panneau (bord gauche < panneau_px).
    21/11/2026 : « visage couvert » refusait 27 passages du podcast, visage entier à droite sur chaque image."""
    import cv2
    f, boites, (w, h) = _visages(plaque, fps)
    m = images_gris(master, w, h, fps=fps)
    lim = panneau_px * w / sonde(master)['w']
    casc = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    n = min(len(f), len(m))
    couverts = []
    for i in range(n):
        if boites[i] is None or _dans(i / fps, valides, fps):
            continue
        v = casc.detectMultiScale(m[i], 1.1, 5, minSize=(w // 12, w // 12))
        borne = lim if _panneau_visible(m[i]) else 0
        if not len(v) or max(v, key=lambda b: b[2] * b[3])[0] < borne:
            couverts.append(i)
    suites = [(a, b) for a, b in plages(couverts) if b - a + 1 >= min_suite]
    vus = sum(b is not None for b in boites[:n])
    return Resultat('visage couvert', not suites,
                    detail=f"panneau {panneau_px} px, visage vu sur {vus}/{n} échantillons de la plaque, {len(suites)} passage(s) couvert(s)"
                    + ''.join(f" ; {tc(a / fps)}-{tc((b + 1) / fps)}" for a, b in suites[:6]),
                    defauts=[{'debut_s': a / fps, 'fin_s': (b + 1) / fps} for a, b in suites])


def cadrage(plaque, yeux_cible=0.34, tolerance=0.06, fps=0.5):
    """Hauteur médiane des yeux : 40 % de la boîte du visage depuis son haut."""
    f, boites, (w, h) = _visages(plaque, fps)
    ys = [(b[1] + 0.4 * b[3]) / h for b in boites if b is not None]
    if not ys:
        return Resultat('cadrage', False, bloquant=False, detail='aucun visage détecté sur la plaque')
    med = float(np.median(ys))
    ok = abs(med - yeux_cible) <= tolerance
    return Resultat('cadrage', ok, detail=f"yeux à {med * 100:.0f} % de la hauteur (cible {yeux_cible * 100:.0f} ± {tolerance * 100:.0f} %)")
