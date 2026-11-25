# Format podcast : spécification

Format validé par Lucien le 20/11/2026. Maquette de référence : `maquette-panneau.jpg` (option 2, gris foncé).

## Cadre

- Sortie 2560x1440, 50 i/s, x1,06, voix OBS polie à -15,76 LUFS. Aucune musique, aucun bruitage.
- Étalonnage choisi par Lucien sur la planche du tournage.
- Police Helvetica Neue partout. Logos officiels en couleur, jamais redessinés.

## Plan « panneau » (80 % du temps)

Depuis le 21/11/2026 : branding de l'écran partagé de la VSL pré-call (composant `Partage`, branche `claude/vsl-precall`), à l'échelle 4/3. Panneau `#232323` de 1 247 px, « SCALAI » Barlow 800 et accroche Arimo italique en haut, titre Alegreya 700 centré. Phrase seule centrée au milieu du panneau, grande. Une image différente par carte, jamais répétée, aucune plaque blanche, aucun grand vide. Les lignes ci-dessous valent pour la v1 et cèdent devant celles-ci.

- Panneau gris foncé `#1c1c1e` sur 44 % de la largeur, à gauche.
- Lucien à droite sur 56 % de la largeur. Recadrage centré sur ses yeux, cadre fixe.
- Haut du panneau : sujet en petit, gris `#969696`, 2 % de la hauteur.
- Titre : phrase courte de Lucien, blanc gras, 3 lignes au plus. Mot clé en bleu ScalAI `#2e6bff`.
- Sous le titre : image de la source, coins arrondis, largeur du panneau moins les marges.
- Le texte entre ligne par ligne, calé sur les mots dits (temps Scribe).
- L'image entre avec son texte, jamais seule, jamais sur un panneau vide.
- Une carte reste au moins 5 s. Elle change à chaque idée nouvelle.

## Images

- Ordre de préférence : capture de la source citée dans le script, logo officiel, photo réelle de la personne citée.
- Capture headless pleine page à 1280 px, échelle 2. Bandeau cookies masqué en CSS, jamais accepté.
- Aucune image générée par IA, aucune mascotte.
- Chaque image porte sa source dans `panneaux.json`.

## Plan « Lucien seul » (20 % du temps)

- Intro : de la première image jusqu'au premier sujet. Lucien parle dès la première image.
- Toutes les 30 s à 1 min : une dizaine de secondes sur une phrase forte, puis retour au panneau.
- Fin : de « c'est tout ce que vous devez savoir » jusqu'à la dernière image.
- Zoom et dézoom alternés entre 1,00 et 1,25, origine fixe : le point médian des yeux, mesuré une fois. Aucun suivi de la tête, jamais (règle de Lucien du 21/11/2026). Les yeux restent à la même hauteur d'un cadrage à l'autre.
- Aucun retour face caméra de moins de 1,5 s entre deux panneaux.

## Coupes

- Retirer : répétitions, prises refaites, gros bégaiements, faux départs, pauses muettes longues.
- Retirer aussi les répétitions flagrantes : phrase qui redit la précédente (« super intéressantes. On va commencer par quelque chose d'intéressant »), faux départ, bégaiement suivi de « pardon ». Règle de Lucien du 21/11/2026.
- Blancs entre deux mots : 0,7 s au plus, ramenés à 0,5 s (règle du 21/11/2026, remplace « pauses jusqu'à 2,5 s »). Contrôle : plus grand écart entre deux mots gardés mesuré sur `mots-montage.json` avant livraison.
- Garder la dernière version complète d'une phrase redite.
- Une phrase qui annonce une partie jamais tournée part avec la pause qui la suit.

## Contrôles avant livraison

- Visage présent à l'image 0.
- Panneau entre 70 et 85 % de la durée.
- Aucun bloc « Lucien seul » au-delà de 15 s hors intro et fin.
- `controles.livrer` passe, carte dans la Salle de projection.
