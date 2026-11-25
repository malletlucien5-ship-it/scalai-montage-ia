# Règles datées du montage

Encadrés déplacés de SKILL.md le 20/10/2026, mot pour mot. Les règles marquées « machine » dans SKILL.md sont vérifiées par le code.
Lire ce fichier avant d'écrire la première consigne d'une vidéo.

> [!warning] Première consigne d'une vidéo = plaque + planche, rien d'autre — 18/10/2026
> Avant d'écrire une consigne pour une nouvelle vidéo (pub comprise), relire ce skill.
> La première routine livre seulement le proxy 540x960 avec compteur d'images, la plaque et la planche d'étalonnage.
> Sobre, motion et rendu final attendent les coupes de Lucien et son choix d'étalonnage. Les assets motion se préparent en parallèle, sans rendu final.
> Récidive du 18/10 sur la pub 60h : consigne complète écrite sans relire le skill.

> [!important] Version vierge d'abord, assets en parallèle — 15/10/2026
> Pour chaque vidéo, pub comme long format, livrer d'abord une version vierge : coupes, assemblage caméra + OBS, voix améliorée une fois, look A.
> Aucun motion design, aucune musique, aucun sous-titre, aucun zoom, aucun flash dans cette version.
> L'envoyer à Lucien dès qu'elle sort, en proxy léger (540x960, compteur d'images) et sur son bureau.
> Développer les assets et le motion design en parallèle pendant qu'il fait ses coupes dans Resolve.
> Ses coupes fixent ensuite la timeline : les reporter à l'image près sur les versions finales (`cuts`), sans coupe automatique en plus.
> Exception : une vidéo que Lucien a déjà coupée (EDL ou projet Resolve fourni) saute la version vierge. Ses coupes s'appliquent directement.


> [!warning] Routine cloud : code dans le dépôt — 16/10/2026
> Le code du chantier part sur une branche `chantier/<projet>` de `martell-motion-cloud`. La Storage Box ne fournit que des données.
> La consigne commence par `git checkout` de la branche puis `cloud/preflight_routine.sh`. Code 2 = arrêt avant tout calcul.
> Cause : le classifieur du cloud refuse d'exécuter une archive de code téléchargée (R2 et R4 bloquées la nuit du 15/10).

> [!important] Ordre fixe de chaque montage — 15/10/2026
> 1. Plaque brute envoyée à Lucien : assemblage, coupes, voix améliorée, sans étalonnage.
> 2. Planche d'étalonnage en même temps : brut, look A pur, variantes légères, visage zoomé, extraits de 20 s.
> 3. Motion design codé en parallèle.
> 4. Lucien choisit l'étalonnage et ajoute ses coupes. Rendu final ensuite.
> Tout tourne en session cloud Claude Code. Hetzner seulement pour une étape que le cloud ne peut pas faire.
> Textes en Helvetica Neue. Logos de marque officiels en couleur, jamais redessinés.

> [!warning] Serveur éteint hors demande — 15/10/2026
> Un serveur Hetzner n'existe que pendant un calcul demandé par Lucien.
> La chaîne finit par : dépôt vérifié, archive de l'état sur la Storage Box, suppression du serveur par l'API.
> Jamais de serveur allumé la nuit ni gardé pour les retours. Une reprise recrée un serveur et restaure l'état.

> [!warning] Aucun calcul sur le MacBook de Lucien — 09/10/2026
> `prep`, `plan`, `render`, `assemble`, Whisper et ffmpeg lourd tournent sur un worker Hetzner.
> Le Mac envoie seulement les rushs vers la Storage Box, en rsync limité et `nice`.
> Lucien l'a exigé après un `prep` local sur les rushs AI Advantage.

> [!warning] Après les coupes DaVinci de Lucien, aucune coupe automatique — 10/10/2026
> Sa timeline fait foi. `cuts` applique ses coupes et rien d'autre : ni creux, ni reprises, ni relecture fine.
> Rien ne s'ajoute de soi-même : ni fin de mot rallongée, ni raccord réparé. Ses demandes écrites passent par `DIR/restaurations.json`.
> Le rendu refuse de sortir s'il est plus court que sa timeline.
> Les mots tranchés par ses propres coupes lui sont listés, jamais retouchés.
> La plaque livrée pour ses coupes passe d'abord le garde-fou des raccords : aucun mot tranché avant DaVinci.

> [!important] Shorts après deux accords de Lucien — 09/10/2026
> Attendre l’acceptation explicite de la version finale du long format.
> Proposer ensuite « Préparer les Shorts » et attendre un accord distinct.
> La proposition seule ne lance aucune sélection, adaptation ou génération.
> Les statuts techniques prêt et livré ne valent jamais acceptation humaine.
> Une nouvelle révision invalide les accords de la version précédente.
> La validation du lot de Shorts précède son envoi et sa programmation.

> [!important] Répartition des modèles — 09/10/2026
> Opus 5.5 code les animations et réalise le montage éditorial.
> Codex peut coder l’infrastructure et superviser le montage.
> Le quota Opus laisse le travail d’infrastructure continuer.
> La sélection reprend le Clipper actuel de Lucien avec son code, ses prompts et ses paramètres.
> Codex sur abonnement ChatGPT sélectionne. Jev contrôle chaque candidat.
> Une liste manuelle `clips_json` arrête le parcours cloud.
> Parcours serveur des Shorts : lire `references/sources-et-clipper.md`.

> [!important] Shorts : lot réparti sur plusieurs sessions cloud — 11/11/2026
> Un lot dont les médias dépassent le disque d'une session (24 Gio) part en plusieurs sessions cloud, jamais sur Hetzner.
> Le runner calcule les médias de chaque clip (`clipper.engine clip-media`) et groupe les clips par rush.
> Chaque session rend sa part (`--only-clips`) sous `g<N>/parties/p<n>/`. Les clips vont sous `g<N>/clips/`.
> Un clip à cheval sur deux gros rushs lit le second en flux par son lien signé (`--stream-media`).
> Prod fusionne les `result.json` des parties. Tests : `control/tests/test_decoupage_cloud.py`, `clipper/tests/test_only_clips.py`.
> Un guetteur de lot attend aussi les états `preparation` et `calcul`.
> La passerelle ferme une lecture longue sans erreur : toute lecture en flux reprend par Range jusqu'à la taille attendue.
> Bruitages à moins de 9 dB au-dessus de la musique : le moteur baisse la musique de l'écart, dans la plage 21-27 LU sous la voix.
> Si la plage ne suffit pas (g3 : c04 et c17), le moteur comprime les crêtes de la musique et garde son niveau dans la plage. Contrôle : `MusiqueSousBruitages` de `tests/test_only_clips.py`.
> Une session cloud ne recopie jamais un lien signé : les liens d'envoi arrivent dans `cloud/envois.json` et `shorts-moteur/envoyer_sorties.py` les utilise (g4, c24 perdu sur un lien recopié faux). Contrôle : `test_une_session_par_partie_avec_sa_part`.
> Description d'un Short : « ▶️ Vidéo complète : lien » puis `prompts/yt_description.md`, jamais le champ `description` du sélecteur (lot cabinets : 24 Shorts partis avec la note « Deux chiffres forts… », corrigés par l'API). Contrôle : `test_description_standard_jamais_la_note_du_selecteur`.
> Vidéo similaire : Studio refuse le navigateur du serveur. Dès qu'un lot passe à « programmé SANS vidéo liée », elle se pose dans le Chrome de Lucien sans lui demander, avec `scripts/lier-video-similaire.js`, se relit après rechargement et s'enregistre par `liaison_chrome.py marquer` sur prod. Contrôle : hook `shorts-liaison.py` à chaque message (lot cabinets du 11/11 : 24 Shorts sans vidéo similaire, Lucien « Pourquoi ça ne s'est pas fait ? »).

> [!important] Shorts : sound design complet et musique Epidemic — 18/10/2026
> Chaque Short porte les bruitages des animations du long format, en plus des whooshes et shutters du moteur.
> Une musique de fond Epidemic Sound accompagne chaque Short, 21 à 27 LU sous la voix, avec ducking.
> Registres méthode, astuce, alerte et épique : A/B test sur 3 morceaux choisis par Lucien (CHECKMATE, Out of Order, DOX Pt. II), répartis à parts égales, jamais deux Shorts consécutifs sur le même morceau.
> Registre humain : Constellation (Shuta Yasukochi). Jev juge humain ou non, le code attribue le morceau.
> Morceau journalisé par clip et par video_id pour comparer vues, rétention et swipe.
> Bibliothèque : Storage Box `martell/bibliotheque-musique-shorts/`, manifeste avec registre et SHA-256 par morceau.
> Jamais de son viral ni de morceau commercial dans le fichier : claim Content ID, Short bloqué au-delà de 60 s.
> Un son viral se pose seulement dans l'app YouTube mobile avant publication. Lucien a écarté ce flux le 18/10/2026.
> Les Shorts déjà programmés gardent leur son. Décision : [[Intelligence/decisions/2026-10-18-shorts-sound-design-epidemic-par-registre]].

> [!warning] Collaboration avec Ruben terminée — 09/10/2026
> Les anciens parcours d’envoi restent archivés.
> Aucun message ni réactivation d’accès sans nouvelle demande explicite de Lucien.

> [!warning] Punch-in : les yeux ne bougent pas — 14/10/2026
> Pendant un punch-in ou un zoom, les yeux de Lucien restent au même endroit de l'image.
> Ancrer le zoom sur le point entre ses yeux, mesuré par détection de visage sur le morceau.
> Jamais d'ancrage sur le centre de l'image ni de rabattement aux bords qui déplace ce point.
> Si la marge manque, réduire le zoom. Contrôle : yeux à 6 px près sur la première et la dernière image du zoom.

> [!important] Voix OBS, toujours
> Quand un enregistrement OBS existe, il porte la voix. Le micro DJI sert seulement à la synchronisation.
> Cette règle vaut pour le montage local et pour l'envoi au monteur Ruben.
> Le son caméra exige une demande écrite de Lucien pour la vidéo concernée.

> [!important] Étalonnage look A, toujours
> Chaque `montage.mp4` sort étalonné avec le look A, caméra seule.
> `pipeline.py assemble` le fait d'office. Méthode et contrôles : skill `etalonnage-look-a`.

> [!important] Écran seulement quand Lucien montre son écran (05/10/2026)
> Le plan « caméra + écran » sert uniquement aux moments de démo : studio, rendu, site, pricing, résultat affiché.
> Tout le reste passe en visage, script et OBS compris, même entre deux démos.
> `split_ranges.json` liste les secondes écran de démo.
> `forbidden_ranges.json` en est le complément exact, de 0 à 100000.
> Contrôler chaque bord de plage à la seconde sur `work/scrframes`.
> Retirer toute seconde où le script, la fenêtre OBS ou Mission Control apparaît.
> Une image moyenne plus claire que 190 sur 255 signale souvent le Google Doc : la regarder.

> [!warning] Capture OBS en 2940x1912
> Le crop écran figé `0:0:1920:1080` coupe cette capture.
> Mesurer la résolution OBS avec `ffprobe`, puis écrire `{"--screen-crop": "0:0:L:H"}` dans `DIR/cut_params.json` avant `plan`.

## Section « Montage vidéo » du CLAUDE.md du vault, texte intégral au 20/10/2026

Opus 5.5 code les animations et réalise le montage éditorial.
Codex peut coder l’infrastructure du montage et superviser son exécution.
Cette autorisation couvre l’orchestration, les transferts, les caches, les tests, le déploiement et la publication.
Une limite de quota Opus laisse ces travaux d’infrastructure continuer avec Codex.
Les nouvelles animations et les décisions de montage restent confiées à `claude-opus-5-5`.

Aucun calcul de montage ne tourne sur le MacBook. Le Mac envoie seulement les rushs vers la Storage Box.
AWS est périmé pour les montages depuis le 05/10/2026. Les rendus AWS sont indisponibles.
Le calcul de montage tourne dans les sessions cloud Claude Code, sur les serveurs Anthropic (compte Max, routine ou session cloud). Règle du 15/10/2026.
Cela couvre la synchro, la transcription, les coupes, le rendu Remotion et FFmpeg.
Hetzner sert seulement à une étape que le cloud Claude Code ne peut pas exécuter, au plus court. Le motif est écrit dans le journal du projet.
Les médias restent dans la Storage Box privée.
Chaque montage suit cet ordre : plaque brute (assemblage, coupes, voix), planche d'étalonnage, motion en parallèle, choix de Lucien, rendu final.
Toute nouvelle vidéo, pub comprise, charge le skill `montage-multicam` ou `recreer-motion-design` avant d'écrire la moindre consigne. Règle du 18/10/2026.
La première consigne cloud d'une vidéo livre seulement la plaque brute en proxy 540x960 avec compteur d'images, et la planche d'étalonnage.
Une consigne qui demande sobre, motion ou rendu final avant les coupes de Lucien et son choix d'étalonnage est interdite. Seuls les assets motion se préparent en parallèle, sans rendu final.
Les textes des montages sont en Helvetica Neue. Les logos de marque sont les logos officiels en couleur.
Le gateway `<passerelle-de-lucien>` fournit les liens de livraison.
Les sessions Opus 5.5 utilisent le compte Claude de Lucien en arrière-plan.

Un serveur Hetzner de montage tourne seulement pendant un calcul demandé par Lucien.
Dès la livraison vérifiée, sauvegarder l'état sur la Storage Box puis supprimer le serveur.
Jamais de serveur allumé la nuit ni gardé « pour les retours ». Une reprise recrée un serveur.
Le gardien `montage-gardien` sur prod sauvegarde puis supprime tout serveur inactif depuis 25 min.

Chaque Short publié ouvre sur le visage de Lucien face caméra, dès la première image.
Aucun Short ne commence par du motion design, une diapositive, une démo ou une animation qui le fait apparaître.
Le moteur Shorts pose 1,5 s de caméra avant toute animation d'ouverture.
Sans source caméra disponible, le Short est refusé ou recoupé, jamais publié ainsi.
Règle du 14/10/2026, valable pour les Shorts déjà programmés et futurs.

> [!warning] Fichiers texte hors de « A REGARDER » — 21/10/2026
> Le nettoyeur de « A REGARDER » met à la corbeille tout .md, .json, .txt ou .tar.
> Les scripts `recuperer.sh` déposent audits, passages et états dans le dossier de la vidéo sur le bureau.
> Incident : audit du script et passage montage de la vidéo IA entreprise jetés à la corbeille le 21/10.

> [!warning] Reprises reformulées et premier mot entier — 21/10/2026
> Le détecteur mot à mot garde les reprises où Lucien reformule la même idée, même au milieu d'une phrase.
> Le plan lance une passe LLM unique (`tools/reprises_semantiques.py`) : dernière version complète gardée, texte exact retiré, coupe calée sur les mots.
> Aucune coupe ne finit au milieu d'un mot (`caler_sur_mots` dans `pipeline.py`). Incident : « en 2027 » tranché en tête de plaque.
> Avant livraison d'une plaque : `tools/controle_repetitions.py` sur les mots du montage. Code 1 = relire chaque cas, couper ou justifier.
> Modèle des étapes de transcription par API : Sonnet 5.5, jamais Opus (Lucien, 21/10/2026).
> Incident : plaque IA entreprise v1 livrée avec une vingtaine de reprises, vues par Lucien dès la première minute.

> [!important] Inserts écran et défilements de site — 23/10/2026
> Un insert écran se rend comme un asset : plage de la plaque en images (fin exclue), carré visage pris dans la plaque aux mêmes images, sans audio, nombre d'images exact.
> La timeline Resolve est un `.fcpxml` 1.9 posé dans le dossier de la vidéo : plaque sur V1/A1, inserts sur V2. Générateur : `~/.local/share/montage-ia-entreprise-2026-10-20/inserts/timeline.py`.
> Site cité à l'oral : capture headless pleine page à 1280 px échelle 2 (`agent-browser`, une session neuve par capture, contrôler `devicePixelRatio` = 2 dans l'eval). Bandeau cookies masqué en CSS, jamais accepté. Couper l'image avant la répétition de page que Framer ajoute sous le pied de page.
> Vérifier que le domaine cité répond avec le bon site : jev.ai est parqué, Jev vit sur typesafe.ai.
> Quota Max au-delà de 90 % : un rendu ffmpeg déterministe sans agent passe par `hetzner_render.py run` sur prod (worker CPX62 détruit en fin de tâche), motif écrit au journal du projet.
> Graphe ffmpeg : le passer en argument `-filter_complex`. `-filter_complex_script` n'existe plus en ffmpeg 8 (Mac) et `-/filter_complex` n'existe pas en ffmpeg 6 (worker).
> Correction du même jour : Lucien avait déjà exporté ses coupes (« Timeline 1.edl » sur le bureau). Une timeline se construit toujours depuis son EDL, inserts coupés aux mêmes images. Le hook `timeline-recente.py` (UserPromptSubmit) liste les exports de moins de 72 h.

