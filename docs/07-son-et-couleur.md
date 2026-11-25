# Son et couleur

> Un mot inconnu ? Il est expliqué dans [00-lexique.md](00-lexique.md).

Claude te demande à chaque vidéo : nos réglages ou les tiens.
Nos réglages sont dans le code, gratuits et validés par Lucien.
Si tu débutes, prends nos réglages.

## Couleur

### Le problème

Une caméra ne rend jamais les couleurs parfaitement.
Selon la lumière du jour, le visage de Lucien peut sortir un peu vert, terne ou sombre.
Corriger ça s'appelle l'étalonnage.

### Le look A

Le look A est le réglage de couleur choisi par Lucien pour toutes ses vidéos.
Par rapport à l'image brute, il rend l'image :

- un peu plus lumineuse ;
- un peu plus contrastée, avec des noirs plus profonds ;
- un peu plus colorée, avec une peau plus chaude ;
- un peu plus nette.

Il ne s'applique qu'au visage filmé par la caméra.
La capture de l'écran d'ordinateur garde ses couleurs d'origine.

### Comment Claude l'applique

Claude procède en deux temps :

1. **La base.** Claude mesure chaque rush et corrige ses écarts de lumière. Tous les rushs deviennent pareils.
2. **Le look A.** Claude applique ensuite le même réglage à tous. Ce réglage ne change jamais.

Pour info, voici les réglages exacts, écrits pour ffmpeg. Tu n'as rien à taper.

```
base   = colorchannelmixer=rr=R:gg=G:bb=B,eq=gamma=1.03:contrast=1.05:saturation=1.05
look A = colorchannelmixer=rr=1.0:gg=0.972:bb=0.99,eq=brightness=0.03:contrast=1.06:saturation=1.12,unsharp=5:5:0.5
```

Lecture : un peu moins de vert (`gg=0.972`), +3 % de luminosité, +6 % de contraste, +12 % de saturation, un peu de netteté.

- Mesure de la base : `code/auto-edit/tools/etalonnage.py bases`.
- La couleur est appliquée d'office au montage. Elle n'est retirée que sur demande écrite de Lucien.
- Réglage pour Resolve et pour les Shorts : `reference/skills-lucien/short-icones-pointage/powergrade/`.
- Détail complet : `reference/skills-lucien/etalonnage-look-a/SKILL.md`.

Tu préfères étalonner toi-même dans Resolve ? Dis-le au brief.
Claude livre alors la vidéo sans couleur corrigée, avec une image du look A comme modèle.

## Voix

### D'où vient la voix

Lucien a deux micros : celui de la caméra et celui branché à l'ordinateur.
Le micro de l'ordinateur, enregistré par OBS, sonne mieux. C'est lui qui donne la voix.
Le son de la caméra sert seulement au calage.

### La chaîne voix

La voix brute contient des bruits et des écarts de volume.
Claude la fait passer par une suite de traitements, dans cet ordre :

| # | Traitement | Ce qu'il fait |
|---|---|---|
| 1 | Débruitage (DeepFilterNet3) | Retire le bruit de fond : ventilateur, rue, souffle |
| 2 | Gate | Coupe le son entre les phrases |
| 3 | Débruitage léger | Retire le souffle qui reste |
| 4 | Coupe-bas 65 Hz | Retire les grondements très graves |
| 5 | Coupe-haut 12 kHz | Retire les sifflements très aigus |
| 6 | Égalisation 7 bandes | Équilibre les graves, médiums et aigus de la voix |
| 7 | Exciter | Ajoute de la brillance |
| 8 | Dé-esseur | Adoucit les « s » sifflants |
| 9 | Compresseur | Rend le volume régulier |
| 10 | Normalisation à -15,76 LUFS | Règle le volume final |

**Règle importante.** La voix passe dans cette chaîne une seule fois.
Une voix traitée deux fois sonne métallique. Claude garde donc la voix traitée et ne la retraite jamais.

- Valeurs exactes : `reference/skills-lucien/montage-multicam/references/chaine-audio.md`.
- La même fiche donne l'équivalent dans Resolve, si tu traites la voix toi-même.
- Code : `code/auto-edit/auto_edit.py`, fonction `polish_audio`, et `code/motion/voix/`.

## Bruitages

Les bruitages sont les petits sons des animations : clic, « whoosh », frappe de clavier.
Plan de référence : `code/motion/SOUND-DESIGN.md` et `code/motion/SFX-REGLES.md`.

### Les volumes à respecter

| Couche | Volume | En clair |
|---|---|---|
| Voix | -16 LUFS | Le volume de référence de la vidéo |
| Musique | 21 à 27 LU sous la voix | On l'entend, sans gêner la voix |
| Bruitage grave à l'apparition d'un élément | 12 dB au-dessus de la musique | On l'entend nettement |
| Clic, frappe de clavier | Sous la voix | Discret, une frappe par lettre affichée |

- Chaque bruitage doit s'entendre.
- Aucun son ne doit saturer, c'est-à-dire toucher 0 dBFS.
- Aucun clic ne doit être plus fort que la voix.

### D'où viennent les bruitages

Les bruitages de Lucien viennent d'Epidemic Sound, sous licence à son nom. Ils restent chez lui.
Trois choix au brief :

- ta propre bibliothèque ;
- des fichiers envoyés par Lucien pour cette vidéo ;
- une banque gratuite : Mixkit SFX ou Pixabay.

## Pistes séparées

Claude livre toujours trois fichiers son à part : `stems/voix.wav`, `stems/musique.wav`, `stems/bruitages.wav`.
Si Lucien demande « musique plus basse », Claude ne touche qu'à la musique.
La voix reste intacte et le travail prend quelques minutes.
