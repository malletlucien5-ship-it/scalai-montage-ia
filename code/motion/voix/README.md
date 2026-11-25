# Voix, synchronisation et proxy

`voix/ameliorer_voix.py` prépare l'étape 1 de la SOP monteur.
Il améliore la voix, la synchronise sur les rushs caméra et fabrique un proxy 1080p.
Les rushs 4K restent dans S3. Le script ne les télécharge jamais.

## Voie automatique (GitHub Actions)

Depuis le Mac : `bash cloud/envoyer_rushs.sh PROJET FICHIER...` avec tous les rushs DJI et tous les OBS. L'OBS porte la voix (`maitre`, défaut dès qu'un OBS est fourni). Le son caméra exige `--forcer-son-camera RAISON`.
Le script envoie les rushs, puis lance `.github/workflows/etape1.yml`. Aucune session Claude n'est requise.

| Job | Script | Rôle |
|---|---|---|
| `voix` | `voix/etape1.py` | Son caméra extrait (`extraire_audio_camera.py`) ou maître WAV/OBS, chaîne audio, synchro, `voix.wav` et `sources.json` dans S3 (`ameliorer_voix.py rendre --sans-proxy`) |
| `proxy` | `voix/proxy_parties.py partie` | Une tranche de 10 min de proxy par job, en parallèle, saut précis ffmpeg ; la même passe encode l'aperçu 720p |
| `assembler` | `voix/proxy_parties.py assembler` | Concaténation en copie, `voix.wav`, contrôles, envoi ; `apercu.mp4` (720p H.264 + AAC, faststart) ; liens 7 jours |

Fin : une issue « Proxy prêt : PROJET » assignée au propriétaire du dépôt, avec le lien de visionnage en ligne et le lien de téléchargement. Échec : une issue « Étape 1 en échec ».
Secrets du dépôt : `REMOTION_AWS_ACCESS_KEY_ID`, `REMOTION_AWS_SECRET_ACCESS_KEY`.

Coût : 0 $ d'AWS pour le calcul. Minutes GitHub Actions (estimation à mesurer au premier run) : environ 4 min de runner par minute de rush 4K (2 vCPU),
soit environ 300 min pour 71 min de rushs. Le proxy Remotion Lambda coûtait 6,17 $ pour 71 min
et décalait des raccords de 4 à 12 images (27/09/2026) : il n'est plus utilisé par l'étape 1.

### Son caméra comme voix

`voix/extraire_audio_camera.py --projet P` extrait le son de chaque rush caméra en WAV PCM 48 kHz 24 bits
(`inputs/P/audio-camera/`). Contrôle : 20 premières secondes égales au décodage direct du MP4.
Le même passage écrit le son témoin 16 kHz dans le cache : le rush n'est lu qu'une fois.
Un WAV nommé comme un rush ne s'apparie qu'avec ce rush.
Un WAV déjà dans `audio-camera/` pour la même version du rush (métadonnée S3 `rush-ident`) est réutilisé.

### Son caméra en secours (audio=maitre)

En mode `maitre`, `etape1.py` extrait aussi le son de chaque rush et le passe en `--secours` à `ameliorer_voix.py`.
Un secours ne s'apparie qu'avec son rush (même horloge : offset et dérive nuls) et passe après tous les maîtres
principaux (OBS, WAV), quelle que soit sa confiance. L'OBS couvre tout ce qu'il peut ; le son caméra ne remplit
que les trous : faux départ absent de l'OBS, fin de rush après l'arrêt de l'OBS (incidents I5, I6 du 03/10).
Plus de silence de remplissage tant qu'un secours existe. Chaque usage du secours est un `[AVERTISSEMENT]`,
et `rapport-rendre.json` donne pour chaque rush `couverture_obs_pct`, `couverture_secours_pct` et `plages_secours`.
L'appairage n'est refusé que pour un rush sans maître principal ni secours. Rushs, ordre et exclusions ne changent pas.
Une extraction en échec ne bloque jamais l'étape : le rush garde alors l'OBS seul.

## Entrées

Tout se trouve dans `s3://remotionlambda-eunorth1-08ow3rdhea/inputs/PROJET/rushs/`.

| Fichier | Rôle |
|---|---|
| Enregistrement OBS, MOV ou MKV | Audio maître : piste micro en PCM 24 bits 48 kHz. L'image d'écran n'est pas utilisée. |
| WAV séparé, facultatif | Audio maître accepté à la place du fichier OBS, ou en plus. |
| 1 à 5 rushs caméra | 4K, 50 i/s constants, son témoin. DJI, jusqu'à 1 h et 40 Go chacun. |

Classement automatique :

- un fichier sans vidéo est un audio maître ;
- une vidéo dont l'audio est en PCM est un fichier OBS, donc un audio maître ;
- une vidéo au nom OBS par défaut (`2026-09-26 10-00-00.mkv`) est aussi un audio maître ;
- un nom qui commence par `DJI_` reste toujours un rush caméra ;
- toute autre vidéo est un rush caméra.

