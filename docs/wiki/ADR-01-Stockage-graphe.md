# ADR-01 - Stockage graphe : SQLite pour le MVP

> Registre : [[ADR-Register]]

**Statut** : Propos�
**Date** : � compl�ter
**D�cideurs** : `architect-reviewer`, `graph-cartographer`, `database-administrator`

## Contexte

Le graphe applicatif COBOL doit �tre interrogeable en < 500ms sur 500 programmes.
Plusieurs options ont �t� �valu�es : Neo4j, PostgreSQL + pgvector, SQLite avec CTEs r�cursifs.

## Options �valu�es

| Option | Avantages | Inconv�nients |
|--------|-----------|---------------|
| **SQLite + CTE r�cursifs** | Z�ro d�pendance externe, fichier local, suffisant pour MVP (< 500 programmes) | Pas de langage de requ�te graphe natif, scalabilit� limit�e |
| Neo4j | Cypher expressif, travers�es natives | Service externe requis, complexit� d�ploiement |
| PostgreSQL + ltree | SQL standard, bon pour �quipes | Lourd pour mode d�veloppeur local |

## D�cision

**SQLite avec CTEs r�cursifs** pour le MVP local.
Upgrade vers Neo4j document� dans [[Architecture-technique]] pour le mode �quipe.

## Cons�quences

- `database-administrator` fournit un DDL SQLite + CTEs test�s sur 500 nouds.
- Le sch�ma est d�fini dans `packages/graph-schema/` - ind�pendant du moteur de stockage.
- La couche `backend/src/graph/` expose une interface abstraite permettant de brancher Neo4j sans changer les appelants.
- Performance cible : impact copybook sur 500 programmes < 500ms.

## Validation

- [ ] Benchmark CTE r�cursif sur 500 nouds / 2000 relations
- [ ] Interface abstraite valid�e par `architect-reviewer`