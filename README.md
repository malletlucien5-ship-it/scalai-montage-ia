# Montage IA de Lucien

Ce dépôt contient toute la chaîne de montage vidéo de Lucien.
Tu ouvres Claude Code dans ce dossier et Claude fait le montage.
Tu fournis les rushs (les vidéos brutes filmées par Lucien), tu réponds à ses questions et tu valides les étapes.

**Tu débutes en montage ?** Aucun souci. Lis d'abord [docs/00-lexique.md](docs/00-lexique.md).
Il explique chaque mot du dépôt et raconte la fabrication d'une vidéo en 10 lignes.
Claude t'explique aussi chaque terme quand il l'emploie. Demande-lui dès qu'un mot bloque.

## Démarrage en 15 minutes

1. Prends un abonnement Claude Max sur ton propre compte.
2. Ouvre l'application Terminal de ton Mac. Tu y tapes les commandes des étapes suivantes.
3. Installe Claude Code : `curl -fsSL https://claude.ai/install.sh | bash`, puis connecte-toi à ton compte Claude quand il le demande.
4. Télécharge le dépôt : `git clone https://github.com/malletlucien5-ship-it/scalai-montage-ia.git`.
   Si le Mac propose d'installer les « outils de développement », accepte puis relance la commande.
5. Entre dans le dossier avec `cd scalai-montage-ia`, puis lance `claude`.
6. Écris « on commence ». Claude lance l'entretien d'accueil.

Claude te pose alors trois séries de questions :

- Accueil, une seule fois : local ou cloud, clés API, outils installés.
- Par vidéo : type de vidéo, rushs, motion design, b-roll, son, couleur, musique.
- Avant chaque livraison : validation de l'aperçu.

## Où lire quoi

| Question | Fiche |
|---|---|
| Les mots du montage expliqués | [docs/00-lexique.md](docs/00-lexique.md) |
| À quoi sert ce dépôt | [docs/01-a-quoi-ca-sert.md](docs/01-a-quoi-ca-sert.md) |
| Local ou cloud, ce que ça change | [docs/02-local-ou-cloud.md](docs/02-local-ou-cloud.md) |
| Quelles clés API brancher | [docs/03-cles-api.md](docs/03-cles-api.md) |
| Le process complet, étape par étape | [docs/04-process-complet.md](docs/04-process-complet.md) |
| Motion design et références | [docs/05-motion-design.md](docs/05-motion-design.md) |
| B-roll : tournés, cherchés, générés | [docs/06-b-roll.md](docs/06-b-roll.md) |
| Son et couleur | [docs/07-son-et-couleur.md](docs/07-son-et-couleur.md) |
| Musique | [docs/08-musique.md](docs/08-musique.md) |
| Livraison et validation par Lucien | [docs/09-livraison.md](docs/09-livraison.md) |

## Contenu du dépôt

| Dossier | Contenu |
|---|---|
| `CLAUDE.md` | Consignes que Claude lit à chaque session |
| `.claude/skills/montage-ia/` | Procédure de montage adaptée à ton poste |
| `code/auto-edit/` | Programmes de montage : calage, coupes, alternance visage/écran, couleur, fabrication de la vidéo |
| `code/motion/remotion/` | Animations Remotion : 46 motions de la référence et animations maison |
| `code/motion/controles/` | Contrôles avant livraison |
| `code/motion/voix/` | Chaîne de traitement de la voix |
| `reference/skills-lucien/` | Les skills d'origine de Lucien, règles datées comprises |
| `scripts/` | Installation et vérification du poste |

## Règles de base

- Aucun secret dans le dépôt. Les clés vivent dans `.env`, ignoré par git.
- Aucun média dans le dépôt. Rushs, rendus et bibliothèques restent hors git.
- Jamais de clé `ANTHROPIC_API_KEY`. Claude tourne sur ton abonnement Max.
- Lucien valide les coupes, l'étalonnage et chaque livrable.
