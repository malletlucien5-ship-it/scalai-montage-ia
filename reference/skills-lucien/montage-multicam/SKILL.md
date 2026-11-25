---
name: montage-multicam
description: Use when Lucien has recorded a talking-head video with the DJI camera (one or more DJI_*.MP4 parts) and an OBS screen recording (~/Movies/YYYY-MM-DD HH-MM-SS.mp4) and wants the edited YouTube video, or wants cuts made in a DaVinci Resolve project reapplied to a new render. Also use when Lucien wants long videos sent to the freelance editor Ruben (S3 upload, proxy, YouTube reference). Triggers - "monte la vidéo", "assemble webcam et écran", "fais le montage", "applique mes cuts Resolve", "carré webcam", "auto edit multicam", "envoie à Ruben", "montage Ruben", "envoie les rushs au monteur", "prépare le proxy".
---
# Montage multicam webcam + écran

## Garde-fous automatiques (20/10/2026)

La machine vérifie les règles ci-dessous. Un refus donne la cause et la date de l'incident.

- `~/.claude/hooks/guard-routine.py`, à la création d'une routine : liens GET vivants, état en PUT, quota Max lu, préflight des comptes. Appeler `mcp__ccd_session_mgmt__get_usage` avant de créer la routine.
- Le même hook exige `chantier.json` valide et une livraison par `controles.livrer` pour tout livrable sobre, motion ou final. Il inscrit la routine au guet.
- `~/.claude/hooks/guard-calcul.py` : aucun Whisper, rendu ou encodage sur le Mac, aucune clé API, voix OBS.
- Guet de prod : il suit chaque routine et écrit ses alertes, sans aucun message à Lucien. Consulter `guet etat` et traiter chaque ALERTE soi-même. Ne jamais interroger RemoteTrigger en boucle.
- `guard-routine.py` exige aussi `~/.local/share/montage-<chantier>/calage.json` produit par `scripts/calage_sources.py`. Chaque rush nommé dans la consigne doit y être calé, tous sur le même OBS (08/11/2026).
- `guard-routine.py` exige `tools/audit_mots_perdus.py` (code 0 avant livraison) dans toute routine qui coupe une voix. Coupes admises : silences, bégaiements, prise refaite entière, phrase inachevée redite. Jamais un mot retiré au milieu d'une phrase gardée, jamais une fin de prise laissée (09/11/2026, plaque cabinets v2).
- `guard-routine.py` refuse une première routine (proxy de coupe depuis des rushs DJI) qui ne cite pas les LRF. Sans LRF sur la carte, écrire « LRF absents » dans la consigne (10/11/2026).
- `guard-routine.py` exige des liens PUT `stems/` dans toute routine qui mixe un son et livre. Pistes : `stems/voix.wav`, `stems/musique.wav`, `stems/bruitages.wav`. Une retouche de son repart de ces pistes et reprend l'image en `-c:v copy`. Elle ne repolit jamais la voix (10/11/2026, v3 cabinets : 35 min et une panne mémoire pour baisser un violon).
- `guard-routine.py` exige `python3 -m controles.tranche` dans toute routine de tranche (main 2ba3f5d). Le contrôle écrit ses alertes en images du master et une planche. Montrer chaque alerte à Lucien avant l'assemblage, puis inscrire l'exception validée dans `chantier.json` (09/11/2026 : final en quarantaine à 23 h 25, Lucien couché).
- `salle-projection.py` signale aussi un master présent sur le serveur sans carte dans la Salle. La carte part dès que `controles.livrer` passe, avant le message « livrée ». Ajouter ensuite le nom du fichier au registre (10/11/2026).
- `guard-routine.py` exige `AE_WORDS_FILE` et `AE_SEG_WORDS` dans toute routine qui lance `plan` : mots ElevenLabs Scribe v3 produits avant la routine par `scripts/scribe_chantier.py --chantier <nom> --cam <LRF…> --obs <OBS>` (dépôt Storage Box `inputs/<nom>/scribe/`, liens GET dans la consigne). Code dans `auto-edit` des branches de chantier depuis 85c4c63 (14/11/2026 : plus d'une heure de transcription sur CPU par routine).
- `controles/` sur `main` de martell-motion-cloud : `python3 -m controles.livrer` est la seule porte de livraison. Mode d'emploi : `controles/LISEZMOI.md`.

## Ordre fixe (vérifié par chantier.json)

1. Première routine : proxy 540x960 avec compteur d'images, plaque brute, planche d'étalonnage. Rien d'autre.
   Envoyer d'abord les fichiers LRF de la DJI : une copie 1280x720 par rush, environ 1,4 Go.
   Le proxy de coupe se rend depuis les LRF. Les rushs 4K partent ensuite pour la planche et le rendu final.
   Mesure du 09/11/2026 : proxy livré en 30 min depuis les LRF, contre une nuit depuis la 4K.
2. Assets motion en parallèle, sans rendu final.
3. Lucien coupe dans Resolve et choisit l'étalonnage. `chantier.json` l'enregistre : `coupes.par_lucien`, `etalonnage.choisi_par_lucien`.
4. Sobre, motion puis final, livrés par `controles.livrer`.

## Règles que la machine ne vérifie pas

- Couverture caméra/OBS : seulement depuis `calage.json` (`scripts/calage_sources.py`, GCC-PHAT sur l'audio). Jamais depuis les noms ni les dates des fichiers DJI : la carte écrit avec l'horloge DJI, fausse. Un rush calé sur un autre OBS est une prise d'essai : demander à Lucien avant de l'inclure (08/11/2026).

- Avant la première consigne d'une vidéo, lire `references/regles-datees.md` et `references/regles-lucien.md`.
- Aucun élément hors `elements_valides` sans planche validée par Lucien.
- Un diagnostic dit « mesuré » ou « hypothèse ». Le reproduire en headless avant toute demande de test à Lucien.
- Aucune ETA sans débit mesuré sur deux morceaux. Au-delà de 2 h, répartir le rendu en tranches parallèles.
- Toute consigne de routine demande de pousser `montage.json` et `montage.sources.json` sur sa branche dès le plan fixé, avant le rendu. Le proxy de coupe se rend avant la plaque haute définition. Sans ce plan publié, impossible d'accélérer une routine en cours (08/11/2026, proxy cabinets attendu 5 h après le lancement).
- Toute demande de Lucien hors des plages d'un contrôle (musique plus basse, page à fond noir, plan fixe) s'inscrit dans `chantier.json` `valides` avant le lancement.
- Disque d'une session cloud : 30 Go. Aucun fichier intermédiaire 4K. Lire les rushs en flux, une connexion par fichier (passerelle à 6 connexions).
- Retours dictés par Lucien avant une absence : relire chaque puce et poser la question sur tout mot douteux tant qu'il est là. Fiche `dictee-mot-absurde-phonetique`.
- Resolve reçoit un `.fcpxml` ou une EDL importable. Claude ne pilote jamais l'application.
- Shorts : deux accords distincts de Lucien, long format accepté puis « Préparer les Shorts ».

## Références

- `references/interview.md` : interview de démarrage d'un chantier.
- `references/pieges-et-reprises.md` : pièges, précisions, reprises automatiques, OBS maître.
- `references/regles-datees.md` : encadrés datés (voix OBS, look A, écran sur démos, punch-in, Shorts, Hetzner).
- `references/regles-lucien.md` : index des fiches mémoire sur le montage, les pubs et les Shorts.
- `chaine-audio.md`, `commandes.md`, `introduction.md`, `sources-et-clipper.md`, `envoi-ruben.md`.

Historique de la collaboration terminée : `references/envoi-ruben.md`. Les envois restent désactivés.

Pipeline complet dans `~/CODE/auto-edit` (`multicam.py` + `tools/pipeline.py`).
Réglages figés le 12/09/2026 et validés par Lucien. Une seule vidéo = un dossier
`~/Desktop/montage-<date>/` qui contient plan, plages, cache et sorties.

## Description YouTube automatique des vidéos longues

À chaque envoi privé d’une vidéo longue, préparer et ajouter automatiquement sa description avant de terminer la livraison.
Suivre [la procédure de description](../recreer-motion-design/references/description-youtube-longue.md).
Le rendez-vous précède LinkedIn. Ajouter les ressources annoncées et les chapitres du montage final.
Cette étape exclut les Shorts. Elle conserve le statut privé.

## Livrable attendu

`montage.mp4` : 2560x1440, 50 fps, x1.06, audio poli (chaîne auto_edit complète,
-15,76 LUFS), coupes silences + euh, changement de plan variable 4 à 10 s :

- **face** : visage plein cadre (intro, outro, quand il parle sans visuel, quand
  le script ou la fenêtre OBS est à l'écran).
- **écran** : capture d'écran complète avec le fond du bureau + carré visage
  40 % de la hauteur, coins arrondis, bas droite, marge 40 px. Verrouillé sur
  tout moment visuel (résultat affiché, image, vidéo, pricing, clés API, prompt).
- **jamais** une image du script (Google Doc) ni de la fenêtre OBS.

Vidéo pédagogique au board (09/11/2026) : l'écran domine et le visage occupe environ 20 % de la durée.
Visage plein cadre : transition entre parties, idée forte, chiffre clé, passage sans rien à montrer.
Détail dans la fiche `montage-ecran-demo-et-look-a`.

Si Lucien a un projet Resolve avec des coupes : `montage-cut.mp4` en plus.

`montage.mp4` désigne toujours le projet complet.
Il contient chaque rush caméra demandé dans son ordre chronologique.
Il associe chaque capture OBS correspondante.
Un essai partiel porte un nom explicite comme `test-rush-1.mp4`.
Un essai partiel ne remplace jamais `montage.mp4`.

## Procédure

Tout depuis `~/CODE/auto-edit/tools`, avec `/usr/bin/python3` (3.9 : torch,
faster-whisper, DeepFilterNet, OpenCV 4 installés là). Rien ne s'ouvre à l'écran.

1. **prep** : `pipeline.py prep --cam DJI_A.MP4 DJI_B.MP4 --screen "S.mp4" --out DIR`
   → sync GCC-PHAT (résidu attendu < 1 ms, confiance > 50), frames écran 1 fps,
   planches `DIR/sheets/scan_NN.jpg` (30 vignettes toutes les 6 s).
2. **Relire les planches avec Read** (12 planches pour 36 min). Noter en secondes
   ÉCRAN : (a) une ou deux vignettes de référence du script et de la fenêtre
   OBS (`fNNNNN.jpg` = seconde NNNNN-1), (b) toutes les plages visuelles.
   Ce jugement est le seul pas non automatisé. Ne pas sauter.
3. **ranges** : `pipeline.py ranges --out DIR --script-ref f00006.jpg --obs-ref f00001.jpg,f00135.jpg --split "300-365,372-400,..."`
   → contrôler les bords des plages détectées sur vignettes (contact_sheets.py
   frames DIR/work/scrframes --step 1 sur la zone douteuse). Distance script
   attendue ≤ 0.08, premier faux candidat ≥ 0.18.
4. **plan** : `pipeline.py plan --out DIR` → transcription faster-whisper (10 min
   pour 35 min d'audio), LLM layouts, DP cadence, `montage.json` + analyse.
   Exiger : « ÉCRAN sur plage interdite : [] ». Les runs > 10 s doivent contenir
   un verrou (script, OBS, plage visuelle, intro/outro).
   Pour plusieurs prises, produire un plan source par rush.
   Forcer l'intro sur le premier plan uniquement.
   Forcer l'outro sur le dernier plan uniquement.
   Fusionner ensuite les plans avec `tools/merge_source_plans.py`.
   Fournir tous les rushs via `--expect-cameras`.
   La commande doit échouer si un rush manque ou change d'ordre.
5. **Aperçu avant rendu complet** : rendre 2 segments écran depuis un JSON réduit
   (`--from-json`, `--no-polish`, `--no-clip-cache`), extraire une frame, l'envoyer
   à Lucien avec SendUserFile, attendre son OK sur taille du carré et cadrage.
6. **render** : `pipeline.py render --out DIR --background` puis attendre
   « ✓ Terminé » dans `DIR/work/render-montage.log` (8 à 12 min), puis
   `pipeline.py verify --out DIR`. Exiger Δ audio/vidéo = 0 ms et frames = plan.
   Vérifier aussi `camera_count`, `camera_paths` et `part_count` avant le rendu.
   Comparer ces champs à l'inventaire annoncé lors de `prep`.
7. **cuts** (si projet Resolve) : `pipeline.py cuts --out DIR --resolve-project NOM --media montage.mp4`
   → lit la base SQLite de Resolve (copie), rend `montage-cut.mp4`.
8. Envoyer la planche `DIR/sheets/out_00.jpg` et le récap (durée, frames, Δ).

Itération sur un cadrage ou une taille : éditer `montage.json` (indenté, passer
par json.load, jamais sed) puis `render`. Les clips inchangés viennent du cache
(`DIR/work/clips`), seuls les clips touchés se ré-encodent.

## Après chaque EDL Resolve de Lucien (09/10/2026)

Appliquer ses coupes à l'image près, sans ajout automatique.
Lancer ensuite la détection des mots tranchés (`mots_tranches.py`) et lui envoyer la liste avant tout rendu.
Ne lisser aucun morceau sans demande écrite de Lucien (règle du 31/10/2026).
Détails et autres contrôles : `~/.claude/skills/recreer-motion-design/references/garde-fous-montage.md`.

## Réglages figés (ne pas redemander)

Les valeurs exactes de la chaîne audio sont dans `references/chaine-audio.md`.
Ce fichier donne aussi l'équivalent DaVinci Resolve pour un monteur sans le pipeline.

### Priorité audio demandée le 15 septembre 2026

Quand OBS et DJI enregistrent la voix, OBS fournit l'audio maître.
DJI fournit les images et la piste de référence pour la synchronisation.
Cette priorité couvre le montage complet et ses reprises.
Conserver les canaux et le niveau OBS sans amélioration vocale tant que Lucien n'a pas choisi son traitement.
Présenter deux extraits du même passage de 20 secondes : OBS original et OBS avec traitement vocal habituel.
La comparaison garde une vitesse normale et les mêmes images.
Le moteur caméra-audio historique exige une adaptation avant le rendu OBS maître.
Inscrire le chemin et les bornes OBS dans un champ audio explicite de chaque portion.
Conserver ce champ lors des coupes Resolve et des exports depuis les sources.
Contrôler que le rendu lit ce champ même sur les plans visage.
Lucien valide ensuite la version améliorée pour la vidéo du board IA.
Appliquer la chaîne vocale habituelle à OBS une fois puis conserver ce master dans les reprises.
`source_media.py` accepte le champ `audio` et recale ses bornes lors des coupes.
Le champ `audio_master` exige cette piste sur chaque portion.
Le rendu utilise son tempo propre et conserve les canaux annoncés dans `audio_channels`.

| Quoi | Valeur |
|---|---|
| Sortie | 1440p, 50 fps natif caméra (30 fps = judder), x1.06 |
| Écran | navigateur à l'écran : recadrage 16:9 sous la barre Chrome, ni onglets ni URL, aucun bord noir, carré visage entier sur l'écran (crop `0:258:2940:1654` pour un OBS 2940x1912, 09/11/2026). OBS 1920x1080 sans navigateur : crop `0:0:1920:1080`, fit |
| Carré visage | crop 4K `1050:100:1800:1800`, taille 0.40, rayon 0.08, bas droite, marge 40 |
| Cadence | min 4 s, max 10 s, DP avec verrous |
| Coupes | silences + euh (`--vad auto`), bégaiements, prise refaite entière, phrase inachevée redite. Pauses gardées jusqu'à 2,5 s. Les détecteurs d'amorces (« Reprises automatiques » dans `references/pieges-et-reprises.md`) tournent seulement avec `audit_mots_perdus.py` à code 0 : 229 coupes fausses le 09/11/2026 |
| Transcription | ElevenLabs Scribe v3 (`scribe_v3`) appelé depuis le Mac par `~/.local/share/montage-cabinets-3-systemes-2026-11-14/scribe/scribe.py` : 18 min en 24 s, 0,20 $/h. La clé transcrit (HTTP 200) même si `/v1/user` répond 401. Le modèle local sur CPU dans le cloud prend plus d'une heure par vidéo : repli seulement (14/11/2026, [[Intelligence/decisions/2026-11-14-transcription-elevenlabs-scribe]]) |
| Fenêtre OBS visible | plage interdite, même traitement que le script |
| Suivi visage | refusé par Lucien, crop fixe |

Si Lucien change de pièce ou de cadrage caméra : refaire le crop visage avec une
frame 4K quadrillée (grid 240 px) et sa réponse.

## Ce que Lucien décide

Position du carré, taille, cadence, traitement du script, niveau de coupes.
Ces cinq points sont validés et figurent comme défauts dans `references/interview.md`.
Ne les redemander que si les rushs ou la demande changent.
