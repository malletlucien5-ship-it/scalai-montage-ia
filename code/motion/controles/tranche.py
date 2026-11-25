"""Contrôles d'image sur une tranche de rendu, avant l'assemblage.

Incident du 09/11/2026 (cabinets) : le final rendu en 4 tranches est parti en quarantaine à 23 h 25 pour deux
fausses alertes (page à fond noir, images identiques d'un board). Lucien dormait : une nuit perdue.
Chaque tranche lance donc ce contrôle dès son rendu. Les alertes sortent en images du master, avec une planche
à montrer à Lucien avant l'assemblage. Le contrôle ne bloque rien : la porte reste `controles.livrer`.

  python3 -m controles.tranche "tranche 2 video.mp4" --debut-image 24000 --chantier chantier.json \
    --etat-local etat.md --etat-put "$PUT_ETAT" --planche "alertes tranche 2.jpg" --planche-put "$PUT_ALERTES"

Sortie : « <tranche> - alertes.json », lignes OK ou ALERTE dans l'état, planche des images en alerte.
Code 0 dans tous les cas où le contrôle a tourné."""
import argparse, json, os, subprocess, sys

from . import image
from .commun import sonde, tc


def _decale(plages, debut):
    return [(a - debut, b - debut) for a, b in plages]


def alertes(video, debut_image=0, valides=None):
    """Liste des alertes en images du master. valides : bloc `valides` de chantier.json (images du master)."""
    val = valides or {}
    fps = sonde(video)['fps'] or 30
    out = []
    r = image.noires(video, valides=_decale([tuple(x) for x in val.get('noires', [])], debut_image))
    for d in r.defauts:
        a = round(d['debut_s'] * fps)
        out.append({'controle': 'noires', 'debut': a + debut_image, 'fin': a + d['images'] - 1 + debut_image, 'local_s': a / fps})
    r = image.flashs(video, valides=_decale([tuple(x) for x in val.get('flashs', [])], debut_image))
    for d in r.defauts:
        a = round(d['temps_s'] * fps)
        out.append({'controle': 'flashs', 'debut': a + debut_image, 'fin': a + d['images'] - 1 + debut_image, 'local_s': a / fps})
    for x in out:
        x['tc_master'] = tc(x['debut'] / fps)
    return sorted(out, key=lambda x: x['debut'])


def planche(video, liste, sortie, max_vignettes=24):
    """Une vignette par alerte, avec son contrôle et son temps dans le master."""
    import cv2
    import numpy as np
    vignettes = []
    for x in liste[:max_vignettes]:
        raw = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-ss', f"{x['local_s']:.3f}", '-i', video, '-frames:v', '1',
                              '-vf', 'scale=640:360', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], capture_output=True).stdout
        if len(raw) != 640 * 360 * 3:
            continue
        im = np.frombuffer(raw, np.uint8).reshape(360, 640, 3).copy()
        bandeau = np.full((44, 640, 3), 255, np.uint8)
        cv2.putText(bandeau, f"{x['controle']} {x['tc_master']} images {x['debut']}-{x['fin']}", (8, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2, cv2.LINE_AA)
        vignettes.append(np.vstack([bandeau, im]))
    if not vignettes:
        return None
    while len(vignettes) % 2 and len(vignettes) > 1:
        vignettes.append(np.full_like(vignettes[0], 255))
    cols = 2 if len(vignettes) > 1 else 1
    rangs = [np.hstack(vignettes[i:i + cols]) for i in range(0, len(vignettes), cols)]
    cv2.imwrite(sortie, np.vstack(rangs), [cv2.IMWRITE_JPEG_QUALITY, 88])
    return sortie


def lignes_etat(nom, liste, images):
    if not liste:
        return [f"OK tranche {nom} : 0 alerte d'image sur {images} images"]
    out = []
    for x in liste:
        cle = 'noires' if x['controle'] == 'noires' else 'flashs'
        out.append(f"ALERTE tranche {nom} : {x['controle']} à {x['tc_master']} du master, images {x['debut']} à {x['fin']}. "
                   f"À montrer à Lucien avant l'assemblage. S'il valide : valides.{cle} += [[{x['debut']}, {x['fin']}]]")
    return out


def main():
    from .livrer import ecrire_etat, envoyer
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('video')
    p.add_argument('--debut-image', type=int, required=True, help="rang dans le master de la première image de la tranche")
    p.add_argument('--chantier')
    p.add_argument('--etat-local')
    p.add_argument('--etat-put')
    p.add_argument('--planche')
    p.add_argument('--planche-put')
    a = p.parse_args()
    val = {}
    if a.chantier:
        val = (json.load(open(a.chantier)).get('valides') or {})
    liste = alertes(a.video, a.debut_image, val)
    nom = os.path.splitext(os.path.basename(a.video))[0]
    rapport = os.path.splitext(a.video)[0] + ' - alertes.json'
    json.dump({'tranche': nom, 'debut_image': a.debut_image, 'alertes': liste}, open(rapport, 'w'), ensure_ascii=False, indent=1)
    lignes = lignes_etat(nom, liste, sonde(a.video)['images'])
    if liste and a.planche:
        fait = planche(a.video, liste, a.planche)
        if fait and a.planche_put:
            try:
                envoyer(fait, a.planche_put)
                lignes.append(f"Planche des alertes envoyée : {os.path.basename(fait)}")
            except subprocess.CalledProcessError:
                lignes.append("Planche des alertes non envoyée")
    ecrire_etat(a.etat_local, a.etat_put, lignes)
    print('\n'.join(lignes))
    print(f"ALERTES: {len(liste)}")
    sys.exit(0)


if __name__ == '__main__':
    main()
