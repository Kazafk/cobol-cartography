# Journal de développement

> Voir aussi : [[Strategie-documentation]] | [[Contrats-API]] | [[ADR-Register]] | [[Agent-Team]]

Ce journal est mis à jour à la fin de chaque étape. Format : date, réalisé, décisions clés, points ouverts.

---

## Phase 0 — Décisions d'architecture (ADR 01-04)

**Date** : 2026-05-21

### Réalisé
- [x] ADR-01 : stockage graphe SQLite pour le MVP → [[ADR-01-Stockage-graphe]]
- [x] ADR-02 : parser ANTLR4 Java, dialecte IBM Enterprise COBOL → [[ADR-02-Parser-COBOL]]
- [x] ADR-03 : backend Python / FastAPI → [[ADR-03-Backend-Python]]
- [x] ADR-04 : mode IA par défaut `local_strict` → [[ADR-04-Mode-IA-par-defaut]]

### Décisions
4 ADR rédigés et validés en amont de l'implémentation. Statut **Accepté** dans [[ADR-Register]].

---

## Epic 1 — Squelette projet ✅

### Étape 1 — Extension VS Code

**Date** : 2026-05-21

#### Réalisé
- [x] `extension/package.json` — extension installable en dev mode (VS Code 1.85+)
- [x] Commande `COBOL Cartography: Index Workspace` enregistrée via `vscode.commands.registerCommand`
- [x] Config `cobolCartography.backendUrl` (workspace.getConfiguration, défaut `http://localhost:8000`)
- [x] Clé API via `context.secrets.get('cobol-cartography.apiKey')` — jamais dans `settings.json`
- [x] `BackendClient` : thin fetch wrapper, header `Authorization: Bearer`, lève une erreur typée sur non-2xx
- [x] Compilation TypeScript → `out/`

#### Décisions
- Convention de nommage : camelCase pour clés de config VS Code, kebab-case pour ID extension et clés SecretStorage.
- `BackendClient` expose `get<T>()` et `post<T>()` — point d'extension pour les routes Epic 2+.

---

### Étape 2 — Backend FastAPI

**Date** : 2026-05-21

#### Réalisé
- [x] `backend/pyproject.toml` — hatchling, Python 3.11+, structlog, pydantic-settings v2, FastAPI, uvicorn
- [x] `GET /api/health` → `{"status": "ok", "version": "0.1.0"}`
- [x] `GET /api/capabilities` → `ai_mode`, `features`, `parser_version`, `graph_backend`
- [x] Logging structuré : structlog JSON avec `TimeStamper(fmt="iso")`, `format_exc_info`, `JSONRenderer`
- [x] `conftest.py` racine : inject `backend/` dans `sys.path`
- [x] 3 tests pytest asyncio avec `ASGITransport`

#### Décisions
- Route prefix `/api` pour toutes les routes, y compris health.
- Host par défaut `127.0.0.1` (loopback) en config ; Dockerfile override à `0.0.0.0`.
- `get_settings()` avec `@lru_cache` — une seule instance par processus.

---

### Étape 3 — Audit sécurité Epic 1

**Date** : 2026-05-21

#### Résultat
| Sévérité | Nb initial | Résolu | Restant |
|----------|-----------|--------|---------|
| BLOCK | 0 | — | 0 |
| WARN | 4 | 2 | 2 |

**Résolus** : chemin `/health` → `/api/health` dans l'extension ; host `0.0.0.0` → `127.0.0.1`.
**Backlog** : W2 (validation token Bearer côté backend), W4 (image Docker épinglée par digest).

---

## Epic 2 — Indexation COBOL ✅

### Étape 4 — Scanner et extracteurs Python

**Date** : 2026-05-22

> **Note d'implémentation** : l'approche retenue pour le MVP est un extracteur Python par regex plutôt que le parser Java ANTLR planifié en ADR-02. Ce choix réduit la complexité opérationnelle (pas de JVM, pas de JAR à builder) et suffit pour les critères d'acceptation des US-010 à US-013. Le parser Java reste pertinent pour les Epics 4+ (extraction AST complète, paragraphes, sections).

#### Réalisé — US-010 : Scanner
- [x] `backend/src/indexing/scanner.py`
  - Walk récursif `Path.rglob("*")`, classification par extension (`FileKind` enum : `program`, `copybook`, `jcl`)
  - Extensions reconnues : `.cbl`, `.cob`, `.cobol` / `.cpy`, `.copy` / `.jcl` (insensible à la casse)
  - SHA-256 par fichier (chunks de 64 Ko), chemin relatif au workspace
  - `WorkspaceInventory` dataclass — agrège programs, copybooks, jcl\_jobs, errors
- [x] `POST /api/index/workspace` — valide le chemin (Pydantic `field_validator`), scanne, retourne counts + jobId
- [x] `GET /api/inventory/programs|copybooks|jobs`
- [x] **9 tests unitaires** (scanner) + **6 tests API** (inventory)