> [!warning] Jamais d'essai à blanc du garde-fou des routines — 25/10/2026
> Lancer `guard-routine.py` à la main avec une fausse session interroge prod, peut inscrire une routine fantôme au guet et laisse des tâches de fond qui notifient la session. Le hook ignore désormais tout appel qui ne vient pas de Claude Code (session UUID, `transcript_path`, `PreToolUse`). Pour tester une routine : la créer pour de vrai, le garde-fou répond au moment de `create`.

> [!important] Master refusé : quarantaine, jamais perdu (25/10/2026)
> Deux masters de 1 h 40 perdus avec leur conteneur après un refus de `controles.livrer`.
> Toute routine motion ou finale passe `--quarantaine` avec un lien PUT `quarantaine/`. Le garde-fou l'exige.
> Une plage validée couvre l'échantillon entier qui la chevauche (filtre fps : image prise jusqu'à (i + 0,5)/fps).

> [!important] Sous-titres : Shorts seulement, incrustés (26/10/2026)
> Le long format n'a jamais de sous-titres, ni incrustés ni en fichier .srt.
> Les sous-titres sont incrustés dans l'image des Shorts, dans le pipeline Shorts.
> Suivre le script du skill sans proposer d'étape ni de question qu'il ne prévoit pas.

> [!important] Musique et bruitages audibles — 26/10/2026
> Musique à 18 LU sous la voix et bruitages plafonnés à 6 dB sous la voix : Lucien « on n'entend rien ».
> Musique 12 LU sous la voix par défaut, plage contrôlée de 9 à 15 dB (`controles.son.musique`, main ce80dc3).
> Bruitages plafonnés à 3 dB sous la voix. Un aperçu de l'intro avec le son part à Lucien avant le master final.
> Lucien demande la musique plus basse que la plage : inscrire `valides.musique_ecart` [min, max] dans chantier.json avec sa phrase, AVANT de lancer la routine.
> Incident du 10/11/2026 : v3 cabinets à 20 LU (« le piano moins fort »), refusée par la porte après 35 min de calcul. Code : main 693ab5b.

