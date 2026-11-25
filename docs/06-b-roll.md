# B-roll

> Un mot inconnu ? Il est expliqué dans [00-lexique.md](00-lexique.md).

Un b-roll est un plan d'illustration posé sur la voix de Lucien.
Claude te demande à chaque vidéo d'où viennent les b-roll.

## Les quatre sources

| Source | Quand | Comment |
|---|---|---|
| B-roll personnels | Tu ou Lucien avez filmé des plans (bureau, mains, ville, client) | Dépose-les dans `chantiers/<nom>/broll-perso/`. Claude les place sur les mots |
| Plans de la référence | Une copie de vidéo reprend un plan réutilisable | Extraction image par image depuis la référence |
| Banques libres | Illustration générique (bureau, équipe, ville, écran) | Pexels et Mixkit, sans compte ni clé |
| Génération IA | Plan impossible à trouver, ou plan IA de la référence avec le visage de Lucien | Fal.ai avec ta `FAL_KEY` |

## Bibliothèque existante

La bibliothèque b-roll de Lucien vit sur son serveur. Tu n'y as pas accès.
Construis la tienne dans `bibliotheque/broll/` à la racine. Ce dossier reste hors git.
Claude y range chaque plan téléchargé avec sa source et sa licence dans `bibliotheque/broll/index.json`.

## Banques libres : pièges connus

- Pexels : curl est bloqué par Cloudflare. Claude lit les pages avec WebFetch.
- Fichiers Pexels : `https://videos.pexels.com/video-files/<ID>/<ID>-uhd_3840_2160_<fps>fps.mp4`, User-Agent requis.
- Beaucoup de clips sont verticaux. Vérifier la définition réelle avec ffprobe.
- Mixkit a deux licences. « Free » permet YouTube et la pub. « Restricted » l'interdit : à écarter.
- Un clip Mixkit Restricted ne sert que le fichier `-720.mp4`. 89 clips sur 215 l'étaient en novembre.

## Règles de Lucien

- Jamais de maquette HTML à la place d'un vrai plan.
- Aucun retour visage de moins de 1,5 s entre deux b-roll.
- Une copie de référence reprend ses b-roll exacts, sans rien ajouter par-dessus.
- Un plan IA de la référence se régénère avec le visage de Lucien. Photo source : `code/motion/remotion/public/lucien-photo.png`.
