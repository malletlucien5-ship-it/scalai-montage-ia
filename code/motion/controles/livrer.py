#!/usr/bin/env python3
"""Porte unique de livraison d'un montage. Aucun master ne part sans elle.

1. Valide chantier.json pour l'étape.
2. Décode le master entier et lance tous les contrôles qui s'appliquent.
3. Écrit le rapport dans le fichier d'état (lu par le guet de prod, sans aucun message envoyé).
4. Échec bloquant : rien n'est envoyé, code 1. Sinon : envoi en HTTP/1.1, taille distante vérifiée, code 0.

Usage (depuis la racine du dépôt) :
  python3 -m controles.livrer MASTER.mp4 --chantier chantier.json --put URL_PUT_MASTER \
      [--plaque SOBRE.mp4] [--etat-local etat.md --etat-put URL_PUT_ETAT] \
      [--planche-put URL_PUT_PLANCHE] [--extra FICHIER=URL_PUT ...] [--quarantaine URL_PUT] [--sec]
--sec : contrôles seuls, aucun envoi (essai).
--quarantaine : sur échec des contrôles, garde le master sous ce lien (dossier quarantaine/, jamais rapatrié).
  Une routine suivante le reprend et relance livrer sans refaire le rendu.
  Deux masters perdus avec leur conteneur les 25/10/2026 (1 h 40 de rendu chacun).
Audit du 20/10/2026 : Intelligence/audits/2026-10-20-audit-erreurs-montage."""
import argparse, json, os, subprocess, sys, time

from . import arrets, cadrage, chantier as ch, copie, image, plan, son, source, texte, voix
from .commun import Resultat, sonde


def controles(master, c, plaque=None, planche=None):
    etape = c['etape']
    val = c.get('valides') or {}
    r = []
    s = sonde(master)
    r.append(image.noires(master, valides=[tuple(x) for x in val.get('noires', [])]))
    r.append(image.flashs(master, valides=[tuple(x) for x in val.get('flashs', [])]))
    if c.get('plan') and os.path.exists(c['plan']):
        with open(c['plan']) as fh:
            d = json.load(fh)
        if isinstance(d, dict) and 'plans' in d:
            # 01/11/2026 : ce qui se voit à chaque arrêt, sur le master lui-même (viral X v4, 11 contrôles OK et 27 fautes).
            if etape in ('motion', 'final') and ch.porte_arrets(d):
                a = c.get('arrets') or {}
                r.append(cadrage.controle(c['plan'], a.get('board'), a.get('encres'), a.get('source') or f'video:{master}',
                                          rapport=os.path.splitext(master)[0] + ' - cadrage.md', valides=tuple(val.get('cadrage', []))))
                r.append(arrets.verifier(a.get('manifeste'), c['plan']))
        else:
            r += [plan.cameras_courtes(c['plan']), plan.trous(c['plan']), plan.tronques(c['plan'], acceptes=tuple(val.get('tronques', [])))]
            r.append(plan.visage_motion(c['plan']))
    if plaque:
        r.append(image.saturation(plaque, valides=[tuple(x) for x in val.get('saturation', [])]))
        cad = c.get('cadrage')
        res = image.cadrage(plaque, **({'yeux_cible': cad['yeux'], 'tolerance': cad.get('tolerance', 0.06)} if cad else {}))
        res.bloquant = bool(cad)
        r.append(res)
        if etape in ('motion', 'final') and os.path.abspath(plaque) != os.path.abspath(master):
            vv = [tuple(x) for x in val.get('visage', [])]
            gx = (c.get('panneau') or {}).get('gauche_px')
            # 21/11/2026 : format podcast, Lucien recadré à droite du panneau et zoomé ; contrôle sur le master lui-même.
            r.append(image.visage_panneau(master, plaque, gx, valides=vv) if gx else image.visage(master, plaque, valides=vv))
    if s['audio']:
        r.append(son.niveau(master))
        r.append(son.silences(master))
    else:
        r.append(Resultat('piste audio', False, detail='aucune piste audio dans le master'))
    sn = c.get('son') or {}
    if sn.get('musique') and sn.get('voix'):
        # 10/11/2026 : écart validé par Lucien pour un chantier (« le piano moins fort », violon 20 LU sous la voix).
        e = val.get('musique_ecart')
        r.append(son.musique(sn['musique'], sn['voix'], *(e or ())))
    if sn.get('dossiers_bruitages'):
        r.append(son.fichiers(sn['dossiers_bruitages']))
    k = c.get('coupes') or {}
    if etape != 'plaque' and k.get('images_master'):
        r.append(voix.duree(master, int(k['images_master'])))
    if k.get('raccords_auto_s') or k.get('raccords_lucien_s'):
        r.append(voix.raccords(master, k.get('raccords_auto_s', []), k.get('raccords_lucien_s', [])))
    # 25/10/2026 : les fichiers de mots du chantier passent le lexique (Claude, ChatGPT, ScalAI, n8n).
    if c.get('mots'):
        r.append(texte.lexique(c['mots']))
    v = c.get('voix') or {}
    if v.get('phrases_attendues'):
        t = open(v['transcription_master']).read() if v.get('transcription_master') else voix.transcrire(master)
        r.append(voix.phrases(t, v['phrases_attendues']))
    if c.get('remotion') and os.path.isdir(c['remotion']):
        r.append(source.polices(c['remotion'], c.get('polices') or ['Helvetica Neue']))
        r.append(source.modeles(c['remotion'], acceptes=tuple(val.get('modeles', []))))
        r.append(source.liens(c['remotion']))
    cp = c.get('copie') or {}
    if cp.get('reference') and etape in ('motion', 'final'):
        if cp.get('correspondance'):
            r.append(copie.par_placement(master, cp['reference'], cp['correspondance'], seuil=cp.get('seuil_placement', 0.14),
                                         dossier=os.path.splitext(master)[0] + ' - placements', valides=tuple(val.get('placements', []))))
            if plaque:
                r.append(copie.halo_sombre(master, plaque, cp['correspondance'], valides=tuple(val.get('halo', []))))
        else:
            r.append(copie.superposition(master, cp['reference'], seuil=cp.get('seuil', 0.08), planche=planche,
                                         valides=[tuple(x) for x in val.get('superposition', [])]))
    return r


