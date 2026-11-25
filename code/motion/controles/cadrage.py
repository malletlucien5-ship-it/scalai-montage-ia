#!/usr/bin/env python3
"""Contrôle de ce qui se voit à chaque arrêt d'un plan « board ».

Incident : viral X v4 du 01/11/2026. 11 contrôles OK sur le master, 10 arrêts sur 24 coupaient des textes.
Aucun contrôle ne regardait l'écran. Ce contrôle trouve 29 fautes sur le plan v4 et 0 sur le plan v4b.
Origine : chantiers/viral-x-2026-10-30/motion/tools/cadrage_v4b.py.

  python3 -m controles.cadrage encres BOARD.json TRANCHES/ ENCRES.json
  python3 -m controles.cadrage controle PLAN.json BOARD.json ENCRES.json SOURCE RAPPORT.md

SOURCE donne les images du panneau :
  video:MASTER.mp4   master rendu (panneau découpé selon plan.panneau)
  images:DOSSIER     images fixes F.png ou F.jpg, F = numéro d'image timeline (controles.arrets)
  -                  géométrie seule, traits non mesurés

Règles, pour chaque arrêt d'un plan board :
- vue : rectangle visible en coordonnées du board, centre x, y, zoom z : x ± l/2z, y ± h/2z.
- texte : un texte qui coupe la vue, ou s'en approche à moins de 8 px panneau, fait échouer l'arrêt.
  Sa boîte est l'encre mesurée, jamais la boîte Lucid : une boîte de titre fait 2 883 px pour 300 px d'encre.
- bloc cité : champ `bloc` de l'arrêt, sinon le texte qui porte le trait. Il tient entier avec 40 px de marge.
  Hors du bloc, une image peut sortir du cadre.
- trait, à pleine résolution, entre l'image avant le trait et l'image du trait fini :
  au plus 0,5 % des pixels rouges sur l'encre, jambages compris ; un soulignement a de l'encre juste au-dessus
  d'au moins 85 % de ses colonnes ; une ligne n'est jamais soulignée deux fois.
- diapositive : jamais plus de 1,5 s avec son seul titre.
- contenu : part de pixels porteurs à l'arrêt, relevée au rapport, non bloquante."""
import json, os, subprocess, sys

import cv2
import numpy as np

from .chantier import porte_arrets
from .commun import Resultat, sonde

PANNEAU = {'x': 853, 'w': 1707, 'h': 1440}
MARGE_BLOC = 40    # px panneau
MARGE_TEXTE = 8    # px panneau
APPROCHE, TRAIT = 30, 24   # images : arrivée du pointeur, tracé du trait
TITRE_SEUL_S = 1.5


def panneau(plan):
    return {**PANNEAU, **(plan.get('panneau') or {})}


def _dilate(masque, n):
    return cv2.dilate(masque.astype(np.uint8), np.ones((n, n), np.uint8)) > 0


