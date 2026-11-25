---
type: skill-reference
date: 2026-10-02
status: active
tags: [skill, montage-multicam, clipper]
project: youtube
---

Lire pour produire des clips ou des Shorts depuis les sources originales, gérer le cache multi-prises, les creux silencieux et les commandes intégrées.

## Clips depuis les sources originales, ajout du 13 septembre 2026

Lucien fait ses coupes manuelles dans Resolve.
Après ses coupes, reconstruire le montage depuis les rushs et lui présenter le résultat.
Après son acceptation explicite de la version finale du long format, proposer « Préparer les Shorts ».
Attendre un accord distinct avant toute sélection, adaptation ou génération de Shorts.
Un statut technique prêt ou livré ne vaut aucune de ces deux décisions.
Une nouvelle révision du long format invalide les accords de la version précédente.
Un test technique demandé peut précéder cette approbation.
La publication reste soumise à une demande explicite.

## Parcours serveur des Shorts depuis le 9 octobre 2026

La page propriétaire réside sur `<webhook-de-lucien>`.
Les accès figurent dans la fiche infra `115-martell-shorts.md`.
Aucun onglet ne s’ouvre sans demande de Lucien.
Les décisions peuvent être relayées depuis cette conversation.

Sur `ssh prod`, lire l’état avec :

```bash
/opt/martell-shorts/venv/bin/python /opt/martell-shorts/control/shorts_service.py etat --no-open
```

Après acceptation explicite du long format, enregistrer `decider accepter`.
Fournir le projet et la version affichée par `etat`.
Fournir `--revision` avec l’empreinte exacte.
Fournir `--preuve` avec la date et le message humain exact.
Proposer ensuite « Préparer les Shorts » puis attendre sa réponse.
Avant de transmettre cet accord, actualiser l’accès abonnement depuis le Mac :

```bash
python3 ~/CODE/martell-shorts-acceptation-20261009/cloud/shorts_connexion.py --no-open
```

Cette commande transfère le jeton d’accès existant sans afficher sa valeur.
Les secrets de renouvellement restent sur le Mac.
L’accord distinct utilise `decider preparer` avec les mêmes références.
Un report utilise `decider plus-tard`.
Les commandes exigent `--no-open`.

Le paquet Shorts porte toujours `branding: {profile: clipper-classic, version: 1}`.
La police des sous-titres est Helvetica Neue Bold 88, asset `font-captions` = `HelveticaNeue-Bold.ttf`.
Ne jamais recopier le branding d'un autre paquet : le service refuse tout autre profil (10/10/2026).
Opus 5.5 prépare les métadonnées et adapte les animations.
Le serveur sélectionne avec le Clipper actuel de Lucien sur Claude Code CLI (abonnement Max, Opus 5.5).
Le code et les prompts proviennent de `~/CODE/clipper`.
Jev contrôle chaque candidat et journalise les probabilités.
Les seuils restent 0,85 et 0,55.
`shorts_connexion.py --no-open` synchronise le code et les paramètres avant l’accord de préparation.
Il reprend le moteur déployé sur prod et rafraîchit seulement les pièces du Clipper.
Il refuse toute modification du moteur et tout Clipper qui ne sélectionne pas avec Claude Code.
Une empreinte verrouille la stack pour le paquet exact.
Une preuve signée autorise le worker à utiliser cette sélection.
Le manifeste refuse `clips_json` et toute liste manuelle.
Une portée insuffisante arrête le lot avant toute troncature.
`youtube_upload.py` réserve les Shorts au parcours propriétaire signé.
Les rendus utilisent un worker Hetzner temporaire.
Les demandes d’adaptation restent liées à la révision acceptée.
Les caches survivent à une adaptation interrompue.
`relancer --lot ID --no-open` reprend un lot après correction de son obstacle.

La validation explicite du lot utilise `approuver-lot`.
Fournir `--lot`, `--lot-hash`, `--source-video-id` et `--related-video-id`.
Fournir également `--preuve` et `--no-open`.
La vidéo associée suit la demande de Lucien.
La publication exige une liaison YouTube Studio relue avant programmation.
Une nouvelle révision invalide les accords précédents.

Un accès Claude, Jev ou Studio manquant arrête explicitement le lot.
Claude Code CLI sur le compte Max fait la sélection ; Codex n’est plus utilisé depuis le 18/10/2026.
Opus utilise l’abonnement Claude pour les sources et les adaptations.
Le repli vers une API de génération payante reste désactivé.
Le contrat éditorial réside dans `/opt/martell-shorts/control/CONTRAT-EDITORIAL.md`.

## Sound design et musique des Shorts, 18 octobre 2026

Chaque nouveau lot sort avec son sound design complet.
Les Shorts déjà programmés restent inchangés.
Le moteur pose un whoosh à chaque changement de mode et un shutter à chaque coupe de prise.
Les bruitages des animations du long format arrivent par les `sfx_events` des scènes.
Le contrôleur les extrait seul avec `extraire_sfx.py auto`, sur un worker Hetzner temporaire.
Un long format mixé hors Remotion fournit ses cues dans `donnees/sons.json`.
Un long format mixé dans Remotion passe par la trace audio de la composition.
Chaque son garde sa licence dans `sfx_licences.json`.
Un son sans licence arrête la préparation.

