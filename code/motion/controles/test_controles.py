import numpy as np
"""Tests des contrôles communs sur des médias synthétiques (ffmpeg lavfi). Lancer : python3 -m unittest controles.test_controles"""
import json, os, subprocess, sys, tempfile, unittest

from . import chantier as ch, copie, image, son, source, voix

T = tempfile.mkdtemp(prefix='controles-')


def ff(nom, *args):
    chemin = os.path.join(T, nom)
    subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', *args, chemin], check=True)
    return chemin


def video(nom, filtre_v, filtre_a='sine=frequency=220:sample_rate=48000', d=4):
    return ff(nom, '-f', 'lavfi', '-i', f'{filtre_v}:d={d}', '-f', 'lavfi', '-i', f'{filtre_a}:d={d}',
              '-shortest', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac')


class Image(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gris = video('gris.mp4', 'color=c=gray:s=320x240:r=25')
        cls.noir = ff('noir.mp4', '-f', 'lavfi', '-i', 'color=c=gray:s=320x240:r=25:d=4', '-vf',
                      "drawbox=c=black:t=fill:enable='between(t,1.5,2.2)'", '-c:v', 'libx264', '-pix_fmt', 'yuv420p')
        cls.flash = ff('flash.mp4', '-f', 'lavfi', '-i', 'color=c=gray:s=320x240:r=25:d=4', '-vf',
                       "drawbox=c=white:t=fill:enable='eq(n,50)'", '-c:v', 'libx264', '-pix_fmt', 'yuv420p')
        cls.blanc = ff('blanc.mp4', '-f', 'lavfi', '-i', 'color=c=white:s=320x240:r=25:d=3', '-c:v', 'libx264', '-pix_fmt', 'yuv420p')

    def test_noires(self):
        self.assertTrue(image.noires(self.gris).ok)
        r = image.noires(self.noir)
        self.assertFalse(r.ok)
        self.assertAlmostEqual(r.defauts[0]['debut_s'], 1.5, delta=0.1)

    def test_flashs(self):
        self.assertTrue(image.flashs(self.gris).ok)
        self.assertFalse(image.flashs(self.flash).ok)

    def test_saturation(self):
        self.assertTrue(image.saturation(self.gris).ok)
        self.assertFalse(image.saturation(self.blanc).ok)
        self.assertTrue(image.saturation(self.blanc, valides=[(0, 3)]).ok)
        self.assertFalse(image.saturation(self.blanc, valides=[(0, 1)]).ok)
        # Blanc dès 2,3 s : l'échantillon 2 (image vers 2,48 s) appartient à la plage [2,3 ; 4] (Jev, 25/10/2026).
        tard = ff('blanc_tard.mp4', '-f', 'lavfi', '-i', 'color=c=gray:s=320x240:r=50:d=4', '-vf',
                  "drawbox=c=white:t=fill:enable='gte(t,2.3)'", '-c:v', 'libx264', '-pix_fmt', 'yuv420p')
        self.assertTrue(image.saturation(tard, valides=[(2.3, 4)]).ok)
        self.assertFalse(image.saturation(tard, valides=[(3.1, 4)]).ok)

    def test_visage_sans_visage(self):
        r = image.visage(self.flash, self.gris)
        self.assertTrue(r.ok)

    def test_visage_panneau_sans_visage(self):
        self.assertTrue(image.visage_panneau(self.flash, self.gris, 100).ok)

    def test_panneau_visible(self):
        self.assertTrue(image._panneau_visible(np.full((90, 160), 28, np.uint8)))
        self.assertFalse(image._panneau_visible(np.full((90, 160), 150, np.uint8)))  # plan seul, mur clair


class Son(unittest.TestCase):
    def test_silences(self):
        plein = video('plein.mp4', 'color=c=gray:s=160x120:r=25', 'sine=frequency=300:sample_rate=48000', d=6)
        trou = ff('trou.mp4', '-i', plein, '-af', "volume=enable='between(t,2,4)':volume=0", '-c:v', 'copy', '-c:a', 'aac')
        self.assertTrue(son.silences(plein).ok)
        self.assertFalse(son.silences(trou).ok)

    def test_niveau(self):
        fort = ff('fort.wav', '-f', 'lavfi', '-i', 'sine=frequency=440:d=5', '-af', 'volume=1.0')
        self.assertFalse(son.niveau(fort).ok)  # crête au-dessus de -0,5 dBTP

    def test_musique(self):
        v = ff('voix.wav', '-f', 'lavfi', '-i', 'sine=frequency=200:d=5', '-af', 'volume=0.3')
        m_ok = ff('mus_ok.wav', '-f', 'lavfi', '-i', 'sine=frequency=600:d=5', '-af', 'volume=0.075')
        m_bas = ff('mus_bas.wav', '-f', 'lavfi', '-i', 'sine=frequency=600:d=5', '-af', 'volume=0.03')
        m_muet = ff('mus_muet.wav', '-f', 'lavfi', '-i', 'sine=frequency=600:d=5', '-af', 'volume=0.0005')
        self.assertTrue(son.musique(m_ok, v).ok)
        self.assertFalse(son.musique(m_muet, v).ok)
        self.assertFalse(son.musique(m_bas, v).ok)  # 18 dB sous la voix : inaudible pour Lucien
        self.assertTrue(son.musique(m_bas, v, -21.0, -9.0).ok)  # écart validé par Lucien (valides.musique_ecart)

    def test_fichiers(self):
        d = tempfile.mkdtemp(dir=T)
        open(os.path.join(d, 'whoosh.wav'), 'w').close()
        self.assertTrue(son.fichiers([d]).ok)
        open(os.path.join(d, 'whoosh-lqmp3.mp3'), 'w').close()
        self.assertFalse(son.fichiers([d]).ok)


class Voix(unittest.TestCase):
    def test_raccords(self):
        a = ff('raccord.wav', '-f', 'lavfi', '-i', 'sine=frequency=300:d=4', '-af', "volume=enable='between(t,1.8,2.4)':volume=0")
        r = voix.raccords(a, temps_auto=[1.0, 2.1], temps_lucien=[3.0])
        self.assertFalse(r.ok)
        self.assertEqual([d['temps_s'] for d in r.defauts if d['source'] == 'auto'], [1.0])
        self.assertEqual([d['temps_s'] for d in r.defauts if d['source'] == 'lucien'], [3.0])
        self.assertTrue(voix.raccords(a, temps_auto=[2.1], temps_lucien=[3.0]).ok)

    def test_phrases(self):
        t = "Bonjour à tous, aujourd'hui je vous montre comment j'ai automatisé ma prospection. Vous pouvez gagner plus d'argent."
        self.assertTrue(voix.phrases(t, ["je vous montre comment j'ai automatisé ma prospection"]).ok)
        self.assertFalse(voix.phrases(t, ["vous pouvez gagner plus d'argent", "et ça c'est la phrase oubliée"]).ok)

    def test_duree(self):
        v = video('duree.mp4', 'color=c=gray:s=160x120:r=25', d=2)
        self.assertTrue(voix.duree(v, 50).ok)
        self.assertFalse(voix.duree(v, 60).ok)


class Source(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(dir=T)
        os.makedirs(os.path.join(self.d, 'src'))
        os.makedirs(os.path.join(self.d, 'public', 'fonts'))
        open(os.path.join(self.d, 'public', 'fonts', 'HelveticaNeue-Bold.ttf'), 'w').close()

    def ecrire(self, texte):
        with open(os.path.join(self.d, 'src', 'Scene.tsx'), 'w') as fh:
            fh.write(texte)

    def test_polices(self):
        self.ecrire("const s = {fontFamily: 'Helvetica Neue, sans-serif'};")
        self.assertTrue(source.polices(self.d, ['Helvetica Neue']).ok)
        self.ecrire("const s = {fontFamily: 'Inter'};")
        self.assertFalse(source.polices(self.d, ['Helvetica Neue']).ok)
        self.assertFalse(source.polices(self.d, ['Poppins']).ok)  # fichier absent
        self.ecrire("const s = {fontFamily: 'Poppins'};")
        os.makedirs(os.path.join(self.d, 'node_modules', '@fontsource', 'poppins'))
        self.assertTrue(source.polices(self.d, ['Poppins']).ok)  # paquet @fontsource

    def test_modeles(self):
        self.ecrire("<Text>Claude Opus 5.5</Text>")
        self.assertTrue(source.modeles(self.d).ok)
        self.ecrire("<Text>Sonnet 5 et Fable 5 · Élevé</Text>")
        self.assertEqual(len(source.modeles(self.d).defauts), 1)
        self.ecrire("<Text>Hud Fable 5 · Élevé</Text>")
        self.assertTrue(source.modeles(self.d, acceptes=("Fable 5",)).ok)
        self.ecrire("<Text>Fable 5.1 et Sonnet 5.5</Text>")
        self.assertTrue(source.modeles(self.d).ok)
        self.ecrire("<Text>Opus 4.7 et GPT-4o</Text>")
        self.assertEqual(len(source.modeles(self.d).defauts), 1)
        self.assertFalse(source.modeles(self.d).ok)

    def test_liens(self):
        self.assertTrue(source.liens(self.d).ok)
        os.symlink('/tmp', os.path.join(self.d, 'public', 'plaque.mp4'))
        self.assertFalse(source.liens(self.d).ok)


class Copie(unittest.TestCase):
    def test_superposition(self):
        ref = video('ref.mp4', 'testsrc=s=270x480:r=25', d=3)
        bonne = ff('bonne.mp4', '-i', ref, '-c', 'copy')
        decalee = ff('decalee.mp4', '-i', ref, '-vf', 'hue=h=120,crop=230:440:40:40,scale=270:480', '-c:a', 'copy')
        self.assertTrue(copie.superposition(bonne, ref).ok)
        planche = os.path.join(T, 'planche.jpg')
        self.assertFalse(copie.superposition(decalee, ref, planche=planche).ok)
        self.assertTrue(os.path.getsize(planche) > 1000)


    def test_par_placement_et_halo(self):
        ref = video('ref2.mp4', 'testsrc=s=640x360:r=25', d=4)
        autre = video('autre2.mp4', 'color=c=red:s=640x360:r=25', d=4)
        corr = [{'id': 'M01', 'mode': 'plein', 'ref': [0, 3], 'copie': [0, 3]}]
        self.assertTrue(copie.par_placement(ref, ref, corr).ok)
        self.assertFalse(copie.par_placement(autre, ref, corr).ok)
        gris = video('gris.mp4', 'color=c=gray:s=2560x1440:r=25', d=3)
        sombre = ff('sombre.mp4', '-i', gris, '-vf', 'drawbox=x=200:y=200:w=600:h=200:c=black:t=fill', '-c:a', 'copy')
        clair = ff('clair.mp4', '-i', gris, '-vf', 'drawbox=x=200:y=200:w=600:h=200:c=white:t=fill', '-c:a', 'copy')
        cal = [{'id': 'M05', 'mode': 'calque', 'ref': [0, 2], 'copie': [0, 2]}]
        self.assertFalse(copie.halo_sombre(sombre, gris, cal).ok)
        self.assertTrue(copie.halo_sombre(clair, gris, cal).ok)


class Chantier(unittest.TestCase):
    base = {'nom': 'cameron1', 'type': 'pub', 'etape': 'plaque', 'rushs': [{'nom': 'DJI_0120.MP4', 'sha256': 'ab'}],
            'voix': {'source': 'obs', 'obs_disponible': True}}

    def test_plaque(self):
        self.assertEqual(ch.valider(self.base), [])

    def test_motion_sans_coupes(self):
        c = dict(self.base, etape='motion')
        f = ch.valider(c)
        self.assertTrue(any('par_lucien' in x for x in f))
        self.assertTrue(any('etalonnage' in x for x in f))
        self.assertTrue(any('elements_valides' in x for x in f))

    def test_motion_complet(self):
        c = dict(self.base, etape='motion', elements_valides=[],
                 coupes={'source': 'edl', 'sha256': 'x', 'cadence': 50, 'images_master': 900, 'par_lucien': True},
                 etalonnage={'choisi': 'look-a', 'choisi_par_lucien': True})
        self.assertEqual(ch.valider(c), [])

    def test_voix_camera(self):
        c = dict(self.base, voix={'source': 'camera', 'obs_disponible': True})
        self.assertTrue(ch.valider(c))

    def test_copie(self):
        c = dict(self.base, type='copie', etape='final', elements_valides=[],
                 coupes={'source': 'aucune', 'par_lucien': True}, etalonnage={'choisi': 'look-a', 'choisi_par_lucien': True})
        self.assertTrue(any('inventaire' in x for x in ch.valider(c)))
        c['copie'] = {'reference': 'ref.mp4', 'inventaire': ['M01'], 'correspondance': [{'id': 'M01'}]}
        f = ch.valider(c)
        self.assertTrue(any('apercu_valide_par_lucien' in x for x in f))
        self.assertTrue(any('copie.revue' in x for x in f))
        c['copie'].update(apercu_valide_par_lucien=True, revue={'M01': 'conforme'})
        self.assertEqual(ch.valider(c), [])
        c['copie']['revue'] = {'M01': 'accepte_par_lucien'}
        self.assertEqual(ch.valider(c), [])
        c['copie']['revue'] = {'M01': 'a revoir'}
        self.assertTrue(any('copie.revue' in x for x in ch.valider(c)))


class Livrer(unittest.TestCase):
    def test_bout_en_bout(self):
        v = video('livrer.mp4', 'color=c=gray:s=320x240:r=25', 'anoisesrc=a=0.05:sample_rate=48000', d=4)
        c = os.path.join(T, 'chantier.json')
        json.dump(dict(Chantier.base), open(c, 'w'))
        racine = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        r = subprocess.run([sys.executable, '-m', 'controles.livrer', v, '--chantier', c, '--sec'], cwd=racine,
                           capture_output=True, text=True)
        self.assertIn('images noires', r.stdout)
        json.dump(dict(Chantier.base, etape='final'), open(c, 'w'))
        r = subprocess.run([sys.executable, '-m', 'controles.livrer', v, '--chantier', c, '--sec'], cwd=racine,
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        self.assertIn('ÉCHEC chantier', r.stdout)


if __name__ == '__main__':
    unittest.main()


class Plan(unittest.TestCase):
    """Retours de Lucien du 21/10/2026 : caméra de 0,08 s, jauge coupée."""

    def test_plan(self):
        import json, tempfile
        from controles import plan
        d = {'blocs': [{'type': 'camera', 't0': 0, 't1': 4, 'k': 0},
                       {'type': 'bloc', 't0': 4, 't1': 200, 'k': 1, 'poses': [
                           {'id': 'A10', 'debut': 4, 'fin': 32, 'tronque_images': 106},
                           {'id': 'A11', 'debut': 44, 'fin': 200}]}]}
        f = tempfile.NamedTemporaryFile('w', suffix='.json', delete=False)
        json.dump(d, f); f.close()
        self.assertFalse(plan.cameras_courtes(f.name).ok)
        self.assertFalse(plan.trous(f.name).ok)
        self.assertFalse(plan.tronques(f.name).ok)
        self.assertTrue(plan.tronques(f.name, acceptes=('A10',)).ok)


class Lexique(unittest.TestCase):
    """Règle de Lucien du 25/10/2026 : plus jamais « Cloud » pour Claude ni « chtgpt »."""

    def test_lexique(self):
        from controles import texte
        f = os.path.join(T, 'mots.json')
        json.dump({'words': [{'text': t} for t in 'Utilisez Cloud Code et pas chtgpt dans le cloud.'.split()]}, open(f, 'w'))
        r = texte.lexique([f])
        self.assertFalse(r.ok)
        self.assertEqual([d['apres'] for d in r.defauts], ['Claude', 'ChatGPT'])
        json.dump({'words': [{'text': t} for t in 'Utilisez Claude Code et ChatGPT dans le cloud.'.split()]}, open(f, 'w'))
        self.assertTrue(texte.lexique([f]).ok)


class Tranche(unittest.TestCase):
    """09/11/2026 : final cabinets en quarantaine à 23 h 25 pour deux fausses alertes, vues après l'assemblage."""

    @classmethod
    def setUpClass(cls):
        cls.noir = ff('tranche-noir.mp4', '-f', 'lavfi', '-i', 'color=c=gray:s=320x240:r=25:d=4', '-vf',
                      "drawbox=c=black:t=fill:enable='between(t,1.5,2.2)'", '-c:v', 'libx264', '-pix_fmt', 'yuv420p')
        cls.gris = ff('tranche-gris.mp4', '-f', 'lavfi', '-i', 'color=c=gray:s=320x240:r=25:d=4', '-c:v', 'libx264', '-pix_fmt', 'yuv420p')

    def test_images_du_master(self):
        from . import tranche
        self.assertEqual(tranche.alertes(self.gris, 1000), [])
        a = tranche.alertes(self.noir, 1000)
        self.assertEqual([x['controle'] for x in a], ['noires'])
        self.assertAlmostEqual(a[0]['debut'], 1038, delta=3)
        self.assertGreater(a[0]['fin'], a[0]['debut'])
        self.assertEqual(tranche.alertes(self.noir, 1000, {'noires': [[1030, 1060]]}), [])
        self.assertEqual(len(tranche.alertes(self.noir, 0, {'noires': [[1030, 1060]]})), 1)

    def test_ligne_de_commande(self):
        racine = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        etat, pl = os.path.join(T, 'etat-tranche.md'), os.path.join(T, 'alertes.jpg')
        r = subprocess.run([sys.executable, '-m', 'controles.tranche', self.noir, '--debut-image', '1000',
                            '--etat-local', etat, '--planche', pl], cwd=racine, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('ALERTES: 1', r.stdout)
        self.assertIn('ALERTE tranche', open(etat).read())
        self.assertIn('valides.noires', open(etat).read())
        self.assertTrue(os.path.getsize(pl) > 1000)
        rapport = json.load(open(os.path.splitext(self.noir)[0] + ' - alertes.json'))
        self.assertEqual(rapport['debut_image'], 1000)
        r = subprocess.run([sys.executable, '-m', 'controles.tranche', self.gris, '--debut-image', '0', '--etat-local', etat],
                           cwd=racine, capture_output=True, text=True)
        self.assertIn('ALERTES: 0', r.stdout)


def test_plan_motion_sans_blocs(tmp_path):
    """15/11/2026 : livrer plantait (KeyError 'blocs') sur le plan d'une copie motion."""
    import json
    from controles import plan
    p = tmp_path / 'plan-motion.json'
    p.write_text(json.dumps({'base': 'x.mp4', 'duree': 10, 'visage': {}, 'couches': []}))
    for f in (plan.cameras_courtes, plan.trous, plan.tronques):
        r = f(str(p))
        assert r.ok and not r.bloquant