`--maitre NOM` force le classement d'un fichier en audio maître.
L'option est répétable.

## Commandes

```bash
source cloud/aws-env.sh && require_cloud_aws_env
.venv/bin/python voix/ameliorer_voix.py analyser --projet PROJET
.venv/bin/python voix/ameliorer_voix.py rendre --projet PROJET
```

`analyser` fait l'appairage et la synchro, sans rendu.
`rendre` fait tout, puis envoie les sorties dans S3.
La dernière ligne affichée est le lien de téléchargement du proxy, valable 7 jours.

Options utiles :

| Option | Effet |
|---|---|
| `--local --sortie DOSSIER` | Rien n'est envoyé. Les sorties restent dans `DOSSIER`. |
| `--garder-local` | Garde `proxy.mov` et `voix.wav` après l'envoi. |
| `--travail DOSSIER` | Dossier de cache. Défaut : `out/voix/PROJET`. |
| `--no-denoise` | Coupe DeepFilterNet, le gate VAD et `afftdn`. Pour les tests. |
| `--proxy-mode auto|lambda|conteneur` | `auto` utilise Lambda pour un projet S3. Il bascule sur le conteneur en cas d'échec. |
| `VOIX_PROXY_PRESET=faster` | Préréglage x264 du proxy. Défaut : `veryfast`. |

Des sources explicites remplacent `--projet` : chemins locaux, URL https ou `s3://`.

## Sorties

Dans `s3://…/outputs/PROJET/synchro/` :

| Fichier | Contenu |
|---|---|
| `proxy.mov` | Rushs caméra bout à bout, dans l'ordre chronologique. |
| `voix.wav` | Voix améliorée alignée, PCM 24 bits 48 kHz mono. Échantillon 0 = image 0 du proxy. |
| `sources.json` | Correspondance entre images du proxy et images des rushs 4K. |
| `rapport-rendre.json` | Appairage, offsets, dérive, confiance, niveau, pic, contrôles, temps. |

Le proxy :

- 1920x1080, 50 i/s, H.264 High, 8 Mb/s (plafond 10 Mb/s) ;
- aucune image B. La voie conteneur fixe le GOP à 25 images. Lambda place une image clé au plus toutes les 250 images ;
- timecode de départ 00:00:00:00 ;
- exactement autant d'images que la somme des rushs ;
- audio : `voix.wav` à l'identique, PCM 24 bits 48 kHz.

Un rush d'un autre format que 16:9 est centré avec des bandes noires.

### Format de `sources.json`

Ce format est un contrat avec `voix/recouper.py`. Ne pas le changer sans lui.

```json
{"version": 1, "fps": 50,
 "proxy": {"largeur": 1920, "hauteur": 1080, "images": 90000},
 "plages": [{"proxy_debut": 0, "images": 45000,
             "camera": "s3://bucket/inputs/P/rushs/DJI_0001.MP4", "camera_debut": 0,
             "camera_largeur": 3840, "camera_hauteur": 2160}],
 "audio": {"wav": "s3://bucket/outputs/P/synchro/voix.wav", "sample_rate": 48000}}
```

L'image `f` du proxy, avec `proxy_debut <= f < proxy_debut + images`,
correspond à l'image `camera_debut + (f - proxy_debut)` du fichier caméra.
En mode `--local`, `camera` et `wav` sont des chemins locaux.

## Fonctionnement

1. **Sonde.** ffprobe lit chaque fichier par URL présignée (24 h).
2. **Audio maître.** La piste audio du fichier OBS ou du WAV est extraite une fois en WAV 48 kHz flottant.
3. **Son témoin.** Audio de chaque rush en 16 kHz mono. ffmpeg lit tout le fichier, même avec `-vn`.
   Pour un MP4, le script lit donc la table du `moov` et ne télécharge que les morceaux AAC
   par requêtes HTTP Range. Un contrôle compare les 20 premières secondes au décodage direct.
   Si le MP4 a trop de petits morceaux, ou en cas d'écart, retour à la lecture entière par ffmpeg.
4. **Appairage.** GCC-PHAT de `auto-edit/multicam.py`. Sondes sur tout le maître, puis points fins toutes les minutes.
   Un fit linéaire donne l'offset et la dérive d'horloge. Des fenêtres de validation contrôlent le fit.
5. **Chaîne audio.** Une seule fois par maître complet, réglages figés d'auto-edit (voir plus bas).
6. **Voix alignée.** Chaque rush reçoit sa tranche du maître amélioré, recalée sur l'horloge caméra.
   Rééchantillonnage soxr au rapport exact (1 + dérive), puis retard fractionnaire.
   Précision mesurée : moins de 0,001 µs sur signal connu.
7. **Proxy.** Pour un projet S3, Lambda rend le proxy avec `00-montage-final`.
   Les rushs de plus de 1 Go sont découpés sur leurs images clés en copie de flux.
   Le conteneur assemble la vidéo, ajoute `voix.wav`, puis exécute les contrôles.
   Un échec Lambda déclenche la voie ffmpeg du conteneur.
   Les sources locales utilisent directement cette voie ffmpeg.
