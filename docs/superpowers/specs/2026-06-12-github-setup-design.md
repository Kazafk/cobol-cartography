# Design — Publication GitHub du projet Cobol Carto

**Date :** 2026-06-12  
**Statut :** Approuvé

## Contexte

Le projet `cobol-cartography` existe en local (`C:\Repos\cobol-cartography`) avec un squelette de code fonctionnel (FastAPI backend + extension VS Code) et 17 notes de conception dans le vault Obsidian (`Carto Cobol/`). Aucun remote GitHub n'est configuré.

## Objectif

Publier le projet sur GitHub en rassemblant le code et toute la documentation de conception dans un seul dépôt public.

## Décisions

| Dimension | Choix | Raison |
|---|---|---|
| Visibilité | Public | Partage et open-source potentiel |
| Docs vault | Wiki GitHub | Séparation docs/code, navigation wiki native |
| Fichiers WIP | Inclus (commit initial) | Conserver l'état complet du projet |

## Périmètre d'exécution

### 1. Repo GitHub

- Compte : `Kazafk`
- Nom : `cobol-cartography`
- Description : *"Extension VS Code de cartographie COBOL avec IA — analyse statique, graphe de dépendances, RAG"*

### 2. Code

- Enrichir `README.md` avec vision produit, personas, architecture résumée
- Commiter les fichiers non stagés (routes API, tests, views)
- Pusher toute la branche `epic/1-skeleton`

### 3. Wiki GitHub (17 pages)

Les notes Obsidian sont importées comme pages wiki. Les `[[wikilinks]]` Obsidian sont convertis en liens wiki Markdown. Pages :

- Home (README vault + cadrage produit)
- Architecture-technique
- Modele-graphe
- Pipeline-indexation
- Extension-VSCode
- IA-RAG-Agents
- API-Backend
- Securite-Confidentialite
- Backlog-MVP
- Plan-Tests-Qualite
- Structure-projet
- Decisions-architecture
- Strategie-documentation
- Journal-developpement
- Contrats-API
- Runbook
- ADR-Register + pages ADR individuelles