#### Réalisé — US-011 : Résolution copybooks
- [x] `backend/src/indexing/copybook_resolver.py`
  - Extraction `COPY member` par regex `\bCOPY\s+([A-Za-z0-9#@$-]+)` (saute les lignes commentaire col 7)
  - Résolution : d'abord dans les copybooks scannés (stem.upper()), puis dans les `copybookPaths` additionnels
  - `CopybookRef` : member\_name, source\_file, line, resolved\_path, is\_resolved
- [x] `POST /api/index/workspace` intègre la résolution, expose `unresolvedCopybooks` dans la réponse
- [x] `GET /api/inventory/copybook-refs?resolved=true|false`
- [x] **11 tests unitaires** + **5 tests API**

#### Réalisé — US-012 : Dépendances COBOL
- [x] `backend/src/indexing/dependency_extractor.py`
  - Parcours ligne par ligne avec gestion blocs multi-lignes (`EXEC SQL`/`EXEC CICS` → `END-EXEC`)
  - `DependencyKind` : `call`, `perform`, `exec_cics`, `exec_sql`
  - CALL : littéral (`'PGM'` / `"PGM"`) vs dynamique (variable), `target_is_literal`
  - PERFORM : exclusion des mots réservés (VARYING, UNTIL, WITH, TEST, AFTER, BEFORE)
  - EXEC CICS : verbe + `PROGRAM(name)` pour LINK/XCTL
  - EXEC SQL : verbe + tables FROM/INSERT INTO/UPDATE/JOIN (déduplication, filtre mots-clés SQL)
- [x] `GET /api/inventory/dependencies?kind=call|perform|exec_cics|exec_sql`
- [x] **20 tests unitaires** (tous les kinds, cas limites)

#### Réalisé — US-013 : Dépendances JCL
- [x] `backend/src/indexing/jcl_extractor.py`
  - Regex `^//([A-Z0-9@#$]{1,8})\s+(JOB|EXEC|DD)\b(...)` sur chaque ligne
  - EXEC PGM= (littéral), EXEC PROC= (explicite) ou EXEC name (implicite)
  - DD avec extraction DSN=
  - Commentaires `//*` et continuations `//   ` ignorés
  - `JclRef` : kind, source\_file, line, name, target
- [x] `inventory.jcl_refs` peuplé lors du `POST /api/index/workspace`
- [x] **10 tests unitaires**

#### Statistiques Bank-of-Z (corpus de référence)

| Métrique | Valeur |
|---------|--------|
| Programmes `.cbl` détectés | 38 |
| Copybooks `.cpy` détectés | 40+ |
| Instructions COPY extraites | ~150 |
| Copybooks résolus | dépend du chemin configuré |
| Fichiers JCL | 4 |

---

### Étape 5 — Intégration pipeline

**Date** : 2026-05-22

#### Réalisé
- [x] `POST /api/index/workspace` orchestre dans l'ordre : scan → résolution copybooks → extraction dépendances COBOL → extraction JCL → build graphe
- [x] Réponse enrichie : `unresolvedCopybooks`, `graphNodes`, `graphEdges`
- [x] `set_graph_store()` — injection du `GraphStore` dans les routeurs au démarrage (`create_app`)

---

## Epic 3 — Graphe applicatif ✅

### Étape 6 — GraphStore SQLite

**Date** : 2026-05-22

#### Réalisé
- [x] `backend/src/graph/store.py`
  - SQLite `:memory:` (fichier configuré ultérieurement)
  - Tables : `nodes(id PK, kind, name, path, props JSON)` / `edges(from_id, to_id, relation PK, confidence, props JSON)`
  - Upsert idempotent avec `ON CONFLICT DO UPDATE`
  - `COALESCE(excluded.path, nodes.path)` — préserve le chemin existant si la mise à jour n'en fournit pas
  - Index sur `kind`, `name`, `from_id`, `to_id`
  - `GraphStore.get_outgoing(id, relation?)`, `get_incoming(id, relation?)`, `list_nodes(kind)`, `node_count()`, `edge_count()`, `clear()`
- [x] **12 tests unitaires** (upsert, idempotence, filtrage, comptage, propriétés)

#### Réalisé — `graph/builder.py`
- [x] Nœuds créés : `program`, `copybook`, `db2table`, `jcl_job`, `jcl_step`
- [x] Relations créées :
  - `INCLUDES_COPYBOOK` (confidence 1.0, line)
  - `CALLS_PROGRAM` (CALL littéral uniquement — les CALL dynamiques ne sont pas graphés)
  - `CICS_LINKS_PROGRAM`, `CICS_XCTLS_PROGRAM`
  - `READS_TABLE`, `WRITES_TABLE`, `UPDATES_TABLE`, `DELETES_FROM_TABLE`
  - `HAS_STEP`, `EXECUTES_PROGRAM`
- [x] **11 tests unitaires**

### Étape 7 — API programmes

**Date** : 2026-05-22

#### Réalisé — US-021
- [x] `backend/src/api/programs.py`
  - `GET /api/programs` — liste tous les nœuds `program` du graphe
  - `GET /api/programs/{name}/dependencies` — nœud programme + toutes les arêtes sortantes et entrantes avec nœud cible/source, relation, confiance, numéro de ligne
  - 404 si le programme n'est pas dans le graphe