La musique de fond vient d'Epidemic Sound, choisie par Lucien.
La bibliothèque réside dans `bibliotheque-musique-shorts/manifeste.json` sur la Storage Box.
Son schéma est `martell.musique-shorts/2`, avec un pool `ab-test` et un pool `humain`.
Le pool `ab-test` contient CHECKMATE, Out of Order et DOX Pt. II depuis le 18/10/2026.
Pour ajouter un morceau, déposer le WAV et ajouter sa ligne avec son SHA-256.
Jev juge si chaque clip relève du registre humain, avec les seuils 0,85 et 0,55.
Sous le seuil, le clip va dans le pool `ab-test` et il est signalé.
Le pool `ab-test` répartit ses morceaux à parts égales sur le lot.
Deux Shorts consécutifs ne reçoivent jamais le même morceau.
Le journal `/var/lib/martell-shorts/musique/ab-test.jsonl` relie chaque morceau au `video_id`.
Ce journal sert à comparer vues, rétention et swipe par morceau.

Le profil `martell-sobre@2` règle le mix.
La musique joue 24 LU sous la voix après ducking.
Le contrôle qualité exige entre 21 et 27 LU.
Le morceau démarre au premier instant audible, sans intro silencieuse.
Un fondu ouvre et ferme la musique.
Aucun son ne joue dans une portion muette.
Les bruitages restent au moins 9 dB au-dessus de la musique.
Chaque `qa.json` porte les mesures `music_*` et `sfx_sur_musique_db`.

Les rendus des Shorts passent dans une routine cloud Claude Code, sur le compte Max.
Le moteur vient de la branche `chantier/shorts-cloud`, les données de la Storage Box.
Les liens signés restent dans la consigne de la routine.
Hetzner sert seulement de repli explicite, avec `SHORTS_RENDU=hetzner` et un motif.
Prod lance lui-même ses routines avec la session claude.ai root de Lucien.
La routine adapte elle-même les variantes verticales, puis prod publie l'archive motion.
Après une resynchronisation du sélecteur sur prod, recopier le moteur dans `shorts-moteur/`.

## Périmètre

Inventorier tous les fichiers caméra et écran fournis.
Annoncer les fichiers inclus et leur durée totale avant le rendu.
Une vidéo peut contenir plusieurs prises séparées si Lucien veut les assembler.
Confirmer leur association par le contenu et la corrélation audio.
Présenter distinctement la durée retirée par les coupes et celle gagnée par la vitesse.
Un test sur un seul rush doit porter cette indication dans le compte rendu.
Réserver le nom `montage.mp4` au rendu qui passe le contrôle de complétude.
Le contrôle exige tous les chemins caméra annoncés dans le même ordre.
Rapporter la durée source totale et la durée conservée après auto-edit.
Une forte réduction reste acceptable si chaque rush figure dans la table.
Lucien effectue ensuite les reprises et hésitations subtiles dans Resolve.

`build_source_plan.py --preserve-full --speed 1` sert seulement quand Lucien demande un assemblage sans coupes temporelles.
Le montage Resolve habituel conserve les coupes automatiques de silences et fillers.

## Synchronisation avec coupes indépendantes

Outil : `~/CODE/auto-edit/tools/sync_discontinuous.py`.
Fournir les pistes audio caméra et écran avec `--cam`, `--screen` et `--out`.
Le calcul associe des fenêtres audio puis valide les portions continues avec des mesures intercalées.
Le rapport fournit `regions`, `points`, `validation` et `covered_seconds`.
Chaque région contient un offset et une dérive propres.
Les passages sans correspondance fiable restent en plan visage.
Les ruptures de synchronisation restent explicites dans la table des sources.

Le VPS assure les calculs prolongés par défaut.
Le 13 septembre, Lucien autorise le moteur vidéo matériel du Mac pour ce run.
Le serveur HTTP `media_range_server.py` sert uniquement les chemins déclarés sur localhost.
Son accès distant passe par un tunnel SSH privé.
Utiliser `--no-open` et fermer ces processus après leur usage.

## Table des sources

`montage.sources.json` accompagne `montage.mp4`.
`montage.words.json` contient les mots recalés sur le montage.
Conserver ces fichiers avec les rushs pour reprendre les coupes.

Le format `source-timeline` version 1 contient une cadence et une liste `chunks`.
Chaque portion porte son nombre de frames et son layout `face` ou `split`.
Les champs `camera` et `screen` portent le chemin et les secondes source `start` et `end`.
La découpe conserve l'ordre et les répétitions des passages.
Une seconde passe Resolve se compose sur la table du média actuellement utilisé.

Outils :

