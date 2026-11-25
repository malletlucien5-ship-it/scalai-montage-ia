# Choix des modèles et outils

## Décisions rapides

Utiliser Jev pour les décisions typées sur un grand lot :

- classer 170 images ;
- vérifier 46 compositions ;
- séparer musique, impact, clic, frappe et notification ;
- sélectionner les passages utiles d'un journal ;
- vérifier un rapport contre des règles écrites.

Donner un état court. Poser une question par jugement. Laisser les seuils et les reprises au code.

Commandes :

```bash
python3 ~/CODE/tools/jev/jev.py select \
  --goal "Trouver les messages sur les rendus et les corrections" \
  --files session.jsonl

python3 ~/CODE/tools/jev/jev.py verify \
  --text RETEX.md --rules regles.md
```

## Code répétitif

Utiliser GPT via `codex exec` pour :

- créer plusieurs compositions sur un contrat commun ;
- déplacer des chemins en dur vers une configuration ;
- produire les scripts d'index et de cache ;
- corriger une famille de composants semblables.

Donner la propriété de fichiers distincts à chaque agent. Garder le registre des tâches avant de les lancer. Éviter de relancer un agent déjà actif après une coupure de session.

## Lecture d'images

Utiliser un modèle vision économique pour une première passe. Sonnet ou Haiku conviennent à une lecture descriptive courte. Réserver un modèle plus fort aux scores incertains et aux défauts qui changent le sens.

Deux images par placement suffisent pour le tri initial. Ajouter les états transitoires porteurs d'une information.

## Génération d'images

Réutiliser une image existante lorsque son idée et sa composition conviennent. Pour une nouvelle image, fournir l'image de référence au modèle d'édition. Garder le mouvement dans Remotion quand une animation 2D suffit.

La génération vidéo demande un coût vérifié avant lancement. Générer cinq secondes pour le premier essai.

## Audio

Classer les événements avec Jev à partir de leurs caractéristiques ou d'un descriptif court. Utiliser l'empreinte spectrale pour chercher un fichier identique. Utiliser CLAP pour classer un nombre limité de candidats. Valider le meilleur résultat à l'écoute par le propriétaire de la licence.

## Rendu

Utiliser Remotion Lambda pour chaque vidéo. Utiliser une image fixe locale pour un contrôle ponctuel. Mesurer 10 secondes d'assemblage avant toute estimation.