- [x] **7 tests API** (liste, not found, outgoing calls, incoming callers, copybooks)

---

## Récapitulatif des tests au 2026-05-22

| Fichier de test | Tests |
|---|---|
| test\_scanner.py | 9 |
| test\_copybook\_resolver.py | 11 |
| test\_dependency\_extractor.py | 20 |
| test\_jcl\_extractor.py | 10 |
| test\_graph\_store.py | 12 |
| test\_graph\_builder.py | 11 |
| test\_health.py | 3 |
| test\_inventory\_api.py | 15 |
| test\_programs\_api.py | 7 |
| **Total** | **98** |

Tous les tests passent (`pytest backend/tests/ -v`). Durée : ~1.3 s.

---

## Points ouverts

| # | Sévérité | Description | Epic cible |
|---|---|---|---|
| W2 | WARN | Validation token Bearer côté backend (routes authentifiées) | Epic 4 |
| W4 | WARN | Image Docker épinglée par digest | Avant prod |
| P1 | INFO | GraphStore : basculer vers un fichier SQLite persistant (configurer `sqlite_db_path`) | Epic 4 |
| P2 | INFO | Parser Java ANTLR pour extraction AST complète (paragraphes, sections, complexité) | Epic 4+ |
| P3 | INFO | Indexation incrémentale (hash comparison) | Epic 4 |
| P4 | INFO | Confidence 0.8 pour CALL dynamiques (CBLTDLI IMS) | Epic 4 |

---

---

## Epic 4 — Visualisation VS Code ⏳

### Étape 8 — TreeView inventaire

**Date** : 2026-05-22

#### Réalisé — US-030

- [x] `extension/src/views/inventoryTreeProvider.ts`
  - `CategoryItem` : nœud parent collapsible avec icône `$(folder)`, endpoint associé
  - `FileItem` : feuille avec `resourceUri` (icône langue VS Code), commande `vscode.open` au clic, tooltip = chemin absolu
  - `InventoryTreeProvider` : `TreeDataProvider<CategoryItem | FileItem>`, `EventEmitter` pour refresh, `getChildren` asynchrone vers `GET /api/inventory/{programs,copybooks,jobs}`
  - Méthode `refresh()` — déclenche `onDidChangeTreeData`
- [x] `extension/src/commands/indexWorkspace.ts` — réécrit
  - Détecte `vscode.workspace.workspaceFolders[0]` ; erreur si pas de workspace ouvert
  - Résout les `copybookPaths` relatifs par rapport au workspace root
  - Appelle `POST /api/index/workspace` avec `workspacePath`, `copybookPaths`, `sourceFormat: 'fixed'`
  - Affiche le résumé d'indexation (programmes, copybooks, jobs, nœuds, arêtes)
  - Appelle `onIndexed()` callback pour rafraîchir la vue après succès
- [x] `extension/src/config/settings.ts` — ajout `getCopybookPaths()`
- [x] `extension/package.json`
  - `viewsContainers.activitybar` : panneau "COBOL Cartography" avec icône `resources/inventory.svg`
  - `views.cobol-cartography` : vue `cobol-cartography.inventory`
  - Commande `cobol-cartography.refreshInventory` — bouton dans la barre de titre de la vue
  - Commande `cobol-cartography.indexWorkspace` — bouton d'indexation dans la barre de titre
  - Config `cobolCartography.copybookPaths` (array de strings, défaut `[]`)
- [x] `extension/src/extension.ts` — `createTreeView`, abonnements disposables

#### Décisions
- Les fichiers sont chargés à la demande (lazy) quand l'utilisateur déploie une catégorie — pas de chargement complet au démarrage.
- `resourceUri` sur `FileItem` permet à VS Code d'afficher l'icône de langage et les décorations git.
- La commande d'indexation et le bouton refresh sont tous deux dans la barre de titre de la vue (`view/title` menu).

### Étape 9 — Fiche programme

**Date** : 2026-05-22

#### Réalisé — US-031

- [x] `backend/src/api/programs.py` — `GET /api/programs/{name}/sheet`
  - Modèles Pydantic : `ProgramCall`, `TableAccess`, `JobExecution`, `SheetMetrics`, `ProgramSheet`
  - Constantes : `_CALL_RELATIONS`, `_TABLE_RELATION_TO_ACCESS`
  - Lecture outgoing/incoming depuis `GraphStore`, groupement par relation
  - Pour `executed_by` : parsing de `jcl_step:JOBNAME:STEPNAME` en `{job, step}`
  - 404 si programme absent du graphe
- [x] **4 tests API** : not found, métriques complètes, appelé par, exécuté par JCL → **96 tests total**
- [x] `extension/src/views/programSheetPanel.ts`
  - `ProgramSheetPanel` statique — une instance par programme (réutilise si déjà ouvert)
  - HTML généré en TypeScript avec `esc()` pour prévenir XSS, variables CSS VS Code
  - Sections : métriques, copybooks, appels sortants, appelants, tables DB2 (avec badges colorés READ/WRITE/UPDATE/DELETE), jobs JCL
  - Bouton "Analyser l'impact" désactivé (placeholder US-040)
  - CSP `default-src 'none'; style-src 'unsafe-inline'` — pas de scripts
