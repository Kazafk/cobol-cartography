# Contrats API

> Voir aussi : [[Architecture-technique]] | [[API-Backend]] | [[Journal-developpement]] | [[Runbook]]

Contrats HTTP entre l'extension VS Code et le backend.
Base URL : `http://localhost:8000` (configurable via `cobolCartography.backendUrl`).

Légende : ✅ Implémenté · 🔲 À implémenter

---

## Epic 1 — Santé et capacités ✅

### GET /api/health ✅

```json
{
  "status": "ok",
  "version": "0.1.0"
}
```

### GET /api/capabilities ✅

```json
{
  "ai_mode": "local_strict",
  "features": ["indexing", "graph", "impact"],
  "parser_version": "0.1.0",
  "graph_backend": "sqlite"
}
```

---

## Epic 2 — Indexation ✅

### POST /api/index/workspace ✅

Requête :
```json
{
  "workspacePath": "C:/Repos/Bank-of-Z/src/base/cics",
  "copybookPaths": ["C:/Repos/Bank-of-Z/src/base/cics/copy"],
  "sourceFormat": "fixed",
  "incremental": true
}
```

Réponse `200 OK` :
```json
{
  "jobId": "idx-3f2a1b4c",
  "status": "completed",
  "programs": 28,
  "copybooks": 40,
  "jclJobs": 4,
  "errors": 0,
  "unresolvedCopybooks": 3,
  "graphNodes": 85,
  "graphEdges": 142
}
```

Erreur `422` si `workspacePath` n'est pas un répertoire existant.

---

### GET /api/inventory/programs ✅

```json
[
  {
    "path": "C:/Repos/Bank-of-Z/src/base/cics/cobol/BNKMENU.cbl",
    "relative_path": "cobol/BNKMENU.cbl",
    "kind": "program",
    "size_bytes": 14820,
    "sha256": "a3f2..."
  }
]
```

### GET /api/inventory/copybooks ✅

Même structure, `"kind": "copybook"`.

### GET /api/inventory/jobs ✅

Même structure, `"kind": "jcl"`.

---

### GET /api/inventory/copybook-refs ✅

Query params : `resolved=true|false` (optionnel)

```json
[
  {
    "member_name": "ACCOUNT",
    "source_file": "C:/Repos/.../BNKMENU.cbl",
    "line": 78,
    "resolved_path": "C:/Repos/.../copy/ACCOUNT.cpy",
    "is_resolved": true
  },
  {
    "member_name": "DFHAID",
    "source_file": "C:/Repos/.../BNK1CAC.cbl",
    "line": 67,
    "resolved_path": null,
    "is_resolved": false
  }
]
```

---

### GET /api/inventory/dependencies ✅

Query params : `kind=call|perform|exec_cics|exec_sql` (optionnel)

```json
[
  {
    "kind": "call",
    "source_file": "C:/Repos/.../BANKDATA.cbl",
    "line": 1876,
    "target": "CEEGMT",
    "target_is_literal": true,
    "detail": null
  },
  {
    "kind": "exec_cics",
    "source_file": "C:/Repos/.../BNK1CCA.cbl",
    "line": 459,
    "target": "LINK",
    "target_is_literal": true,
    "detail": "BNK1CAC"
  },
  {
    "kind": "exec_sql",
    "source_file": "C:/Repos/.../BANKDATA.cbl",
    "line": 676,
    "target": "INSERT",
    "target_is_literal": true,
    "detail": "CUSTOMER"
  },
  {
    "kind": "perform",
    "source_file": "C:/Repos/.../BNK1CAC.cbl",
    "line": 174,
    "target": "SEND-MAP",
    "target_is_literal": true,
    "detail": null
  }
]
```

---

## Epic 3 — Graphe ✅

### GET /api/programs ✅

```json
[
  {
    "id": "program:BNKMENU",
    "kind": "program",
    "name": "BNKMENU",
    "path": "C:/Repos/.../BNKMENU.cbl",
    "properties": { "size_bytes": 14820, "sha256": "a3f2..." }
  }
]
```

---

### GET /api/programs/{name}/dependencies ✅

`name` est le nom du programme (insensible à la casse, ex. `BNKMENU` ou `bnkmenu`).

