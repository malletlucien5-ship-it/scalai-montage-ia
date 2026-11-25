#!/usr/bin/env python3
"""chantier.json : l'état d'un chantier de montage, validé avant chaque rendu et chaque livraison.

Remplace les règles écrites « plaque brute d'abord », « coupes de Lucien à la lettre », « étalonnage choisi sur planche »,
« voix OBS » et « copie : inventaire de la référence ». Récidives des 06, 07, 10, 13, 14, 15 et 18/10.

Usage : python3 -m controles.chantier chantier.json [--etape motion]   (code 1 si invalide)

Champs (voir controles/LISEZMOI.md pour un exemple complet) :
  nom, type (youtube | pub | short | copie | faq), etape (plaque | sobre | motion | final)
  rushs [{nom, sha256}]                       rushs choisis, figés
  voix {source, obs_disponible, phrases_attendues[], transcription_master}
  coupes {source (edl | fcpxml | aucune), fichier, sha256, cadence, images_master, par_lucien,
          raccords_lucien_s[], raccords_auto_s[]}
  etalonnage {choisi, choisi_par_lucien, base_gain, controle_ok}
  copie {reference, inventaire[], seuil, correspondance, revue {id: conforme}, apercu_valide_par_lucien, meme_timeline}
                                              obligatoire pour type copie à partir de motion
  elements_valides []                          liste blanche validée par Lucien, obligatoire à partir de motion
  polices [], cadrage {yeux, tolerance}, son {musique, voix, dossiers_bruitages[]}, remotion, valides {}
  plan, arrets {board, encres, manifeste, source}   obligatoires dès qu'un plan du moteur porte des arrêts board"""
import glob, hashlib, json, os, sys

ETAPES = ['plaque', 'sobre', 'motion', 'final']


def _corr(x):
    if isinstance(x, str):
        return json.load(open(x)) if os.path.exists(x) else []
    return x or []


def porte_arrets(plan):
    """Vrai si le plan (dict ou chemin) a au moins un plan board avec des arrêts."""
    if isinstance(plan, str):
        with open(plan) as fh:
            plan = json.load(fh)
    return isinstance(plan, dict) and any(p.get('etat') == 'board' and p.get('arrets') for p in plan.get('plans', []))


def valider(c, etape=None):
    etape = etape or c.get('etape')
    f = []
    if etape not in ETAPES:
        return [f"etape inconnue : {etape!r} (attendu : {', '.join(ETAPES)})"]
    if not c.get('nom'):
        f.append("nom manquant")
    if not isinstance(c.get('rushs'), list) or not c['rushs']:
        f.append("rushs manquants : liste des rushs choisis, avec leur sha256 (mauvais rush pris sur Marvin le 16/10)")
    elif any(not r.get('sha256') for r in c['rushs'] if isinstance(r, dict)):
        f.append("chaque rush doit porter son sha256")
    v = c.get('voix') or {}
    if v.get('obs_disponible') and v.get('source') != 'obs':
        f.append("un OBS existe : voix.source doit valoir « obs » (audio caméra le 03/10)")
    if ETAPES.index(etape) >= 1:
        k = c.get('coupes') or {}
        if not k.get('par_lucien'):
            f.append("coupes.par_lucien absent : aucun rendu sobre, motion ou final avant les coupes de Lucien (18 rendus jetés le 14/10)")
        if k.get('source') not in ('edl', 'fcpxml', 'aucune'):
            f.append("coupes.source doit valoir edl, fcpxml ou aucune (validé sans coupe par Lucien)")
        if k.get('source') in ('edl', 'fcpxml'):
            for champ in ('sha256', 'cadence', 'images_master'):
                if not k.get(champ):
                    f.append(f"coupes.{champ} manquant (EDL lue à la mauvaise cadence les 02 et 06/10)")
            if k.get('fichier') and os.path.exists(k['fichier']) and k.get('sha256'):
                if hashlib.sha256(open(k['fichier'], 'rb').read()).hexdigest() != k['sha256']:
                    f.append("le fichier de coupes a changé depuis chantier.json : une EDL plus récente existe (06/10)")
        e = c.get('etalonnage') or {}
        if not (e.get('choisi') and e.get('choisi_par_lucien')):
            f.append("etalonnage.choisi_par_lucien absent : Lucien choisit sur la planche avant tout rendu (13 et 15/10)")
        if e.get('base_gain') and e.get('controle_ok') is not True:
            f.append("base de gain sans controle_ok vrai : interdite (deux rendus de 48 min perdus le 15/10)")
    if ETAPES.index(etape) >= 2:
        if not isinstance(c.get('elements_valides'), list):
            f.append("elements_valides manquant : liste blanche des éléments validés par Lucien (ajouts non demandés le 14/10)")
        if not c.get('plan') and c.get('remotion'):
            plans = glob.glob(os.path.join(c['remotion'], 'plan', '*.json'))
            if any(porte_arrets(x) for x in plans):
                f.append("le moteur porte un plan à arrêts : plan et arrets obligatoires (viral X v4 : aucun contrôle de ce qui se voit, 01/11/2026)")
        if c.get('type') == 'copie':
            cp = c.get('copie') or {}
            if not cp.get('reference') or not cp.get('inventaire'):
                f.append("copie.reference et copie.inventaire obligatoires : mesurer la référence avant la v1 (30/09, 13/10, 18/10)")
            if not cp.get('meme_timeline') and not cp.get('correspondance'):
                f.append("copie.correspondance obligatoire : chaque placement relié à sa plage de la référence "
                         "(IA entreprise livrée sans comparaison à Yas, 26/10/2026)")
            # 15/11/2026 : correspondance au format placements ({ref: "A01", t, fin}) : livrer plantait (TypeError)
            # après le décodage du master. Le format se vérifie ici, avant tout calcul.
            if isinstance(cp.get('correspondance'), (str, list)):
                try:
                    mal = [p.get('id', '?') for p in _corr(cp['correspondance'])
                           if not (isinstance(p.get('ref'), list) and isinstance(p.get('copie'), list) and len(p['ref']) == len(p['copie']) == 2)]
                except Exception as e:
                    mal = [f'illisible ({type(e).__name__})']
                if mal:
                    f.append(f"copie.correspondance au mauvais format : chaque entrée {{id, mode, ref: [début, fin] s, copie: [début, fin] s}} "
                             f"({len(mal)} fautive(s) : {', '.join(map(str, mal[:5]))})")
            if etape == 'final':
                if cp.get('apercu_valide_par_lucien') is not True:
                    f.append("copie.apercu_valide_par_lucien absent : aucun rendu final avant l'accord de Lucien sur l'aperçu motion (26/10/2026)")
                ids = [p['id'] for p in _corr(cp.get('correspondance'))]
                revue = cp.get('revue') or {}
                # « accepte_par_lucien » : écart restant que Lucien a vu sur l'aperçu et accepté (26/10/2026).
                manque = [i for i in ids if revue.get(i) not in ('conforme', 'accepte_par_lucien')]
                if manque:
                    f.append(f"copie.revue : {len(manque)} placement(s) sans « conforme » ni « accepte_par_lucien » après revue de leur planche ({', '.join(manque[:6])})")
    return f


def main():
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    c = json.load(open(a[0]))
    etape = a[a.index('--etape') + 1] if '--etape' in a else None
    f = valider(c, etape)
    for x in f:
        print('ÉCHEC chantier :', x)
    print('chantier valide' if not f else f'{len(f)} défaut(s)')
    sys.exit(1 if f else 0)


if __name__ == '__main__':
    main()