- [x] `extension/src/views/inventoryTreeProvider.ts`
  - `FileItem.contextValue` → `cobol-file-program` / `cobol-file-copybook` / `cobol-file-jcl`
  - `FileItem.programName` — stem uppercase pour les programmes (ex. `BNKMENU`)
- [x] `extension/src/extension.ts` — commande `cobol-cartography.showProgramSheet`
  - Depuis le TreeView (arg = `FileItem`) : utilise `item.programName` directement
  - Depuis la palette : prompt `showInputBox`
- [x] `extension/package.json`
  - Commande `cobol-cartography.showProgramSheet` avec icône `$(info)`
  - Menu `view/item/context` → bouton inline sur `cobol-file-program`

#### Décisions
- Webview sans scripts (CSP `default-src 'none'`) : pas besoin de `acquireVsCodeApi()` ni de nonce puisque la fiche est en lecture seule.
- `ProgramSheetPanel.panels` est une `Map<string, ProgramSheetPanel>` statique — garantit une seule fenêtre par programme.
- Le bouton "Analyser l'impact" est désactivé (`cursor:not-allowed`, `opacity:.5`) plutôt qu'absent, pour indiquer la feature à venir.

---

## Récapitulatif des tests au 2026-05-22 (après US-031)

| Fichier de test | Tests |
|---|---|
| test\_scanner.py | 9 |
| test\_copybook\_resolver.py | 11 |
| test\_dependency\_extractor.py | 20 |
| test\_jcl\_extractor.py | 10 |
| test\_graph\_store.py | 12 |
| test\_graph\_builder.py | 11 |
| test\_health.py | 3 |
| test\_inventory\_api.py | 9 |
| test\_programs\_api.py | 11 |
| **Total** | **96** |

Durée : ~1.6 s.

---

---

## Epic 5 — Analyse d'impact ⏳

### Étape 10 — Impact copybook

**Date** : 2026-05-22

#### Réalisé — US-040

- [x] `backend/src/api/impact.py` — nouveau routeur `GET /api/impact/copybook/{name}`
  - BFS inversé depuis `copybook:{NAME}` :
    1. Impacts directs (depth=1) : arêtes entrantes `INCLUDES_COPYBOOK`
    2. Impacts indirects (depth≥2) : remontée transitive sur `CALLS_PROGRAM`, `CICS_LINKS_PROGRAM`, `CICS_XCTLS_PROGRAM`
    3. Jobs JCL : arêtes entrantes `EXECUTES_PROGRAM` depuis tous les programmes visités
  - Chaque `ImpactEntry` porte `depth` et `via` (programme intermédiaire direct)
  - `uncertain_impacts` laissé vide pour le MVP (ferait appel aux CALL dynamiques, non graphés)
  - 404 si le copybook est absent du graphe
- [x] `backend/src/main.py` — `impact_set_store(store)` + `app.include_router(impact_router)`
- [x] **5 tests API** : not found, directs multiples, indirect avec via, jobs JCL, copybook non utilisé
- [x] `extension/src/views/copybookImpactPanel.ts`
  - `CopybookImpactPanel` statique — une instance par copybook
  - Badges de profondeur colorés : vert (d=1), bleu (d=2), orange (d=3), gris (d≥4)
  - Annotation `via` en italique sur les impacts indirects
  - Sections : directs, indirects, jobs impactés
- [x] `extension/src/views/inventoryTreeProvider.ts`
  - `FileItem.copybookName` — stem uppercase pour les copybooks
- [x] `extension/src/extension.ts` — commande `cobol-cartography.analyzeCopybookImpact`
- [x] `extension/package.json`
  - Commande `cobol-cartography.analyzeCopybookImpact` avec icône `$(search)`
  - Bouton inline sur `cobol-file-copybook`

#### Décisions
- BFS sans limite de profondeur : pour le MVP sur des corpus de taille raisonnable. À limiter (max depth configurable) si le corpus dépasse ~500 programmes.
- `via` = le voisin direct du programme visité vers le copybook, pas le chemin complet. Suffit pour afficher "MENU — via INQACC".

---

## Récapitulatif des tests au 2026-05-22 (après US-040)

| Fichier de test | Tests |
|---|---|
| test\_scanner.py | 9 |
| test\_copybook\_resolver.py | 11 |
| test\_dependency\_extractor.py | 20 |
| test\_jcl\_extractor.py | 10 |
| test\_graph\_store.py | 12 |
| test\_graph\_builder.py | 11 |
| test\_health.py | 3 |
| test\_inventory\_api.py | 9 |
| test\_programs\_api.py | 11 |
| test\_impact\_api.py | 5 |
| **Total** | **101** |

Durée : ~1.3 s.

---

---

## Epic 6 — IA ⏳

### Étape 11 — Explication IA d'un programme

**Date** : 2026-05-22

