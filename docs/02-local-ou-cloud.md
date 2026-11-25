# Local ou cloud

> Un mot inconnu ? Il est expliqué dans [00-lexique.md](00-lexique.md).

Claude Code tourne à deux endroits : sur ton ordinateur (local) ou sur un ordinateur distant (cloud).
Le choix change l'endroit où la vidéo est fabriquée.

## Comparatif

| Critère | Local (ton Mac) | Cloud (claude.ai/code) |
|---|---|---|
| Où tourne le calcul | Sur ton ordinateur | Sur une machine Linux d'Anthropic |
| Où sont les rushs | Sur ton disque | Téléchargés à chaque session depuis un lien |
| Disque disponible | Le tien | 30 Go par session |
| Ce qui reste après | Tout | Seulement ce qui est poussé ou envoyé ailleurs |
| Ton ordinateur | Occupé pendant les rendus | Libre, même éteint |
| Installation | ffmpeg, Python, Node à installer une fois | Script `scripts/installer.sh` relancé à chaque session |
| Quota Claude | Ton abonnement Max | Ton abonnement Max |

## Recommandation

Commence en **local**. Les rushs 4K pèsent plusieurs dizaines de Go.
En cloud, il faut les héberger derrière un lien direct, puis renvoyer chaque rendu ailleurs.
Sans stockage en ligne à toi, le cloud ajoute ce travail à chaque session.

Passe en **cloud** si ton ordinateur est trop lent ou si tu veux lancer un rendu et partir.
Prépare alors un stockage en ligne avec des liens directs.
Un lien direct télécharge le fichier sans passer par une page web.
Exemples : Dropbox (lien terminé par `?dl=1`), Google Drive public, ou un espace de stockage S3 ou R2.

## Mise en route en local

```bash
bash scripts/installer.sh --no-open
bash scripts/verifier-poste.sh
cp .env.example .env    # puis remplis tes clés
claude
```

Mesure Lucien : version vierge d'une vidéo de 35 min en 8 à 12 min sur un Mac Apple Silicon.
Un ordinateur plus ancien prend plus longtemps. Claude mesure le débit sur deux morceaux avant d'annoncer une durée.

## Mise en route en cloud

1. Ouvre https://claude.ai/code et connecte ton compte GitHub.
2. Choisis le dépôt `scalai-montage-ia`.
3. Crée un environnement. Mets tes clés dans ses variables d'environnement.
4. Dans le script de démarrage de l'environnement, écris `bash scripts/installer.sh --no-open`.
5. Donne à Claude les liens directs de tes rushs dans le premier message.
6. Demande-lui où envoyer les rendus avant la fin de la session.

Une session cloud n'a pas de carte graphique, la puce qui accélère la vidéo. Les rendus y sont plus lents.
Un rendu de plus de 2 h se découpe en morceaux fabriqués en même temps.
