# Montage et clips depuis les sources originales

Statut : construction autorisée le 13 septembre 2026.

## Parcours

1. Inventorier les trois rushs caméra et les deux captures écran.
2. Mesurer les correspondances audio sur toute la durée.
3. Représenter chaque coupe indépendante par une rupture explicite de synchronisation.
4. Construire un montage horizontal avec les règles du skill montage-multicam.
5. Conserver une table reliant chaque frame montée aux sources caméra et écran.
6. Reprendre les coupes Resolve dans cette table.
7. Après approbation du montage, lancer la sélection habituelle du clipper.
8. Rendre chaque extrait depuis les fichiers caméra et écran originaux.

Le run demandé autorise un test réel. La validation du montage final reste requise avant le lot de clips.

## Format vertical

La caméra occupe la zone supérieure. Son cadrage reste large et fixe.
La capture écran originale occupe la zone inférieure.
Les plans visage utilisent directement la caméra originale.
La table du montage fournit les changements de plan et les moments sélectionnés.
Le clipper conserve ses sous-titres et son traitement audio.

La référence visible suggère une séparation vers 34,7 % de la hauteur utile.
La valeur provisoire vaut 666 pixels sur 1920.
Le fichier temporaire reste inaccessible : la mesure native exacte attend une copie accessible.
La configuration garde la hauteur explicite pour permettre cet ajustement.

## Synchronisation

Utiliser une corrélation audio locale avec contrôle du pic secondaire et de la cohérence temporelle.
Chercher largement après chaque perte de correspondance.
Valider les correspondances par des fenêtres indépendantes.
Limiter l'interpolation aux portions continues.
Un passage caméra sans écran fiable devient un plan visage.
Conserver les mesures et leurs scores dans un rapport JSON.

## Exécution

Le premier rush caméra sert au premier test.
Les autres fichiers servent à vérifier les associations et les ruptures.
Les encodages et calculs prolongés tournent sur le VPS.
Un serveur local limité aux fichiers autorisés fournit les plages demandées via un tunnel SSH privé.
La préparation locale copie uniquement les pistes audio compressées.
Aucune fenêtre ne s'ouvre pendant les exécutions de l'agent.

## Vérification

Tester les coupes désordonnées, les répétitions et les raccords caméra.
Tester les ruptures de synchronisation et les intervalles sans correspondance.
Vérifier les durées audio et vidéo ainsi que le nombre de frames.
Examiner des images extraites du rendu réel.
Conserver les sources et les fichiers de travail existants.