> [!important] Tout passe par la Salle de projection — 26/10/2026
> Chaque version livrée (aperçu, intro, final, Shorts) reçoit sa carte dans https://claude.ai/artifact/2bMzPCnQWYbwdtjoF5yVyb.
> Le bureau reste une copie. Hook `salle-projection.py` : signale toute vidéo du bureau sans carte.

> [!warning] Consigne de routine : écrire « aucun serveur hors du cloud » — 30/10/2026
> `guard-routine.py` cherche le mot « Hetzner » dans la consigne, négation comprise, et refuse si le budget est en alerte.
> Incident : consigne refusée le 30/10 à cause de « aucun serveur Hetzner », budget à 1,25 €.

> [!important] Tournage sans démo à l'écran — 30/10/2026
> Quand l'écran OBS montre seulement le script, OBS sert à la voix et rien d'autre.
> Les visuels viennent du board Lucid et des captures pleine page. Format de référence : `chantiers/viral-x-2026-10-30/regles/format-presentation.md`.
> L'export PNG de Lucid sort en 1:1, flou au zoom. Un board à l'écran se recompose dans Remotion : export en fond, images et textes nets par-dessus.

> [!warning] DeepFilterNet dans le cloud : modèle fourni — 30/10/2026
> Le modèle se télécharge depuis GitHub, refusé par le proxy du cloud. Plaques IA entreprise (20/10) et viral X (30/10) polies sans lui.
> Modèle sur la Storage Box : `martell/bibliotheque-modeles/DeepFilterNet3.tar` (copie à signer dans `inputs/<chantier>/`, le portail ne signe que `inputs/` et `outputs/`). La consigne donne son lien GET, l'extrait dans `~/.cache/DeepFilterNet` et installe `torchaudio` à la version de `torch`.
> Une voix polie sans DeepFilterNet n'est plus une issue silencieuse : la routine s'arrête et l'écrit dans l'état. Contrôle : `guard-routine.py`.

