"""Tests du contrôle de cadrage et de l'étape avant rendu. Lancer : python3 -m unittest controles.test_cadrage
L'incident viral X du 01/11/2026 reste un test : 29 fautes sur le plan v4, 0 sur le plan v4b, sur des découpes des masters livrés."""
import json, os, shutil, unittest

import cv2
import numpy as np

from . import arrets, cadrage, chantier as ch, livrer
from .test_controles import T, video

ICI = os.path.dirname(os.path.abspath(__file__))
VIRAL = os.path.join(ICI, 'fixtures', 'viral-x')
BOARD_ESSAI = {'texts': [{'id': 'a', 'plain': 'Titre'}, {'id': 'b', 'plain': 'Loin du cadre'}], 'images': []}
ENCRES_ESSAI = {'a': {'x': 100, 'y': 100, 'w': 60, 'h': 20}, 'b': {'x': 5000, 'y': 5000, 'w': 60, 'h': 20}}


def ecrit(nom, d):
    chemin = os.path.join(T, nom)
    with open(chemin, 'w') as fh:
        json.dump(d, fh)
    return chemin


def plan_essai(x, traits=()):
    """Un plan board de 100 images, panneau 320x240 : la vue couvre x ± 160."""
    return {'fps': 25, 'panneau': {'x': 0, 'w': 320, 'h': 240}, 'plans': [
        {'debut': 0, 'fin': 100, 'etat': 'board', 'nom': 'essai', 'traits': list(traits),
         'arrets': [{'f0': 0, 'f1': 100, 'x': x, 'y': 110, 'zoom': 1}]}]}


class CartesTraits:
    """Découpes des images réelles, reposées sur un panneau vide à leur position (fixtures/viral-x/traits.json)."""

    def __init__(self, version):
        with open(os.path.join(VIRAL, 'traits.json')) as fh:
            self.cartes = json.load(fh)[version]

    def image(self, f):
        c = self.cartes.get(str(f))
        if c is None:
            return None
        im = np.full((1440, 1707, 3), 242, np.uint8)
        d = cv2.imread(os.path.join(VIRAL, 'traits', c['fichier']))[..., ::-1]
        im[c['y']:c['y'] + d.shape[0], c['x']:c['x'] + d.shape[1]] = d
        return im


