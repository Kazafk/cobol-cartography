# Agent Team - Carto Cobol

This document defines the complete agent team for the `cobol-cartography` project: a VS Code extension with an AI-powered backend that cartographs large COBOL portfolios through static analysis and a graph model.

Project structure reference: `cobol-cartography/` monorepo with `extension/`, `backend/`, `parser/`, `packages/`, `samples/`, `deployment/`.
Design documentation: `Carto Cobol/` (this folder) - see `README.md` for the document index.


## Orchestrator

### `carto-cobol-orchestrator`

**File**: `~/.claude/agents/carto-cobol-orchestrator.md`
**Model**: opus

**Role**: Task decomposition and agent sequencing. Does not implement features. Receives any non-trivial backlog item or feature request, produces a structured execution plan: which agents run, in what order, on what inputs, producing what outputs, with acceptance criteria for each step.

Knows the MVP backlog prioritization order (US-001 ? . ? US-051), the five orchestration patterns (new parser extraction, new AI use case, new VS Code view, deployment mode, ADR), and the dependency rules between modules (parser before graph before RAG; schema packages before implementation; security audit before any AI call path merges).

**Trigger conditions**:
- Any task that spans more than one module or more than one agent
- Starting work on a new user story or epic
- Unsure which agent(s) should handle a given feature
- Need to define the API contract between two components before parallel work starts

**Does NOT do**: write code, run tests, audit security, design prompts.

**Always produces**: a written plan with named agents, sequenced steps, explicit contracts, security checkpoint flag, and test strategy.

---
## Custom agents (project-specific)

These four agents are defined in `~/.claude/agents/` and encode knowledge specific to this project that no generic catalog agent carries.

### `cobol-parser-domain`

**File**: `~/.claude/agents/cobol-parser-domain.md`
**Model**: sonnet

**Role**: COBOL language and parsing expert. Owns the `parser/` module (Java/Gradle). Knows IBM Enterprise COBOL dialects, fixed/free source format, copybook resolution (COPY, COPY REPLACING), EXEC SQL/EXEC CICS extraction, JCL structure, ANTLR grammar development, and the intermediate parser output model.

**Trigger conditions**:
- Any work in `parser/src/`
- Adding or modifying COBOL fixtures in `samples/mini-portfolio/`
- Debugging copybook resolution failures or dialect-specific parse errors
- Extending the intermediate model schema in `packages/shared-model/`

**Does NOT do**: graph queries, LLM calls, VS Code API, infrastructure.

**Hands off to**:
- `graph-cartographer` - receives the intermediate model and builds graph nodes/relations
- `java-architect` - for Gradle/build toolchain issues
- `fastapi-developer` - for the indexing pipeline API that invokes the parser

---

### `graph-cartographer`

**File**: `~/.claude/agents/graph-cartographer.md`
**Model**: sonnet

**Role**: Graph schema and impact query specialist. Owns `backend/src/graph/` and `packages/graph-schema/`. Knows all node types (Program, Copybook, JCLJob, JCLStep, DB2Table, DB2Column, File, DDName, CICSTransaction, Paragraph, Section, BusinessRuleCandidate), all relation types with directionality, confidence level semantics (1.0 deterministic to 0.2 uncertain), and SQLite/Neo4j query patterns for impact analysis.

See [[Modele-graphe]] for the full schema specification.

**Trigger conditions**:
- Any change to `packages/graph-schema/`
- Any change to `backend/src/graph/`
- Designing or debugging impact analysis queries (copybook impact, DB2 table impact, batch chain)
- Reasoning about which relations should exist between two nodes
- Assigning confidence levels on any relation

**Does NOT do**: COBOL source parsing, LLM calls, VS Code UI, deployment.

**Hands off to**:
- `rag-context-builder` - provides sub-graphs for AI context assembly
- `fastapi-developer` - exposes graph query results via REST endpoints
- `database-administrator` - for index tuning on large portfolios
- `cobol-parser-domain` - for questions about what the parser can extract deterministically

---

### `rag-context-builder`

**File**: `~/.claude/agents/rag-context-builder.md`
**Model**: opus

**Role**: RAG pipeline and AI agent architect. Owns `backend/src/rag/`, `backend/src/ai/`, and `packages/prompt-templates/`. Designs the four-layer hybrid retrieval strategy (graph ? fulltext ? vector ? heuristics), assembles traceable context bundles, defines the five specialized agents (Inventaire, Analyse COBOL, Documentation, Impact, Modernisation), enforces the AI response schema, and manages prompt versioning.

See [[IA-RAG-Agents]] for the full agent and use-case specification.

**Trigger conditions**:
- Any change to `backend/src/rag/` or `backend/src/ai/`
- Adding or modifying prompt templates in `packages/prompt-templates/`
- Implementing a new AI use case (explain program, extract rules, summarize impact)
- Tuning retrieval quality or context size
- Adding embedding logic or vector store integration
- Reviewing any LLM call for guard-rail compliance

**Does NOT do**: graph schema definition, COBOL parsing, VS Code extension code.

**Always pairs with**: `security-confidentiality-guard` - any new LLM call path must be reviewed for ai_mode compliance before shipping.

**Hands off to**:
- `graph-cartographer` - to store BusinessRuleCandidate nodes (confidence 0.5, status=candidate) from AI output
- `fastapi-developer` - for `/explain`, `/rules`, `/impact-summary` API endpoints
- `prompt-engineer` - for prompt quality review cycles

