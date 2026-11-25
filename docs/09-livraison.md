# Livraison et validation

> Un mot inconnu ? Il est expliqué dans [00-lexique.md](00-lexique.md).

## Ce que Lucien valide

| Étape | Ce que tu lui envoies | Sa réponse attendue |
|---|---|---|
| Version vierge | Copie légère (proxy) avec le numéro d'image dans un coin | Ses coupes faites dans Resolve |
| Planche d'étalonnage | Une image : brut, look A, variantes | Le look choisi |
| Motion | Deux images par animation | OK ou corrections |
| Sobre, motion, final | Lien de partage + planche d'images | OK ou retours |
| Shorts | Rien avant son « prépare les Shorts » | Accord explicite |

## Comment envoyer

- Un lien de partage (Drive, Dropbox, WeTransfer). Jamais la vidéo dans git.
- Nom de fichier explicite : `final.mp4` pour le projet complet, `test-rush-1.mp4` pour un essai.
- Un essai partiel ne remplace jamais `montage.mp4`.

## Contrôles avant tout envoi

- Le son et l'image ont exactement la même durée, et le nombre d'images correspond au plan (`pipeline.py verify`).
- Volume de la voix à -16 LUFS. Aucun son ne sature (aucune crête à 0 dBFS).
- Aucun mot coupé au milieu d'une phrase gardée.
- Aucun script ni fenêtre OBS à l'écran.
- Chaque animation et chaque b-roll vus sur deux images.
- `python3 -m controles.livrer` quand le chantier a un `chantier.json` (mode d'emploi : `code/motion/controles/LISEZMOI.md`).

## Retours dictés

Lucien dicte souvent ses retours. Un mot absurde est souvent un son proche (« bouche » = « whoosh »).
Relis chaque puce et pose la question sur tout mot douteux avant de modifier.

## Description YouTube

Pour une vidéo longue : rendez-vous avant LinkedIn, ressources annoncées, chapitres du montage final.
Procédure : `reference/skills-lucien/recreer-motion-design/references/description-youtube-longue.md`.
