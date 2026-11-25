# Contrôles communs des montages

Une seule copie des contrôles, importée par tous les chantiers. Aucun chantier ne les recopie.
Audit d'origine : `Intelligence/audits/2026-10-20-audit-erreurs-montage` (vault de Lucien).

## Dans une routine cloud

Récupérer les contrôles depuis `main`, quelle que soit la branche du chantier :

```bash
git fetch origin main && git checkout origin/main -- controles
pip install numpy "opencv-python-headless<5"
```

Livrer un master uniquement par `livrer.py` :

```bash
python3 -m controles.livrer "cameron1 - motion.mp4" --chantier chantier.json \
  --plaque "cameron1 - sobre.mp4" --put "$PUT_MASTER" \
  --etat-local etat.md --etat-put "$PUT_ETAT" --planche-put "$PUT_PLANCHE"
```

- Code 1 : un contrôle bloquant a échoué. Rien n'est envoyé. L'état reçoit la ligne « ÉCHEC ».
- Le guet de prod lit l'état et écrit ses alertes dans `alertes.jsonl`, lu par `guet etat`. Jamais de Telegram pour un montage (règle du 20/10/2026).
- `--sec` lance les contrôles sans rien envoyer.

## chantier.json

`--quarantaine URL_PUT` garde le master refusé dans un dossier `quarantaine/` de la Storage Box.
Le Mac ne rapatrie jamais ce dossier. Une routine suivante télécharge ce master et relance `livrer.py`.
Le rendu ne se refait donc pas après un faux positif. Règle du 25/10/2026 : deux masters perdus avec leur conteneur.

Le fichier décrit le chantier. `livrer.py` le valide avant tout contrôle.

```json
{
  "nom": "cameron1",
  "type": "pub",
  "etape": "motion",
  "rushs": [{"nom": "DJI_0120.MP4", "sha256": "…"}],
  "voix": {"source": "obs", "obs_disponible": true, "phrases_attendues": ["…"]},
  "coupes": {"source": "edl", "fichier": "coupes.edl", "sha256": "…", "cadence": 50,
             "images_master": 1832, "par_lucien": true,
             "raccords_lucien_s": [3.2, 7.84], "raccords_auto_s": []},
  "etalonnage": {"choisi": "look-a", "choisi_par_lucien": true},
  "elements_valides": ["sous-titres", "zoom-yeux", "carte-chiffre-10h"],
  "polices": ["Helvetica Neue"],
  "cadrage": {"yeux": 0.34, "tolerance": 0.06},
  "son": {"musique": "stems/musique.wav", "voix": "stems/voix.wav", "dossiers_bruitages": ["sons/"]},
  "remotion": "moteur-v4/v2",
  "plan": "moteur-v4/v2/plan/v4.plan.json",
  "arrets": {"board": "public/board/board.json", "encres": "public/board/encres.json", "manifeste": "arrets/arrets.json"},
  "valides": {"noires": [], "flashs": [], "superposition": [], "visage": [], "saturation": []}
}
```

| Étape | Exigé en plus |
|---|---|
| plaque | nom, rushs avec sha256, voix OBS si un OBS existe |
| sobre | coupes validées par Lucien, cadence et nombre d'images, étalonnage choisi par Lucien |
| motion, final | liste blanche `elements_valides` ; pour une copie, `copie.reference` et `copie.inventaire` ; `plan` et `arrets` si le moteur porte un plan à arrêts |

`panneau.gauche_px` (format `montage-podcast`) : « visage couvert » cherche le visage sur le master, à droite du panneau, au lieu de sa place sur la plaque (21/11/2026).

`valides` : exceptions validées par Lucien, plage par plage. `noires` et `flashs` en images du master ; `visage` (pleins écrans voulus) et `saturation` (écran blanc voulu sur la plaque) en secondes `[debut_s, fin_s]`. `musique_ecart` : `[min, max]` en dB, remplace la plage -15 à -9 quand Lucien demande la musique plus basse (10/11/2026). Tout ce qui sort de ces plages reste bloquant (25/10/2026).