> [!important] Bilan du chantier cabinets (08 au 10/11/2026) — 10/11/2026
> Onze routines et trois nuits pour une vidéo de 32 min. Temps perdu, par cause :
> - Une nuit : proxy de coupe rendu depuis 41 Go de 4K lus en flux. Les LRF de la DJI le sortent en 30 min. Contrôle : `lrf_requis` dans `guard-routine.py`.
> - 3 h : plaque v2 avec 231 mots coupés par les détecteurs d'amorces. Contrôle : `audit_mots_perdus.py`.
> - 45 min : tranches 1 et 4 arrêtées au démarrage sur un 503 de la passerelle. Contrôle : réessai du PUT dans `preflight_routine.sh`.
> - Une nuit : final en quarantaine à 23 h 25 pour deux fausses alertes, Lucien couché. Contrôle : `controles.tranche` (main 2ba3f5d), exigé par `tranche_requise` dans `guard-routine.py`.
> - Une matinée : « bouche » lu « bougé » au lieu de « whoosh », puis violon baissé deux fois. La retouche v3 a repoli toute la voix. Contrôle : `stems_requis` dans `guard-routine.py`.
> - 35 min : v3 refusée pour un violon sous la plage du contrôle. Exception à inscrire dans `chantier.json` avant le lancement.
>
> - Un message de Lucien : final v3 annoncé « livrée » sans carte de Salle, master resté sur le serveur. Contrôle : `masters_serveur` dans `salle-projection.py`.
>
> Intro d'un long format, retours de Lucien :
> - Un seul zoom rapide depuis le cadre large, léger flou de vitesse, cadre fixe ensuite. Aucun suivi du visage.
> - Aucun whoosh sur ce zoom.
> - Violon sous la voix : 12 LU et 16 LU jugés trop forts, 20 LU accepté. Inscrire `valides.musique_ecart` avant la routine.
> - Sous-titres sur les 20 premières secondes, branding `clipper-classic`, à sa demande seulement. Le reste du long format reste sans sous-titres.
> - Aperçus d'écran de 2 s : plage contrôlée sur sa première image, sa dernière et une image par seconde. Aucun clic dans la plage.
> - Écran recadré sous la barre Chrome. Écran dominant, visage à 20 % de la durée.