```json
{
  "program": {
    "id": "program:BNKMENU",
    "kind": "program",
    "name": "BNKMENU",
    "path": "C:/Repos/.../BNKMENU.cbl",
    "properties": {}
  },
  "outgoing": [
    {
      "relation": "INCLUDES_COPYBOOK",
      "confidence": 1.0,
      "line": 65,
      "node": {
        "id": "copybook:BNK1MAI",
        "kind": "copybook",
        "name": "BNK1MAI",
        "path": "C:/Repos/.../copy/BNK1MAI.cpy",
        "properties": {}
      }
    },
    {
      "relation": "CICS_LINKS_PROGRAM",
      "confidence": 1.0,
      "line": 304,
      "node": {
        "id": "program:BNK1CAC",
        "kind": "program",
        "name": "BNK1CAC",
        "path": null,
        "properties": {}
      }
    },
    {
      "relation": "READS_TABLE",
      "confidence": 1.0,
      "line": 52,
      "node": {
        "id": "db2table:CUSTOMER",
        "kind": "db2table",
        "name": "CUSTOMER",
        "path": null,
        "properties": {}
      }
    }
  ],
  "incoming": [
    {
      "relation": "EXECUTES_PROGRAM",
      "confidence": 1.0,
      "line": 3,
      "node": {
        "id": "jcl_step:DB2BIND:BIND",
        "kind": "jcl_step",
        "name": "BIND",
        "path": null,
        "properties": { "program": "BNKMENU", "job": "DB2BIND" }
      }
    }
  ]
}
```

Erreur `404` si le programme n'est pas dans le graphe.

Relations possibles en sortie : `INCLUDES_COPYBOOK`, `CALLS_PROGRAM`, `CICS_LINKS_PROGRAM`, `CICS_XCTLS_PROGRAM`, `READS_TABLE`, `WRITES_TABLE`, `UPDATES_TABLE`, `DELETES_FROM_TABLE`.

Relations possibles en entrée : `CALLS_PROGRAM`, `CICS_LINKS_PROGRAM`, `EXECUTES_PROGRAM`.

---

## Epic 4 — Visualisation VS Code ⏳

### GET /api/programs/{name}/sheet ✅

`name` insensible à la casse. Erreur `404` si le programme n'est pas dans le graphe.

```json
{
  "name": "BNKMENU",
  "path": "C:/Repos/.../BNKMENU.cbl",
  "size_bytes": 14820,
  "metrics": {
    "copybooks_included": 3,
    "programs_called": 2,
    "tables_accessed": 1,
    "called_by_count": 0,
    "executed_by_jobs": 1
  },
  "copybooks": ["BNK1MAI", "BNK1ACC", "DFHAID"],
  "calls": [
    { "name": "BNK1CAC", "relation": "CICS_LINKS_PROGRAM", "line": 304 }
  ],
  "called_by": [],
  "tables": [
    { "name": "CUSTOMER", "access": "READ" }
  ],
  "executed_by": [
    { "job": "DB2BIND", "step": "BIND" }
  ]
}
```

Accès tables possibles : `READ`, `WRITE`, `UPDATE`, `DELETE`.

### GET /api/graph/export ✅

Export D3.js pour la webview graphe (US-032).

```json
{
  "nodes": [
    { "id": "program:BNKMENU", "kind": "program", "name": "BNKMENU", "path": "C:/Repos/.../BNKMENU.cbl" },
    { "id": "copybook:BNK1MAI", "kind": "copybook", "name": "BNK1MAI", "path": "C:/Repos/.../copy/BNK1MAI.cpy" },
    { "id": "db2table:CUSTOMER", "kind": "db2table", "name": "CUSTOMER", "path": null }
  ],
  "links": [
    { "source": "program:BNKMENU", "target": "copybook:BNK1MAI", "relation": "INCLUDES_COPYBOOK", "confidence": 1.0 },
    { "source": "program:BNKMENU", "target": "db2table:CUSTOMER", "relation": "READS_TABLE", "confidence": 1.0 }
  ]
}
```

Retourne l'intégralité du graphe. Filtrage par kind côté client (webview).

---

## Epic 5 — Analyse d'impact ⏳

### GET /api/impact/copybook/{name} ✅

`name` insensible à la casse. Erreur `404` si le copybook n'est pas dans le graphe.