- `auto-edit/tools/transcribe_cpu.py` : transcription Whisper et VAD ONNX sur serveur CPU.
- `auto-edit/tools/build_source_plan.py` : plan depuis transcription et synchronisation validée.
- `clipper/clipper/source_media.py` : conversion de plan multicam, coupes et rendu depuis les rushs.
- `pipeline.py cuts` : reprise des coupes dans la table quand le fichier adjacent existe.
- `clipper/scripts/source_preview.py` : aperçu réel avec les sous-titres du clipper.

Le rendu horizontal brut nécessite ensuite le traitement audio habituel `auto_edit.polish_audio`.
La table doit conserver exactement le même nombre de frames que le média approuvé.

## Format vertical

Les moments `split` prennent la caméra originale en haut et la capture écran originale en bas.
Le cadrage caméra reste large et fixe.
Les moments `face` utilisent un cadrage vertical directement dans le rush caméra.
Le clipper récupère les changements de plan depuis la table du montage.
Il conserve sa sélection de moments et ses effets habituels.
Les sous-titres passent dans la zone basse pendant les plans visage.

Géométrie testée : 1080 × 1920 à 50 fps.
La caméra occupe 666 pixels et l'écran 1254 pixels.
Lucien valide ce format sur les 17 clips Astra le 15 septembre 2026.
Utiliser cette géométrie par défaut pour les prochains lots depuis les sources originales.
Cette valeur vient de la référence affichée.
Le fichier temporaire original reste protégé : sa mesure native exacte reste à confirmer.
Le champ `vertical.camera_height` permet cet ajustement.
Lucien délègue le choix du cadrage écran : conserver l'écran entier avec un fond flouté.

Le clipper détecte automatiquement le fichier adjacent `.sources.json`.
Les options `--source-manifest` et `--source-map` permettent un chemin explicite ou un accès distant.
Les mots du fichier adjacent `.words.json` évitent une nouvelle transcription.
Les huit tests de `clipper/tests/test_source_media.py` vérifient les coupes et les raccords.
Vérifier aussi le nombre de frames et les durées audio et vidéo du rendu réel.

## Cache et rendu de plusieurs prises

Le cache d'une portion dépend seulement des fichiers utilisés par cette portion.
L'ajout d'un rush ne doit plus invalider les prises déjà rendues.
`source_media.py --workdir` accepte un cache partagé.
Les rendus parallèles doivent traiter des groupes de portions disjoints.
Deux processus ne doivent jamais écrire la même portion temporaire.
Chaque sortie utilise sa propre liste de concaténation dans le cache partagé.

## Petits creux silencieux et coupes Resolve, 14 septembre 2026

Lucien demande de retirer les creux presque muets de 0,13 à 0,25 seconde.
La durée seule ne suffit jamais pour supprimer une portion.
Un mot court peut occuper une portion courte.
Une frontière de layout peut aussi produire une portion d'une seule frame.

`auto-edit/tools/quiet_cleanup.py` mesure le RMS sur des fenêtres de 10 ms.
Le seuil conservateur vaut -55 dBFS.
Les creux admissibles durent entre 0,13 et 1 seconde.
Chaque retrait conserve 20 ms à chaque bord.
La quantification arrondit vers l'intérieur du silence.
Les centres de mots portent une protection supplémentaire de 25 ms.
Les pauses plus longues restent sous le contrôle du VAD et des coupes manuelles.

`build_source_plan.py` et `multicam.detect_segments_multicam` appliquent ce contrôle avant le rendu.
Dans multicam, appliquer ce contrôle après la fusion des pauses courtes.
Une fusion ultérieure pourrait restaurer les silences retirés.

Pour Resolve, sauvegarder la base avec l'API SQLite backup depuis une connexion en lecture seule.
Vérifier la piste, le média et les bornes de chaque portion.
Conserver exactement les portions manuelles dans leur ordre.
Utiliser `quiet_cleanup.refine_kept` pour soustraire les creux et contrôler les nouveaux raccords.
Ne jamais restaurer une marge supprimée manuellement.
`pipeline.py cuts` utilise cette passe quand la transcription adjacente existe.

Après le rendu, exécuter :

```bash
/usr/bin/python3 ~/CODE/auto-edit/tools/quiet_cleanup.py \
  --video VIDEO.mp4 --words VIDEO.words.json --out quiet-audit.json --no-open
```

La commande échoue quand des creux admissibles restent présents.
`pipeline.py verify` applique également ce contrôle si la transcription existe.
Conserver le rapport avec la table des sources.
Comparer aussi le nombre de mots avant et après le nettoyage.

Pour réutiliser un master existant, conserver son nombre de canaux et son niveau.
Une conversion mono vers stéréo peut atténuer chaque canal de 3 dB.
Éviter une nouvelle passe d'amélioration vocale sur un master déjà traité.
L'option `denoise=False` désactive maintenant DeepFilterNet, le gate VAD et `afftdn`.
L'égalisation et la normalisation gardent leurs réglages propres.
Le modèle du nouveau micro et l'amélioration visée restent à confirmer avec Lucien.

Commandes intégrées du 15/09 : `commandes.md`.
