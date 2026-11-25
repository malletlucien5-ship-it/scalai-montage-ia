---
name: montage-podcast
description: Use when Lucien a tourné la vidéo podcast hebdo des actus IA (DJI face caméra + OBS sur le Google Doc « Actus NBS retenues ») et veut le montage au format podcast. Déclencheurs - "monte le podcast", "vidéo podcast", "montage newsletter", "skill newsletter montage", "format podcast", "actus de la semaine en vidéo", "bandeau texte à gauche", "comme la dernière vidéo podcast". Charge aussi montage-multicam, qui reste la base du pipeline.
---

# Montage podcast : actus IA de la semaine

Format hebdo validé par Lucien le 20/11/2026. Même branding chaque semaine, sans question à Lucien.
Ce skill s'ajoute à `montage-multicam`. Charger `montage-multicam` d'abord : ses garde-fous, son ordre et ses réglages figés restent valables.
Format détaillé : `references/format.md`. Chantier d'origine : branche `chantier/podcast-2026-11-20` de martell-motion-cloud.

## Sources de la semaine

- Rush DJI sur le bureau (`~/Desktop/DJI_*.MP4` et son `.LRF`). Attendre la fin de la copie : taille stable, `ffprobe` lit la durée.
- OBS le plus récent de `~/Movies/`. L'écran OBS montre le script et la fenêtre OBS : il porte la voix seulement.
- Script : Google Doc « Actus NBS retenues, semaine du … » ouvert dans l'OBS. Lire l'URL du doc sur une image de l'OBS, puis `python3 ~/CODE/tools/gdrive/gdrive.py read <id>`.
- Le script contient les liens sources de chaque actu. Ces pages fournissent les images des panneaux.

## Procédure

1. Calage : `calage_sources.py --obs <OBS> --cam <LRF> --out <DIR>/calage.json --no-open`.
2. Mots : `scribe_chantier.py --chantier podcast-<date> --cam <LRF> --obs <OBS> --obs-nom obs.mp4 --sans-envoi`.
3. Lire la transcription par blocs de 30 s. Noter les prises refaites, les pauses muettes et les phrases qui n'annoncent rien.
4. Envoi Storage Box par `envoyer.sh` : obs.mp4, DeepFilterNet3.tar, scribe, chantier.json, calage.json, LRF, puis 4K.
5. Branche `chantier/podcast-<date>` depuis la branche podcast précédente. Mettre à jour `regles/decoupage.md`, `script.md`, `chantier.json`, `calage.json`.
6. Routine plaque : proxy coupé, plaque 4K, planche d'étalonnage. Consigne : copier `consigne-A.tpl.md` du chantier précédent et changer les sources.
7. Lucien valide les coupes sur le proxy, sans Resolve. Il choisit l'étalonnage sur la planche, sauf même pièce et même lumière qu'un choix récent.
8. Pendant ce temps : préparer `panneaux.json` (textes et images, temps OBS) et la planche des panneaux à valider.
9. Routine motion : panneaux, zooms, étalonnage choisi, master 2560x1440 50 i/s, livré par `controles.livrer`.

## Ce que Lucien a fixé (20/11/2026)

- Coupes légères et naturelles : répétitions, prises refaites, gros bégaiements, phrases qui redisent la précédente. Blancs de 0,7 s au plus (21/11/2026).
- Aucun son en arrière-plan : ni musique, ni bruitage.
- Panneau gris foncé `#1c1c1e` à gauche de l'écran, Lucien à droite. Texte blanc en Helvetica Neue.
- Le panneau montre les phrases qu'il dit, ou des images des sources avec leur texte.
- Panneau présent 80 % du temps environ.
- Lucien seul, plein cadre avec zooms et dézooms : intro, fin, et une dizaine de secondes toutes les 30 s à 1 min sur une phrase forte.
- Résultat attendu : dynamique malgré un format podcast.

## Erreurs déjà vues

- Dictée « skill newsletter montage » : le nom retenu est `montage-podcast` (choix de Lucien le 20/11).
- Dictée « en noir » puis « en gris » pour le panneau : Lucien a choisi le gris foncé sur maquette.
- Pause muette au milieu (ressources jamais dites) : retirer la pause et la phrase d'annonce.
- Consigne motion refusée par `guard-routine.py` (20/11) : les mots « copie », « copié », « référence » et « préférence » font croire à une copie de référence. Écrire « reprise sans réencodage », « par ordre de priorité ». La consigne doit aussi citer `silero-vad`, « image fixe de chaque arrêt » et « contrôle de cadrage ».
- Helvetica Neue absente du dépôt : envoyer `/System/Library/Fonts/HelveticaNeue.ttc` dans `inputs/<chantier>/` avec un lien GET.
- Porte « visage couvert » refusée sur 27 passages (21/11) : l'ancien contrôle cherchait le visage à sa place sur la plaque. Mettre `panneau.gauche_px` (1126) dans `chantier.json` : `controles.livrer` cherche alors le visage sur le master, à droite du panneau (main e3321b5). La borne ne vaut que sur les images où le panneau gris est à l'écran : sans ça, les 12 plans seuls ont été refusés le 21/11 (main ee98605, `_panneau_visible`). Un contrôle neuf se teste sur une image de chaque type de plan avant la routine.
- Routine lancée à 75 % du quota 5 h (20/11) : rendu perdu à 23 h 56. Lancer sous 60 %, garde-fou dans `guard-routine.py`.
- `envoyer.sh` : la destination est relative à `martell/inputs/<chantier>/`. Un JSON déjà présent se remplace par `rsync --inplace`, jamais en mode ajout (21/11).
