#!/usr/bin/env python3
"""Étape avant rendu : une image fixe de chaque arrêt, le contrôle de cadrage et une planche pour relecture.

Cause : viral X v4, 01/11/2026. Le premier regard sur les arrêts est venu après 1 h de rendu.
Lucien a demandé pourquoi les textes coupés n'ont pas été vus au premier rendu.

  python3 -m controles.arrets avant-rendu PLAN.json --remotion DIR --sortie DIR \
      [--board BOARD.json --encres ENCRES.json] [--composition PanneauV4]
  python3 -m controles.arrets planche PLAN.json --sortie DIR [--board BOARD.json --encres ENCRES.json]

avant-rendu rend les images fixes sur la machine du chantier, jamais sur le Mac. planche repart d'images déjà présentes.
Sortie : DIR/F.png, DIR/planche-arrets.jpg, DIR/rapport-cadrage.md, DIR/arrets.json (empreinte du plan, nombre de fautes).
livrer.py refuse un plan à arrêts sans arrets.json à jour. Code 1 si une image manque ou si le contrôle trouve une faute."""
import argparse, hashlib, json, os, subprocess, sys, unicodedata

import cv2
import numpy as np

from . import cadrage
from .commun import Resultat

ICI = os.path.dirname(os.path.abspath(__file__))
TUILE_L, TUILE_H, BANDE, COLONNES = 640, 540, 34, 4


def empreinte(chemin):
    with open(chemin, 'rb') as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def rendre(chemin_plan, remotion, sortie, composition='PanneauV4', images=None):
    """Rend les images manquantes. Une image déjà là reste : la reprise ne refait rien."""
    with open(chemin_plan) as fh:
        plan = json.load(fh)
    os.makedirs(sortie, exist_ok=True)
    manque = [f for f in (images or cadrage.images_requises(plan)) if cadrage.Images(sortie).image(f) is None]
    if manque:
        subprocess.run(['node', os.path.join(ICI, 'images_arrets.mjs'), os.path.abspath(chemin_plan), os.path.abspath(remotion),
                        os.path.abspath(sortie), composition, ','.join(map(str, manque))], check=True)
    return manque


def tuiles(plan):
    """(image, légende) de chaque arrêt, plans board et sites."""
    fps = plan.get('fps', 50)
    return [(cadrage.arret_image(a), f"{(a['f0'] / fps):.1f} s  {p.get('nom', p['etat'])[:30]}  arret {k + 1}  z {a['zoom']}", i, k)
            for i, p in enumerate(plan['plans']) for k, a in enumerate(p.get('arrets', []))]


def _ascii(t):
    return unicodedata.normalize('NFKD', t).encode('ascii', 'ignore').decode()


def planche(plan, dossier, sortie, fautes=()):
    """Grille de tous les arrêts. Bandeau rouge sur un arrêt en faute, bandeau jaune sur une image absente."""
    rouges = {(x['plan'], x['n']) for x in fautes if x['type'] == 'arrêt'}
    src = cadrage.Images(dossier)
    items = tuiles(plan)
    rangs = (len(items) + COLONNES - 1) // COLONNES
    pl = np.full((rangs * (TUILE_H + BANDE + 8) + 8, COLONNES * (TUILE_L + 8) + 8, 3), 17, np.uint8)
    absentes = 0
    for n, (f, legende, i, k) in enumerate(items):
        x, y = 8 + (n % COLONNES) * (TUILE_L + 8), 8 + (n // COLONNES) * (TUILE_H + BANDE + 8)
        im = src.image(f)
        if im is None:
            absentes += 1
            couleur, legende = (0, 200, 255), f'ABSENTE image {f}  {legende}'
        else:
            pl[y + BANDE:y + BANDE + TUILE_H, x:x + TUILE_L] = cv2.resize(im[..., ::-1], (TUILE_L, TUILE_H), interpolation=cv2.INTER_AREA)
            couleur = (0, 0, 220) if (i, k) in rouges else (50, 50, 50)
        pl[y:y + BANDE, x:x + TUILE_L] = couleur
        cv2.putText(pl, _ascii(legende), (x + 6, y + 23), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.imwrite(sortie, pl, [cv2.IMWRITE_JPEG_QUALITY, 90])
    return absentes


def relire(chemin_plan, dossier, board=None, encres=None):
    """Contrôle sur les images fixes, planche et manifeste. Renvoie le nombre de fautes."""
    with open(chemin_plan) as fh:
        plan = json.load(fh)
    fautes = []
    if cadrage.porte_arrets(plan):
        if not (board and encres):
            sys.exit('le plan porte des arrêts board : --board et --encres obligatoires')
        fautes, L = cadrage.examiner(plan, cadrage.Board(board, encres), cadrage.Images(dossier))
        with open(os.path.join(dossier, 'rapport-cadrage.md'), 'w') as fh:
            fh.write('\n'.join(['# Contrôle de cadrage et de traits', '', f'{len(fautes)} faute(s).', ''] + L) + '\n')
    absentes = planche(plan, dossier, os.path.join(dossier, 'planche-arrets.jpg'), fautes)
    with open(os.path.join(dossier, 'arrets.json'), 'w') as fh:
        json.dump({'plan_sha256': empreinte(chemin_plan), 'arrets': len(tuiles(plan)), 'absentes': absentes, 'fautes': len(fautes)}, fh, indent=1)
    return len(fautes) + absentes


def verifier(manifeste, chemin_plan):
    """Pour livrer : les images fixes existent, viennent de ce plan, et n'ont aucune faute."""
    nom = 'images fixes des arrêts'
    if not (manifeste and os.path.exists(manifeste)):
        return Resultat(nom, False, detail="arrets.manifeste absent : lancer controles.arrets avant-rendu avant tout rendu")
    with open(manifeste) as fh:
        m = json.load(fh)
    if m.get('plan_sha256') != empreinte(chemin_plan):
        return Resultat(nom, False, detail='le plan a changé depuis les images fixes : relancer controles.arrets avant-rendu')
    if m.get('fautes') or m.get('absentes'):
        return Resultat(nom, False, detail=f"{m.get('fautes')} faute(s), {m.get('absentes')} image(s) absente(s) dans la planche d'avant rendu")
    return Resultat(nom, True, detail=f"{m.get('arrets')} arrêt(s) en planche")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('commande', choices=['avant-rendu', 'planche'])
    p.add_argument('plan')
    p.add_argument('--remotion')
    p.add_argument('--sortie', required=True)
    p.add_argument('--board')
    p.add_argument('--encres')
    p.add_argument('--composition', default='PanneauV4')
    a = p.parse_args()
    if a.commande == 'avant-rendu':
        if not a.remotion:
            p.error('--remotion obligatoire pour avant-rendu')
        rendre(a.plan, a.remotion, a.sortie, a.composition)
    n = relire(a.plan, a.sortie, a.board, a.encres)
    print(f"{n} faute(s) ou image(s) absente(s), planche : {os.path.join(a.sortie, 'planche-arrets.jpg')}")
    sys.exit(1 if n else 0)


if __name__ == '__main__':
    main()
