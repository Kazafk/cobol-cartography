> Voir aussi : [[Architecture-technique]] | [[Backlog-MVP]] | [[Decisions-architecture]] | [[Home]]

# Structure de projet recommandée

## Monorepo recommandé

```text
cobol-cartography/
  README.md
  docs/
  extension/
  backend/
  parser/
  packages/
  samples/
  tests/
  deployment/
```

## Dossier `extension`

```text
extension/
  package.json
  tsconfig.json
  src/
    extension.ts
    commands/
    views/
    webviews/
    api/
    config/
  media/
  test/
```

Responsabilités :

- Extension VS Code.
- Commandes.
- Tree views.
- Webviews.
- Client API backend.

## Dossier `backend`

```text
backend/
  pyproject.toml
  src/
    main.py
    api/
    indexing/
    graph/
    rag/
    ai/
    security/
    config/
  tests/
```

Responsabilités :

- API.
- Orchestration indexation.
- RAG.
- IA.
- Sécurité.

## Dossier `parser`

```text
parser/
  build.gradle
  src/
    main/
      java/
    test/
      java/
```

Responsabilités :

- Parsing COBOL.
- Prétraitement.
- Extraction modèle intermédiaire.

## Dossier `packages`

```text
packages/
  shared-model/
  graph-schema/
  prompt-templates/
```

Responsabilités :

- Types partagés.
- Schémas JSON.
- Prompts versionnés.

## Dossier `samples`

```text
samples/
  mini-portfolio/
    cobol/
    copybooks/
    jcl/
    db2/
```

Responsabilités :

- Patrimoine de test.
- Démonstrations.
- Non-régression.

## Dossier `deployment`

```text
deployment/
  docker/
  docker-compose.yml
  helm/
  scripts/
```

Responsabilités :

- Déploiement local.
- Déploiement serveur.
- Packaging.

## Convention de branches

Branches :

- `main`
- `develop`
- `feature/*`
- `fix/*`
- `spike/*`

## Convention de documentation

Documents à maintenir :

- Architecture decision records.
- Schéma graphe.
- Spécification API.
- Guide développeur.
- Guide installation.
- Guide sécurité.

