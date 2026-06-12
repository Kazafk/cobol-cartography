# Stratégie de documentation

> Voir aussi : [[Home]] | [[Agent-Team]] | [[Journal-developpement]] | [[Contrats-API]] | [[Runbook]] | [[ADR-Register]]

## Principe

Toute la documentation vivante du projet **cobol-cartography** réside dans ce vault Obsidian.
Le code source est dans `C:\Repos\cobol-cartography\` (ou le répertoire équivalent).
La documentation est **mise à jour à la fin de chaque étape** du plan MVP, pas après le projet entier.

## Types de documents

| Type | Fichier | Mis é jour par | Quand |
|------|---------|----------------|-------|
| Design produit & technique | [[Cadrage-produit]] . [[Decisions-architecture]] | `architect-reviewer` | Avant de coder |
| Journal de développement | [[Journal-developpement]] | Agent ayant terminé l'étape | é la fin de chaque étape |
| Contrats API | [[Contrats-API]] | `fastapi-developer` ou `typescript-pro` | Dés qu'un contrat est finalisé |
| Runbook | [[Runbook]] | `docker-expert` / `fastapi-developer` | é la fin de chaque Epic |
| Registre ADR | [[ADR-Register]] | `architect-reviewer` | é chaque décision d'architecture |
| ADR individuels | [[ADR-01-Stockage-graphe]] . | `architect-reviewer` | é chaque décision |
| Agents de l'équipe | [[Agent-Team]] | `carto-cobol-orchestrator` | Lors d'un ajout d'agent |

## Régle d'or

**Une étape n'est pas terminée tant que le journal de développement n'a pas été mis é jour.**
L'agent `carto-cobol-orchestrator` vérifie cette condition dans les critéres d'acceptation de chaque étape.

## Structure du vault

```
Carto Cobol/
  README.md                       - index général
  AGENTS.md                       - équipe d'agents
  13-strategie-documentation.md   - ce fichier
  14-journal-developpement.md     - log running par étape
  15-contrats-api.md              - contrats HTTP finalisés
  16-runbook.md                   - installer, configurer, lancer
  17-adr-register.md              - registre des ADR
  ADR/
    ADR-01-stockage-graphe.md
    ADR-02-parser-cobol.md
    ADR-03-backend-python.md
    ADR-04-mode-ia-par-defaut.md
  01-cadrage-produit.md           - design docs (existants)
  .
  12-decisions-architecture.md
```

## Conventions de rédaction

- Chaque section du journal commence par `## étape N - <nom>` suivi de la date ISO (YYYY-MM-DD).
- Les décisions importantes (`DéCISION :`) sont en gras dans le journal, puis reportées dans le registre ADR si elles affectent l'architecture.
- Les liens wiki `[[fichier]]` sont utilisés pour relier les docs entre eux.
- Les extraits de code sont en blocs ` ``` ` avec le langage indiqué.
- Les items non résolus sont marqués `> ?? é résoudre :`.