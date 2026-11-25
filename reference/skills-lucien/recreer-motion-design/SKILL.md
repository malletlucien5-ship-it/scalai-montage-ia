---
name: recreer-motion-design
description: Recrée fidèlement les animations d'une vidéo de référence et les pose sur une autre vidéo. Utiliser pour « recrée les motion designs de », « copie le montage de », « motion design comme Dan Martell », « applique les motions à ma vidéo », personnalisation Remotion, sound design et rendu Remotion sur AWS Lambda.
---

# Recréer un motion design

> [!warning] Première consigne d'une vidéo = plaque + planche, rien d'autre — 18/10/2026
> Avant d'écrire une consigne pour une nouvelle vidéo (pub comprise), relire ce skill.
> La première routine livre seulement le proxy 540x960 avec compteur d'images, la plaque et la planche d'étalonnage.
> Sobre, motion et rendu final attendent les coupes de Lucien et son choix d'étalonnage. Les assets motion se préparent en parallèle, sans rendu final.
> Récidive du 18/10 sur la pub 60h : consigne complète écrite sans relire le skill.

> [!warning] « Proche de la référence » seulement après la superposition — 26/10/2026
> IA entreprise livrée sans comparaison à Yas : chantier.json typé « youtube », la superposition de livrer n'a jamais tourné.
> Lucien a trouvé les textes et les animations laids. Halo sombre sale sous les textes, poids trop gras, plans appauvris.
> Toute copie porte type « copie » et copie.reference dans chantier.json. Le garde-fou le vérifie.
> Textes en pleine résolution comparés à la référence avant tout rendu final.

> [!warning] Revue image par image avant toute livraison — 19/10/2026
> Claude regarde la superposition référence/copie à 2 i/s et liste chaque écart avant d'écrire à Lucien. Un score de conformité ne vaut pas validation.
> Sons en WAV Epidemic seulement, jamais les aperçus lqmp3. Clavier : une frappe par caractère, niveau mesuré contre la référence.

> [!warning] Couleurs et positions de la référence, à l'identique — 19/10/2026
> Copie vidéo : jamais de bleu ScalAI. Le corail et le logo orange de Claude restent tels quels.
> Chaque élément au même endroit, même taille, même zoom : superposition référence/copie image par image, boîtes à 2 % près.
> Tout aperçu livré porte le son, sans crête à 0 dBFS. Garde-fou : `guard-routine.py`.

> [!warning] Plans IA et son de la référence : copie exacte — 18/10/2026
> Un plan IA de la référence (avatar 3D, armure, illustration animée, vidéo d'ouverture) se régénère avec le visage de Lucien (media-gen : `nano-banana-pro-edit` avec sa photo et l'image de la référence, puis image vers vidéo). Jamais sauté, jamais remplacé par du HTML.
> Chaque son se recopie au même instant et au même niveau. Frappe = un clic par caractère, sous la voix, arrêté avec la frappe. Whooshes, clics et flashs viennent d'Epidemic Sound, jamais de la bibliothèque générique.
> Débordement mesuré texte par texte dans sa carte. Cause : vidéo 1000 h de Claude, 7 plans IA sautés, whooshes cheap, clics plus forts que la voix.

