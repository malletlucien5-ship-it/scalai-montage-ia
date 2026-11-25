# Garde-fous d'un montage long (retours du montage IA, 08-09/10/2026)

Chaque défaut ci-dessous a été relevé par Lucien sur une version livrée.
Chaque garde-fou est un contrôle à lancer avant le rendu final, pas après.
Les scripts cités sont dans `~/CODE/montage-ia-20261006/projets/montage-ia/` (copie serveur : `/srv/montage-ia/projets/montage-ia/`).

## Défauts, causes et garde-fous

| Défaut vu par Lucien | Cause | Garde-fou |
|---|---|---|
| Mot tranché : « à vo- », « le fa- », « un mo- », « super chi- », « des exp- », « obs- » | Le bord d'une coupe Resolve tombe dans le mot. La v3 comblait ces fins en automatique, Lucien a refusé les ajouts automatiques. Les versions suivantes appliquaient l'EDL sans signaler les mots tranchés. | Après chaque EDL : `mots_tranches.py` (mots des prises brutes + énergie audio). Envoyer la liste à Lucien. Restaurer seulement les mots validés (`fins_de_mots` du plan). |
| Plan d'une seule image avant un zoom ou une transition | L'EDL laisse 1 à 3 images entre deux coupes. Ces morceaux sautent à un autre instant de la prise. Les segments d'écran v3 avaient aussi des bouts de 0,04 s. | `construire_v8.py` : un morceau de 3 images ou moins continue l'image du morceau précédent, la voix est gardée. Écrans 3D : un segment de moins de 0,1 s prolonge le précédent. |
| Écran en retard sur la voix (jusqu'à 0,44 s) | Les segments d'écran étaient calés sur la coupe v3 et lus à vitesse 1, alors que la base tourne à x1,06. | Recalculer les segments depuis les morceaux de la coupe finale, à leur vitesse réelle (`rate`), à chaque nouvelle coupe. |
| Le carré caméra montre le bras | Le carré découpe toujours le coin bas droit de la base. Sur un morceau caméra plein cadre, ce coin contient le bras ou le mur. | `pipCrops` : sur un morceau « face », le carré recadre le visage (x 700, y 60, côté 1200). |
| Carré figé ou mauvais moment dans le carré | Plaque caméra absente (photo d'aperçu). Plaque lue avec la cadence réelle (50 i/s) au lieu de l'horloge des compositions (30 i/s). | Toute vidéo dans une composition passe par `Sequence` et `OffthreadVideo` de `shared/rt`, temps en secondes × 30. Comparer une image du carré avec la base au même instant. |
| Voix v3 rejouée par l'offre de fin | Une prop absente prend sa valeur par défaut. `voixSrc` par défaut pointait vers une voix v3. | Toute prop de média (voix, base) est écrite dans le placement, vide si inutile. Rechercher `base-v` et `voix` dans les valeurs par défaut des compositions. |
| « +900 000 € » en deux sous-titres | La transcription sort « 900 » et « 000 ». La découpe coupe à 4 mots. | `gen_extras.py` : un nombre, ses milliers et son unité forment un seul mot insécable. |
| Sous-titres superposés (« zéro publicité ») | La dernière phrase d'un bloc durait 0,25 s de plus sans regarder le bloc suivant. | `gen_extras.py` : une phrase s'arrête 20 ms avant la suivante et avant tout plein cadre. Contrôle : zéro chevauchement entre phrases. |
| Chiffre qui dépasse de sa carte | Taille fixe de 150 px, « +900 000 € » mesure 714 px pour 644 px utiles. | `mia-mot-chiffre` calcule la taille sur la valeur finale. Contrôle : une image à l'état final de chaque chiffre. |
| « Ok, là on peut voir » en plan caméra | Les plages écran ne couvraient pas ce moment. Une phrase qui montre quelque chose doit montrer l'écran. | Repérer « on peut voir », « regardez », « ici », « là » : écran + caméra et zoom sur l'élément montré, puis caméra seule pendant l'explication. |
| Trompette, chats, rire trop présents | Bruitages comiques posés à 0,55 sans écoute. | Bruitage comique à 0,2 au plus. Rire et moquerie seulement sur demande de Lucien. |
| Avant/après peu parlant | Comparatif sur un seul cas client. | Un avant/après montre la même vidéo : 15 s sans montage, puis 15 s montées. |
| Rendu complet arrêté sur une tranche (« durationInFrames must be positive ») | Un segment d'écran recalculé durait moins d'une image. | Aucun segment ni recadrage de moins d'une image : un bout de tête est absorbé par le segment suivant. Contrôle chiffré avant rendu. |
| Connexion SSH coupée par son propre `pkill -f` | Le motif apparaît dans la ligne de commande de la session SSH elle-même. | Arrêter une unité systemd (`systemctl stop`), jamais `pkill -f` lancé par SSH. |
| Chaîne arrêtée après le rendu : liste des morceaux de son vide | Script écrit par un heredoc dans `ssh '…'` : l'apostrophe a fermé la commande et les variables se sont vidées. | Écrire le script en local, l'envoyer par `scp`, puis `bash -n` avant de lancer. |
| 0,26 s d'image noire à l'entrée d'un asset plein écran (A80, 1000 h, 20/10/2026) | Scène ouverte 0,25 s avant son premier élément ; le fond de l'asset apparaissait en fondu avec le contenu ; en plein écran la caméra n'est plus dessous. Le contrôle « image vide » ne couvrait que l'intro. | Fond opaque dès la première image d'un plein écran, ou caméra gardée dessous jusqu'au fond opaque. `cloud/controles/images_noires.py VIDEO` sur toute la vidéo avant envoi : code 1 = pas d'envoi. |
| Texte d'un écran web avec bandeau cookies | — | Masquer le bandeau par CSS, ne jamais cliquer « Accepter ». Vérifier trois images. |
| Écran qui « sature », « lag » et sursaute (13:05, v8) | Quatre transitions visuelles (flash, fuite, glitch) posées en v3 sur des coupes. Les EDL ont déplacé les coupes, les calques sont restés : écart de 1,2 à 9,8 s, en plein plan. Le glitch imite un écran qui saute. | Aucun flash, fuite ni glitch. Seules les montées sonores de chapitre restent. Contrôle : aucune `mia-pro-transition` visuelle dans les props. |
| Zoom « Maya » ou « Sam » qui montre le script | Les segments écran 3D suivent la voix. À ce moment, l'OBS montrait le Google Doc du script. Le zoom visait la bonne position, sur la mauvaise image. | Scanner chaque segment écran (une image par 0,5 s) : plus de 60 % de pixels blancs signale un document. Regarder chaque image signalée. Script visible : reprendre une image du même écran où l'objet nommé apparaît, sinon passer en caméra. Mesurer la plage propre au dixième de seconde, jamais sur une planche à 1 image/s (v9 : départ à 1303 s, script visible jusqu'à 1304,4 s). Studio OBS 184935 propre de 1304,5 à 1313,5 s. Contrôler la première image du plan corrigé, puis une image toutes les 0,2 s. |
| Chiffres qui sautent et changent de police (12:33, « 17,3 centimes », « 34 minutes ») | Un des onglets de rendu n'avait pas Barlow. Une image sur huit à dix sortait en police de secours à empattements. La tranche a été rendue sans erreur, donc mise en cache. | `rendu_tranches.py` contrôle chaque tranche (`images_isolees`) et la relance s'il trouve une image isolée. `flashs_police.py VIDEO PROPS` contrôle la vidéo entière avant envoi : zéro image isolée exigé. |

## Ordre des contrôles avant le rendu final

1. Appliquer l'EDL, puis `mots_tranches.py`. Envoyer la liste à Lucien.
2. Construire la coupe : `construire_v8.py` (coupes hors créneaux d'insert, fins de mots validées, plans de 3 images lissés).
3. Rendre la base : seuls les morceaux changés repartent. Un morceau intact doit rester identique à l'octet près, sinon le cache saute.
4. Voix : `voix_v5.py` puis `voix_combler.py` pour les bouts absents de la voix traitée.
5. Props : `integrer_v8.py` sans sous-titres, `gen_extras.py`, puis `integrer_v8.py`.
6. Contrôles chiffrés : zéro segment de moins d'une image, zéro chevauchement de sous-titres, zéro sous-titre sur un début de plein cadre, zéro plan de 1 à 3 images, zéro trou de 1 à 3 images entre pleins cadres.
7. Images de contrôle : chaque chiffre à l'état final, chaque carré caméra, chaque insert.
8. Contrôles bloquants, à mettre dans la chaîne de rendu avant l'envoi :
   - `ecrans_sans_script.py --props PROPS --valides <plans blancs voulus>` : chaque segment écran 3D lu toutes les 0,1 s dès sa première image. Code 1 = pas d'envoi.
   - `rendu_tranches.py` relance toute tranche qui contient une image isolée (police de secours).
   - `flashs_police.py VIDEO PROPS` sur la vidéo muette assemblée : zéro image isolée exigé.
9. Plan corrigé à la demande de Lucien : contrôler sa première image et chaque image jusqu'à la fin de l'entrée, jamais une seule image au milieu.
8. Son des motions : vérifier qu'aucune composition ne rejoue une voix.

## Panneau vide en début de scène (15/10/2026)

- **Défaut :** la scène démarre sur le premier mot de la phrase. Son premier élément attend un mot plus loin. Le panneau reste vide environ 1 s.
- **Cause :** début de scène et cues calés sur des mots différents. Aucun contrôle avant le rendu complet.
- **Contrôle :** ouvrir chaque scène 0,25 s avant son premier cue (`timeline.py`, défaut). Rendre une image à +0,4 s de chaque début en basse résolution (`controle_debuts.mjs`). `panneaux_vides.py` doit sortir en 0 avant le rendu complet.

### Caméra éclair, voile lourd, animation coupée (vidéo 1000 h, retours du 21/10/2026)
- **Défaut :** la caméra de Lucien apparaît 0,08 s après le flash de l'intro. Ses textes sur caméra portent un voile noir flou à 58 %. La jauge « Débutant » est coupée au bout de 0,56 s.
- **Cause :** les ancres mot à mot compressent un plan caméra de la référence. Le contraste a été obtenu par une boîte sombre. `plan_blocs.py` tronque une pose quand la suivante commence, sans regarder son animation.
- **Contrôle :** `controles/plan.py` dans la porte (`plan` dans chantier.json) : caméra seule ≥ 0,8 s, trou entre poses ≥ 0,5 s, aucune pose tronquée hors `valides.tronques`. Textes sur caméra : voile en dégradé radial large et léger, jamais de boîte ni de carré (réglage du 21/10 dans `texte-camera-sans-voile`), essai en image fixe avant rendu. La caméra interne de l'intro se vérifie à la main sur W(ref).
