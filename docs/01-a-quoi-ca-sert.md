# À quoi sert ce dépôt

> Un mot inconnu ? Il est expliqué dans [00-lexique.md](00-lexique.md).

Lucien filme ses vidéos face caméra et enregistre son écran en même temps.
Ce dépôt transforme ces rushs en vidéo montée, prête pour YouTube ou une pub.
Claude pilote toute la chaîne. Tu décides des choix créatifs et tu valides.

## Ce que Lucien te donne

| Source | Fichier | Rôle |
|---|---|---|
| Caméra DJI, 4K (image très détaillée), 50 images par seconde | `DJI_XXXX.MP4` + `DJI_XXXX.LRF` | Image du visage. Les `.LRF` sont des copies légères pour couper vite |
| Capture OBS | `AAAA-MM-JJ HH-MM-SS.mp4` | Écran de l'ordinateur et voix principale |
| Script | Google Doc | Texte lu au prompteur, jamais montré à l'écran |

## Ce que la chaîne produit

| Format | Sortie |
|---|---|
| YouTube long | 2560x1440, 50 i/s, alternance visage et écran, motion design, musique |
| Pub ou VSL (vidéo de vente) | Même base, animations plus denses, appel à l'action |
| Short | 1080x1920, ouverture sur le visage de Lucien, sous-titres |
| Podcast hebdo | Panneau gris à gauche, actus IA (skill `montage-podcast`) |

## Ce que Claude fait seul

- Caler la caméra sur OBS : mettre l'image du visage et le son de l'ordinateur en phase, à la milliseconde.
- Transcrire chaque mot avec son heure exacte dans la vidéo.
- Couper silences, « euh », bégaiements et prises ratées.
- Choisir quand montrer le visage et quand montrer l'écran.
- Étalonner l'image caméra (corriger ses couleurs) et nettoyer la voix.
- Coder les animations avec Remotion et les faire apparaître sur les bons mots.
- Chercher ou générer des b-roll (plans d'illustration), poser musique et bruitages.
- Contrôler le rendu avant livraison.

## Ce que tu décides

- Local ou cloud, et quelles clés API tu branches.
- Pour chaque vidéo : motion design, b-roll, son, couleur, musique.
- Ce qui part chez Lucien pour validation.
