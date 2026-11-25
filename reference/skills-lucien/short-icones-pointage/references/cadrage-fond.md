# Cadrage et fond prolongé

## Viser la référence

Mesurer sur la référence : centre de la tête en y, hauteur de la tête, position du doigt. Exemple Dan debout : tête centrée à 34 % de la hauteur, tête haute de 13 %.

La prise DJI verticale fait 2160x3840. Réduire la vidéo (0,9 dans le premier short) et la poser sur un fond 1080x1920. La tête descend à la hauteur voulue.

## Fond

1. Extraire une image fixe de la prise, à la taille réduite.
2. Appeler `fal-ai/bria/expand` : `canvas_size [1080, 1920]`, `original_image_size`, `original_image_location`. Prompt : mur peint uni, même couleur, même lumière.
3. Bria garde la zone d'origine à l'identique. Vérifier l'écart moyen : environ 1 niveau sur 255.
4. Supprimer les coins de mur avec `scripts/plate_mur_plat.py` : miroir alterné d'un pan plat de 100 px, sans prise électrique.

## Composition

`scripts/render.py` superpose la vidéo au fond avec un masque. Le masque fond le haut sur 24 px. Il fond le côté du mur prolongé sur 80 px.

Ne jamais prolonger un bord que le corps touche. Contrôler les bords sur toutes les images où Lucien tourne le buste.

## Pièges ffmpeg 8

- `-filter_complex_script` n'existe plus : utiliser `-/filter_complex fichier`.
- `-vsync` n'existe plus : utiliser `-fps_mode passthrough`.
- Une image en boucle impose 25 i/s si `-framerate` manque.
