# Pièges, précisions et reprises

Déplacé de SKILL.md le 20/10/2026, mot pour mot.

## Pièges rencontrés (chacun a coûté un rendu)

- **Clips courts d'une frame → audio en avance de 1,8 s** en fin de vidéo. Cause :
  `fps=` dans un `filter_complex` ne remplit pas jusqu'à `-frames:v`. Le `tpad`
  en fin de chaîne vidéo dans `multicam.py` est la correction. Ne jamais l'enlever.
  Symptôme : durée audio > frames/fps dans `verify`.
- **Le JSON de plan prime sur la CLI** en `--from-json` pour pip/speed/layout.
  Modifier le JSON.
- **`--from-json` exige quand même les fichiers caméra en positionnel.**
- **Heredoc bash contenant `open(`** : bloqué par le hook anti-ouverture. Écrire
  le script dans un fichier (Write) ou utiliser `Path.read_text`.
- **OpenCV 5 n'a plus `CascadeClassifier`** : `opencv-python-headless<5`.
- **Whisper gomme les euh** : 5 fillers coupés au lieu de dizaines. Lucien le sait.
- **La cascade gloutonne `enforce_layout_constraints` ne tient pas une borne sur
  les deux layouts.** La cadence vient de `solve_layouts_dp`, activé par `--max-face`.
- **Plages interdites appliquées après la cadence → fragments < 4 s**. Le DP reçoit
  les verrous, un verrou remet le compteur à zéro et la portion libre avant le
  verrou paie son dépassement.
- **Une planche « toutes les 30 s » n'est pas la cadence du montage.** Le dire
  quand on envoie une planche, Lucien l'a confondue une fois.
- **Resolve App Store** : base `~/Library/Containers/com.blackmagic-design.DaVinciResolveLite/…/Projects/<nom>/Project.db`,
  table `Sm2TiItem` (`In`, `Duration`, `MediaFilePath`), timeline 50 fps qui
  démarre à 180000. L'API scripting répond None dans cette version : lire la base.
  Toutes les versions rendues d'un même plan partagent les mêmes frames de sortie,
  c'est ce qui rend les coupes transposables. Lucien relinke parfois le projet
  sur `montage-cut.mp4` et continue de couper : vérifier `--media` sur la base.
- **Rendus successifs** : renommer l'ancien avant de relancer (`render` le fait),
  supprimer les intermédiaires à la fin, garder `montage.json` et les plages.
- **Jamais de sync-check à l'oreille** : GCC-PHAT + `verify_output.py`.
- **« Rupture possible : fournir une table de sync par portions validées »** (05/10/2026) :
  l'OBS a perdu du temps en cours d'enregistrement (0,5 s vers 25:41 sur la prise 2).
  Une démo qui rejoue l'audio d'un rush fausse aussi des ancres GCC-PHAT : ne pas s'y fier seules.
  Localiser le saut avec `sync_discontinuous.py`, puis des fenêtres de 1,5 s autour du saut.
  Corriger les ancres de `DIR/work/sync.json`, écrire la seconde caméra du saut dans `DIR/sync_breaks.json`.
  Couper la zone du saut dans `DIR/cut_ranges.json` quand elle est muette : l'audio OBS y est discontinu.
  `source_media.from_multicam` lit `sync.breaks` et n'interpole jamais à travers.

## Précisions (questions posées par un agent de test)

- `--split` et `--script-ref`/`--obs-ref` : secondes ÉCRAN, comptées depuis le
  début de l'enregistrement OBS, jamais depuis le montage final.
- `--cam` : parties DJI dans l'ordre chronologique du nom de fichier
  (`DJI_YYYYMMDDHHMMSS_NNNN`). Une prise continue scindée par la caméra a des
  parties contiguës et `multicam.py` les enchaîne sans trou. Deux prises séparées
  (arrêt puis reprise) = deux vidéos, deux dossiers.
- Sync : le fit linéaire est accepté si résidu < 15 ms, sinon ancres par morceaux
  automatiques. Confiance < 6 sur un point = point ignoré. Si tous les points
  sont faibles, l'écran n'a pas de piste audio exploitable : vérifier avec
  `ffprobe` que l'OBS enregistre le micro, sinon `--offset` mesuré à la main.