# ------------------------------------------------------------------ encre des textes
def encres(board_json, tranches, sortie):
    """Écrit {id: {x, y, w, h}} : pixels de la boîte Lucid proches de la couleur du texte et loin du fond local.
    Les pointillés d'une zone ou un connecteur d'une autre couleur ne comptent pas."""
    with open(board_json) as fh:
        board = json.load(fh)
    lues, out = {}, {}
    for t in board['texts']:
        x0, y0, x1, y1 = int(t['x']) - 2, int(t['y']) - 2, int(t['x'] + t['w']) + 3, int(t['y'] + t['h']) + 3
        acc = np.zeros((y1 - y0, x1 - x0), bool)
        for s in board['slices']:
            ay0, ay1 = max(y0, s['y']), min(y1, s['y'] + s['h'])
            ax0, ax1 = max(x0, s['x']), min(x1, s['x'] + s['w'])
            if ay1 <= ay0 or ax1 <= ax0:
                continue
            if s['src'] not in lues:
                lues[s['src']] = cv2.imread(os.path.join(tranches, os.path.basename(s['src'])))[..., ::-1].astype(np.int16)
            rgb = lues[s['src']][ay0 - s['y']:ay1 - s['y'], ax0 - s['x']:ax1 - s['x']]
            bord = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]])
            vals, n = np.unique(bord // 8, axis=0, return_counts=True)
            fond = vals[n.argmax()] * 8 + 4
            coul = np.array([int(t['color'][k:k + 2], 16) for k in (1, 3, 5)], np.int16)
            acc[ay0 - y0:ay1 - y0, ax0 - x0:ax1 - x0] = (np.abs(rgb - fond).max(2) > 40) & (np.abs(rgb - coul).max(2) < 100)
        if not acc.any():
            out[t['id']] = {'x': t['x'], 'y': t['y'], 'w': t['w'], 'h': t['h'], 'vide': True}
            continue
        ys, xs = np.nonzero(acc)
        out[t['id']] = {'x': x0 + int(xs.min()), 'y': y0 + int(ys.min()),
                        'w': int(xs.max() - xs.min() + 1), 'h': int(ys.max() - ys.min() + 1)}
    with open(sortie, 'w') as fh:
        json.dump(out, fh, indent=0)
    return out


# ------------------------------------------------------------------ géométrie
def rect_vue(a, pan=PANNEAU):
    z = a['zoom']
    return {'x': a['x'] - pan['w'] / 2 / z, 'y': a['y'] - pan['h'] / 2 / z, 'w': pan['w'] / z, 'h': pan['h'] / z}


def inter(a, b):
    return a['x'] < b['x'] + b['w'] and a['x'] + a['w'] > b['x'] and a['y'] < b['y'] + b['h'] and a['y'] + a['h'] > b['y']


def dedans(a, r, m=0.0):
    return a['x'] >= r['x'] + m and a['y'] >= r['y'] + m and a['x'] + a['w'] <= r['x'] + r['w'] - m and a['y'] + a['h'] <= r['y'] + r['h'] - m


def union(rs):
    x0 = min(r['x'] for r in rs)
    y0 = min(r['y'] for r in rs)
    return {'x': x0, 'y': y0, 'w': max(r['x'] + r['w'] for r in rs) - x0, 'h': max(r['y'] + r['h'] for r in rs) - y0}


class Board:
    def __init__(self, board_json, encres_json):
        with open(board_json) as fh:
            b = json.load(fh)
        with open(encres_json) as fh:
            enc = json.load(fh)
        ret = set(b.get('retires') or [])
        self.textes = [{**enc[t['id']], 'id': t['id'], 'plain': t['plain']} for t in b['texts']
                       if t['id'] not in ret and not enc.get(t['id'], {}).get('vide')]
        self.images = {i['id']: i for i in b['images']}

    def bloc_de(self, lignes):
        """Bloc cité par défaut : le plus petit texte (encre) qui porte les lignes du trait."""
        L = union(lignes)
        porteurs = [t for t in self.textes if inter(t, L)]
        return union([min(porteurs, key=lambda t: t['w'] * t['h']), L]) if porteurs else L

    def bloc(self, spec):
        """spec : liste d'ids (textes ou images) et de rectangles."""
        rs = []
        for s in spec:
            if isinstance(s, dict):
                rs.append(s)
            elif s in self.images:
                rs.append(self.images[s])
            else:
                rs.append(next(t for t in self.textes if t['id'] == s))
        return union(rs)

    def coupes(self, vue, z=1.0):
        return [t for t in self.textes if inter(t, vue) and not dedans(t, vue, MARGE_TEXTE / z)]


def verifier_vue(B, a, bloc, pan=PANNEAU):
    vue = rect_vue(a, pan)
    f = [f"texte coupé « {t['plain'][:38]} » ({t['id']})" for t in B.coupes(vue, a['zoom'])]
    if bloc is not None and not dedans(bloc, vue, MARGE_BLOC / a['zoom']):
        f.append('bloc cité hors cadre ou marge < 40 px')
    return f


# ------------------------------------------------------------------ images du panneau
class Images:
    """Images fixes F.png ou F.jpg, F = numéro d'image timeline. None si l'image manque."""

    def __init__(self, dossier):
        self.dossier = dossier

    def image(self, f):
        for ext in ('png', 'jpg'):
            chemin = os.path.join(self.dossier, f'{f}.{ext}')
            if os.path.exists(chemin):
                return cv2.imread(chemin)[..., ::-1]
        return None


class Video:
    """Master rendu : le panneau est découpé à l'image demandée, décodage depuis 60 images avant."""

    def __init__(self, master, plan):
        self.master, self.fps, self.pan = master, plan.get('fps', 50), panneau(plan)
        s = sonde(master)
        if s['w'] < self.pan['x'] + self.pan['w'] or s['h'] < self.pan['h']:
            raise ValueError(f"master {s['w']}x{s['h']} plus petit que le panneau {self.pan}")

    def image(self, f):
        p = self.pan
        raw = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-ss', f'{max(0, f - 60) / self.fps:.4f}', '-i', self.master,
                              '-vf', f"select=eq(n\\,{min(f, 60)}),format=rgb24,crop={p['w']}:{p['h']}:{p['x']}:0",
                              '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                             capture_output=True, check=True).stdout
        return np.frombuffer(raw, np.uint8).reshape(p['h'], p['w'], 3)


def source(spec, plan):
    if spec == '-':
        return None
    kind, chemin = spec.split(':', 1)
    return {'video': lambda: Video(chemin, plan), 'images': lambda: Images(chemin)}[kind]()


def part_contenu(im):
    m = np.abs(im.astype(np.int16) - 242).max(2) > 18
    return float(_dilate(m, 25).mean())


def rouge(im):
    im = im.astype(np.int16)
    return (im[..., 0] > 190) & (im[..., 1] < 110) & (im[..., 2] < 110)


def encre_locale(im, y0=0, y1=None, x0=0, x1=None):
    """Encre : écart > 60 à la couleur dominante d'une fenêtre de 160 px autour de chaque case de 80 px
    (fond local : gris du board, lavande d'une zone, noir d'une carte), rouge exclu. Seules les cases de la zone sont calculées."""
    a = im.astype(np.int16)
    h, w = a.shape[:2]
    y1, x1 = y1 or h, x1 or w
    enc = np.zeros((h, w), bool)
    for y in range(y0 // 80 * 80, y1, 80):
        for x in range(x0 // 80 * 80, x1, 80):
            reg = a[max(0, y - 40):min(h, y + 120), max(0, x - 40):min(w, x + 120)]
            vals, cnt = np.unique(reg.reshape(-1, 3) // 8, axis=0, return_counts=True)
            fond = vals[cnt.argmax()] * 8 + 4
            enc[y:y + 80, x:x + 80] = np.abs(a[y:y + 80, x:x + 80] - fond).max(2) > 60
    return enc & ~rouge(im)


def analyse_trait(avant, apres, forme):
    """Renvoie (part de pixels rouges sur l'encre, part de colonnes soulignées), ou None si le trait manque.
    Un soulignement qui traverse les jambages de « Chaque », « reçoit », « post » compte : il se lit comme un trait à travers le texte."""
    h, w = apres.shape[:2]
    R = rouge(apres) & ~_dilate(rouge(avant), 5)
    ys, xs = np.nonzero(R)
    if len(ys) < 50:
        return None
    x0, x1 = max(0, int(xs.min()) - 20), min(w, int(xs.max()) + 21)
    y0, y1 = max(0, int(ys.min()) - 90), min(h, int(ys.max()) + 91)
    enc = encre_locale(avant, y0, y1, x0, x1)[y0:y1, x0:x1]
    r = R[y0:y1, x0:x1]
    barre = (r & _dilate(enc, 5)).sum() / r.sum()
    if forme != 'souligner':
        return float(barre), None
    encx = _dilate(enc, 25)
    cols = np.nonzero(r.any(0))[0]
    ok = sum(1 for c in cols if encx[max(0, np.nonzero(r[:, c])[0].min() - 40):max(0, np.nonzero(r[:, c])[0].min() - 2), c].any())
    return float(barre), ok / max(1, len(cols))


# ------------------------------------------------------------------ images demandées
def arret_image(a):
    return a['f1'] - 1


def trait_images(p, t):
    """Image avant le trait et image du trait fini, bornées au plan."""
    return max(p['debut'], t['debut'] - APPROCHE - 1), min(t['debut'] + TRAIT + 4, p['fin'] - 1)


def images_requises(plan):
    """Numéros d'image à voir avant rendu : fin de chaque arrêt, avant et après chaque trait."""
    s = set()
    for p in plan['plans']:
        for a in p.get('arrets', []):
            s.add(arret_image(a))
        if p['etat'] == 'board':
            for t in p.get('traits', []):
                s.update(trait_images(p, t))
    return sorted(s)


# ------------------------------------------------------------------ contrôle
def _traits(i, p, src):
    """Fautes des traits d'un plan board. La géométrie (double soulignement) ne demande aucune image."""
    soul, lignes, fautes = [], [], []
    for j, t in enumerate(p['traits']):
        f = []
        if t['forme'] == 'souligner':
            for l in t['lignes']:
                for jj, l2 in soul:
                    ov = min(l['y'] + l['h'], l2['y'] + l2['h']) - max(l['y'], l2['y'])
                    if ov > 0.5 * min(l['h'], l2['h']) and inter(l, l2):
                        f.append(f'ligne déjà soulignée par le trait {jj}')
            soul += [(j, l) for l in t['lignes']]
        if src:
            av, ap = (src.image(n) for n in trait_images(p, t))
            r = analyse_trait(av, ap, t['forme']) if av is not None and ap is not None else None
            if av is None or ap is None:
                f.append('image du trait absente')
            elif r is None:
                f.append('trait introuvable')
            else:
                barre, sous = r
                if barre > 0.005:
                    f.append(f"trait à travers le texte ({barre * 100:.1f} % des pixels rouges sur l'encre)")
                if sous is not None and sous < 0.85:
                    f.append(f'soulignement mal posé ({sous * 100:.0f} % des colonnes sous du texte)')
        lignes.append(f"- plan {i} {p['nom']} trait {j} « {t['texte'][:40]} » ({t['debut']} i) : {'OK' if not f else 'FAUTE'}"
                      + ''.join(f'\n  - {x}' for x in f))
        if f:
            fautes.append({'plan': i, 'type': 'trait', 'n': j, 'image': t['debut'], 'detail': f})
    return fautes, lignes


def examiner(plan, B, src=None):
    """Renvoie (fautes, lignes du rapport). Une faute = un arrêt, un trait ou une diapositive."""
    fps, pan = plan.get('fps', 50), panneau(plan)
    fautes, L = [], []
    for i, p in enumerate(plan['plans']):
        if p['etat'] == 'diapo' and p.get('puces'):
            d = p['puces'][0]['f'] - p['debut']
            ok = d <= TITRE_SEUL_S * fps
            L.append(f"- plan {i} diapo {p['nom']} : titre seul {d / fps:.2f} s {'OK' if ok else 'FAUTE'}")
            if not ok:
                fautes.append({'plan': i, 'type': 'diapo', 'image': p['debut'], 'detail': [f'titre seul {d / fps:.2f} s']})
        if p['etat'] != 'board':
            continue
        for k, a in enumerate(p['arrets']):
            tr = [t for t in p['traits'] if a['f0'] <= t['debut'] < a['f1']]
            bloc = B.bloc(a['bloc']) if a.get('bloc') else (B.bloc_de(tr[0]['lignes']) if tr else None)
            f = verifier_vue(B, a, bloc, pan)
            im = src.image(arret_image(a)) if src else None
            note = f', contenu {part_contenu(im) * 100:.0f} %' if im is not None else ''
            L.append(f"- plan {i} {p['nom']} arrêt {k} ({a['f0'] / fps:.1f}-{a['f1'] / fps:.1f} s, z {a['zoom']}{note}) : "
                     f"{'OK' if not f else 'FAUTE'}" + ''.join(f'\n  - {x}' for x in f))
            if f:
                fautes.append({'plan': i, 'type': 'arrêt', 'n': k, 'image': a['f0'], 'detail': f})
        ft, lt = _traits(i, p, src)
        fautes += ft
        L += lt
    return fautes, L


def controle(chemin_plan, board, encres_json, spec_source, rapport=None, valides=()):
    """Résultat bloquant pour livrer. Un board ou des encres absents font échouer : un contrôle sauté a laissé passer la v4.
    valides : fautes vues et acceptées par Lucien, sous la forme « plan/type/n » (9/arrêt/0, 34/trait/1, 12/diapo/None)."""
    if not (board and encres_json and os.path.exists(board) and os.path.exists(encres_json)):
        return Resultat('cadrage des arrêts', False, detail='le plan porte des arrêts : arrets.board et arrets.encres sont obligatoires')
    with open(chemin_plan) as fh:
        plan = json.load(fh)
    try:
        src = source(spec_source, plan)
    except (ValueError, subprocess.CalledProcessError) as e:
        return Resultat('cadrage des arrêts', False, detail=f'images illisibles : {e}')
    fautes, L = examiner(plan, Board(board, encres_json), src)
    fautes = [x for x in fautes if f"{x['plan']}/{x['type']}/{x.get('n')}" not in valides]
    if rapport:
        with open(rapport, 'w') as fh:
            fh.write('\n'.join(['# Contrôle de cadrage et de traits', '', f'{len(fautes)} faute(s).', ''] + L) + '\n')
    fps = plan.get('fps', 50)
    defauts = [f"plan {x['plan']} {x['type']} à {x['image'] / fps:.1f} s : {' ; '.join(x['detail'])}" for x in fautes]
    return Resultat('cadrage des arrêts', not fautes, detail=f"{len(fautes)} faute(s)" + ''.join(f" ; {d}" for d in defauts[:5]), defauts=defauts)


def main():
    a = sys.argv[1:]
    if len(a) == 4 and a[0] == 'encres':
        print(f"{len(encres(*a[1:]))} boîtes d'encre")
    elif len(a) == 6 and a[0] == 'controle':
        r = controle(*a[1:])
        print(r.ligne())
        sys.exit(0 if r.ok else 1)
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