## Contrôles

| Module | Contrôle | Bloquant | Incident d'origine |
|---|---|---|---|
| image | images noires | oui | 13 images noires, 20/10 ; 16 panneaux vides, 15/10 |
| image | images isolées | oui | 84 plans d'une image, 09/10 |
| image | pixels brûlés (plaque) | oui | 15 à 20 % brûlés, 02/10 |
| image | visage couvert (motion contre sobre) | oui | 01, 02, 14, 15/10 |
| image | cadrage des yeux | si `cadrage` est donné | tête trop basse, 17/10 |
| son | niveau et crête | oui | aperçus saturés, 19/10 |
| son | silences | oui | aperçu muet, 19/10 |
| son | musique sous la voix | oui | musique à 0,085, 14/10 |
| son | bruitages en WAV | oui | aperçus lqmp3, 19/10 |
| voix | durée égale à la timeline | oui | coupes modifiées, 07 et 10/10 |
| voix | mots coupés aux raccords | raccords automatiques seulement | 04 au 10/10 |
| voix | phrases du tournage | oui | phrase supprimée, 10/10 ; Marvin v4, 17/10 |
| source | polices du chantier présentes | oui | Inter, 15/10 ; Liberation, 19/10 ; DejaVu, 10/10 |
| source | modèles périmés | oui | Opus 4.7 à l'écran, 15/10 |
| source | liens symboliques dans public/ | oui | 404 Remotion, 13 et 15/10 |
| copie | superposition toutes les 0,2 s et planche | oui | trois versions sur des scores, 18-19/10 |
| cadrage | texte coupé par le panneau, bloc cité, trait sur le texte, diapositive sans puce | oui, dès que le plan porte des arrêts | v4 viral X à 11 contrôles OK, 01/11 |
| arrets | images fixes et planche faites avant rendu, sur ce plan, sans faute | oui, dès que le plan porte des arrêts | v4 viral X, 01/11 |

`modeles-actuels.json` liste les noms périmés. Le mettre à jour à chaque nouvelle génération de modèles.

## Rendu en tranches (10/11/2026)

Cause : le final cabinets du 09/11 est parti en quarantaine à 23 h 25 pour deux fausses alertes, Lucien couché.
Chaque tranche lance le contrôle d'image dès son rendu, avant l'assemblage :

```bash
python3 -m controles.tranche "tranche 2 video.mp4" --debut-image 24000 --chantier chantier.json \
  --etat-local etat.md --etat-put "$PUT_ETAT" --planche "alertes tranche 2.jpg" --planche-put "$PUT_ALERTES"
```

- `--debut-image` : rang dans le master de la première image de la tranche. Les alertes sortent en images du master.
- Contrôles : images noires et images isolées, avec les plages `valides` de `chantier.json`.
- L'état reçoit une ligne « ALERTE tranche » par alerte, avec la plage à inscrire dans `valides` si Lucien valide.
- La planche montre chaque image en alerte. Elle part à Lucien avant l'assemblage.
- Code 0 : ce contrôle ne bloque rien. La porte reste `controles.livrer`.

## Tests

`python3 -m unittest controles.test_controles controles.test_cadrage` sur prod ou en CI (`.github/workflows/controles.yml`). Jamais sur le Mac.


## Copie d'une référence sur une autre timeline (26/10/2026)

Cause : le motion de Yas posé sur la vidéo IA entreprise a été livré sans comparaison à la référence.
`chantier.json` portait le type « youtube ». La superposition n'a jamais tourné.