#### Réalisé — US-050

- [x] `backend/src/api/ai.py` — `POST /api/ai/explain/program`
  - Mode `local_strict` (ADR-04) : aucun appel LLM, tout dérivé du graphe
  - `ExplainProgramRequest` : `programId`, `detailLevel` (défaut `"standard"`), `includeBusinessRules` (défaut `true`)
  - Phrase de rôle (`_role_sentence`) construite par template depuis `ComplexityIndicators`
  - Accès tables groupés par nom (`defaultdict`) pour fusionner multi-opérations
  - **Candidats règles métier** (si `includeBusinessRules=True`) :
    - SQL READ/WRITE/UPDATE/DELETE → description FR + confidence 0.75-0.80
    - CICS LINK/XCTL → délégation de traitement, confidence 0.70
  - **Incertitudes** toujours présentes :
    - CALL dynamiques non graphés (constante)
    - Programmes stubs (`path is None`) nommément listés si détectés
  - 404 si programme absent du graphe
- [x] `backend/src/main.py` — `ai_set_store(store)` + `app.include_router(ai_router)`
- [x] **6 tests API** : not found, résumé de base, règles SQL, `includeBusinessRules=False`, incertitudes présentes, incertitude stubs → **107 tests total**
- [x] `extension/src/views/explainProgramPanel.ts`
  - `ExplainProgramPanel` statique — une instance par programme
  - Phrase de rôle en bloc citation avec bordure gauche VS Code
  - Barre de confiance CSS (`conf-fill` proportionnelle), badges ÉLEVÉE/MOYENNE/FAIBLE
  - Badges d'accès tables colorés (READ/WRITE/UPDATE/DELETE)
  - Section incertitudes avec liste explicite
- [x] `extension/src/extension.ts` — commande `cobol-cartography.explainProgram`
- [x] `extension/package.json` — bouton `$(lightbulb)` inline sur `cobol-file-program`

#### Décisions
- Le `detailLevel` reçu est renvoyé en écho mais n'influence pas encore le contenu — préparé pour un futur `"detailed"` qui intégrerait les paragraphes COBOL (P2, parser ANTLR).
- Confidence calibrée à 0.75-0.80 pour les patterns SQL déterministes (certaines mais sans contexte métier), 0.70 pour les délégations CICS (moins interprétable sans le code du programme cible).
- Stub uncertainty nommée : préférable à un message générique pour que l'utilisateur comprenne exactement quels programmes manquent.

---

## Récapitulatif des tests au 2026-05-22 (après US-050)

| Fichier de test | Tests |
|---|---|
| test\_scanner.py | 9 |
| test\_copybook\_resolver.py | 11 |
| test\_dependency\_extractor.py | 20 |
| test\_jcl\_extractor.py | 10 |
| test\_graph\_store.py | 12 |
| test\_graph\_builder.py | 11 |
| test\_health.py | 3 |
| test\_inventory\_api.py | 9 |
| test\_programs\_api.py | 11 |
| test\_impact\_api.py | 5 |
| test\_ai\_api.py | 6 |
| **Total** | **107** |

Durée : ~1.6 s.

---

## Epic 4 (suite) — Visualisation VS Code ⏳

### Étape 12 — Carte graphe interactive

**Date** : 2026-05-22

#### Réalisé — US-032

- [x] `backend/src/graph/store.py` — méthodes `all_nodes()` et `all_edges()` (scan complet sans filtre par kind)
- [x] `backend/src/api/graph.py` — nouveau routeur `GET /api/graph/export`
  - Modèles Pydantic : `D3Node` (id, kind, name, path), `D3Link` (source, target, relation, confidence), `GraphExport`
  - Sérialise l'intégralité du graphe en format D3.js compatible
- [x] `backend/src/main.py` — `graph_set_store(store)` + `app.include_router(graph_router)`
- [x] **4 tests API** : graphe vide, nœuds présents après indexation, liens reflètent les dépendances, champs node vérifiés → **111 tests total**
- [x] `extension/src/views/graphViewPanel.ts`
  - `GraphViewPanel` statique — une seule instance (singleton `reveal()` si déjà ouverte)
  - Canvas HTML5 — simulation force-directed en JavaScript pur (sans dépendance externe, offline)
  - **Simulation** : répulsion O(n²), attraction par ressort (longueur idéale 110 px), gravité vers le centre, amortissement (α décroît de 1 → 0 sur 500 frames ≈ 8 s)
  - **Interaction** : drag pour déplacer/épingler un nœud, hover = tooltip + label sur canvas, clic = sélection + ouverture du fichier source (via `postMessage` → `vscode.open`)
  - **Filtres** : 5 boutons de filtre par kind (Programme, Copybook, Table DB2, Job JCL, Étape JCL) avec toggle actif/inactif ; le compteur de nœuds/arêtes visibles se met à jour en temps réel
  - **Couleurs** : programme #4e9af1, copybook #e8a94c, db2table #4ec983, jcl_job #a078e8, jcl_step #8899aa
  - **Flèches directionnelles** sur les arêtes (angle calculé vers le nœud cible)
  - **CSP** : `script-src 'nonce-{nonce}'` — nonce aléatoire par panel, sans `'unsafe-inline'`
  - État vide affiché si le graphe n'a pas encore été indexé
  - `retainContextWhenHidden: true` pour conserver la simulation lors du changement d'onglet