---

### `security-confidentiality-guard`

**File**: `~/.claude/agents/security-confidentiality-guard.md`
**Model**: sonnet

**Role**: Security and confidentiality reviewer. Read-only: audits and reports, does not write code. Enforces data classification (COBOL source = CONFIDENTIAL), ai_mode rules (local_strict / enterprise_controlled / external_authorized), audit trail requirements for every LLM call, secret storage patterns (VS Code SecretStorage extension-side, vault/env backend-side), and access control roles for team mode.

See [[Securite-Confidentialite]] for the full security specification.

**Trigger conditions**:
- Any new or modified LLM call path in `backend/src/ai/` or `backend/src/rag/`
- Any export endpoint in `backend/src/api/`
- Any configuration loading code touching `security.*` settings
- Any secret access in `extension/src/` or `backend/src/`
- Before finalizing a Docker image or CI/CD pipeline that handles API keys
- Any feature that sends data outside the local process

**Reports findings as**: BLOCK (must fix before ship) / WARN (fix soon) / INFO (suggestion). Never modifies files.

**Called by**: `rag-context-builder` before every new outbound LLM call path is finalized.

---

## Catalog agents - one per technical domain

Standard agents from the Claude Code catalog. Invoke for their respective module.

| Agent | Module | When to invoke |
|-------|--------|----------------|
| `typescript-pro` | `extension/` | VS Code extension code, webviews, tree views, TypeScript type issues, VS Code API |
| `fastapi-developer` | `backend/` | Python async API routes, dependency injection, ASGI, Pydantic v2, background jobs |
| `java-architect` | `parser/` | Gradle build, Java architecture, ANTLR integration, multi-module project setup |
| `database-administrator` | Graph + vector storage | Neo4j configuration, SQLite schema, pgvector, index strategy for large portfolios |
| `ml-engineer` | `backend/src/rag/` (embeddings) | Embedding pipeline, vector store selection, LanceDB or pgvector integration |
| `llm-architect` | `backend/src/ai/` | Multi-model routing, model selection, inference serving, quantization |
| `test-automator` | All modules | Unit, integration, E2E tests and fixture design across `parser/`, `backend/`, `extension/` |
| `docker-expert` | `deployment/` | Multi-service docker-compose, image layering, local/team/on-premise modes |
| `architect-reviewer` | Cross-cutting | ADR review, interface contract validation, cross-module consistency |

---

## Agent collaboration map

```
User action in VS Code
        |
        v
  typescript-pro -- extension/
        | HTTP / WebSocket
        v
  fastapi-developer -- backend/api/
        |
        +---> graph-cartographer -- backend/graph/ + packages/graph-schema/
        |         |
        |         +---<-- cobol-parser-domain -- parser/ ---> java-architect
        |         |
        |         +---->  database-administrator -- Neo4j / SQLite / pgvector
        |
        +---> rag-context-builder -- backend/rag/ + backend/ai/ + packages/prompt-templates/
        |         |
        |         +---<-- graph-cartographer (sub-graphs)
        |         +---<-- ml-engineer (embedding pipeline)
        |         +---<-- llm-architect (model serving)
        |         +---->  security-confidentiality-guard (pre-flight check)
        |
        +---> test-automator -- tests/

Cross-cutting:
  architect-reviewer ---> all modules (ADR review, interface contracts)
  security-confidentiality-guard ---> all AI/export paths (audit)
```

---

## Trigger cheat sheet

| Task | Primary agent | Supporting agents |
|------|--------------|-------------------|
| Parse a new COBOL construct | `cobol-parser-domain` | `java-architect` |
| Add a new graph node or relation type | `graph-cartographer` | `database-administrator` |
| Add an impact analysis query | `graph-cartographer` | `fastapi-developer` |
| Implement a new AI use case | `rag-context-builder` | `security-confidentiality-guard`, `llm-architect` |
| Add a VS Code tree view or command | `typescript-pro` | - |
| Add a backend REST endpoint | `fastapi-developer` | `security-confidentiality-guard` (if data export) |
| Add embedding or vector search | `rag-context-builder` | `ml-engineer` |
| Set up Docker compose | `docker-expert` | `database-administrator` |
| Write parser tests with COBOL fixtures | `cobol-parser-domain` | `test-automator` |
| Review an ADR | `architect-reviewer` | relevant domain agent |
| Audit a new AI call for confidentiality | `security-confidentiality-guard` | - |

---

## Project-wide guard-rails

These apply to all agents and all modules:

1. **No invented dependencies.** The LLM must never create a graph relation not produced by the parser or derived from an explicit graph query. AI-suggested relations are confidence <= 0.5 and status=candidate until a human validates them.

2. **Source code stays local by default.** `security.allowExternalAi` is false. COBOL source, copybook content, SQL, and JCL never leave the process boundary unless the user explicitly enables and confirms external AI mode.

3. **Every LLM call is audited.** Timestamp, user, model, data types sent, token count, status. Full prompts and source excerpts are never written to audit logs.

4. **Read-only relative to the portfolio.** No agent modifies COBOL, JCL, or copybook files. The tool analyzes, documents, and explains - it does not refactor or transform source automatically.

5. **Confidence is always visible.** Every impact result and AI response surfaces the confidence level. Users distinguish facts (1.0), inferences (0.8), AI proposals (0.5), and uncertainties (0.2).