> [!important] Version vierge d'abord, assets en parallèle — 15/10/2026
> Pour chaque vidéo, livrer d'abord une version vierge : coupes, assemblage caméra + OBS, voix améliorée une fois, look A.
> Aucun motion design, aucune musique, aucun sous-titre, aucun zoom, aucun flash dans cette version.
> L'envoyer à Lucien dès qu'elle sort, en proxy léger (540x960, compteur d'images) et sur son bureau.
> Développer les assets et le motion design en parallèle pendant qu'il fait ses coupes dans Resolve.
> Ses coupes fixent ensuite la timeline : les reporter à l'image près sur les versions sobre et motion, sans coupe automatique en plus.
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

Produire une copie mesurée de chaque animation de la référence. Personnaliser le texte et les identifiants demandés. Poser les animations sur les mots de la vidéo cible.

## Règles dures

1. Lire les règles du projet avant toute commande.
2. Mesurer la référence image par image. Conserver la composition, les mouvements, les couleurs, les polices et les durées.
3. Chercher un asset existant avant de générer ou coder. Lancer `scripts/index_assets.py` sur les projets disponibles.
4. Respecter les coupes validées. Conserver chaque fin de mot.
5. Rendre les vidéos Remotion sur les serveurs Hetzner du projet. AWS est retiré depuis le 05/10/2026.
6. Garder le Mac pour les images fixes et l'assemblage final léger.
7. Conserver chaque rendu valide dans le cache. Invalider une composition selon son code, ses props, ses assets et sa plage.
8. Mesurer une fenêtre de 10 secondes avant d'annoncer un délai d'assemblage.
9. Contrôler deux images par placement. Comparer chaque image avec la référence.
10. Ne jamais extraire ni publier un asset sous licence. Utiliser les fichiers acquis par le propriétaire du projet.
11. Avant tout rendu final d'un montage long, passer les garde-fous de [references/garde-fous-montage.md](references/garde-fous-montage.md) : mots tranchés listés à Lucien, plans de 1 à 3 images lissés, écran recalé sur la voix, sous-titres sans chevauchement, aucune transition flash, fuite ou glitch, aucun script dans un segment écran (`ecrans_sans_script.py`), zéro image isolée (`flashs_police.py`). Un plan corrigé se contrôle dès sa première image.

12. Punch-in et zoom : les yeux de Lucien restent au même endroit de l'image pendant tout le zoom (règle du 14/10/2026). Ancrer chaque zoom sur le point entre ses yeux, mesuré par détection de visage sur le morceau, jamais sur le centre de l'image. Aucun rabattement aux bords ne doit déplacer ce point : si le cadre manque de marge, réduire le zoom. Contrôle avant rendu : position des yeux sur la première et la dernière image du zoom, écart de 6 px au plus en 1080x1920.

## Description YouTube automatique des vidéos longues

À chaque envoi privé d’une vidéo longue, préparer et ajouter automatiquement sa description avant de terminer la livraison.
Suivre [la procédure de description](references/description-youtube-longue.md).
Le rendez-vous précède LinkedIn. Ajouter les ressources annoncées et les chapitres du montage final.
Cette étape exclut les Shorts. Elle conserve le statut privé.

## Mode cloud

Lire [references/cloud.md](references/cloud.md). Lancer `cloud/setup.sh` au début de la session.

Télécharger les vidéos avec `cloud/fetch_inputs.sh`. Utiliser `cloud/transcribe.py --asr fal` pour les mots horodatés.

Rendre sur Lambda dans `eu-north-1`. Assembler les segments avec ffmpeg dans le conteneur cloud.

Si Jev manque, utiliser le modèle de la session. Appliquer les mêmes questions et seuils de contrôle.

Envoyer la vidéo finale avec `cloud/push_output.sh`. Conserver l'URL présignée dans le rapport.

## Processus

### 1. Inventorier la référence

Créer un catalogue avec un identifiant par animation. Noter les plages de référence, le texte, le mode plein écran ou calque et les sons.

Critère de sortie : chaque occurrence possède un début, une fin et un état visuel attendu.

### 2. Chercher dans la bibliothèque

Lire [references/pipeline.md](references/pipeline.md). Générer `assets-index.json`. Comparer l'idée à illustrer avec les compositions et images déjà présentes.

Critère de sortie : chaque animation pointe vers un asset réutilisé, adapté ou à créer.

### 3. Recréer fidèlement

Extraire les états utiles de la référence. Mesurer les positions et les tailles. Construire une composition Remotion. Comparer plusieurs images. Utiliser Jev pour noter les écarts en masse.

Critère de sortie : deux passes de comparaison sont terminées. Les écarts restants sont listés.

### 4. Personnaliser

Changer les noms, handles, profils et textes demandés. Garder la largeur visuelle des textes. Chercher les restes de la marque source.

Critère de sortie : la recherche textuelle ne trouve aucun nom interdit. Les textes tiennent dans leurs cadres.

### 5. Ajouter le son

Classer les événements sonores. Chercher les fichiers dans la bibliothèque sous licence. Utiliser le même morceau quand il est disponible. Poser les sons sur la première image visible.

Critère de sortie : chaque événement a un fichier, une image de départ et un gain.

### 6. Caler sur la vidéo cible

Lire [references/pipeline.md](references/pipeline.md). Produire les mots horodatés. Reporter la carte référence vers cible. Recalculer après chaque nouvelle coupe.

Critère de sortie : les placements suivent les mots. Le contrôle des fins de mot passe.

### 7. Rendre sur Lambda

Lire [references/aws-lambda.md](references/aws-lambda.md). Déployer le site après un changement de code. Rendre les compositions dont l'empreinte a changé.

Critère de sortie : chaque média est lisible avec `ffprobe`. Chaque fichier a une signature de cache.

### 8. Assembler par segments

Lire [references/pipeline.md](references/pipeline.md). Copier les plages sans calque quand les codecs le permettent. Réencoder les plages touchées. Précalculer les masques. Tester 10 secondes.

Critère de sortie : les raccords gardent la bonne image et la bonne couleur. Le délai annoncé vient d'une mesure.

### 9. Contrôler en masse

Lire [references/qa-checklist.md](references/qa-checklist.md). Extraire deux images par placement. Faire juger chaque paire par Jev ou un modèle vision économique. Revoir les scores incertains.

Critère de sortie : chaque placement a un statut. Chaque défaut confirmé est corrigé ou documenté.

### 10. Livrer

Vérifier la durée, le codec, la résolution, la fréquence et l'audio. Écrire un rapport avec les corrections, les écarts, le coût AWS et le temps mesuré.

Critère de sortie : le fichier final passe `ffprobe`. Le rapport permet de reprendre le projet.

## Routage des détails

- Série de vidéos en parallèle (préflight, Hetzner, une session par vidéo, contrôles) : [references/serie-videos.md](references/serie-videos.md)
- Branding des vidéos du funnel : `Resources/standards/branding-video-faq-precall.md` du vault

- Bibliothèque motion de Lucien (intro TEMPS, horloge à palettes, défilement de ses vidéos, flash, écrans d'offre, archive des médias) : [[Skills/recreer-motion-design/references/bibliotheque-motion-lucien|bibliotheque-motion-lucien]] (`references/bibliotheque-motion-lucien.md`)
- Commandes et formats : [references/pipeline.md](references/pipeline.md)
- Erreurs observées : [references/erreurs.md](references/erreurs.md)
- Garde-fous d'un montage long (défaut, cause, contrôle) : [references/garde-fous-montage.md](references/garde-fous-montage.md)
- Contrôle visuel : [references/qa-checklist.md](references/qa-checklist.md)
- AWS Lambda : [references/aws-lambda.md](references/aws-lambda.md)
- Choix des modèles : [references/modeles.md](references/modeles.md)
- Étalonnage des prises DJI de Lucien (look A, bases par pièce) : `~/.claude/skills/short-icones-pointage/references/couleurs.md`