- `verify` : Δ ≤ 5 ms accepté (1 ms vu après polish). 1,8 s ou tout multiple de
  clips = tpad manquant.
- Resolve : la version App Store range ses projets dans le conteneur
  `com.blackmagic-design.DaVinciResolveLite`. La version site Blackmagic les met
  dans `~/Library/Application Support/Blackmagic Design/DaVinci Resolve/Resolve Disk Database/Resolve Projects/Users/guest/Projects/<nom>/Project.db`
  et son API scripting répond. `resolve_cuts.py` ne connaît que le premier
  chemin : adapter `LIB` si besoin.
- Deux montages le même jour : `montage-<date>-b`.
- Lucien supprime rushs et dossier dès qu'il a fini. Ne rien recréer sur le
  Bureau après coup, et prévenir si le projet Resolve pointe vers un fichier
  disparu.

## Clips, introduction et commandes (ajouts des 13 au 15 septembre 2026)

- Clips et Shorts depuis les sources, cache multi-prises, creux silencieux, commandes intégrées : lire `references/sources-et-clipper.md` puis `references/commandes.md`.
- Introduction dynamique et cadrage validés : lire `references/introduction.md`.

## Reprises automatiques et OBS maître, 23 septembre 2026

Lucien veut chaque amorce ratée coupée : seule la dernière tentative reste.
Cette règle vient de ses 38 coupes Resolve sur le montage du 17 septembre.

### Pourquoi Whisper les laissait passer

Whisper transcrit un flux continu comme une phrase propre.
« et vous pouvez utiliser… et vous pouvez utiliser ça » sort une seule fois.
Les apartés (« Ok, là, je reprends », « autant pour moi ») disparaissent aussi.
Ne jamais chercher les reprises dans `multicam.transcache.json` seul.

### Méthode

1. `tools/segment_transcribe.py` transcrit chaque portion du plan séparément.
   Le modèle est `mlx-whisper large-v3-turbo`, environnement `~/CODE/auto-edit/.venv-mlx`.
   Compter 1 s par portion, cache par fichier `.cache.json`.
2. `tools/restart_detect.py` coupe une portion quand une des 6 suivantes, dans les 30 s, recommence par les mêmes mots.
   Tout ce qui sépare l'amorce de la reprise part avec elle.
   Les connecteurs de tête (donc, et, alors, ok) sont ignorés.
   Une portion sans mot (souffle transcrit « ... ») part aussi.
   Un aparté court (« je reprends », « je continue », « autant pour moi ») part aussi.
3. `phrase_repeats` coupe une répétition de 5 mots dans un même passage, entre 1 et 10 s.
   Elle s'appuie sur la transcription globale, qui garde parfois ces répétitions internes.
4. `pipeline.py plan` enchaîne ces étapes, écrit `restarts_auto.json` et replanifie jusqu'à stabilité (3 passes au plus).
   Le rapport lisible est `work/restarts.report.json`.
   `--no-restarts` désactive l'étape.
   `cut_ranges.json` reste disponible pour les coupes manuelles.
