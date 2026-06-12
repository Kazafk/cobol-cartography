> Voir aussi : [[Architecture-technique]] | [[IA-RAG-Agents]] | [[Securite-Confidentialite]] | [[Backlog-MVP]] | [[Home]]

# API backend

## Objectif

Définir une API initiale entre l’extension VS Code et le serveur d’analyse.

## Endpoints système

### GET `/health`

Retourne l’état du backend.

Réponse :

```json
{
  "status": "ok",
  "version": "0.1.0",
  "graph": "connected",
  "ai": "enabled"
}
```

### GET `/capabilities`

Retourne les fonctionnalités disponibles.

## Indexation

### POST `/index/workspace`

Lance l’indexation d’un workspace.

Requête :

```json
{
  "workspacePath": "/path/to/workspace",
  "copybookPaths": ["copybooks"],
  "sourceFormat": "fixed",
  "incremental": true
}
```

Réponse :

```json
{
  "jobId": "idx-20260514-001",
  "status": "started"
}
```

### GET `/index/jobs/{jobId}`

Retourne l’état d’un job d’indexation.

## Inventaire

### GET `/inventory/programs`

Liste les programmes.

### GET `/inventory/copybooks`

Liste les copybooks.

### GET `/inventory/jobs`

Liste les jobs JCL.

### GET `/inventory/tables`

Liste les tables DB2.

## Programme

### GET `/programs/{programId}`

Retourne la fiche technique d’un programme.

### GET `/programs/{programId}/dependencies`

Retourne les dépendances entrantes et sortantes.

### GET `/programs/{programId}/graph`

Retourne un sous-graphe centré sur le programme.

## Analyse d’impact

### POST `/impact/analyze`

Requête :

```json
{
  "sourceType": "copybook",
  "sourceId": "CPY-CUSTOMER",
  "depth": 3,
  "includeIndirect": true
}
```

Réponse :

```json
{
  "source": {
    "type": "copybook",
    "id": "CPY-CUSTOMER"
  },
  "directImpacts": [],
  "indirectImpacts": [],
  "uncertainImpacts": [],
  "paths": []
}
```

## IA

### POST `/ai/explain/program`

Requête :

```json
{
  "programId": "PGM-CUSTOMER-UPDATE",
  "detailLevel": "standard",
  "includeBusinessRules": true
}
```

### POST `/ai/explain/selection`

Requête :

```json
{
  "programId": "PGM-CUSTOMER-UPDATE",
  "startLine": 120,
  "endLine": 180
}
```

### POST `/ai/documentation/program`

Génère une fiche programme Markdown.

## Validation métier

### POST `/business-rules/{ruleId}/validate`

Requête :

```json
{
  "status": "validated",
  "comment": "Règle confirmée par l’équipe applicative."
}
```

## Export

### POST `/export/documentation`

Génère un export Markdown ou JSON.

Requête :

```json
{
  "scope": "application",
  "applicationId": "APP-CLAIMS",
  "format": "markdown"
}
```