def envoyer(fichier, url):
    """PUT en HTTP/1.1 avec reprises (502 en HTTP/2 les 16-17/10). curl --fail échoue sur toute réponse en erreur."""
    subprocess.run(['curl', '--http1.1', '--fail', '-sS', '--retry', '4', '--retry-all-errors', '-T', fichier, url],
                   check=True, stdout=subprocess.DEVNULL)
    return True


def ecrire_etat(local, url, lignes):
    if not local:
        return
    with open(local, 'a') as f:
        f.write('\n'.join(lignes) + '\n')
    if url:
        try:
            envoyer(local, url)
        except subprocess.CalledProcessError:
            print("état non envoyé (le guet ne le verra pas)", file=sys.stderr)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('master')
    p.add_argument('--chantier', required=True)
    p.add_argument('--put')
    p.add_argument('--plaque')
    p.add_argument('--etat-local')
    p.add_argument('--etat-put')
    p.add_argument('--planche-put')
    p.add_argument('--extra', action='append', default=[])
    p.add_argument('--quarantaine')
    p.add_argument('--sec', action='store_true')
    a = p.parse_args()
    if not a.sec and not a.put:
        p.error('--put obligatoire hors --sec')
    if a.quarantaine and '/quarantaine/' not in a.quarantaine.split('?')[0]:
        p.error('--quarantaine doit viser un dossier quarantaine/ (jamais rapatrié sur le Mac)')
    c = json.load(open(a.chantier))
    nom = os.path.basename(a.master)
    horo = time.strftime('%H:%M', time.gmtime()) + ' UTC'
    fautes = ch.valider(c)
    if fautes:
        lignes = [f"- {horo} ÉCHEC chantier {nom} : {f}" for f in fautes]
        print('\n'.join(lignes))
        if not a.sec:
            ecrire_etat(a.etat_local, a.etat_put, lignes)
        sys.exit(1)
    planche = os.path.splitext(a.master)[0] + ' - superposition.jpg'
    res = controles(a.master, c, a.plaque, planche if (c.get('copie') or {}).get('reference') else None)
    echecs = [r for r in res if not r.ok and r.bloquant]
    rapport = {'master': nom, 'etape': c['etape'], 'ts': time.time(),
               'resultats': [{'nom': r.nom, 'ok': r.ok, 'bloquant': r.bloquant, 'detail': r.detail, 'defauts': r.defauts} for r in res]}
    json.dump(rapport, open(os.path.splitext(a.master)[0] + ' - controles.json', 'w'), ensure_ascii=False, indent=1, default=str)
    for r in res:
        print(r.ligne())
    if echecs:
        lignes = [f"- {horo} ÉCHEC contrôles {nom} ({len(echecs)}/{len(res)}) : rien n'est livré."] + \
                 [f"  - {r.ligne()}" for r in echecs]
        if not a.sec and a.quarantaine:
            envoyer(a.master, a.quarantaine)
            lignes.append("  - Master gardé en quarantaine (non livré) : une routine peut relancer livrer sans refaire le rendu.")
        if not a.sec:
            ecrire_etat(a.etat_local, a.etat_put, lignes)
        sys.exit(1)
    if a.sec:
        print(f"contrôles OK ({len(res)}), aucun envoi (--sec)")
        return
    envoyer(a.master, a.put)
    if a.planche_put and os.path.exists(planche):
        envoyer(planche, a.planche_put)
    for e in a.extra:
        f, url = e.split('=', 1)
        envoyer(f, url)
    alertes = [r for r in res if not r.ok]
    ecrire_etat(a.etat_local, a.etat_put,
                [f"- {horo} LIVRÉ {nom} : contrôles OK ({len(res) - len(alertes)}/{len(res)})"] +
                [f"  - {r.ligne()}" for r in alertes])
    print('livré')


if __name__ == '__main__':
    main()