## Format présentation : retours du 31/10/2026

Une capture de site s'affiche en largeur entière dans son panneau, jamais recadrée à gauche ni à droite.
Un aplat de texte DOM ne recouvre jamais un connecteur ou un bord de bloc.
Avant un rendu de board, comparer le board en direct à l'export : Lucien peut supprimer un nœud après l'export.
Un arrêt montre au moins 35 % de contenu et dure au moins 5 s.
Un arrêt ne coupe aucun titre ni texte par le bord du panneau. Contrôle sur la géométrie des nœuds, pas sur la densité seule.
Un trait souligne sous sa ligne et ne barre jamais le texte.

> [!warning] Retouche du son : reprendre la consigne qui a passé — 10/11/2026
> Aperçu son v4 cabinets arrêté sur deux fautes de consigne, 15 min perdues.
> L'audit des mots était lancé sans `--audio` et a sorti 57 faux défauts. La voix était polie sur un extrait de 70 s : loudnorm et latence changent avec la durée.
> Toute étape inchangée recopie la commande exacte de la dernière routine passée. Une voix à recaler se polit sur toute la timeline.
> Contrôles : `mots_perdus_requis` (--audio exigé) et `voix_polie_entiere` dans `guard-routine.py`.

> [!important] Shorts : titres et durée selon Analytics (13/11/2026)
> Titre en question tendue, contraste ou histoire concrète avec un nom ou un chiffre. Jamais une phrase descriptive à plat, jamais deux titres de même ouverture dans un lot.
> Clip de 20 à 40 s, plafond 55 s. Le hook motion retient mieux : le montage reste.
> Contrôle : `controle_titres.py` sur prod, écarts affichés à la validation du lot. Mesure hebdo `com.scalai.shorts-hooks`.

