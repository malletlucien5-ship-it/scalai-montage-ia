# Musique

> Un mot inconnu ? Il est expliqué dans [00-lexique.md](00-lexique.md).

Claude te demande à chaque vidéo d'où vient la musique.

## Les trois choix

| Choix | Conséquence |
|---|---|
| Ta bibliothèque (Epidemic, Artlist ou autre) | Tu fournis les pistes ou ta clé. Licence à ton nom ou à celui de la chaîne |
| Pistes envoyées par Lucien | Lucien choisit dans son Epidemic Sound et t'envoie les fichiers de la vidéo |
| Banque libre | YouTube Audio Library ou Pixabay Music. Vérifier la licence de chaque piste |

La bibliothèque musicale de Lucien est sous licence Epidemic Sound à son nom. Elle reste chez lui.

## Le style validé

Choix de Lucien pour la vidéo « 6 niveaux de Claude », une piste par chapitre :

| Chapitre | Piste Epidemic | Artiste |
|---|---|---|
| Intro | Unseen | Elin Piel |
| Amateur | Apparent Solution | Brendon Moeller |
| Habitué | Steall Waters | Luba Hilman |
| Intégrateur | The Shape of Memory | Luba Hilman |
| Opérateur | Shadowed | John B Lund |
| Bâtisseur | Fallout | Lennon Hutton |
| Orchestrateur | The Farmhouse | Silver Maple |
| Outro | Pink Pulsar | ELFL |

Repère : nappe électronique calme, sans voix, tempo modéré, qui change à chaque partie.

## Règles de mix

- Musique 21 à 27 LU sous la voix : on l'entend, sans gêner la voix. Plus forte quand personne ne parle.
- La musique baisse toute seule quand Lucien parle et remonte quand il se tait (ducking).
- Changement de piste sur un changement de chapitre, jamais au milieu d'une phrase.
- Un Short garde une piste unique.
- Piste séparée livrée dans `stems/musique.wav`.

Code utile : `code/motion/sound/align_music.py` cale une piste sur la structure de la vidéo.
