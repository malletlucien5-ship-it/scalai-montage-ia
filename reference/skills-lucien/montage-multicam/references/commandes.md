---
type: skill-reference
date: 2026-10-02
status: active
tags: [skill, montage-multicam, commandes]
project: youtube
---

Commandes intégrées le 15 septembre 2026, suite de `sources-et-clipper.md`.

## Commandes intégrées le 15 septembre 2026

`pipeline.py plan` utilise directement le nouveau crop caméra.
Configurer la référence dans `DIR/intro.json` après la validation du style.
Cette spécification contient le média, les crops et les intervalles visage de la référence.
Elle contient aussi sa durée cible et l'autorisation de reprise.

`pipeline.py cuts` produit automatiquement `montage-final.mp4` quand `intro.json` existe.
Le média destiné à Resolve conserve ses coupes et son nom.
La commande autonome utilise `pipeline.py finish --out DIR --media montage-cut.mp4 --no-open`.
L'option `--preview-only` produit uniquement l'introduction sous un nom distinct.
L'option `render --finish` ajoute l'introduction au rendu sans passage Resolve.
Les lancements en arrière-plan conservent les tables des sources et cette étape finale.

Le moteur d'introduction commun est `auto-edit/tools/intro.py`.
Il utilise les rushs caméra originaux et conserve le master audio lors du rendu complet.
Son cache dépend de la référence et des réglages de chaque rendu.
Le rendu reste idempotent et conserve les versions précédentes.

Le run du clipper utilise les fichiers sources et mots adjacents à la vidéo approuvée.
Exécuter `clipper run VIDEO.mp4 --no-open` avec la sélection habituelle.
La sélection utilise désormais Codex CLI avec la session ChatGPT.
Présenter les clips vérifiés pour validation avant leur envoi YouTube.
Après cette validation, utiliser la programmation habituelle avec `--source-url URL`.
Ce lien accompagne la description et la vidéo similaire de chaque Short.
Contrôler les identifiants du lot dans le manifest après l'envoi.
Confirmer les dates et les descriptions avec une lecture API YouTube.
Contrôler chaque liaison Studio dans le cache des succès.
Relancer seulement les liaisons manquantes en mode headless.
Un code de sortie nul ne garantit jamais la réussite du lot entier.
Studio utilise aussi POST pour ses lectures de médias.
Attendre la mutation `metadata_update` portant les deux identifiants attendus avant le rechargement de contrôle.