```json
{
  "copybook_name": "ACCOUNT",
  "direct_impacts": [
    { "name": "INQACC", "depth": 1, "via": null, "confidence": 1.0 }
  ],
  "indirect_impacts": [
    { "name": "MENU", "depth": 2, "via": "INQACC", "confidence": 1.0 }
  ],
  "uncertain_impacts": [],
  "impacted_jobs": [
    { "name": "BATCHJOB" }
  ],
  "total_programs": 2,
  "total_jobs": 1
}
```

Traversal : BFS inversé depuis le copybook → `INCLUDES_COPYBOOK` (depth=1) → remontée transitive `CALLS_PROGRAM` / `CICS_LINKS_PROGRAM` / `CICS_XCTLS_PROGRAM` (depth≥2). Jobs via `EXECUTES_PROGRAM` de tout programme visité.

### GET /api/impact/table/{name} ✅

`name` insensible à la casse. Erreur `404` si la table n'est pas dans le graphe.

```json
{
  "table_name": "CUSTOMER",
  "readers":  [{ "name": "INQCUST", "confidence": 1.0 }],
  "writers":  [{ "name": "CRECUST", "confidence": 1.0 }],
  "updaters": [{ "name": "UPDCUST", "confidence": 1.0 }],
  "deleters": [],
  "associated_jobs": [{ "name": "BATCHJOB" }]
}
```

Relations graphe utilisées : `READS_TABLE` → readers · `WRITES_TABLE` → writers · `UPDATES_TABLE` → updaters · `DELETES_FROM_TABLE` → deleters. Jobs via `EXECUTES_PROGRAM` depuis tous les programmes accédant à la table.

---

## Post-MVP — Jobs JCL

### GET /api/jobs/{name}/programs ✅

`name` insensible à la casse. Erreur `404` si le job n'est pas dans le graphe.

```json
{
  "job_name": "BATCHJOB",
  "steps": [
    {
      "step_name": "STEP1",
      "program_name": "BNKMENU",
      "program_path": "C:/Repos/Bank-of-Z/src/base/cics/cobol/BNKMENU.cbl"
    },
    {
      "step_name": "STEP2",
      "program_name": "EXTPGM",
      "program_path": null
    }
  ],
  "total_programs": 2
}
```

`program_path` est `null` si le programme n'est pas dans le workspace (stub). `total_programs` = cardinal de l'ensemble dédupliqué des programmes sur toutes les étapes.

Traversal graphe : `jcl_job:{NAME}` → `HAS_STEP` → `jcl_step:JOB:STEP` → `EXECUTES_PROGRAM` → `program:{NAME}`.

---

## Epic 6 — IA 🔲

### POST /api/ai/explain/program ✅

Requête :
```json
{ "programId": "BNKMENU", "detailLevel": "standard", "includeBusinessRules": true }
```

Réponse `200 OK` :
```json
{
  "program_id": "BNKMENU",
  "detail_level": "standard",
  "mode": "local_strict",
  "ai_mode": "local_strict",
  "summary": {
    "role": "BNKMENU est un programme COBOL qui inclut 3 copybook(s), appelle 2 programme(s), accède à 1 table(s) DB2.",
    "complexity_indicators": { "copybooks_included": 3, "programs_called": 2, "tables_accessed": 1, "called_by_count": 0, "executed_by_jobs": 1 }
  },
  "interactions": {
    "copybooks": ["BNK1MAI"],
    "outgoing_calls": [{ "target": "BNK1CAC", "mechanism": "CICS LINK" }],
    "table_accesses": [{ "table": "CUSTOMER", "operations": ["READ"] }],
    "executed_by_jobs": ["DB2BIND"]
  },
  "business_rule_candidates": [
    { "description": "Consultation de la table CUSTOMER", "confidence": 0.75, "evidence": "EXEC SQL READ ... FROM/INTO CUSTOMER" }
  ],
  "uncertainties": [
    "Les CALL dynamiques (cibles variables) ne sont pas tracés dans le graphe."
  ]
}
```

Erreur `404` si le programme n'est pas dans le graphe. Aucun appel LLM externe (`mode: local_strict`).

### POST /api/ai/explain/selection 🔲

```json
{
  "programId": "BNKMENU",
  "startLine": 120,
  "endLine": 180
}
```