- `type` vaut « copie » dès qu'un motion recopie une référence.
- `copie.correspondance` relie chaque placement à sa plage de la référence : `[{id, mode, ref: [a, b], copie: [a, b], boite_ref}]`, temps en secondes.
- `copie.par_placement` produit une planche par placement (référence à gauche, copie à droite) et un écart chiffré indicatif.
- `copie.halo_sombre` bloque tout calque qui assombrit plus de 1 % de l'image par rapport au sobre. Étalonné sur le master du 25/10 : textes au halo noir de 1,4 à 8 %, logos propres sous 0,5 %.
- Étape finale : `copie.revue` porte « conforme » pour chaque placement, après lecture de sa planche.
- Étape finale : `copie.apercu_valide_par_lucien` vaut vrai. Aucun rendu final avant l'accord de Lucien sur l'aperçu motion.

## Ce qui se voit aux arrêts (01/11/2026)

Cause : la v4 viral X a passé 11 contrôles alors que 10 arrêts sur 24 coupaient des textes. Aucun contrôle ne regardait l'écran.
Le premier regard est venu après le rendu. Le contrôle et les images fixes passent donc avant.
Un plan à arrêts est un fichier `{plans: [...]}` avec au moins un plan `etat: board` et ses `arrets`.

### Avant tout rendu

Préparer une fois les boîtes d'encre, puis lancer l'étape après chaque changement du plan :

```bash
python3 -m controles.cadrage encres public/board/board.json TRANCHES/ public/board/encres.json
python3 -m controles.arrets avant-rendu plan/v4.plan.json --remotion moteur --sortie arrets \
  --board public/board/board.json --encres public/board/encres.json
```

- Sortie : une image `F.png` par arrêt et par trait, `planche-arrets.jpg`, `rapport-cadrage.md`, `arrets.json`.
- Code 1 : une faute ou une image absente. Corriger le plan et relancer. Les images déjà rendues restent.
- Bandeau rouge sur la planche : arrêt en faute. Bandeau jaune : image absente.
- Lire la planche avant le rendu. Le contrôle ne juge pas le contenu.
- Tourne en session cloud ou sur la machine du chantier, jamais sur le Mac : Chromium rend chaque image.
- La composition `PanneauV4` reçoit `{plan, images: [f]}` et montre l'image `f` à son image 0. `--composition` en change le nom.

### À la livraison

`livrer.py` lance deux contrôles bloquants quand `plan` porte des arrêts, aux étapes motion et final :

- `cadrage des arrêts` relit le master, panneau découpé selon `plan.panneau` (défaut x 853, 1707x1440). Rapport : `MASTER - cadrage.md`.
- `images fixes des arrêts` exige `arrets.manifeste`, avec l'empreinte du plan livré et zéro faute.
- `valides.cadrage` liste les fautes vues et acceptées par Lucien, sous la forme `plan/type/n` : `34/trait/1`.
- `arrets.board` ou `arrets.encres` absent : échec. Un contrôle sauté a laissé passer la v4.
- `chantier.py` refuse un moteur qui contient un plan à arrêts sans `plan` dans `chantier.json`.

### Règles et valeurs

| Règle | Valeur |
|---|---|
| Texte et bord du panneau | 8 px panneau au moins, encre mesurée |
| Bloc cité (`bloc` de l'arrêt, sinon texte du trait) | entier, 40 px de marge |
| Image hors du bloc | peut sortir du cadre |
| Pixels rouges du trait sur l'encre | 0,5 % au plus |
| Colonnes d'un soulignement sous du texte | 85 % au moins |
| Diapositive avec son seul titre | 1,5 s au plus |
| Contenu du panneau à l'arrêt | relevé au rapport, non bloquant |

Le test rejoue l'incident sur `fixtures/viral-x/` : 29 fautes sur le plan v4, 0 sur le plan v4b. La fixture garde les boîtes du board et une découpe JPEG de chaque trait, prises sur les masters livrés.
Le chiffre de 27 du 01/11 vient d'une version de travail non committée. Le contrôle d'origine donne 29 sur `board.tar` et le paquet v4, comme ce portage.
Le test `test_images_fixes_par_remotion` rend de vraies images par `remotion-essai/`. Il tourne seulement en CI.
