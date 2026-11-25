# Interview de démarrage

Déplacé de SKILL.md le 20/10/2026, mot pour mot.


Cette interview sert à l'opérateur qui découvre le pipeline.
Elle évite les surprises des comportements par défaut.
Le pipeline ajoute une introduction, accélère l'image et coupe les silences sans le demander.
Un monteur qui ignore ces règles croit à une erreur de rendu.

Poser les questions avant la commande `prep`.
Utiliser l'outil AskUserQuestion en trois appels de quatre questions.
Placer le défaut en première option de chaque question.
Le défaut reprend un réglage déjà validé par Lucien.
Attendre les douze réponses avant de lancer le pipeline.
Écrire les réponses dans `DIR/brief.json` à la création du dossier.
Rappeler ce fichier dans le compte rendu final.

Sauter l'interview quand Lucien opère lui-même sur une configuration inchangée.
Reposer les questions dès que les rushs, la pièce ou la demande changent.

### Appel 1 : périmètre et sources

**Q1. Quel livrable final attends-tu ?** (choix multiple)

| Option | Ce que ça produit |
|---|---|
| `montage.mp4` seul (défaut) | Rendu horizontal complet, coupes automatiques, prêt pour un passage Resolve manuel. |
| `montage-cut.mp4` | Reprise des coupes manuelles d'un projet Resolve existant. |
| `montage-final.mp4` | Ajout de l'introduction dynamique après les coupes. |
| Lot de Shorts verticaux | Clips 1080 × 1920 produits ensuite par le clipper. |

**Q2. Combien de prises caméra composent cette vidéo ?**

| Option | Conséquence |
|---|---|
| Une prise, fichiers DJI contigus (défaut) | `multicam.py` enchaîne les parties sans trou. |
| Plusieurs prises séparées, une seule vidéo | Un plan source par rush, fusion par `merge_source_plans.py`. |
| Plusieurs prises, plusieurs vidéos | Un dossier et un montage par prise. |

**Q3. L'enregistrement OBS contient-il la voix ?**

| Option | Conséquence |
|---|---|
| Oui, OBS porte le master audio (défaut) | La caméra sert aux images et à la synchronisation. |
| Non, seule la caméra porte la voix | Le moteur caméra-audio historique reprend la main. |
| Incertain | Contrôler la piste avec `ffprobe` avant `prep`. |

**Q4. Le script ou la fenêtre OBS apparaissent-ils dans la capture d'écran ?**

| Option | Conséquence |
|---|---|
| Les deux (défaut) | Relever une vignette de référence pour chacun, ces moments passent en visage. |
| Le script seulement | Fournir `--script-ref` sans `--obs-ref`. |
| Ni l'un ni l'autre | Toutes les plages visuelles restent éligibles à l'écran. |

### Appel 2 : traitement

**Q5. Faut-il ajouter l'introduction dynamique ?**

Le pipeline construit cette introduction dès que `DIR/intro.json` existe.
Elle reprend le rythme des trente premières secondes d'une vidéo de référence autorisée.
Supprimer ce fichier pour l'éviter.

| Option | Commande |
|---|---|
| Non pour ce rendu (défaut) | Garder `montage.mp4` propre pour les coupes Resolve. |
| Oui, après les coupes manuelles | `pipeline.py finish --out DIR --media montage-cut.mp4 --no-open` |
| Oui, directement sur le rendu | `render --finish` |
| Aperçu de l'introduction seule | `finish --preview-only` |

**Q6. Quel niveau de coupes ?**

| Option | Conséquence |
|---|---|
| Silences et euh (défaut) | `--vad auto`, plus le nettoyage des creux de 0,13 à 1 seconde. |
| Silences seulement | Les hésitations restent, Lucien les coupe dans Resolve. |
| Aucune coupe temporelle | `build_source_plan.py --preserve-full --speed 1`, assemblage brut. |

Annoncer la durée retirée par les coupes séparément de la durée gagnée par la vitesse.

**Q7. Quelle vitesse d'image ?**

| Option | Conséquence |
|---|---|
| x1,06 (défaut) | Valeur validée, audio recalé par `atempo`. |
| x1,00 | Aucune accélération, durée source conservée. |
| Autre valeur | À inscrire dans `montage.json`, jamais en CLI sur `--from-json`. |

**Q8. Quel traitement de la voix ?**

| Option | Conséquence |
|---|---|
| Chaîne complète sur la piste OBS, -15,76 LUFS (défaut) | Débruitage, égalisation, normalisation, une seule passe. |
| Piste OBS conservée brute | Canaux et niveau d'origine gardés. |
| Comparatif avant décision | Deux extraits de 20 secondes du même passage, vitesse normale, mêmes images. |

Ne jamais appliquer une seconde passe d'amélioration sur un master déjà traité.

### Appel 3 : image et livraison

**Q9. Quelle alternance entre le visage et l'écran ?**

| Option | Conséquence |
|---|---|
| Écran verrouillé sur chaque plage visuelle, cadence 4 à 10 s (défaut) | Solveur DP avec verrous, contrôle « ÉCRAN sur plage interdite : [] ». |
| Écran dominant | Cadence à redéfinir dans `montage.json`. |
| Visage dominant | L'écran n'apparaît que sur les preuves demandées. |

**Q10. Quel carré visage pendant les plans écran ?**

| Option | Conséquence |
|---|---|
| Bas droite, 40 % de hauteur, marge 40 px, crop fixe (défaut) | 576 pixels de côté, rayon 0,08, aucun suivi de visage. |
| Autre position ou taille | Éditer `montage.json` puis relancer `render`, le cache garde les clips intacts. |
| Aucune incrustation | Capture plein cadre. |

**Q11. Le cadrage caméra a-t-il changé depuis le dernier tournage ?**

| Option | Conséquence |
|---|---|
| Non (défaut) | Crop 4K `1050:100:1800:1800` valable. |
| Oui | Refaire le crop sur une frame 4K quadrillée au pas de 240 px. |
| Incertain | Extraire une frame et la soumettre à Lucien avant `plan`. |

**Q12. Où livrer le rendu et sous quel nom ?**

| Option | Conséquence |
|---|---|
| `~/Desktop/montage-<date>/` (défaut) | Dossier unique avec plan, plages, cache et sorties. |
| Deux montages le même jour | Suffixe `-b`. |
| Essai partiel | Nom explicite du type `test-rush-1.mp4`, jamais `montage.mp4`. |

### Ce que l'interview ne demande jamais

Les valeurs du tableau « Réglages figés » restent hors interview.
Résolution, fréquence d'images, crop écran, seuils de silence et transcripteur en font partie.
Un opérateur qui veut changer une de ces valeurs le signale à Lucien avant le rendu.

### Aperçu obligatoire après l'interview

Rendre deux segments écran depuis un JSON réduit.
Extraire une frame et l'envoyer avec SendUserFile.
Attendre l'accord sur la taille du carré et le cadrage.
Cet aperçu vaut pour chaque nouvel opérateur, même avec les défauts.

