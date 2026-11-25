---
name: montage-ia
description: Monter une vidéo de Lucien (YouTube long, pub, VSL, Short, podcast) depuis ses rushs DJI et sa capture OBS. Déclencher sur « monte la vidéo », « nouveau montage », « on commence », « j'ai des rushs », « ajoute le motion design », « fais le son », « étalonne », « prépare les Shorts ».
---

# Montage IA

Procédure du poste du frère de Lucien. Les règles de goût viennent de `reference/skills-lucien/`.
L'infrastructure de Lucien (Storage Box, Hetzner, hooks, routines) n'existe pas ici.

Le frère débute en montage. Explique chaque terme à sa première apparition avec `docs/00-lexique.md`.
À chaque étape, dis-lui ce qui se passe, pourquoi, et ce qu'il doit regarder pour valider.

## Avant tout calcul

1. `.montage-poste.json` absent : faire l'entretien d'accueil de `CLAUDE.md`.
2. Nouvelle vidéo : faire l'entretien de chantier de `CLAUDE.md`.
3. Créer `chantiers/<AAAA-MM-JJ>-<sujet>/` avec `brief.json`. Les médias restent hors git.
4. Charger l'environnement : `. .venv/bin/activate; set -a; source .env; set +a` (local). En cloud, les clés sont déjà dans l'environnement.

## Ordre fixe d'un montage

Chaque étape attend la validation de la précédente.

| # | Étape | Sortie | Qui valide |
|---|---|---|---|
| 1 | Calage caméra et OBS sur l'audio | `calage.json` | Claude (contrôle chiffré) |
| 2 | Transcription mot à mot | `mots.json` | Claude |
| 3 | Version vierge : coupes, alternance visage/écran, voix traitée une fois | `montage.mp4` + proxy léger | Lucien |
| 4 | Planche d'étalonnage : brut, look A, variantes | `planche-etalonnage.jpg` | Lucien |
| 5 | Coupes manuelles de Lucien dans Resolve (EDL) | `montage-cut.mp4` | Lucien |
| 6 | Motion design et b-roll, préparés en parallèle des étapes 3 à 5 | aperçus par animation | Le frère puis Lucien |
| 7 | Sobre : coupes finales + look A + son | `sobre.mp4` | Lucien |
| 8 | Motion : animations, b-roll, sous-titres, musique, bruitages | `motion.mp4` | Lucien |
| 9 | Final : contrôles passés, description YouTube | `final.mp4` | Lucien |

Une vidéo déjà coupée par Lucien (EDL fournie) saute l'étape 3.

## Commandes du pipeline multicam

Depuis `code/auto-edit/tools`, avec le Python du poste.

```bash
python3 pipeline.py prep --cam DJI_A.MP4 DJI_B.MP4 --screen OBS.mp4 --out DIR
python3 pipeline.py ranges --out DIR --script-ref fNNNNN.jpg --obs-ref fNNNNN.jpg --split "300-365,..."
python3 pipeline.py plan --out DIR
python3 pipeline.py render --out DIR --background
python3 pipeline.py verify --out DIR
python3 pipeline.py cuts --out DIR --resolve-project NOM --media montage.mp4
```

- `prep` cale les sources et produit des planches `DIR/sheets/scan_NN.jpg`.
- Relire chaque planche avec Read. Noter les plages visuelles et les vignettes du script et d'OBS.
- `plan` doit afficher « ÉCRAN sur plage interdite : [] ».
- Avant `render`, rendre 2 segments écran en aperçu et attendre l'accord.
- `verify` exige Δ audio/vidéo = 0 ms et un nombre d'images égal au plan.
- Détail complet : `reference/skills-lucien/montage-multicam/SKILL.md`.

## Réglages validés par Lucien (défauts)

| Quoi | Valeur |
|---|---|
| Sortie | 2560x1440, 50 i/s, vitesse x1,06 |
| Visage | crop 4K fixe `1050:100:1800:1800`, aucun suivi de tête |
| Carré visage sur écran | bas droite, 40 % de la hauteur, rayon 0,08, marge 40 px |
| Écran | capture 16:9 sous la barre Chrome, ni onglets ni URL |
| Cadence | changement de plan entre 4 et 10 s |
| Coupes | silences, « euh », bégaiements, prise refaite, phrase inachevée redite. Pauses gardées jusqu'à 2,5 s |
| Jamais à l'écran | le script (Google Doc) et la fenêtre OBS |
| Voix | piste OBS, chaîne `docs/07-son-et-couleur.md`, -15,76 LUFS, une seule passe |
| Couleur | look A sur l'image caméra, capture d'écran intacte |
| Shorts | premier plan = visage de Lucien face caméra |

## Coupes : ce qui est interdit

- Retirer un mot au milieu d'une phrase gardée.
- Laisser la fin d'une prise ratée.
- Lisser ou recouper les coupes de Lucien sans demande écrite.
- Contrôle : `code/auto-edit/tools/tail_guard.py` et la revue des mots tranchés avant tout rendu.

## Motion, b-roll, son, musique

Suivre les réponses de `brief.json` et les fiches `docs/05` à `docs/08`.
Une animation s'ancre sur un mot de la transcription, jamais sur une seconde fixe.
Rendre deux images par animation placée et les montrer avant le rendu complet.

## Livraison

Lancer `python3 -m controles.livrer` depuis `code/motion` quand le chantier a un `chantier.json`.
Sinon, vérifier à la main : durée, Δ audio/vidéo, niveau -16 LUFS, aucune crête à 0 dBFS, images clés.
Envoyer à Lucien le lien de partage du fichier et une planche d'images. Jamais la vidéo dans git.