> [!warning] Routine plaque : 4K en flux par script, Silero sans GitHub, Scribe — 14/11/2026
> Plaque claude-cabinets-guide : la routine a téléchargé le rush 4K entier (17 Go) malgré « lis la 4K en flux ». Disque de 30 Go plein, encodage reparti de zéro.
> L'intermédiaire 4K passe par `scripts/intermediaire_flux.sh` copié dans `auto-edit/tools/` du chantier. Contrôle : `flux_4k_requis` dans `guard-routine.py`.
> Silero VAD par torch.hub : GitHub refusé dans le cloud, 25 min perdues. `load_silero` lit le paquet PyPI `silero-vad` (chantier claude-cabinets-guide, 98dc200). Contrôle : `silero_pypi_requis`.
> Transcription par ElevenLabs Scribe v3 depuis le Mac (`scribe_chantier.py`), jamais Whisper sur CPU. Contrôle : `scribe_requis`.
> Plusieurs rushs : `AE_SYNC_HINT` (offset de calage.json) à chaque prep et plan. Sinon le rush qui commence loin dans l'OBS se cale faux (0008 à +50 s au lieu de +1 592 s). Code : multicam.py du chantier claude-cabinets-guide (70a093c). Contrôle : `sync_hint_requis`.

> [!warning] Sobre claude-cabinets-guide : fins de mots, notification — 15/11/2026
> L'audit du sobre a trouvé 12 fins de phrase coupées par la plaque (30 à 250 ms, « tout est prê[t] »). L'audit de la plaque sur mots Whisper ne les voyait pas. Restauration depuis le rush et l'OBS par `placement/fins_mots.py` du chantier, insertion dans le sobre, plan de placement décalé (`construire.py --insertions`).
> La routine a envoyé une notification push à Lucien malgré « aucun message ». Contrôle : `guard-routine.py` exige « PushNotification est interdit » dans toute consigne de montage.