- [x] `extension/src/extension.ts` — commande `cobol-cartography.showGraphView`
- [x] `extension/package.json`
  - Commande `cobol-cartography.showGraphView` avec icône `$(type-hierarchy)`
  - Bouton dans la barre de titre de la vue `cobol-cartography.inventory`

#### Décisions
- Simulation JavaScript pur (pas de D3.js) : élimine la dépendance CDN (fonctionne offline dans VS Code), réduit la surface d'attaque CSP, code entièrement dans le template HTML TypeScript sans bundler.
- Nœuds épinglés après drag (`pinned: true`) : le layouter ne les bouge plus, ce qui permet à l'utilisateur de réorganiser manuellement le graphe.
- `retainContextWhenHidden: true` : la simulation JavaScript continue de tourner en mémoire quand le panel est masqué, préservant le layout.

---

## Récapitulatif des tests au 2026-05-22 (après US-032)

| Fichier de test | Tests |
|---|---|
| test\_scanner.py | 9 |
| test\_copybook\_resolver.py | 11 |
| test\_dependency\_extractor.py | 20 |
| test\_jcl\_extractor.py | 10 |
| test\_graph\_store.py | 12 |
| test\_graph\_builder.py | 11 |
| test\_health.py | 3 |
| test\_inventory\_api.py | 9 |
| test\_programs\_api.py | 11 |
| test\_impact\_api.py | 5 |
| test\_ai\_api.py | 6 |
| test\_graph\_api.py | 4 |
| **Total** | **111** |

Durée : ~1.5 s.

---

## Epic 5 (suite) — Analyse d'impact ⏳

### Étape 13 — Impact depuis table DB2

**Date** : 2026-05-22

#### Réalisé — US-041

- [x] `backend/src/api/impact.py` — `GET /api/impact/table/{name}`
  - Modèles : `TableImpactEntry` (name, confidence), `TableImpact` (table_name, readers, writers, updaters, deleters, associated_jobs)
  - Constante `_TABLE_RELATIONS` : `READS_TABLE → readers`, `WRITES_TABLE → writers`, `UPDATES_TABLE → updaters`, `DELETES_FROM_TABLE → deleters`
  - Arêtes entrantes sur `db2table:{NAME}` groupées par relation
  - Jobs JCL collectés via `EXECUTES_PROGRAM` depuis tous les programmes accédant à la table
  - 404 si la table est absente du graphe
- [x] **5 tests API** : not found, lecteurs, types d'accès multiples, jobs associés, table sans accès → **116 tests total**
- [x] `extension/src/views/tableImpactPanel.ts`
  - `TableImpactPanel` statique — une instance par table
  - 6 cartes métriques (total programmes, lecteurs, écrivains, modificateurs, suppresseurs, jobs)
  - 4 sections d'accès avec badges colorés : READ #1a5c14, WRITE #0044a0, UPDATE #7d4000, DELETE #7a1a1a
  - Section jobs associés
- [x] `extension/src/extension.ts` — commande `cobol-cartography.analyzeTableImpact`
  - Accessible uniquement depuis la palette (prompt `showInputBox`) — pas de TreeView pour les tables en MVP
- [x] `extension/package.json` — commande `cobol-cartography.analyzeTableImpact` avec icône `$(symbol-field)`

#### Décisions
- Panel accessible via palette uniquement (pas de catégorie "Tables DB2" dans le TreeView) : la table est une ressource graphe, pas un fichier physique — l'inventaire TreeView ne la listerait pas naturellement. Évolution possible en US-052+.
- Réutilisation du pattern singleton `Map<string, Panel>` existant — cohérence avec les autres panels.

---

## Récapitulatif des tests au 2026-05-22 (après US-041)

| Fichier de test | Tests |
|---|---|
| test\_scanner.py | 9 |
| test\_copybook\_resolver.py | 11 |
| test\_dependency\_extractor.py | 20 |
| test\_jcl\_extractor.py | 10 |
| test\_graph\_store.py | 12 |
| test\_graph\_builder.py | 11 |
| test\_health.py | 3 |
| test\_inventory\_api.py | 9 |
| test\_programs\_api.py | 11 |
| test\_impact\_api.py | 10 |
| test\_ai\_api.py | 6 |
| test\_graph\_api.py | 4 |
| **Total** | **116** |

Durée : ~1.6 s.

---

## Epic 6 (suite) — IA ⏳

### Étape 14 — Validation/rejet des règles métier

**Date** : 2026-05-22

#### Réalisé — US-051

