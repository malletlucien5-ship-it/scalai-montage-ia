"""Lexique des transcriptions : aucun « Cloud » pour Claude, aucun « chtgpt » pour ChatGPT.

Règle de Lucien du 25/10/2026 : « je veux que les transcriptions ne fassent plus jamais ces erreurs ».
Incident : lot Shorts 1000h v6, 20 « Cloud » et 3 « Scalaï » dans les sous-titres.
Le lexique vit dans cloud/lexique_lucien.py, copie identique dans le Clipper et sur prod."""
import json
import os
import sys

from .commun import Resultat

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'cloud'))
import lexique_lucien as lx  # noqa: E402


def lexique(chemins):
    """Chaque fichier de mots (words.json, montage.words.json) doit passer le lexique sans correction."""
    defauts = []
    for chemin in chemins:
        doc = json.load(open(chemin))
        mots, cle = lx._liste_et_cle(doc)
        for j in lx.fautes(mots, cle):
            defauts.append({'fichier': os.path.basename(chemin), **j})
    return Resultat('lexique des transcriptions', not defauts,
                    detail=f"{len(defauts)} faute(s)" + ''.join(f" ; {d['avant']} -> {d['apres']}" for d in defauts[:6])
                    + ("" if not defauts else " ; corriger : python3 cloud/lexique_lucien.py FICHIER --corriger FICHIER"),
                    defauts=defauts)
