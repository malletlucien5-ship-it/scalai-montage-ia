"""Contrôles du plan de montage (blocs.json de plan_blocs.py), avant et après rendu.

Incidents de la vidéo 1000 h (retours de Lucien du 21/10/2026) :
- caméra visible 0,08 s après un flash : « ça fait comme un bug » ;
- jauge « Débutant » coupée par l'écran suivant au bout de 0,56 s (9 poses tronquées en tout).

- cameras_courtes : aucune apparition de la caméra seule sous 0,8 s (morceau caméra ou trou entre deux poses plein écran).
- trous : aucun trou de moins de 0,5 s entre deux poses d'un même bloc.
- tronques : aucune pose coupée avant la fin de son animation (`tronque_images`), sauf poses déclarées dans valides.tronques.
"""
import json

from .commun import Resultat


def _blocs(chemin):
    with open(chemin) as fh:
        d = json.load(fh)
    # 15/11/2026 : plan d'une copie motion ({base, duree, visage, couches}), sans blocs caméra/écran.
    # La porte plantait (KeyError 'blocs') après 2 h de rendu : ces contrôles sont alors sans objet.
    if isinstance(d, dict) and 'blocs' not in d and 'couches' in d:
        return None, d.get('fps', 50)
    return d['blocs'] if isinstance(d, dict) else d, (d.get('fps', 50) if isinstance(d, dict) else 50)


def _sans_objet(nom):
    return Resultat(nom, True, bloquant=False, detail='plan motion (couches) : contrôle des blocs sans objet')


def cameras_courtes(chemin, min_s=0.8):
    blocs, fps = _blocs(chemin)
    if blocs is None:
        return _sans_objet('caméra trop courte')
    defauts = [f"k{b['k']:03d} images {b['t0']}-{b['t1']} ({(b['t1'] - b['t0']) / fps:.2f} s)"
               for b in blocs if b['type'] == 'camera' and b['t1'] - b['t0'] < min_s * fps]
    return Resultat('caméra trop courte', not defauts, detail=f"{len(defauts)} plan(s) sous {min_s} s" + ''.join(f" ; {d}" for d in defauts[:5]),
                    defauts=defauts)


def trous(chemin, min_s=0.5):
    blocs, fps = _blocs(chemin)
    if blocs is None:
        return _sans_objet('trous entre poses')
    defauts = []
    for b in blocs:
        ps = b.get('poses', [])
        for p, q in zip(ps, ps[1:]):
            if 0 < q['debut'] - p['fin'] < min_s * fps:
                defauts.append(f"{p['id']}→{q['id']} {q['debut'] - p['fin']} images")
    return Resultat('trous entre poses', not defauts, detail=f"{len(defauts)} trou(s)" + ''.join(f" ; {d}" for d in defauts[:5]), defauts=defauts)


def tronques(chemin, acceptes=()):
    blocs, _ = _blocs(chemin)
    if blocs is None:
        return _sans_objet('animations coupées')
    defauts = [f"{p['id']} ({p['tronque_images']} images coupées)" for b in blocs for p in b.get('poses', [])
               if p.get('tronque_images') and p['id'] not in acceptes]
    return Resultat('animations coupées', not defauts, detail=f"{len(defauts)} pose(s)" + ''.join(f" ; {d}" for d in defauts[:6]), defauts=defauts)


def visage_motion(chemin, part_min=0.35):
    """15/11/2026 (motion v1 cabinets) : visage 17 % du temps, zoom ×1,22, photos de Lucien en bio, archives de remplissage.
    Plan de copie motion : aucun zoom, aucune composition Bio, aucune archive sans texte, visage ≥ 35 % du temps."""
    with open(chemin) as fh:
        d = json.load(fh)
    if 'couches' not in d:
        return _sans_objet('visage et remplissage')
    defauts = []
    z = (d.get('visage') or {}).get('zoom', 1.0)
    if abs(z - 1.0) > 1e-6:
        defauts.append(f'zoom fixe x{z} sur la plaque')
    defauts += [f"{c['id']} : photo de Lucien ({c['comp']})" for c in d['couches'] if 'Bio' in (c.get('comp') or '')]
    defauts += [f"{c['id']} : archive sans texte" for c in d['couches'] if c.get('type') == 'broll' and not c.get('texte')]
    # 16/11/2026 (intro v3) : « ça doit toujours commencer avec moi qui parle », « je réapparais une demi-seconde, ça fait
    # super bizarre », « les photos de Derrick, je ne veux plus jamais les voir ».
    pleins = sorted((c['de'], c['a']) for c in d['couches'] if c.get('type') in ('comp', 'broll'))
    if pleins and pleins[0][0] < 0.05:
        defauts.append('la vidéo ne commence pas sur Lucien qui parle (plan plein cadre à 0 s)')
    fin = 0.0
    for de, a in pleins:
        if 0.01 < de - fin < 1.5 and fin > 0:
            defauts.append(f'visage {de - fin:.2f} s seulement entre {fin:.2f} et {de:.2f} s (minimum 1,5 s)')
        fin = max(fin, a)
    defauts += [f"{c['id']} : photo de Derrick bannie" for c in d['couches']
                if 'derrick' in json.dumps(c, ensure_ascii=False).lower()]
    occupe = sum(c['a'] - c['de'] for c in d['couches'] if c.get('type') in ('comp', 'broll'))
    part = 1 - occupe / max(d.get('duree') or 1, 1e-6)
    if part < part_min:
        defauts.append(f'visage {part:.0%} du temps (minimum {part_min:.0%})')
    return Resultat('visage et remplissage', not defauts, detail=f'visage {part:.0%}' + ''.join(f' ; {x}' for x in defauts[:6]), defauts=defauts)
