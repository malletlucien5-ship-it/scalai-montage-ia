---
type: skill-reference
date: 2026-10-11
status: active
tags: [motion-design, remotion, bibliotheque, vsl, ai-advantage, son]
project: martell-motion-cloud
---

Animations signature de la VSL « AI Advantage », validée le 11/10/2026. Cette fiche sert à les réutiliser dans une autre vidéo. Skill parent : [[Skills/recreer-motion-design/SKILL|recreer-motion-design]].

Les cartes texte génériques (`Card.tsx`) et les b-roll restent hors de cette bibliothèque.

## Où sont les choses

| Élément | Emplacement |
|---|---|
| Code | `~/CODE/ai-advantage-vsl`, branche `claude/ai-advantage-vsl` du dépôt martell-motion-cloud |
| Composants | `remotion/src/comps/ai-advantage/` |
| Compositions seules | `Compositions.tsx` : `AIA-Intro`, `AIA-Titre`, `AIA-Horloge`, `AIA-Nom`, `AIA-Plan`, `AIA-Logo`, `AIA-Motion`, `AIA-Flash`, `AIA-Prix`, `AIA-Etapes`, `AIA-CTA` |
| Composition maître | `AIA-Master` (`Master.tsx`), plan écrit par `tools/aia_master.py` |
| Intro et son | `tools/aia_intro.py` (chronologie de l'intro), `tools/aia_audio.py` (mix, bruitages, ducking) |
| Rendu | `remotion/tools/aia-master-render.sh`, `aia-master-tranches.sh`, `aia-stills.mjs` |
| Médias (serveur) | `<serveur-de-lucien>:/srv/ai-advantage/motion/remotion/public/` |
| Archive des médias | Storage Box `outputs/bibliotheque-motion/ai-advantage-2026-10-11.tgz` (267 481 098 octets, 91 fichiers) |
| Manifeste | `qa/bibliotheque/MANIFEST.json` (chemin, octets, sha256, source, licence) |
| Planche | `qa/bibliotheque/planche-bibliotheque.jpg`, 2 images clés par animation |
| Plan final de référence | `plans/master-v3-final.json` dans l'archive |

Format commun : plaque 2560x1440, 50 i/s. Toutes les cotes du code sont en px 1080p, multipliées par `k = hauteur / 1080`. Le bleu de marque est `#1A5CFF` (`theme.ts`).

## Règles communes

- Ancrer chaque animation sur les mots de la transcription (cue). Ne jamais poser une animation sur des secondes fixes.
- Écrire les cues dans `cues.json`, puis générer le plan avec `aia_master.py`. Ne jamais éditer `master.json` à la main.
- Lancer le rendu sur le serveur Hetzner. Aucun calcul sur le Mac.
- Contrôler deux images par placement avant toute livraison.

Forme d'un calque dans le plan Master :

```json
{"id": "NAME-lucien", "type": "nom", "de": 24.14, "a": 25.62, "opaque": false, "plein": true, "cue": "NAME-lucien", "props": {}}
```

- `de`, `a` : secondes de la plaque.
- `opaque: true` : le calque cache la plaque (plans, prix, étapes, logo, horloge).
- `plein: true` : aucun sous-titre pendant le calque.
- Ordre d'empilement (`NIVEAU` dans `Master.tsx`) : plan 0, cartes et écrans 1, nom et CTA 2, flash 3, puis sous-titres.

Forme d'un bruitage dans `plan.sons` (lu par `aia_audio.py`) :

```json
{"t": 3.916, "pic": 4.4, "quoi": "whoosh", "fichier": "sfx/faq/whoosh.wav", "gain_db": -15.6, "calque": "INTRO"}
```

- `t` : départ du fichier. `pic` : instant du maximum d'énergie. `t = pic - pic du fichier`.

Commande de rendu seul, sur le serveur :

```bash
ssh -i <cle-ssh-de-lucien> <serveur-de-lucien>
cd /srv/ai-advantage/motion/remotion
nice -n 10 npx --no-install remotion render src/index.ts AIA-Intro ../out/intro.mp4 \
  --codec=h264 --crf=16 --color-space=bt709 --concurrency=16 --props=../props/intro.json --log=error
```

- Remplacer `AIA-Intro` par la composition voulue.
- Omettre `--props` pour garder les valeurs par défaut (valeurs du plan final validé).
- Pour un calque transparent (`AIA-Nom`, `AIA-Flash`, `AIA-CTA`), ajouter `--codec=prores --prores-profile=4444 --pixel-format=yuva444p10le --image-format=png`.
- Pour une image fixe, lister les images dans un JSON et lancer `nice -n 10 node tools/aia-stills.mjs liste.json`.

Commande de rendu du Master complet :

```bash
cd /srv/ai-advantage/motion/remotion
tools/aia-master-tranches.sh ../out/final.mp4 --plan ../PLAN.json --scale 1 --tranche 3000 --concurrency 40 --crf 16
```

## 1. Intro « TEMPS »

**Usage.** Ouvrir une VSL sur le mot clé de la promesse. Un mot géant en police très fine passe sur six fonds noir et blanc. Une horloge à palettes bascule ensuite de 4:59 à 5:00.

**Moment du discours.** Règle de la référence (Igor, 4,77-8,675 s) :

- Trois sous-titres d'accroche d'abord (« J'ai envie de vous parler du TEMPS… »).
- Le titre couvre la phrase thèse qui définit le mot clé. Exemple : « Parce que le temps est la seule chose dont vous ne pouvez pas créer davantage. »
- Le titre est plein 0,07 s après l'attaque du premier mot de la phrase.
- L'horloge part à la fin du dernier mot de la phrase. Elle dure 0,5 s.

**Composants.** `Title.tsx` (prop `fonds`) puis `Horloge.tsx`, en coupe franche. Composition seule : `AIA-Intro`.

**Exemple de props (`AIA-Intro`).**

```json
{
  "titre": {
    "mot": "TEMPS",
    "sousTitre": "La seule chose dont vous ne pouvez pas créer davantage.",
    "duree": 3.54,
    "fonds": [
      {"src": "hd/broll-libre/TITLE.mp4", "de": 0.0, "debut": 1.0},
      {"src": "intro-v4/fonds/F2-horloge-murale.mp4", "de": 0.766, "debut": 0.0},
      {"src": "intro-v4/fonds/F3-wagon.mp4", "de": 1.32, "debut": 0.0},
      {"src": "hd/broll-libre/TITLE-b.mp4", "de": 1.843, "debut": 0.5},
      {"src": "intro-v4/fonds/F5-quai.mp4", "de": 2.43, "debut": 0.0},
      {"src": "intro-v4/fonds/F6-foule.mp4", "de": 3.018, "debut": 0.0}
    ]
  },
  "horloge": {"duree": 0.5, "avant": ["4", "59"], "apres": ["5", "00"], "bascule": 0.13, "dureeBascule": 0.1, "poussee": 1.035}
}
```

- `fonds[].de` : secondes depuis le début du calque titre. `debut` : point d'entrée dans la vidéo.
- Les coupes suivent les proportions de la référence : 0 ; 0,568 ; 1,135 ; 1,669 ; 2,269 ; 2,870 (fractions de 3,404 s).
- `aia_intro.py` met ces coupes à l'échelle de la phrase. Garder ce calcul pour une phrase plus longue ou plus courte.
- Prop `particules: false` pour retirer les confettis blancs. Prop `espacement` (em) pour l'interlettrage.

**Médias.**

| Rôle | Fichier dans `public/` | Source |
|---|---|---|
| Fond 1, escalier de métro | `hd/broll-libre/TITLE.mp4` | Pexels 853874 |
| Fond 2, horloge murale x4 | `intro-v4/fonds/F2-horloge-murale.mp4` | Mixkit 28886 |
| Fond 3, wagon flou | `intro-v4/fonds/F3-wagon.mp4` | Mixkit 4333 |
| Fond 4, ville à l'aube | `hd/broll-libre/TITLE-b.mp4` | Pexels 32324777 |
| Fond 5, quai | `intro-v4/fonds/F5-quai.mp4` | Mixkit 1622 |
| Fond 6, foule x2 | `intro-v4/fonds/F6-foule.mp4` | Mixkit 4180 |
| Nappe | `sons-libres/musique/echoes.wav` | Mixkit 188 |
| Percussions | `sons-libres/musique/epical-drums-01.wav` | Mixkit 676 |
| Bruitages | `sons-libres/sfx/*.wav`, `sfx/faq/whoosh.wav` | Mixkit, Freesound CC0, Epidemic |
| Mix de référence | `intro-v4/audio-intro-v4-mix.m4a` et son rapport | rendu du 11/10 |

Le composant Title met chaque fond en noir et blanc (`grayscale(1) contrast(1.12) brightness(0.82)`). Ajouter un vignettage radial. Les fonds Mixkit sont déjà convertis en N&B.

**Minutage exact (secondes de la plaque, VSL AI Advantage).** Ancres : « Parce » à 4,34 s (voix audible à 4,40 s). Fin de « davantage » à 7,64 s (voix éteinte à 7,80 s).

| Instant | Image | Son |
|---|---|---|
| 0,00 | Visage, sous-titres Poppins de l'accroche | Nappe Echoes entre : source 18 s, gain +4,5 dB, passe-haut 90 Hz, fondu 0,1 s |
| 3,916 | Visage | Départ du whoosh (pic 4,40 s, gain -15,6 dB) |
| 4,26 | Début du calque titre. Le sous-titre s'arrête à cette image | Nappe baissée de 6 dB en 0,15 s |
| 4,33 | Balayage diagonal, bande sombre, confettis (0,5 s) | Percussions Epical Drums 01 : source 4,6 s, gain -4,8 dB, fondu 0,02 s |
| 4,47 | Titre plein sur le fond 1. Le mot se pose de 1,33 à 1,0 en 0,35 s | |
| 4,704 | | Pic du boom grave (-4,6 dB) |
| 5,026 | Coupe vers le fond 2 | |
| 5,58 | Coupe vers le fond 3 | |
| 5,692 | | Cliquet long (+11,4 dB) |
| 6,103 | Coupe vers le fond 4 | |
| 6,279 | | Cliquet court (-2,6 dB) |
| 6,435 | | Pic de l'impact trailer (-7,6 dB) |
| 6,69 | Coupe vers le fond 5 | |
| 6,846 | | Pic du coup grave (-11,6 dB) |
| 7,278 | Coupe vers le fond 6 | |
| 7,80 | Coupe franche vers l'horloge 4:59, poussée lente de +3,5 % | |
| 7,91 | | Mécanisme (cliquet court, -8,6 dB) |
| 7,93 | Les palettes tombent (0,1 s) | Pic du clac des palettes (-5,6 dB) |
| 8,03 | 5:00 posé | |
| 8,30 | Coupe franche vers le visage, sous-titres Bebas | |
| 8,67 | | Fondu de sortie des percussions (0,6 s) |
| 12,0 | | Relais vers « Trace » (fondu d'entrée 3 s) |
| 13,0-16,0 | | Fondu de sortie de la nappe |

Formules dans `aia_intro.py` :

- `plein = début de « Parce » + 0,06 + 0,07`.
- `début du titre = plein - 0,21`.
- `horloge = fin de « davantage » + 0,16`, pendant 0,5 s.
- `bascule = horloge + 0,13`.
- Bruitages : instant de la référence ramené par `p(t) = plein + (t - 4,771) × (durée de la phrase / 3,404)`.

**Niveaux de mix.** Écart fond (musique + bruitages) moins voix, mesuré sur le mix final :

| Section | Plage | Cible | Mesuré | Référence |
|---|---|---|---|---|
| Nappe avant le titre | 0,3-4,16 s | -10 LU | -10,0 LU | -17,8 LU |
| Titre et horloge | 4,36-8,30 s | -3,5 LU | -4,0 LU | -7,0 LU |
| Nappe après l'horloge | 9,1-12,0 s | -14 LU | -13,6 LU | -24,4 LU |

- Voix : -16,2 LUFS, jamais traitée. Mix : -16,2 LUFS, crête -1,4 dBTP.
- Lucien a demandé ces niveaux au-dessus de la référence (11/10). Il veut entendre la musique sur un haut-parleur de téléphone.
- Bruitages : crêtes de la référence + 2,7 dB (écart de voix) + 3,4 dB (rehausse demandée).

**Ducking.** `sidechaincompress` sur les couches de l'intro, clé = voix. Seuil 0,06, ratio 2, attaque 20 ms, relâche 350 ms, genou 4. Limiteur du bus de l'intro à -8 dB. « Trace » reste à -22,8 dB, sans ducking.

**Insertion dans un plan Master.**

1. Écrire le cue `TITLE` dans `cues.json` : ancres « Parce » et « davantage », `texte_ecran.titre`, `texte_ecran.sous_titre`, `masque_sous_titres: true`.
2. Générer le plan : `/srv/ai-advantage/venv/bin/python tools/aia_master.py --cues ... --out PLAN.json`.
3. Retoucher l'intro : `/srv/ai-advantage/venv/bin/python tools/aia_intro.py --plan PLAN.json`. Le script refuse un plan déjà retouché.
4. Mixer : `/srv/ai-advantage/venv/bin/python tools/aia_audio.py --plan PLAN.json`. Lire le rapport `intro` et comparer les écarts aux cibles.
5. Le script ajoute le calque `CLOCK-horloge` (type `horloge`, opaque) et retire la plaque pendant l'horloge.

## 2. Horloge à palettes

**Usage.** Marquer le temps qui passe, en plan noir et blanc de 0,5 s. Utilisable seule après n'importe quelle phrase sur le temps ou une échéance.

**Moment du discours.** À la fin d'une phrase sur le temps, dans le silence avant la phrase suivante. Référence : fin de « of. » à 8,17 s, horloge 8,175-8,675 s, reprise de la voix à 8,85 s.

**Composant.** `Horloge.tsx`, composition `AIA-Horloge`, type de calque `horloge`.

```json
{"duree": 0.5, "avant": ["4", "59"], "apres": ["5", "00"], "bascule": 0.13, "dureeBascule": 0.1, "poussee": 1.035}
```

- `avant`, `apres` : heures puis minutes. Les deux blocs basculent ensemble.
- `bascule` : début de la chute, en secondes depuis le début du plan. Défaut du composant : 0,215 s (référence).
- La VSL utilise 0,13 s pour poser 5:00 avant la reprise de la voix.

**Sons.** `sons-libres/sfx/palettes-clac.wav` (pic 0,052 s) posé sur la bascule. `sons-libres/sfx/cliquet-court.wav` 0,02 s avant.

**Insertion.** Calque `{"type": "horloge", "opaque": true, "plein": true}`. Retirer la plaque sur la même plage (`plaque.visibles`), comme `aia_intro.py`.

**Rendu seul.** `remotion render src/index.ts AIA-Horloge ../out/horloge.mp4 --props='{"duree":0.5}'`.

## 3. Bandeau nom

**Usage.** Présenter Lucien à l'écran.

**Moment du discours.** Sur « je m'appelle Lucien », jusqu'à la fin de la proposition. VSL : 24,14-25,62 s. Référence : 27,56-31,5 s.

**Composant.** `Name.tsx`, composition `AIA-Nom`, type `nom`, calque transparent.

```json
{"nom": "LUCIEN", "role": "FONDATEUR, SCALAI", "duree": 1.48}
```

- Entrée 0,6 s : la barre bleue se déroule, le nom monte de derrière le masque.
- Sortie 0,5 s, mouvement inverse.
- Options : `hautBarre` (y 1080p, défaut 929), `couleurRole` (défaut `#18130B`).

**Son.** Whoosh `sfx/faq/whoosh.wav` à -19 dB, pic à `de + 0,1 s`.

**Insertion.** Cue `NAME` avec `texte_ecran.nom`, `texte_ecran.titre`, `masque_sous_titres: true`.

## 4. Portrait fondateur

**Usage.** Montrer Lucien et sa société, juste après le nom.

**Moment du discours.** Sur « j'ai fondé ScalAI ». VSL : 25,72-27,16 s. Référence : 31,6-35,27 s.

**Composant.** `Plan.tsx`, `rendu: "portrait"`, composition `AIA-Plan`, type `plan`.

```json
{"rendu": "portrait", "duree": 1.44, "image": "lucien-photo.png", "titre": "SCALAI", "legende": "FONDÉE IL Y A 3 ANS", "tailleGrand": 120}
```

- Fond sombre quadrillé avec lueur bleue (`FondPreuve`).
- La photo glisse depuis la gauche en 0,45 s. Le texte entre à 0,12 s (`debutTexte`).

**Médias.** `lucien-photo.png`.

**Sons.** Whoosh à `de`. Impact `sfx/faq/impact.wav` (-21 dB) à `de + debutTexte`.

**Insertion.** Entrée `broll.json` (type `PROOF`, `chemin_public: lucien-photo.png`). Ajouter son id à `RENDU_BROLL` avec `rendu='portrait'`.

## 5. Carte 3D : chaîne YouTube qui défile

**Usage.** Appuyer un chiffre de preuve sociale avec la vraie chaîne de Lucien.

**Moment du discours.** Sur la phrase qui cite le chiffre. VSL : « J'ai cumulé plus de 3 millions de vues sur tous mes réseaux », 30,78-32,86 s. Référence : 39,41-42,11 s.

**Composant.** `Plan.tsx`, `rendu: "carte3d"`, composition `AIA-Plan`.

```json
{
  "rendu": "carte3d", "duree": 2.08, "rotY": 14,
  "morceaux": [{"de": 0, "duree": 2.08, "src": "broll-existant/mur-yt-chaine-0.mp4", "image": false, "debut": 0}],
  "chiffre": "+3 MILLIONS", "legendeLignes": ["de vues sur tous mes", "réseaux"],
  "debutTexte": 0.64, "tailleGrand": 98.09
}
```

- La carte pivote de `rotY + 14°` à `rotY` en 0,5 s et pousse de +3 %.
- `chiffre` : Poppins 800 italique bleu, à droite.
- `debutTexte` = début du mot chiffré moins `de` (31,42 - 30,78 = 0,64 s).
- Sans `chiffre` ni `titre`, la carte s'élargit et se centre.
- `defilement: true` fait glisser l'image de 5 % vers le haut. La vidéo de la chaîne défile déjà seule : ne pas l'activer avec ce média.

**Médias.** `broll-existant/mur-yt-chaine-0.mp4` (page de chaîne qui défile, 1920x1080, 5 s).

**Sons.** Whoosh à `de`. Impact à `de + debutTexte`.

**Sous-titres.** Ils restent affichés (`masque_sous_titres: false`).

## 6. Mur 3D de miniatures

**Usage.** Montrer le volume de contenus de Lucien sur une phrase de mission.

**Moment du discours.** Sur la phrase qui décrit ce que fait Lucien. VSL : « prendre ce qui semble déconcertant avec l'IA et le décomposer… », 34,64-37,84 s. Référence : 44,21-47,35 s.

**Composant.** `Plan.tsx`, `rendu: "mur3d"`, composition `AIA-Plan` (props par défaut).

```json
{"rendu": "mur3d", "duree": 3.2, "rotX": 20, "rotZ": -9,
 "morceaux": [{"de": 0, "duree": 3.2, "src": "broll-existant/mosaique.mp4", "image": false, "debut": 0}]}
```

- Entrée : recul de 1,18 à 1 en 0,5 s.
- Défilement diagonal lent : -2,5 % en x, -4 % en y sur la durée.
- Vignettage sombre sur les bords.
- Durée maximale : 3,2 s (`MUR_DUREE`).

**Médias.** `broll-existant/mosaique.mp4` (2560x1440, 6,06 s).

**Sons.** Whoosh à `de`.

**Insertion.** Cue `PROOF-miniatures`. `aia_master.py` pose le mur seul si aucun autre plan n'occupe le cue.

## 7. Flash de transition

**Usage.** Passer d'un plan à un autre, ou entrer sur un écran plein.

**Moment du discours.** Sur un changement d'idée. La coupe tombe sur le mot du cue `FLASH`. Avant chaque écran prix, un flash `entree` finit au début de l'écran.

**Composant.** `Flash.tsx`, composition `AIA-Flash`, type `flash`.

```json
{"mode": "complet", "intensite": 1, "fusion": "ecran"}
```

| Mode | Durée | Usage |
|---|---|---|
| `complet` | 1,0 s | Transition entre deux plans. Coupe à 0,33 s. `de = mot - 0,33` |
| `entree` | 0,33 s | Avant un écran plein. Finit sur le blanc |
| `sortie` | 0,67 s | Après un écran plein. Part du blanc |

Chronologie : lueur de coin 0-0,17 s, voile ciel-bleu-violet 0,1-0,27 s, pic blanc 0,27-0,35 s, voile clair qui descend jusqu'à 1,0 s.

**Son.** Whoosh -19 dB au pic (`de + 0,33`).

**Insertion.** Cue `FLASH`. `aia_master.py` retire un flash qui chevauche un plan opaque ou un autre flash.

## 8. Motion « tâche » et « réexplications »

**Usage.** Illustrer une phrase quand aucun b-roll libre ne colle. Identité : fond crème pailleté, éclairs dorés 3D, bleu, Poppins.

**Moment du discours.**

- `tache` : sur une comparaison avant/maintenant chiffrée. VSL : « Une tâche qui prenait avant 1 h se règle maintenant en quelques minutes », 259,4-262,3 s.
- `reexplications` : sur une énumération de frustrations. VSL : « Davantage de réexplications, davantage de résultats génériques… », 482,4-485,46 s.

**Composant.** `Motion.tsx`, composition `AIA-Motion`, type `plan` avec `rendu: "motion"`.

```json
{"rendu": "motion", "scene": "tache", "duree": 2.9,
 "textes": {"titre": "Une tâche", "avant": "AVANT", "avantDuree": "1 H", "apres": "MAINTENANT", "apresDuree": "QUELQUES\nMINUTES"},
 "temps": {"avant": 0.15, "uneHeure": 1.1, "apres": 1.4}}
```

```json
{"rendu": "motion", "scene": "reexplications", "duree": 3.06,
 "textes": {"fenetre": "Assistant IA", "compteur": "Réexplications", "message": "Je te réexplique : mon offre, mes clients, mon ton…",
            "reponse": "Voici quelques conseils généraux pour développer votre activité…", "tampon": "GÉNÉRIQUE"},
 "temps": {"reexplications": -0.02, "generique": 1.78}}
```

- `temps` : secondes depuis le début du plan. Caler chaque clé sur le mot prononcé.
- `tache` : la barre « avant » se remplit jusqu'à `uneHeure`. La ligne « maintenant » entre à `apres`, puis la coche.
- `reexplications` : trois bulles bleues à 0,12, 0,5 et 0,88 s après `reexplications`. La réponse s'écrit à `generique`. Le tampon arrive 0,55 s après.

**Son.** Whoosh à `de`.

**Insertion.** Entrée `broll.json` avec `asset.statut: "motion"` et `asset.rendu` = props ci-dessus. Ancre `ancre_fr.plaque_v3_s`. Le calque sort `plein: true`, donc sans sous-titres.

## 9. Écrans de l'offre : prix, étapes, CTA

Ces trois écrans portent du texte, mais leur mise en page sert à toute VSL d'offre. Ils s'enchaînent dans cet ordre.

### Prix

**Moment.** Sur l'annonce du prix. VSL : « Pour 0 euros, je vais vous guider… », 285,3-288,06 s.

**Composant.** `Price.tsx`, composition `AIA-Prix`, type `prix`.

```json
{"ligne1": "Mon accompagnement", "ligne2": "900 €", "barre": true, "prix": "0 €", "echelleTitre": 0.808, "duree": 2.76}
```

- Entrée depuis le blanc : violet, bleu, puis noir en 0,6 s. Éclair de verre qui glisse depuis la gauche en 0,75 s.
- Prix lettre par lettre : flou 28 px vers net, départ 0,2 s, pas de 0,11 s.
- Poser un flash `entree` de `de - 0,33` à `de`. `aia_master.py` le fait seul.
- Sons : whoosh à `de`, impact à `de + 0,45`.

### Étapes

**Moment.** Juste après le prix, sur la durée ou la méthode. VSL : « Comptez environ une heure de votre temps… », 288,06-291,08 s.

**Composant.** `Steps.tsx`, composition `AIA-Etapes`, type `etapes`.

```json
{"ligne1": "Comptez environ", "ligne2Sans": "UNE HEURE", "ligne2Serif": "de votre temps", "ligne3": "PAS SEULEMENT DE LA THÉORIE",
 "vignetteVideo": "ai-advantage/plaque-v3-etal.mp4", "vignetteDebut": 288.06, "vignetteCadrage": "51% 30%", "echelle3": 0.737, "duree": 3.02}
```

- Entrée en coupe franche. Vignette du visage en bas à droite : la plaque lue à `vignetteDebut = de`.
- Sons : whoosh à `de`, impact à `de + 0,2`.

### CTA

**Moment.** Sur « cliquez sur le bouton » jusqu'à la fin de l'appel. VSL : 511,4-518,22 s.

**Composant.** `Cta.tsx`, composition `AIA-CTA`, type `cta`, calque transparent.

```json
{"bouton": "CLIQUEZ SUR LE BOUTON", "ligne1": "DANS LA DESCRIPTION", "ligne2": "ACCÈS IMMÉDIAT", "duree": 6.82}
```

- Le CTA apparaît d'un coup au pic blanc d'un flash `complet`. Poser le flash à `de - 0,33`.
- Chevrons qui rebondissent de 22 px, période 1,67 s.
- Son : impact à `de + 0,35`.

## 10. Logo sur clavier

**Usage.** Afficher l'outil cité par Lucien, posé sur un plan de clavier sombre.

**Moment du discours.** Sur le nom de l'outil. VSL : « On va construire votre clone ensemble avec Claude », 294,42-296,32 s.

**Composant.** `LogoPlan` dans `Plan.tsx`, composition `AIA-Logo`, type `logo`.

```json
{"fond": "vsl/brolls/clavier.mp4", "fondDebut": 1.05, "logo": "ai-advantage/claude.svg", "mot": "Claude", "duree": 1.9}
```

- `fondDebut = max(0 ; 3,0 - durée - 0,05)` : le plan finit avant la fin du fichier de 3 s.
- Logo et mot en Playfair blanc. Entrée : échelle 0,9 vers 1 et fondu en 0,35 s.
- Sons : whoosh à `de`, impact à `de + 0,2`.

**Médias.** `vsl/brolls/clavier.mp4` (Pexels 8128358) et `ai-advantage/claude.svg`. Remplacer le SVG pour un autre outil.

## Sons des transitions (hors intro)

| Fichier | Gain | Pose |
|---|---|---|
| `sfx/faq/whoosh.wav` (pic 0,451 s) | -19 dB | Début de plan 3D, motion, titre, logo, étapes, prix ; pic d'un flash complet ; nom + 0,1 s |
| `sfx/faq/impact.wav` (pic 0,356 s) | -21 dB | Texte d'une preuve, titre et logo + 0,2 s, prix + 0,45 s, CTA + 0,35 s |
| `musique/trace_lennon-hutton.wav` | -22,8 dB | Fond de toute la vidéo, en boucle, fondus 1 s et 2 s |

Aucun whoosh sur un recadrage PUNCH. Aucun son d'interface.

## Restaurer la bibliothèque

1. Restaurer le code depuis git :

```bash
cd ~/CODE/martell-motion-cloud
git fetch origin claude/ai-advantage-vsl
git worktree add ~/CODE/ai-advantage-vsl claude/ai-advantage-vsl
```

2. Signer une URL de lecture depuis le Mac. Ne jamais afficher la clé ni l'URL signée :

```bash
cd ~/CODE/martell-motion-cloud/cloud && set -a && . ~/.config/scalai/credentials.env && set +a
U=$(/usr/bin/python3 -c "import storage_gateway as g;print(g.signed_url('outputs/bibliotheque-motion/ai-advantage-2026-10-11.tgz','GET',seconds=3600))")
```

3. Télécharger l'archive sur le serveur de rendu :

```bash
printf '%s' "$U" | ssh -i <cle-ssh-de-lucien> <serveur-de-lucien> \
  'U=$(cat); curl -sS -o /tmp/biblio.tgz "$U" && ls -l /tmp/biblio.tgz && sha256sum /tmp/biblio.tgz'
```

4. Vérifier l'archive : 267 481 098 octets, sha256 `dff305121dc01a907b60b2be53565d6d3cbbdd2e8480a41e6bf9ef3058161a08`.
5. Extraire : `mkdir -p /tmp/biblio && tar xzf /tmp/biblio.tgz -C /tmp/biblio`.
6. Vérifier chaque fichier avec `MANIFEST.json` (sha256 par fichier).
7. Copier les médias dans le projet : `rsync -a /tmp/biblio/public/ <projet>/remotion/public/`.
8. Les chemins de `public/` restent ceux du code. Aucune prop n'est à changer.

Contenu de l'archive :

- `MANIFEST.json` à la racine.
- `plans/master-v3-final.json` : plan final validé, intro comprise.
- `public/intro-v4/` : quatre fonds Mixkit et mix de référence de l'intro.
- `public/sons-libres/` : nappe, percussions, bruitages de l'intro, originaux et `LICENCES.md`.
- `public/sfx/` : kit Epidemic du funnel (whoosh, impact, etc.).
- `public/musique/trace_lennon-hutton.wav`.
- `public/fonts/` : polices woff2 des sous-titres et des cartes.
- `public/broll-existant/mosaique.mp4` et `mur-yt-chaine-0.mp4`.
- `public/lucien-photo.png`.
- `public/broll-libre/TITLE*.mp4` (originaux Pexels) et `public/hd/broll-libre/TITLE*.mp4` (copies lues par le rendu).
- `public/vsl/brolls/clavier.mp4` et `public/ai-advantage/claude.svg` (plan logo).

Licences : Mixkit et Pexels autorisent l'usage commercial sans attribution. Freesound 261244 est en CC0. Les fichiers Epidemic (`sfx/`, « Trace ») demandent l'abonnement de Lucien et la chaîne déclarée. Les vidéos `broll-existant/` et la photo appartiennent à Lucien.

## Pièges

| Piège | Règle |
|---|---|
| Flash sur fond crème | La fusion `ecran` éclaircit seulement les zones sombres. Sur un fond crème ou blanc, le flash disparaît. Poser le flash sur la plaque, avant l'écran plein. Sur un fond clair, passer `fusion: "normal"`. La fusion agit seulement dans la même composition : rendre la plaque sous le flash dans Remotion. |
| Sous-titres sur un plein écran | Aucun sous-titre pendant un calque `plein`. `aia_master.py` arrête un bloc 20 ms avant et retire un bloc de moins de 0,25 s. `aia_intro.py` coupe le bloc à l'image exacte où le titre et l'horloge commencent. Vérifier `masque_sous_titres: true` dans chaque cue d'écran plein. Les motions crème sortent `plein: true`. |
| Cache des tranches | Une tranche se reprend seulement si le plan, la plaque et les réglages sont identiques. `aia-master-tranches.sh` signe sha256 du plan, taille et date de la plaque, échelle, CRF, taille de tranche. Une signature différente vide le cache. Ne jamais copier des tranches d'un autre rendu à la main. |
| Plaque sans image clé régulière | Préparer la plaque avec `-g 25 -keyint_min 25 -sc_threshold 0` : une image clé toutes les 0,5 s. `OffthreadVideo` recherche chaque coupe de `plaque.visibles`. Sans ces images clés, chaque recherche décode de longues portions et le rendu ralentit. Même règle pour les copies `hd/`. |
| Étalonnage appliqué deux fois | Appliquer l'étalonnage une seule fois, à la plaque (`plaque-v3-etal.mp4`). Ne rien ajouter dans Remotion ni à l'export. La voix vient de la plaque non étalonnée (`plaque.voix`). La vignette des étapes lit la plaque déjà étalonnée. |
| Nombre d'images de la plaque | `aia-v3-final.sh` refuse une plaque dont le nombre d'images diffère de la coupe (26 450 pour la VSL). Garder ce verrou pour une nouvelle vidéo. |
| Plan de 1 à 3 images | `aia_intro.py` et `aia_master.py` signalent un plan de moins de 4 images autour de l'horloge et des pleins cadres. Un trou de moins de 0,4 s entre deux pleins cadres est comblé. |
| Musique inaudible au téléphone | Lucien a rejeté l'intro aux niveaux de la référence. Garder les écarts -10 / -3,5 / -14 LU et vérifier le rapport `intro` d'`aia_audio.py`. |

Voir aussi [[Skills/recreer-motion-design/references/erreurs|erreurs]] et [[Skills/recreer-motion-design/references/garde-fous-montage|garde-fous-montage]].