class Cadrage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.board = cadrage.Board(os.path.join(VIRAL, 'board.json'), os.path.join(VIRAL, 'encres.json'))
        cls.b, cls.e = ecrit('b.json', BOARD_ESSAI), ecrit('e.json', ENCRES_ESSAI)

    def fautes(self, version):
        with open(os.path.join(VIRAL, f'{version}.plan.json')) as fh:
            return cadrage.examiner(json.load(fh), self.board, CartesTraits(version))[0]

    def test_v4_toutes_les_fautes(self):
        """La règle finale donne 29 fautes. Les 27 annoncées le 01/11 viennent d'une version de travail jamais committée :
        75c541c en donne 30 (contenu bloquant), f687cac 29, sur board.tar et le paquet v4 (rejeu du 01/11/2026)."""
        attendues = {(i, 'diapo', None) for i in (12, 15, 30, 31, 55)}
        attendues |= {(i, 'arrêt', n) for i, n in ((9, 0), (9, 1), (17, 0), (17, 2), (21, 0), (27, 0), (34, 2), (36, 2), (56, 0), (56, 1), (58, 0), (58, 1))}
        attendues |= {(i, 'trait', n) for i, n in ((9, 0), (21, 0), (25, 0), (27, 0), (29, 0), (34, 0), (34, 1), (36, 1), (36, 2), (56, 0), (56, 1), (58, 0))}
        self.assertEqual({(x['plan'], x['type'], x.get('n')) for x in self.fautes('v4')}, attendues)

    def test_v4b_zero_faute(self):
        self.assertEqual(self.fautes('v4b'), [])

    def test_arrets_du_cahier_v4_detectes(self):
        """Arrêts relevés par Lucien (regles/retours-v4b.md) : playbook, Prestige bias, 60 minutes, Paid partnership, clipping."""
        vus = {(x['plan'], x['n']) for x in self.fautes('v4') if x['type'] == 'arrêt'}
        self.assertLessEqual({(9, 0), (9, 1), (17, 0), (17, 2), (21, 0), (27, 0), (34, 2), (58, 0), (58, 1)}, vus)

    def test_texte_coupe_par_le_bord(self):
        B = cadrage.Board(self.b, self.e)
        self.assertEqual(cadrage.examiner(plan_essai(200), B)[0], [])       # vue 40-360 : titre entier
        self.assertEqual(len(cadrage.examiner(plan_essai(300), B)[0]), 1)   # vue 140-460 : titre coupé
        self.assertEqual(cadrage.examiner(plan_essai(400), B)[0], [])       # vue 240-560 : titre sorti, permis hors bloc
        self.assertEqual(len(cadrage.examiner(plan_essai(255), B)[0]), 1)   # vue 95-415 : bord à 5 px du titre

    def test_boite_lucid_large_sans_encre_coupee(self):
        """Seule l'encre compte : une boîte de 2 883 px pour 300 px d'encre ne coupe aucune lettre."""
        board = {'texts': [{'id': 'a', 'plain': 'Titre', 'x': -1000, 'y': 100, 'w': 2883, 'h': 20}], 'images': []}
        B = cadrage.Board(ecrit('b2.json', board), self.e)
        self.assertEqual(cadrage.examiner(plan_essai(200), B)[0], [])

    def test_bloc_cite_hors_marge(self):
        B = cadrage.Board(self.b, self.e)
        p = plan_essai(200)
        p['plans'][0]['arrets'][0]['bloc'] = ['a', {'x': 300, 'y': 100, 'w': 40, 'h': 20}]   # 340 > 360 - 40 : marge entamée
        p['plans'][0]['arrets'][0]['x'] = 195
        self.assertEqual(len(cadrage.examiner(p, B)[0]), 1)

    def test_trait_barre_le_texte(self):
        fond = np.full((400, 800, 3), 242, np.uint8)
        fond[100:130, 100:700] = 20
        sous, travers = fond.copy(), fond.copy()
        sous[136:140, 100:700] = (255, 37, 37)
        travers[113:117, 100:700] = (255, 37, 37)
        barre, part = cadrage.analyse_trait(fond, sous, 'souligner')
        self.assertLessEqual(barre, 0.005)
        self.assertGreaterEqual(part, 0.85)
        self.assertGreater(cadrage.analyse_trait(fond, travers, 'souligner')[0], 0.005)
        self.assertIsNone(cadrage.analyse_trait(fond, fond, 'souligner'))

    def test_ligne_soulignee_deux_fois(self):
        B = cadrage.Board(self.b, self.e)
        ligne = {'x': 100, 'y': 100, 'w': 60, 'h': 20}
        t = [{'forme': 'souligner', 'lignes': [ligne], 'debut': d, 'texte': 'Titre'} for d in (10, 50)]
        self.assertEqual([x['n'] for x in cadrage.examiner(plan_essai(200, t), B)[0] if x['type'] == 'trait'], [1])

    def test_diapo_titre_seul(self):
        p = {'fps': 50, 'plans': [{'debut': 0, 'fin': 400, 'etat': 'diapo', 'nom': 'd', 'puces': [{'f': 76}]},
                                  {'debut': 400, 'fin': 800, 'etat': 'diapo', 'nom': 'e', 'puces': [{'f': 475}]}]}
        self.assertEqual([x['plan'] for x in cadrage.examiner(p, None)[0]], [0])

    def test_encres_mesurees_sur_les_tranches(self):
        d = os.path.join(T, 'tranches')
        os.makedirs(d, exist_ok=True)
        tr = np.full((400, 800, 3), 242, np.uint8)
        tr[110:130, 150:210] = 20
        cv2.imwrite(os.path.join(d, 't.png'), tr)
        b = ecrit('bt.json', {'slices': [{'src': 'board/t.png', 'x': 100, 'y': 0, 'w': 800, 'h': 400}],
                              'texts': [{'id': 'a', 'x': 200, 'y': 90, 'w': 500, 'h': 60, 'color': '#141414'}]})
        e = cadrage.encres(b, d, os.path.join(T, 'et.json'))
        self.assertEqual(e['a'], {'x': 250, 'y': 110, 'w': 60, 'h': 20})


def images_fixes(plan, dossier):
    os.makedirs(dossier, exist_ok=True)
    for f in cadrage.images_requises(plan):
        cv2.imwrite(os.path.join(dossier, f'{f}.png'), np.full((240, 320, 3), 200, np.uint8))


