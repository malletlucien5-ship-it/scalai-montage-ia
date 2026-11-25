# Remotion Lambda sur AWS

## Préconditions

Lire la région dans AWS Settings ou dans `~/.aws/config`. Créer toutes les ressources régionales dans cette région. Vérifier le plan :

```bash
aws freetier get-account-plan-state --profile PROFIL
```

Vérifier aussi le plafond de dépenses dans AWS Settings. Un projet suspendu peut renvoyer `AccessDenied` après avoir fonctionné.

## Profils

Utiliser un profil humain temporaire pour les commandes AWS. Utiliser un profil dédié pour le SDK Remotion.

```bash
aws sts get-caller-identity --profile remotion-project >/dev/null
aws configure get region --profile remotion-project
```

Renouveler une session expirée :

```bash
aws login --profile remotion-project
```

Les scripts lisent les noms de profils et la région depuis leur configuration. Ils n'affichent aucune clé.

## Import d'un fichier de clés

Lire l'emplacement du fichier depuis la carte d'infrastructure. Garder les valeurs hors des journaux et des arguments de commande.

Importer un CSV AWS sans afficher son contenu :

```bash
aws configure import --csv file:///chemin/credentials.csv
chmod 600 ~/.aws/credentials
aws sts get-caller-identity --profile PROFIL >/dev/null
```

Déplacer le CSV vers la corbeille après la réussite du contrôle STS. Ajouter seulement son emplacement et son usage à la carte d'infrastructure.

## Politiques et SCP

Valider les politiques Remotion :

```bash
cd "$REMOTION_DIR"
AWS_PROFILE=remotion-project npx remotion lambda policies validate
```

Une politique IAM valide peut rester bloquée par la SCP gérée du projet. Relever l'action refusée dans l'erreur. Vérifier les services autorisés pour le plan du projet. Garder Lambda, S3 et CloudWatch dans la région sélectionnée.

## Déploiement

Épingler la même version pour Remotion et `@remotion/lambda`.

```bash
cd "$REMOTION_DIR"
AWS_PROFILE=remotion-project npx remotion lambda functions deploy \
  --memory=3008 --disk=10240 --timeout=900

AWS_PROFILE=remotion-project npx remotion lambda sites create src/index.ts \
  --site-name=motion-project

AWS_PROFILE=remotion-project npx remotion lambda quotas
```

La concurrence de toutes les fonctions d'un rendu doit rester sous la limite du projet. Un rendu à la fois avec six fonctions internes convient à une limite de dix.

## Rendu

```bash
AWS_PROFILE=remotion-runtime REMOTION_AWS_REGION="$REGION" \
  npx remotion lambda render motion-project COMPOSITION SORTIE \
  --frames=DEBUT-FIN --codec=h264 --crf=12 \
  --frames-per-lambda=250 --log=info
```

Pour un calque alpha :

```bash
AWS_PROFILE=remotion-runtime REMOTION_AWS_REGION="$REGION" \
  npx remotion lambda render motion-project COMPOSITION SORTIE.mov \
  --frames=DEBUT-FIN --codec=prores --prores-profile=4444 \
  --pixel-format=yuva444p10le --image-format=png \
  '--props={"showPlate":false}'
```

Lire le coût estimé dans la sortie. Additionner les essais ratés et les seconds rendus. Le montant AWS final peut arriver plus tard.

## Cache

Calculer une empreinte avec :

- la commande Lambda sans la concurrence ;
- la plage d'images ;
- les fichiers partagés ;
- le dossier de la composition ;
- le dossier public de la composition ;
- les props.

Écrire l'empreinte après le téléchargement et le contrôle `ffprobe`. Garder les autres compositions en cache.

## Diagnostic

1. Vérifier `aws sts get-caller-identity`.
2. Vérifier la région du profil.
3. Vérifier l'état du plan et le plafond de dépenses.
4. Lire l'action refusée par AWS.
5. Relancer `policies validate`.
6. Vérifier la SCP du projet.
7. Contrôler la concurrence et le délai de la fonction.
8. Vérifier le déploiement du site après chaque changement de code.
