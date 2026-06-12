# Registre des ADR

> Voir aussi : [[Decisions-architecture]] | [[Strategie-documentation]] | [[Journal-developpement]]

Les ADR (Architecture Decision Records) documentent les décisions d'architecture importantes et leur justification.
Format individuel dans `ADR/ADR-XX-<slug>.md`.

## Registre

| N° | Titre | Statut | Date | Agent |
|----|-------|--------|------|-------|
| [[ADR/ADR-01-stockage-graphe\|ADR-01]] | Stockage graphe : SQLite pour le MVP | Accepté | 2026-05-21 | `architect-reviewer` |
| [[ADR/ADR-02-parser-cobol\|ADR-02]] | Parser COBOL : ANTLR4 Java, dialecte IBM | Accepté | 2026-05-21 | `architect-reviewer` |
| [[ADR/ADR-03-backend-python\|ADR-03]] | Backend : Python / FastAPI | Accepté | 2026-05-21 | `architect-reviewer` |
| [[ADR/ADR-04-mode-ia-par-defaut\|ADR-04]] | Mode IA par défaut : local_strict | Accepté | 2026-05-21 | `security-confidentiality-guard` |
| ADR-05 | Réservé (gap schéma graphe si détecté) | - | - | - |
| ADR-06 | Modèle IA local (Epic 6) | À rédiger | - | `llm-architect` |

## Statuts possibles

- **Proposé** - rédigé, en attente de validation par l'équipe
- **Accepté** - validé, applicable immédiatement
- **Remplacé** - supplanté par un ADR ultérieur (lien dans la colonne Titre)
- **Obsolète** - plus applicable (contexte changé)