class Arrets(unittest.TestCase):
    """Étape avant rendu et branchement dans livrer."""

    @classmethod
    def setUpClass(cls):
        cls.master = video('panneau.mp4', 'color=c=gray:s=320x240:r=25')
        cls.b, cls.e = ecrit('b.json', BOARD_ESSAI), ecrit('e.json', ENCRES_ESSAI)

    def preparer(self, nom, x):
        p = plan_essai(x)
        chemin, d = ecrit(f'{nom}.plan.json', p), os.path.join(T, nom)
        shutil.rmtree(d, ignore_errors=True)
        images_fixes(p, d)
        return chemin, d

    def livrer(self, chemin, d):
        c = {'etape': 'motion', 'plan': chemin, 'arrets': {'board': self.b, 'encres': self.e, 'manifeste': os.path.join(d, 'arrets.json')}}
        return {r.nom: r for r in livrer.controles(self.master, c)}

    def test_planche_et_manifeste(self):
        chemin, d = self.preparer('propre', 200)
        self.assertEqual(arrets.relire(chemin, d, self.b, self.e), 0)
        self.assertGreater(cv2.imread(os.path.join(d, 'planche-arrets.jpg')).shape[1], arrets.TUILE_L)
        self.assertTrue(arrets.verifier(os.path.join(d, 'arrets.json'), chemin).ok)

    def test_image_absente_compte(self):
        chemin, d = self.preparer('trou', 200)
        os.remove(os.path.join(d, '99.png'))
        self.assertEqual(arrets.relire(chemin, d, self.b, self.e), 1)
        self.assertFalse(arrets.verifier(os.path.join(d, 'arrets.json'), chemin).ok)

    def test_plan_change_apres_les_images(self):
        chemin, d = self.preparer('change', 200)
        arrets.relire(chemin, d, self.b, self.e)
        ecrit('change.plan.json', plan_essai(205))
        self.assertIn('changé', arrets.verifier(os.path.join(d, 'arrets.json'), chemin).detail)

    def test_livrer_bloque_un_texte_coupe(self):
        chemin, d = self.preparer('coupe', 300)
        arrets.relire(chemin, d, self.b, self.e)
        r = self.livrer(chemin, d)
        self.assertFalse(r['cadrage des arrêts'].ok)
        self.assertTrue(r['cadrage des arrêts'].bloquant)
        self.assertFalse(r['images fixes des arrêts'].ok)

    def test_livrer_passe_un_plan_propre(self):
        chemin, d = self.preparer('net', 200)
        arrets.relire(chemin, d, self.b, self.e)
        r = self.livrer(chemin, d)
        self.assertTrue(r['cadrage des arrêts'].ok, r['cadrage des arrêts'].detail)
        self.assertTrue(r['images fixes des arrêts'].ok)

    def test_livrer_sans_board_echoue(self):
        chemin, _ = self.preparer('nu', 200)
        r = {x.nom: x for x in livrer.controles(self.master, {'etape': 'motion', 'plan': chemin})}
        self.assertFalse(r['cadrage des arrêts'].ok)
        self.assertFalse(r['images fixes des arrêts'].ok)

    def test_plan_sans_arrets_passe_sans_controle(self):
        chemin = ecrit('sans.plan.json', {'fps': 25, 'plans': [{'debut': 0, 'fin': 100, 'etat': 'visage'}]})
        self.assertNotIn('cadrage des arrêts', {x.nom for x in livrer.controles(self.master, {'etape': 'motion', 'plan': chemin})})

    def test_plan_blocs_inchange(self):
        chemin = ecrit('blocs.json', {'fps': 25, 'blocs': []})
        self.assertIn('trous entre poses', {x.nom for x in livrer.controles(self.master, {'etape': 'motion', 'plan': chemin})})

    def test_chantier_doit_declarer_son_plan(self):
        d = os.path.join(T, 'moteur', 'plan')
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, 'v4.plan.json'), 'w') as fh:
            json.dump(plan_essai(200), fh)
        c = {'nom': 'x', 'rushs': [{'sha256': 'a'}], 'coupes': {'par_lucien': True, 'source': 'aucune'}, 'elements_valides': [],
             'etalonnage': {'choisi': 'a', 'choisi_par_lucien': True}, 'remotion': os.path.dirname(d)}
        self.assertTrue(any('plan à arrêts' in x for x in ch.valider(c, 'motion')))
        self.assertFalse(any('plan à arrêts' in x for x in ch.valider({**c, 'plan': 'p'}, 'motion')))

    @unittest.skipUnless(os.path.isdir(os.path.join(ICI, 'remotion-essai', 'node_modules')), 'CI : npm install dans remotion-essai')
    def test_images_fixes_par_remotion(self):
        p = plan_essai(200)
        p['plans'][0]['arrets'].insert(0, {'f0': 40, 'f1': 49, 'x': 200, 'y': 110, 'zoom': 1})
        chemin, d = ecrit('remotion.plan.json', p), os.path.join(T, 'remotion')
        moteur = os.path.join(ICI, 'remotion-essai')
        self.assertEqual(sorted(arrets.rendre(chemin, moteur, d)), [48, 99])
        pair, impair = cv2.imread(os.path.join(d, '48.png')), cv2.imread(os.path.join(d, '99.png'))
        self.assertEqual(pair.shape, (270, 320, 3))
        self.assertGreater(abs(int(pair[0, 0, 1]) - int(impair[0, 0, 1])), 40)   # chaque image montre bien son numéro
        self.assertEqual(arrets.rendre(chemin, moteur, d), [])                   # reprise : rien à refaire


if __name__ == '__main__':
    unittest.main()
