# cobol-cartography

Extension VS Code de cartographie COBOL avec IA — analyse statique déterministe, graphe de dépendances applicatif, explication et documentation assistées par IA.

## Vision

Permettre aux architectes, développeurs et responsables de modernisation mainframe de **comprendre, explorer, documenter et analyser l'impact** d'un patrimoine COBOL volumineux directement depuis VS Code.

Principe directeur : construire d'abord une cartographie déterministe fiable (parsing + graphe), puis ajouter l'IA comme couche d'explication, d'enrichissement et d'assistance.

## Fonctionnalités MVP

| Fonctionnalité | Statut |
|---|---|
| Scan et classification du workspace (COBOL, copybooks, JCL) | ✅ |
| Résolution des copybooks (COPY + EXEC SQL INCLUDE) | ✅ |
| Extraction dépendances : CALL, PERFORM, EXEC SQL, EXEC CICS | ✅ |
| Extraction JCL : JOB, EXEC PGM, PROC, DD | ✅ |
| Graphe applicatif SQLite (nœuds + relations + confiance) | ✅ |
| TreeView inventaire VS Code (programmes, copybooks, JCL) | ✅ |
| Fiche programme (métriques, dépendances, tables DB2, jobs) | ✅ |
| Carte graphe interactive force-directed (filtrage par type) | ✅ |
| Analyse d'impact copybook (BFS inversé, impacts directs/indirects) | ✅ |
| Analyse d'impact table DB2 (readers/writers/updaters/deleters) | ✅ |
| Explication IA programme (mode `local_strict`, sans LLM externe) | ✅ |
| Règles métier candidates avec validation/rejet utilisateur | ✅ |
| Panel programmes exécutés par un job JCL | ✅ |

**126 tests** (backend Python) — tous passent. Durée : ~1.7 s.

## Architecture

```
cobol-cartography/
├── extension/          # VS Code extension (TypeScript)
│   ├── src/commands/   # Commandes utilisateur
│   ├── src/views/      # TreeView + WebviewPanels
│   └── src/api/        # Client HTTP backend
├── backend/            # API FastAPI (Python 3.11+)
│   ├── src/api/        # Routeurs REST
│   ├── src/graph/      # GraphStore SQLite + builder
│   ├── src/indexing/   # Scanner, copybook resolver, extracteurs
│   └── src/ai/         # Explication IA (local_strict)
├── parser/             # Parser COBOL ANTLR4 Java (prévu Epic 4+)
├── packages/           # Types partagés, schémas, prompts
├── samples/            # Patrimoine de test (Bank-of-Z)
└── deployment/         # Docker Compose
```

**Stack :** TypeScript / VS Code API · Python 3.11 / FastAPI / Pydantic v2 / SQLite · Java / ANTLR4 (parser, prévu)

## Démarrage rapide

### Prérequis

- VS Code 1.85+
- Node.js 20 LTS
- Python 3.11+

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/macOS
pip install -e ".[dev]"
cp .env.example .env
python -m uvicorn src.main:app --reload --port 8000
```

### Extension

```bash
cd extension
npm install
npm run compile
```

Ouvrir `extension/` dans VS Code, puis **F5** pour lancer l'Extension Development Host.

### Vérification

```bash
curl http://localhost:8000/api/health
# {"status": "ok", "version": "0.1.0"}
```

## Tests

```bash
cd backend
pytest -v
# 126 tests, ~1.7 s
```

## Sécurité

Le mode IA par défaut est `local_strict` : aucun code COBOL n'est envoyé à un service externe.  
`security.allowExternalAi` est `false` par défaut et ne peut être activé que par confirmation explicite.

## Documentation

Toute la documentation de conception est disponible dans le **[Wiki GitHub](../../wiki)** :

- [Cadrage produit](../../wiki/Cadrage-produit) — vision, personas, périmètre MVP
- [Architecture technique](../../wiki/Architecture-technique) — composants, flux, modes de déploiement
- [Modèle graphe](../../wiki/Modele-graphe) — nœuds, relations, niveaux de confiance
- [Pipeline d'indexation](../../wiki/Pipeline-indexation) — scan, parsing, résolution, graphe
- [Extension VS Code](../../wiki/Extension-VSCode) — commandes, vues, webviews
- [IA, RAG et agents](../../wiki/IA-RAG-Agents) — cas d'usage, architecture RAG, garde-fous
- [API Backend](../../wiki/API-Backend) — endpoints REST
- [Sécurité et confidentialité](../../wiki/Securite-Confidentialite) — modes IA, audit, contrôle d'accès
- [Backlog MVP](../../wiki/Backlog-MVP) — user stories, état d'avancement
- [Journal de développement](../../wiki/Journal-developpement) — log par étape
- [Runbook](../../wiki/Runbook) — installation, configuration, troubleshooting
- [ADR Register](../../wiki/ADR-Register) — décisions d'architecture

## Licence

À définir.