> [!warning] Routine arrêtée par la limite de 5 h — 15/11/2026
> La passe 2 du chantier claude-cabinets-guide s'est arrêtée à 15 h 03, sobre à 27 morceaux sur 37. Cause : limite de 5 h du compte Max. Les morceaux locaux sont perdus avec la session.
> Un guet git ne voit pas cet arrêt. Après l'heure annoncée sans push, lire `list_runs` : `worker_status` idle avec un `last_event_at` ancien signale l'arrêt.
> Relancer avec `run` dès la remise à zéro du quota, lue par `get_usage`.

> [!warning] Quota lu dans le même message que la création — 16/11/2026
> Écrire un corps de routine de 17 000 caractères a pris plus de 30 min : le garde-fou a refusé trois fois la création pour quota périmé.
> Appeler `get_usage` puis `RemoteTrigger create` dans le même message, l'un après l'autre.

> [!warning] Préflight : jamais sur le fichier d'état d'une passe précédente — 16/11/2026
> `cloud/preflight_routine.sh` écrit un test sur le lien PUT qu'on lui donne. La relivraison du motion v2 lui a passé l'état de la passe 4 : tout l'historique a été écrasé.
> Une routine qui reprend une passe reçoit son propre fichier d'état, ou passe au préflight un lien PUT de test distinct.

> [!warning] Ouverture, interfaces, photos, réapparitions — retour de Lucien du 16/11/2026
> Toute vidéo de Lucien commence sur Lucien qui parle, à la première image.
> Une interface montrée est toujours la version la plus récente du produit, capturée le jour du montage.
> Les photos de Derrick sont bannies de tout montage.
> Aucun retour face caméra de moins de 1,5 s entre deux plans de b-roll ou de motion : on ne peut pas parler en une demi-seconde.
> Une copie reproduit la référence exactement, b-roll de l'intro compris : rien n'est ajouté par-dessus.
> Contrôle à écrire dans `controles/` : visage présent à l'image 0, plans visage ≥ 1,5 s dans placements.json, aucun asset nommé « derrick ».
