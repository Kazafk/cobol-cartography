# Backlog MVP

> Voir aussi : [[Cadrage-produit]] | [[Architecture-technique]] | [[Plan-Tests-Qualite]] | [[Structure-projet]] | [[Home]]

Légende : ✅ Terminé · ⏳ En cours · 🔲 À faire

---

## Epic 1 — Initialisation projet ✅

### US-001 — Créer le squelette extension VS Code ✅ → [[Extension-VSCode]]

Critères d'acceptation : extension installable en mode développement, commande de test, configuration utilisateur minimale.

**Réalisé** : `extension/src/extension.ts`, commande `cobol-cartography.indexWorkspace`, config `cobolCartography.backendUrl` via `workspace.getConfiguration`, clé API via `SecretStorage`. Compilation TypeScript → `out/`. Voir [[14-journal-developpement#Étape 1]].

### US-002 — Créer le backend API ✅ → [[API-Backend]]

Critères d'acceptation : endpoint `/health`, endpoint `/capabilities`, logs structurés.

**Réalisé** : `GET /api/health` et `GET /api/capabilities` avec FastAPI + structlog JSON. Voir [[14-journal-developpement#Étape 2]].

---

## Epic 2 — Indexation COBOL ✅ → [[Pipeline-indexation]]

### US-010 — Scanner un workspace ✅

Critères d'acceptation : détection programmes COBOL, copybooks, JCL, inventaire retourné par API.

**Réalisé** : `indexing/scanner.py` — walk récursif, classification par extension (`.cbl/.cob/.cobol`, `.cpy/.copy`, `.jcl`), SHA-256 par fichier. `POST /api/index/workspace` + `GET /api/inventory/{programs,copybooks,jobs}`. 9 tests unitaires + 6 tests API.

### US-011 — Résoudre les copybooks ✅

Critères d'acceptation : chemins configurables, relations programme-copybook créées, non résolus signalés.

**Réalisé** : `indexing/copybook_resolver.py` — extraction des instructions `COPY` par regex (insensible à la casse, saute les lignes de commentaire colonne 7), résolution par stem de fichier dans les copybooks scannés puis dans les chemins additionnels. `GET /api/inventory/copybook-refs?resolved=true|false`. 11 tests unitaires + 5 tests API.

### US-012 — Extraire les dépendances COBOL principales ✅

Critères d'acceptation : extraction CALL, PERFORM, EXEC SQL, EXEC CICS.

**Réalisé** : `indexing/dependency_extractor.py` — parcours ligne par ligne, blocs multi-lignes EXEC SQL/CICS collectés jusqu'à `END-EXEC`. CALL littéral vs dynamique, PERFORM avec exclusion des mots réservés, CICS LINK/XCTL avec extraction `PROGRAM(name)`, SQL verbe + tables (FROM/INSERT INTO/UPDATE/JOIN, déduplication). `GET /api/inventory/dependencies?kind=call|perform|exec_cics|exec_sql`. 20 tests unitaires.

### US-013 — Extraire les dépendances JCL principales ✅

Critères d'acceptation : extraction JOB, EXEC PGM, PROC, DD.

**Réalisé** : `indexing/jcl_extractor.py` — regex sur lignes `//name keyword params`, détection EXEC PGM=, EXEC PROC= (explicite) et EXEC procname (implicite), DD avec DSN=. Commentaires `//*` et continuations ignorés. 10 tests unitaires.

---

## Epic 3 — Graphe applicatif ✅ → [[Modele-graphe]]

### US-020 — Créer le modèle graphe ✅

Critères d'acceptation : nœuds Program, Copybook, JCLJob, JCLStep, DB2Table ; relations principales ; requêtes de base.

**Réalisé** : `graph/store.py` — SQLite en mémoire (`:memory:`), tables `nodes` et `edges` avec upsert idempotent, index sur `kind`, `name`, `from_id`, `to_id`. `graph/builder.py` — populate depuis `WorkspaceInventory` : nœuds Program/Copybook/DB2Table/JCLJob/JCLStep, relations INCLUDES_COPYBOOK, CALLS_PROGRAM, CICS_LINKS_PROGRAM, CICS_XCTLS_PROGRAM, READS_TABLE, WRITES_TABLE, UPDATES_TABLE, DELETES_FROM_TABLE, HAS_STEP, EXECUTES_PROGRAM. Attribut `confidence=1.0` sur toutes les relations déterministes. 12 tests store + 11 tests builder.

### US-021 — Consulter les dépendances d'un programme ✅

Critères d'acceptation : API dépendances entrantes/sortantes, affichage dans VS Code.

**Réalisé** : `api/programs.py` — `GET /api/programs` (liste) et `GET /api/programs/{name}/dependencies` (dépendances entrantes + sortantes avec nœud cible, relation, confiance, numéro de ligne). La réponse `POST /api/index/workspace` inclut désormais `graphNodes` et `graphEdges`. 7 tests API.

---

## Epic 4 — Visualisation VS Code ⏳ → [[Extension-VSCode]]

### US-030 — TreeView inventaire ✅

Critères d'acceptation : liste programmes/copybooks/jobs, ouverture fichier au clic.

**Réalisé** : `extension/src/views/inventoryTreeProvider.ts` — `InventoryTreeProvider` implémentant `vscode.TreeDataProvider`. Trois catégories (Programs, Copybooks, JCL Jobs) chargées depuis `GET /api/inventory/{programs,copybooks,jobs}`. Ouverture fichier au clic via commande `vscode.open`. Commande `cobol-cartography.refreshInventory` enregistrée dans la barre de titre de la vue. `POST /api/index/workspace` déclenché depuis la commande `indexWorkspace` avec chemin workspace et `copybookPaths` configurables ; affiche les comptes en retour. Icône d'activité `resources/inventory.svg`.

### US-031 — Fiche programme ✅

Critères d'acceptation : résumé technique, dépendances, tables et fichiers, bouton "analyser impact".

**Réalisé** : `GET /api/programs/{name}/sheet` — retourne `ProgramSheet` (métriques, copybooks, appels sortants, appelants, tables DB2, jobs JCL). `extension/src/views/programSheetPanel.ts` — `WebviewPanel` statique (une instance par programme), HTML généré côté TypeScript avec variables CSS VS Code pour le thème. Bouton "Analyser l'impact" désactivé (placeholder US-040). Commande `cobol-cartography.showProgramSheet` enregistrée avec bouton `$(info)` inline sur les items de type programme dans le TreeView. Icône déclenchable depuis la palette de commandes (prompt inputBox) si invoquée hors contexte arbre. 4 nouveaux tests API backend (96 tests total).

### US-032 — Carte graphe ✅

Critères d'acceptation : webview graphe, filtrage par type de nœud, navigation vers source.

**Réalisé** : `GET /api/graph/export` — sérialise tous les nœuds et arêtes en format D3.js. `extension/src/views/graphViewPanel.ts` — webview Canvas avec simulation force-directed JavaScript pur, filtrage par kind (5 boutons), drag & drop, hover tooltip, clic → ouverture fichier source. Bouton `$(type-hierarchy)` dans la barre de titre de la vue inventaire. 4 tests API (111 tests total).

---

## Epic 5 — Analyse d'impact ⏳

### US-040 — Impact depuis copybook ✅

Critères d'acceptation : liste programmes impactés, jobs impactés, chemins d'impact.

**Réalisé** : `GET /api/impact/copybook/{name}` — BFS inversé depuis le nœud copybook : impacts directs (programs avec `INCLUDES_COPYBOOK`, depth=1) puis impacts indirects par remontée transitive des arêtes d'appel (`CALLS_PROGRAM`, `CICS_LINKS_PROGRAM`, `CICS_XCTLS_PROGRAM`). Chaque entrée indirecte porte `via` (le programme intermédiaire) et `depth`. Jobs JCL impactés via `EXECUTES_PROGRAM` depuis tous les programmes visités. `extension/src/views/copybookImpactPanel.ts` — webview avec métriques, listes directs/indirects/jobs, badges colorés par profondeur. Bouton `$(search)` inline sur les items copybook du TreeView. 5 tests API (101 tests total).

### US-041 — Impact depuis table DB2 ✅

Critères d'acceptation : programmes lecteurs, programmes modificateurs, jobs associés.

**Réalisé** : `GET /api/impact/table/{name}` — retourne `readers`, `writers`, `updaters`, `deleters` (programmes par type d'accès SQL) + `associated_jobs` (jobs JCL exécutant ces programmes). `extension/src/views/tableImpactPanel.ts` — webview statique par table, 6 cartes métriques, 4 sections par type d'accès avec badges colorés. Commande `cobol-cartography.analyzeTableImpact` accessible depuis la palette. 5 tests API (116 tests total).

---

## Epic 6 — IA ⏳ → [[IA-RAG-Agents]]

### US-050 — Explication IA d'un programme ✅

Critères d'acceptation : contexte construit depuis graphe, réponse structurée, incertitudes explicites.

**Réalisé** : `POST /api/ai/explain/program` — mode `local_strict` (ADR-04), aucun appel LLM externe. Phrase de rôle générée par template depuis les métriques du graphe. Regroupement des accès tables par nom (multi-opérations). Candidats règles métier : SQL (READ/WRITE/UPDATE/DELETE → templates FR, confidence 0.75-0.80) + CICS LINK/XCTL (confidence 0.70). Incertitudes : CALL dynamiques toujours signalés ; programmes stubs (path=None, hors workspace) identifiés nominalement. `extension/src/views/explainProgramPanel.ts` — phrase de rôle en bloc citation, barre de confiance CSS, badges colorés par niveau (ÉLEVÉE/MOYENNE/FAIBLE), badges d'accès tables. Bouton `$(lightbulb)` inline sur les items programme du TreeView. 6 tests API (107 tests total).

### US-051 — Règles métier candidates ✅

Critères d'acceptation : extraction candidates, niveau de confiance, preuves techniques, validation/rejet utilisateur.

**Réalisé** : `extension/src/views/explainProgramPanel.ts` réécriture — `enableScripts: true` avec nonce CSP, boutons "✓ Accepter" / "✗ Rejeter" par règle candidate. État persisté dans `context.workspaceState` (clé `cobol-cartography.rules.{PROGRAM}`). Re-clic sur le bouton actif annule la validation. Indicateur coloré par règle (vert = validée, rouge = rejetée). État rechargé à la réouverture du panel. Extraction et preuves inchangées (US-050). Aucun nouveau test backend — logique purement côté extension.

---

---

## Post-MVP — Fonctionnalités additionnelles

### Programmes exécutés par un job JCL ✅

**Date** : 2026-05-23

Critères d'acceptation : depuis le TreeView, cliquer sur un job JCL ouvre un panel listant toutes ses étapes EXEC PGM avec le programme exécuté et son chemin physique (ou "stub" si absent).

**Réalisé** :
- `backend/src/api/jobs.py` — `GET /api/jobs/{name}/programs` : traversal `HAS_STEP` → `EXECUTES_PROGRAM`, retourne `steps[]` (step_name, program_name, program_path) et `total_programs` dédupliqué.
- `extension/src/views/jobProgramsPanel.ts` — webview statique, tableau étapes + badges stub, 3 cartes métriques.
- `extension/src/views/inventoryTreeProvider.ts` — `FileItem.jclJobName` pour les items JCL.
- `extension/src/extension.ts` — commande `cobol-cartography.showJobPrograms` (TreeView + palette).
- `extension/package.json` — icône `$(list-tree)` inline sur `cobol-file-jcl`.
- 5 tests API (`test_jobs_api.py`).

### Guide de test en mode développeur ✅

**Date** : 2026-05-23

- `extension/.vscode/launch.json` — configuration `"Launch Extension"` (F5, type `extensionHost`)
- `extension/.vscode/tasks.json` — tâches `npm: compile` et `npm: watch`

### Correctif — Copybooks SQL INCLUDE non liés au graphe ✅

**Date** : 2026-05-23

- `backend/src/indexing/copybook_resolver.py` — `extract_copy_statements()` étendue pour détecter `EXEC SQL INCLUDE member END-EXEC` (tracking stateful `in_exec_sql`).
- `backend/src/graph/builder.py` — skip des `DependencyRef` avec `target="INCLUDE"` dans le handler SQL (évite les faux nœuds `db2table`).
- +5 tests (test_copybook_resolver.py +4, test_graph_builder.py +1).

---

## Priorisation recommandée

~~US-001~~ ✅ → ~~US-002~~ ✅ → ~~US-010~~ ✅ → ~~US-011~~ ✅ → ~~US-012~~ ✅ → ~~US-013~~ ✅ → ~~US-020~~ ✅ → ~~US-021~~ ✅ → ~~US-030~~ ✅ → ~~US-031~~ ✅ → ~~US-040~~ ✅ → ~~US-050~~ ✅ → ~~US-032~~ ✅ → ~~US-041~~ ✅ → ~~US-051~~ ✅ → **MVP complet** 🎉 → JCL programs ✅ → SQL INCLUDE fix ✅