5. Faux départs dans une même portion (09/10/2026) : Whisper fusionne l'essai raté et la reprise quand ils tiennent dans une portion.
   `restart_detect.split_phrases` découpe chaque portion en phrases sur la voix OBS (creux de 0,12 s à −55 dB) et les transcrit une à une.
   `false_starts` coupe une phrase reprise par la suivante à moins de 1,5 s, du mot précédent jusqu'au début de la reprise.
   `assemble` l'applique après le nettoyage des creux (`work/fine_cuts.json`, `--no-fine` pour l'éviter) ; `plan` l'ajoute à `restarts_auto.json`.
   Mesure sur Livres Claude : 3 faux départs de Lucien trouvés, 0 faux positif sur 341 phrases (`tools/test_coupes_lucien_livres.py`).
   Ses 4 coupes de pause venaient de fausses rallonges de l'ancien tail_guard : le nouveau ne les crée plus.
   Test de bout en bout : `tools/test_livres_bout_en_bout.py` (`AUTO_EDIT_E2E=1` relance l'assemblage --dry complet).

### Phrase unique entre une amorce et sa reprise (10/10/2026)

Une portion située entre une amorce et sa reprise ne part que si ses mots reviennent après la reprise.
Avant ce correctif, « Vous pouvez gagner plus d'argent, agrandir votre équipe » disparaissait du montage AI Advantage.
Whisper avait isolé cette phrase entre une amorce et sa reprise, alors qu'elle n'était dite qu'une fois.
Test : `tools/test_reprises_ai_advantage.py`.

**Audit obligatoire avant livraison d'une vidéo lue sur script :**
`tools/audit_script.py --out DIR --script SCRIPT.txt --takes DIR/prise1 DIR/prise2`.
Exiger 0 phrase « dite mais absente du montage ».
Relire chaque phrase signalée sur le texte : une reformulation peut sortir en faux positif.
L'audit retranscrit l'audio réel du montage : le texte déduit des horodatages invente des trous.
Lancer l'audit sur le serveur Hetzner, jamais sur le Mac.

### Mot coupé en deux par un raccord (10/10/2026)

Le silence d'une consonne passait pour une fin de mot : « ré|ponse », « ré|flexion », « vont pivoter ».
`tools/raccords_mots.py` retranscrit finement l'audio maître autour de chaque raccord.
Un mot qui enjambe la frontière est restauré : la portion s'allonge, ou la suivante recule.
`assemble` le lance d'office : la plaque envoyée à Lucien ne contient aucun mot tranché.
Dans `cuts`, il liste seulement (`work/raccords-mots.json`) : rien ne bouge sans demande de Lucien.
Coupes DaVinci exportées en EDL : `pipeline.py cuts --out DIR --edl TIMELINE.edl --media montage.mp4 --no-open`, sur Hetzner.
Avec `--edl`, aucun nettoyage de creux supplémentaire : les coupes de Lucien s'appliquent à la lettre.

Mesure sur les coupes de Lucien : 38 détectées sur 38.
Quatre coupes en plus sont de vraies répétitions qu'il avait laissées.
Une énumération (« un outil pour un projet / un outil pour vous aider ») reste gardée.

### Fins de mot rognées

La détection de silence tourne sur le micro caméra.
Une syllabe finale faible (« répon-se ») passait sous le seuil et la portion s'arrêtait en plein mot.
`tools/tail_guard.py` relit l'audio maître à chaque raccord, fin et début de portion.
Version du 09/10/2026, après « entreprise », « Schwartz », « pitch », « étape » et « Ce que » coupés sur Livres Claude :
- passe-haut à 80 Hz avant toute mesure : le grondement du micro OBS empêchait de voir le silence et créait de fausses rallonges de bruit ;
- tranches de 10 ms, seuils calés sur la parole du fichier (voix = parole − 24 dB, silence = parole − 36 dB) ;
- un mot finit après 150 ms sans voix : la pause avant un « p » ou un « t » final ne coupe plus le mot ;
- une voyelle qui revient après 50 ms de blanc est un nouveau mot : la rallonge s'arrête avant, une reprise coupée reste coupée ;
- débuts de portion avancés de 0,3 s au plus ; toute la rallonge est protégée contre la passe des creux.
Sur une reprise Resolve, seules les fins issues des coupes automatiques sont examinées, et les débuts restent intacts.
L'audit des creux protège ces rallonges par des faux mots (`montage.protect.json`).
Test : `tools/test_tail_guard_livres.py` rejoue 10 raccords réels.

### Audio OBS et assemblage

`pipeline.py prep --audio obs` (défaut) fait de la piste OBS l'audio maître.
`pipeline.py assemble --out DIR --takes DIR/prise1 DIR/prise2` produit `montage.mp4` :
tables source par prise, fins de mot, fusion avec contrôle des rushs, reprises entre prises,
creux mesurés sur le PCM avant la vidéo, un seul rendu, chaîne vocale, vérification.
`--dry` prépare tout sans rendu vidéo.
Sans `--takes`, la commande assemble la prise unique de `DIR`.
`pipeline.py cuts` applique aussi la correction des fins de mot et le niveau -15,76 LUFS.

Une capture OBS qui ne montre que la fenêtre OBS donne `forbidden_ranges.json = [[0, 100000]]` : tout passe en visage.
OpenRouter répond 402 depuis le 23 septembre 2026 : les layouts passent par l'heuristique.
