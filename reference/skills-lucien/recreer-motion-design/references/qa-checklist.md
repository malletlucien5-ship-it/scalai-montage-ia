# Liste de contrôle visuel

## Échantillonnage

Extraire deux images par placement. Prendre une image après l'entrée et une image avant la sortie. Ajouter les états transitoires qui portent une information.

Comparer chaque image avec la référence à la même phase de l'animation.

## Défauts bloquants

- Un libellé affiche un chiffre temporaire à l'état final.
- Une orbe, une carte ou une fenêtre reste vide.
- Un cadre prévu pour une image montre la vidéo située dessous.
- Un cadre gris devient transparent.
- La webcam coupe la tête, les épaules ou le bureau utile.
- Le cadre webcam garde un mauvais ratio.
- Un texte reste dans la langue source.
- Le nom, le handle ou le profil de la personne source reste visible.
- Le nom Dan Martell ou le handle danmartell reste visible.
- Un texte dépasse de son cadre.
- La police ou la taille change pour compenser une traduction longue.
- Un logo générique remplace le logo visible dans la référence.
- Un mouvement manque.
- Un élément arrive une image trop tôt ou trop tard.
- Un plein écran laisse voir la vidéo cible.
- Un calque couvre le visage ou un élément utile.
- Une coupe retire la fin d'un mot.
- Une reprise ratée reste dans la vidéo.
- Un son démarre avant l'image visible.
- Plusieurs sons doublent un seul événement.
- Une musique commence au mauvais chapitre.
- Un raccord de segment répète ou saute une image.
- Une conversion change les noirs ou les couleurs au raccord.

## Jugement en masse

Utiliser une question par défaut. Exemple :

```json
[
  {
    "id": "cadre_vide",
    "question": "Un cadre destiné à contenir une image ou une interface est vide ou transparent.",
    "type": "probability"
  },
  {
    "id": "texte_source",
    "question": "Un texte ou un identifiant de la vidéo source reste visible.",
    "type": "probability"
  }
]
```

Au-dessus de 0,85 : créer un défaut confirmé. Entre 0,55 et 0,85 : demander un second jugement. En dessous de 0,55 : classer conforme. Revoir manuellement les défauts qui changent une information.

## Contrôle technique

Vérifier avec `ffprobe` :

- durée attendue ;
- codec vidéo ;
- résolution ;
- fréquence d'images ;
- canal alpha des calques ;
- présence de l'audio ;
- fréquence audio ;
- fichier entièrement décodable.

Comparer les images situées avant et après chaque raccord. Compter les images pour détecter un saut.

