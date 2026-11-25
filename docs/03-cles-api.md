# Clés API

> Un mot inconnu ? Il est expliqué dans [00-lexique.md](00-lexique.md).

Tu utilises tes propres comptes. Aucune clé de Lucien ne passe dans ce dépôt.

## Tableau

| Clé | Service | À quoi elle sert | Obligatoire | Coût indicatif | Sans elle |
|---|---|---|---|---|---|
| Aucune | Claude Max | Claude lui-même | Oui (abonnement) | Abonnement Max | Rien ne marche |
| `ELEVENLABS_API_KEY` | ElevenLabs | Transcription mot à mot (Scribe v3) | Recommandée | Environ 0,20 $ par heure d'audio | Transcription locale faster-whisper, plus lente |
| `FAL_KEY` | Fal.ai | B-roll et images générés par IA | Non | Quelques centimes à 1 $ par plan | Pas de b-roll IA |
| `OPENROUTER_API_KEY` | OpenRouter | Choix visage/écran par un modèle | Non | Quelques centimes | Règle automatique de repli, ou Claude décide en session |
| `EPIDEMIC_API_KEY` | Epidemic Sound | Recherche et téléchargement de musiques et bruitages | Non | Ton abonnement | Musique choisie à la main ou banque libre |

## Interdit

- `ANTHROPIC_API_KEY` : jamais. Elle facture à l'appel et contourne ton abonnement Max.
- Une clé dans le chat, un commit, une issue ou un nom de fichier.

## Où poser les clés

**Local** : copie `.env.example` en `.env` et remplis-le. Git ignore `.env`.
Claude le charge avec `set -a; source .env; set +a`.

**Cloud** : variables d'environnement de ton environnement claude.ai/code.
Ne crée pas de `.env` en cloud.

## Créer les comptes

- ElevenLabs : https://elevenlabs.io, menu Developers puis API Keys. Droit « Speech to Text » suffisant.
- Fal : https://fal.ai, Dashboard puis Keys. Ajoute un petit crédit.
- OpenRouter : https://openrouter.ai, Keys.
- Epidemic Sound : vérifie que ton abonnement donne accès à leur service MCP ou API. Sinon, télécharge à la main.

## Vérifier

```bash
bash scripts/verifier-poste.sh
```

Le script dit quelles clés sont présentes, sans jamais afficher leur valeur.
