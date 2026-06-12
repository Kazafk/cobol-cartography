# Décisions d'architecture à arbitrer

> Voir aussi : [[Architecture-technique]] | [[Modele-graphe]] | [[Pipeline-indexation]] | [[Securite-Confidentialite]] | [[Home]]

## ADR-001 — Backend local ou serveur partagé → [[Architecture-technique]]

**Option A — Backend local** : simple pour MVP, moins d'infrastructure, données proches du développeur. Limite : collaboration réduite, duplication des index.

**Option B — Backend partagé** : index centralisé, collaboration, meilleure gouvernance. Limite : infrastructure et authentification nécessaires.

**Recommandation** : MVP en local, architecture compatible serveur partagé dès le départ.

## ADR-002 — Graphe Neo4j ou PostgreSQL → [[Modele-graphe]]

**Option A — Neo4j** : naturel pour graphes, requêtes d'impact expressives, écosystème mature. Limite : compétences Cypher.

**Option B — PostgreSQL** : standard entreprise, facile à opérer, extensions vecteur possibles. Limite : requêtes graphe moins naturelles.

**Recommandation** : Neo4j pour accélérer le MVP graphe. PostgreSQL si contrainte d'urbanisation SI.

## ADR-003 — Parser Java ou TypeScript/Python → [[Pipeline-indexation]]

**Option A — Parser Java** : écosystème ANTLR mature, cohérent avec parseurs COBOL existants. Limite : stack supplémentaire.

**Option B — Parser TypeScript/Python** : stack homogène avec extension/IA, développement rapide. Limite : parsing COBOL potentiellement moins robuste.

**Recommandation** : Parser Java avec modèle intermédiaire JSON. Backend IA en Python ou TypeScript.

## ADR-004 — IA externe ou IA on-premise → [[IA-RAG-Agents]] | [[Securite-Confidentialite]]

**Option A — IA externe** : qualité élevée, mise en œuvre rapide, peu d'infrastructure. Limite : risques confidentialité, dépendance fournisseur.

**Option B — IA on-premise** : contrôle des données, meilleure acceptabilité sécurité. Limite : coût infrastructure, qualité variable.

**Recommandation** : prévoir les deux. Désactiver l'externe par défaut. Rendre le fournisseur IA interchangeable.

## ADR-005 — Modification automatique de code

**Recommandation** : interdire dans le MVP. Autoriser uniquement l'explication, la documentation et la suggestion. Toute modification doit rester manuelle ou passer par une validation explicite.