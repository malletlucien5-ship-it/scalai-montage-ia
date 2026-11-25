---
type: skill-reference
date: 2026-10-03
status: active
tags: [montage, ruben, obs, s3]
---

# Envoi d'une vidéo longue au monteur Ruben

Ruben coupe dans Resolve sur un proxy, puis le formulaire lance le rendu automatique.
Le dépôt est `~/CODE/martell-motion-cloud`. Ses scripts gèrent l'envoi, la voix et le proxy.

## Règle audio, sans exception

L'enregistrement OBS porte la voix dès qu'il existe.
Chaque rush DJI se cale sur son OBS par GCC-PHAT.
Le micro DJI sert seulement à la synchronisation.
Le son caméra exige une demande écrite de Lucien pour cette vidéo.
Un précédent ne vaut jamais demande : video-gpt-new et Livres Claude ont suivi une consigne ponctuelle.

## Procédure

1. Inventorier les rushs DJI sur le Bureau et les OBS dans `~/Movies/`.
2. Associer chaque prise DJI à son OBS par la durée avec `ffprobe`.
   L'horloge DJI avance d'environ six minutes sur l'heure OBS.
   Deux fichiers DJI contigus forment une seule prise. Ils partagent un OBS.
3. Écouter le début et la fin de chaque OBS avec `mlx_whisper`. Regrouper les prises par sujet.
4. Trouver la référence YouTube de chaque sujet.
   Chercher avec `yt-dlp "ytsearch10:…"`. Transcrire 90 secondes de la candidate.
   La référence est validée quand son ouverture correspond au script de Lucien.
5. Envoyer avec un nom de projet `video-<sujet>` :
   `bash cloud/envoyer_rushs.sh PROJET --reference URL DJI… OBS…`
   Passer tous les DJI et tous les OBS du sujet. Ne pas passer `--audio`.
   Le script choisit `maitre` et refuse le son caméra quand un OBS est fourni.
6. Contrôler la ligne « Audio de la voix : maitre » dans la sortie.
7. Déposer la référence dans `inputs/PROJET/reference/reference.mp4`.
8. Ouvrir la vidéo au formulaire : ajouter le projet à `PROJECTS` de `cloud/monteur_service.py`.
   Ajouter la ligne à la table de `docs/ROUTINE-PROMPT.md` et à la routine `trig_0152qavujwrEcJADyHtL5H9m`.
   Redéployer avec `cloud/deploy_formulaire_monteur.py`, workflows désactivés puis réactivés.
9. Attendre l'issue « Proxy prêt : PROJET ». Le lien du proxy part à Ruben par Lucien.

## Plusieurs vidéos en parallèle

Chaque vidéo a son verrou d'envoi et ses versions à partir de v1.
Ne jamais supprimer ni écraser un dossier `inputs/` ou `outputs/` d'une autre vidéo.
Avant de relancer une étape 1 sur une vidéo existante, copier `outputs/PROJET/synchro/` dans un dossier daté.
Utiliser `aws s3 cp --recursive --copy-props none` : la clé n'a pas le droit de lire les tags.

## Envoi long

Le débit mesuré est de 4 à 6 Mo/s. Compter 3 heures pour 46 Go.
Lancer l'envoi sous `caffeinate -ims`.
Une coupure réseau arrête `aws s3 cp`. Comparer chaque taille S3 à la taille locale, puis renvoyer les manquants.
