# Sound design

## Règle

Ne jamais extraire la musique ni les bruitages d'un Short de référence. Recréer chaque bruitage par synthèse, après mesure de la référence.

## Mesurer un bruitage de la référence

1. Extraire l'audio de la référence en WAV mono 48 kHz, pour analyse seulement.
2. Repérer les attaques (`ebur128`, `astats` ou enveloppe numpy).
3. Pour chaque attaque : fréquence dominante (FFT), durée, enveloppe, niveau par rapport à la musique.
4. Caler chaque attaque sur l'image de révélation correspondante.

## Recréer

Synthétiser avec numpy : sinus à la fréquence mesurée, attaque de 2 ms, décroissance mesurée. Ajouter une harmonique si le spectre en montre une. Exporter en WAV 48 kHz.

Poser chaque bruitage sur la première image où l'icône devient nette, sauf écart mesuré sur la référence.

## Musique

Musique de fond : un morceau Epidemic Sound de `martell/bibliotheque-musique-shorts/`, attribué par A/B test (3 morceaux), sauf registre humain : Constellation. 21 à 27 LU sous la voix, avec ducking.

Jamais de son viral ni de morceau commercial dans le fichier. Un son viral se pose seulement dans l'app YouTube mobile, avant publication : aucune API, aucun ajout après upload. Lucien a choisi Epidemic seul le 18/10/2026.