8. **Contrôles.** Images, cadence, timecode, nombre d'échantillons, audio du proxy identique à `voix.wav`,
   niveau à -15,76 LUFS à 0,5 LU près, pic vrai sous -1 dBTP, résidu de synchro sous 10 ms.
9. **Envoi.** `aws s3 cp`, puis lien boto3 avec `Content-Disposition: attachment`.

En cas d'échec d'un contrôle, rien n'est envoyé. Code de sortie 3. Les sorties restent en local.
Une entrée invalide ou un rush sans correspondance (ni maître principal ni secours) donne le code 2.

Le cache (`out/voix/PROJET/cache`) garde les audios 16 kHz et les masters améliorés.
Une relance ne refait ni l'extraction ni la chaîne audio.

## Chaîne audio

Copie de `~/CODE/auto-edit/auto_edit.py` (`polish_audio`), réglages figés le 12/09/2026.
Valeurs dans `voix/chaine_audio.py`. Ne pas les changer sans mesure.

DeepFilterNet3 par blocs de 120 s, gate VAD Silero à -80 dB, `afftdn`, coupe-bas 65 Hz,
coupe-haut 12 110 Hz, égaliseur 7 bandes, exciter, dé-esseur, compresseur unique,
`loudnorm` deux passes à -15,76 LUFS et -1,19 dBTP, latence de chaîne compensée.

Retour de 192 kHz à 48 kHz après `loudnorm` : SWR. soxr bloquait ffmpeg 6.1 à la vidange finale
(27/09/2026, 3 s avant la fin). `VOIX_RESAMPLER=soxr` le rétablit.
Plusieurs maîtres : un processus par maître (`spawn`), `VOIX_CHAINE_PROCESSUS` borne leur nombre.

## Disque

Le conteneur a environ 30 Go. Le script vérifie la place avant de commencer.
Besoin : proxy au débit plafond (4,5 Go par heure) + `voix.wav` (0,5 Go par heure)
+ maître brut et amélioré (1,4 Go par heure de maître).
Cinq rushs d'une heure demandent donc environ 27 Go avec un maître de 5 h.
Après l'envoi, `proxy.mov` et `voix.wav` sont supprimés du conteneur.

## Temps mesurés

Conteneur 4 CPU, le 26/09/2026. Un autre agent chargeait la machine en même temps
(charge moyenne de 7 à 20) : ces temps sont pessimistes.

| Étape | Mesure | Temps |
|---|---|---|
| Chaîne audio complète | `voice-cut.m4a`, 22,3 min de voix réelle | 201,5 s, soit **9,0 s par minute d'audio** |
| dont DeepFilterNet3 | | 102,8 s |
| dont gate VAD, filtres, loudnorm | | 24,7 s, 14,1 s, 59,6 s |
| Proxy 1080p | 2 rushs synthétiques de 30 s en 4K50 (H.264 100 Mb/s, HEVC 10 bits 80 Mb/s), lus par URL | 164 s pour 1 min, soit **2,7 min par minute de 4K** (18 à 23 i/s) |
| Son témoin, lecture entière | rush de 381 Mo par URL | 18 à 20 s, environ 20 Mo/s |
| `rendre` de bout en bout | OBS de 100 s + 1 min de 4K, S3 vers S3 | 225 s |

Projection pour 5 rushs d'une heure : environ 13 h de proxy et 45 min de chaîne audio.
Le proxy est l'étape limitante : décodage 4K et x264 sur 4 CPU.
`VOIX_PROXY_PRESET=faster` ou une machine plus large réduisent ce temps.

## Tests

```bash
.venv/bin/python -m pytest -q voix
python -m unittest voix/test_secours.py voix/test_etape1_audio.py   # numpy seul, aussi en CI garde-fous
```

Médias synthétiques générés par ffmpeg :

- un MOV façon OBS avec le micro en PCM 24 bits, et un WAV séparé ;
- trois rushs caméra à 50 i/s, dans le désordre, deux résolutions, son témoin AAC dégradé avec dérive ;
- chaque rush porte son numéro d'image incrusté par drawtext ;
- la lecture du son témoin par plages d'octets est comparée à ffmpeg.

Les tests vérifient :

- appairage et offset à moins de 1 ms, dérive retrouvée à 2 µs/s près ;
- proxy : H.264 1920x1080, 50 i/s, 4000 images, timecode, GOP de 25, PCM 24 bits ;
- proxy image pour image : le numéro est relu dans chacune des 4000 images ;
- `sources.json` conforme au contrat et cohérent avec les rushs ;
- voix alignée à moins de 1 ms des deux maîtres, par corrélation indépendante ;
- recalage de dérive exact sur signal analytique ;
- chaîne complète avec DeepFilterNet.

## Dépendances

```bash
.venv/bin/pip install -r voix/requirements.txt
.venv/bin/pip install --no-deps deepfilternet==0.5.6
```

ffmpeg 6.1 avec libx264, boto3 et la CLI aws du venv.