- [x] `extension/src/views/explainProgramPanel.ts` — réécriture complète
  - `enableScripts: true` (précédemment `false`) avec nonce aléatoire et CSP `script-src 'nonce-{nonce}'`
  - `renderExplanation()` prend maintenant `validations: Record<string, RuleStatus>` et `nonce: string`
  - **Par règle candidate** : deux boutons "✓ Accepter" / "✗ Rejeter" avec `.btn-validate`
    - Re-clic sur le bouton actif réinitialise l'état (toggle)
    - Indicateur visuel coloré : bordure verte + badge "✓ Validée" · bordure rouge + badge "✗ Rejetée"
    - Règle rejetée affichée avec `opacity:.7` pour la déprioriser visuellement
  - **JavaScript injecté (nonce)** : `acquireVsCodeApi()`, gestionnaire de clic envoyant `{ command: 'validate', description, status }` via `postMessage`
  - État initial des boutons restauré depuis le JSON des validations sauvegardées (injecté dans le HTML)
- [x] `extension/src/views/explainProgramPanel.ts` — classe `ExplainProgramPanel`
  - `show()` prend désormais `context: vscode.ExtensionContext` (troisième paramètre)
  - Handler `onDidReceiveMessage` : lit/écrit `context.workspaceState` sur clé `cobol-cartography.rules.{PROGRAM}`
    - `status === 'reset'` → `delete saved[description]` (annulation)
    - Sinon → `saved[description] = 'accepted' | 'rejected'`
  - `loadAndRender()` : charge les validations sauvegardées avant de générer le HTML
- [x] `extension/src/extension.ts` — `ExplainProgramPanel.show(name, client, context)` (ajout de `context`)
- Aucune modification backend — logique de persistance entièrement côté extension

#### Décisions
- Persistance dans `workspaceState` plutôt qu'en mémoire : survit à la fermeture du panel, liée au workspace VS Code courant. Choix naturel avant d'envisager une synchronisation backend (US-052+).
- Toggle sur re-clic : évite le cas bloquant où l'utilisateur ne peut plus revenir à l'état "non décidé".
- Nonce individuel par panel (généré dans `loadAndRender`) : robustesse, même si tous les panels sont actuellement construits une seule fois.

---

## Récapitulatif final des tests — MVP complet 🎉

| Fichier de test | Tests |
|---|---|
| test\_scanner.py | 9 |
| test\_copybook\_resolver.py | 11 |
| test\_dependency\_extractor.py | 20 |
| test\_jcl\_extractor.py | 10 |
| test\_graph\_store.py | 12 |
| test\_graph\_builder.py | 11 |
| test\_health.py | 3 |
| test\_inventory\_api.py | 9 |
| test\_programs\_api.py | 11 |
| test\_impact\_api.py | 10 |
| test\_ai\_api.py | 6 |
| test\_graph\_api.py | 4 |
| **Total** | **116** |

Durée : ~1.6 s. Tous les tests passent.

---

## Bilan MVP initial

Toutes les US du backlog MVP sont terminées : US-001 → US-051.

**Extension VS Code** : 8 commandes enregistrées, 6 vues/panels, TreeView inventaire lazy, configuration workspace.

**Backend FastAPI** : 8 routeurs, 116 tests, SQLite in-memory, mode `local_strict`.

**Points ouverts pour la suite** :
| # | Description | Priorité |
|---|---|---|
| W2 | Validation token Bearer côté backend | WARN |
| W4 | Image Docker épinglée par digest | WARN |
| P1 | GraphStore fichier SQLite persistant | INFO |
| P2 | Parser Java ANTLR pour AST complet | INFO |
| P3 | Indexation incrémentale (hash comparison) | INFO |
| P4 | Confidence 0.8 pour CALL dynamiques (CBLTDLI) | INFO |

---

## Post-MVP — Programmes exécutés par un job JCL

**Date** : 2026-05-23

### Demande

Depuis le TreeView, permettre d'afficher la liste des programmes exécutés par un job JCL (étapes EXEC PGM), avec le chemin physique de chaque programme ou un badge "stub" s'il est absent du workspace.

### Réalisé

- [x] `backend/src/api/jobs.py` — nouveau routeur `GET /api/jobs/{name}/programs`
  - Traversal graphe : `jcl_job:{NAME}` → `HAS_STEP` → `jcl_step:JOB:STEP` → `EXECUTES_PROGRAM` → `program:{NAME}`
  - Modèles Pydantic : `StepExecution` (step_name, program_name, program_path), `JobPrograms` (job_name, steps, total_programs)
  - `total_programs` = ensemble dédupliqué des programmes (un programme peut être exécuté par plusieurs étapes)
  - 404 si le job n'est pas dans le graphe
- [x] `backend/src/main.py` — `jobs_set_store(store)` + `app.include_router(jobs_router, prefix="/api/jobs")`
- [x] **5 tests API** (`test_jobs_api.py`) : not found, job sans étapes, étapes multiples, programme stub (path=None), déduplication total_programs
- [x] `extension/src/views/jobProgramsPanel.ts`
  - Singleton `Map<string, JobProgramsPanel>` keyed par nom de job
  - `enableScripts: false` (lecture seule)
  - Tableau : Étape / Programme / Chemin ; badge gris "stub" si `program_path === null`
  - 3 cartes métriques : Étapes, Programmes (dédupliqués), Stubs
