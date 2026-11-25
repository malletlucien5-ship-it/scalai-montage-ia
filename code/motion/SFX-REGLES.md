# Règles de sound design des motion designs

Ces règles viennent de la carte des sons de la référence (`sound/sfx_types_par_id.md`) et des deux sons identifiés à l'identique.
Les fichiers sont dans `remotion/public/sfx/`. Tous viennent d'Epidemic Sound, sous licence de Lucien.

## Le kit

| Fichier | Son Epidemic | Rôle |
|---|---|---|
| `nappe-ecran-titre.wav` | Low, Long 03 (identique à Dan) | Début de chaque écran de titre serif plein cadre |
| `impact-chapitre.wav` | Designed, Boom, Low Hit (identique à Dan) | Arrivée du titre d'une carte de chapitre |
| `montee-chapitre.wav` | Designed, Riser, Low Risers | 0,9 s avant l'impact d'une carte de chapitre |
| `whoosh-transition.wav` | Swooshes, Whoosh, Low, Short 02 | Entrée d'une fenêtre, d'un panneau, d'un plein écran ; glissement de caméra |
| `grave-apparition.wav` | Swooshes, Whoosh, Low, Short 06 | Apparition d'un élément sur le speaker : pilule, étape, badge, icône, carte, mot mis en valeur |
| `clic.wav` | Apple Mighty Mouse, Click | Chaque clic de curseur ou appui de bouton visible |
| `frappe-clavier.wav` | Apple Keyboard, Typing | Pendant chaque frappe de texte, coupé à la durée de la frappe |
| `pop.wav` | User Interface, Alert, Pops, Bloop | Petites pastilles, coches, bulles, nœuds qui s'allument |
| `notification.wav` | User Interface, Alert, Notification, Message | Arrivée d'une réponse de Claude ou d'un message reçu |

## Placement

1. Un son se cale sur l'image où l'élément devient visible, pas sur le début de son fondu.
2. Un seul son par élément. Si plusieurs éléments arrivent à moins de 0,12 s d'écart, un seul son.
3. Carte de chapitre : montée à t-0,9 s, impact à l'arrivée du titre, whoosh au glissement de l'ancien titre.
4. Écran de titre serif : nappe à l'image 0, puis grave-apparition sur chaque sphère, carré, étage ou carte qui arrive.
5. Frappe : `frappe-clavier.wav` démarre avec le premier caractère et s'arrête au dernier, fondu de sortie 0,05 s.
6. Sous-titres cinétiques : grave-apparition seulement sur les mots mis en couleur (cyan ou rouge), jamais sur chaque mot.

## Niveaux (gain appliqué dans `<Sfx>`)

| Son | Volume |
|---|---|
| impact-chapitre | 0,9 |
| nappe-ecran-titre | 0,7 |
| montee-chapitre | 0,6 |
| whoosh-transition | 0,5 |
| grave-apparition | 0,55 |
| notification | 0,45 |
| pop | 0,4 |
| clic | 0,5 |
| frappe-clavier | 0,3 |

La voix de Lucien sera à -16 LUFS au montage. Les bruitages se placent environ 12 dB au-dessus de la musique.

## Musique (au montage, pas dans les motion designs)

| Chapitre | Morceau | Statut |
|---|---|---|
| Intro | Unseen, Elin Piel | Équivalent (même style qu'Apparent Solution) |
| 1. Amateur | Apparent Solution, Brendon Moeller | Identique à Dan |
| 2. Habitué | Steall Waters, Luba Hilman | Identique à Dan |
| 3. Intégrateur | The Shape of Memory, Luba Hilman | Équivalent |
| 4. Opérateur | Shadowed, John B. Lund | Identique à Dan |
| 5. Bâtisseur | Fallout, Lennon Hutton | Équivalent |
| 6. Orchestrateur | The Farmhouse, Silver Maple | Identique à Dan |
| Outro | Pink Pulsar, ELFL | Identique à Dan, à partir de 0:44 |

Chaque morceau démarre à 0:00 sur la carte de chapitre. Musique 21 à 27 LU sous la voix, avec ducking.