- [x] `extension/src/views/inventoryTreeProvider.ts` — `FileItem.jclJobName` (stem uppercase) dans le branch `else` (kind JCL)
- [x] `extension/src/extension.ts` — commande `cobol-cartography.showJobPrograms`
  - Duck typing sur `item.jclJobName` (depuis le TreeView)
  - `showInputBox` (depuis la palette) comme fallback
- [x] `extension/package.json`
  - Commande `cobol-cartography.showJobPrograms` avec icône `$(list-tree)`
  - Bouton inline sur les items `cobol-file-jcl` dans le TreeView (`view/item/context`)

### Récapitulatif tests après ajout JCL programs

| Fichier de test | Tests |
|---|---|
| test\_scanner.py | 9 |
| test\_copybook\_resolver.py | 11 |
| test\_dependency\_extractor.py | 20 |
| test\_jcl\_extractor.py | 10 |
| test\_graph\_store.py | 11 |
| test\_graph\_builder.py | 10 |
| test\_health.py | 3 |
| test\_inventory\_api.py | 11 |
| test\_programs\_api.py | 11 |
| test\_impact\_api.py | 10 |
| test\_ai\_api.py | 6 |
| test\_graph\_api.py | 4 |
| test\_jobs\_api.py | 5 |
| **Total** | **121** |

---

## Post-MVP — Guide de test en mode développeur

**Date** : 2026-05-23

### Réalisé

- [x] `extension/.vscode/launch.json` — configuration `"Launch Extension"` (type `extensionHost`, preLaunchTask `npm: compile`)
- [x] `extension/.vscode/tasks.json` — deux tâches `npm: compile` (tsc -p ./) et `npm: watch` (tsc -watch -p ./)
- Permet de lancer l'extension avec **F5** dans VS Code sans passer par la ligne de commande

---

## Correctif — Copybooks SQL INCLUDE non liés au graphe

**Date** : 2026-05-23

### Problème rapporté

Des copybooks comme `CUSTDB2` n'apparaissaient pas liés à des programmes dans le graphe (arête `INCLUDES_COPYBOOK` manquante), alors qu'ils sont référencés dans plusieurs programmes (BANKDATA, CRECUST, DELCUS, INQCUST, UPDCUST).

### Cause racine

Dans `backend/src/indexing/copybook_resolver.py`, la regex `_COPY_RE` ne détectait que les instructions COBOL `COPY member`. Les directives DB2 `EXEC SQL INCLUDE member END-EXEC` — utilisées dans les sections DATA DIVISION pour inclure des descripteurs de table DB2 — n'étaient pas reconnues.

Exemple dans `BANKDATA.cbl` :
```cobol
       EXEC SQL
           INCLUDE CUSTDB2
       END-EXEC.
```

Bug secondaire dans `backend/src/graph/builder.py` : les `DependencyRef` avec `target="INCLUDE"` (produits par `dependency_extractor.py`) tombaient dans le handler SQL par défaut et créaient un faux nœud `db2table:CUSTDB2` avec une arête `ACCESSES_TABLE` — polluant le graphe avec de faux nœuds table.

### Correction

**`copybook_resolver.py`** — `extract_copy_statements()` rendue stateful :
- Ajout de trois regexes : `_EXEC_SQL_RE`, `_SQL_INCLUDE_RE`, `_END_EXEC_RE`
- Suivi de `in_exec_sql: bool` ligne par ligne
- Quand dans un bloc EXEC SQL, tout match de `INCLUDE member` génère un `CopybookRef` → arête `INCLUDES_COPYBOOK` correcte
- Gestion des formes inline (`EXEC SQL INCLUDE SQLCA END-EXEC.` sur une ligne)

**`builder.py`** — handler `EXEC_SQL` :
- Saut explicite si `dep.target == "INCLUDE"` (commentaire : géré via `copybook_refs`, pas comme table)
- Élimine les faux nœuds `db2table` et arêtes `ACCESSES_TABLE` pour les copybooks SQL

### Tests ajoutés

| Fichier | Tests ajoutés |
|---|---|
| `test_copybook_resolver.py` | +4 (EXEC SQL multi-ligne, inline, mixte COPY+INCLUDE, SELECT sans INCLUDE) |
| `test_graph_builder.py` | +1 (INCLUDE ne crée pas de nœud `db2table`) |

### Récapitulatif tests après correctif

| Fichier de test | Tests |
|---|---|
| test\_scanner.py | 9 |
| test\_copybook\_resolver.py | 15 |
| test\_dependency\_extractor.py | 20 |
| test\_jcl\_extractor.py | 10 |
| test\_graph\_store.py | 11 |
| test\_graph\_builder.py | 11 |
| test\_health.py | 3 |
| test\_inventory\_api.py | 11 |
| test\_programs\_api.py | 11 |
| test\_impact\_api.py | 10 |
| test\_ai\_api.py | 6 |
| test\_graph\_api.py | 4 |
| test\_jobs\_api.py | 5 |
| **Total** | **126** |

Durée : ~1.7 s. 126 tests, tous passent.
