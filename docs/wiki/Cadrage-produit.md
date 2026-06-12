# Cadrage produit

> Voir aussi : [[Architecture-technique]] | [[Backlog-MVP]] | [[Plan-Tests-Qualite]] | [[Home]]

## Vision

Créer une extension VS Code permettant de cartographier, explorer et comprendre un patrimoine COBOL massif grâce à une combinaison d'analyse statique déterministe et de capacités IA.

La solution doit aider à répondre rapidement aux questions suivantes :

- Quels programmes, copybooks, JCL, tables DB2, fichiers et transactions composent le patrimoine ?
- Quelles sont les dépendances entre composants ?
- Quel est l'impact d'une modification de copybook, table, fichier ou programme ?
- Quelles règles métier semblent implémentées dans un programme ou une chaîne batch ?
- Quels composants sont candidats à modernisation, refactoring, APIisation ou exposition événementielle ?

## Personas

### Architecte mainframe / modernisation

Objectifs :

- Comprendre les dépendances applicatives. → [[Modele-graphe]]
- Identifier les zones à risque.
- Préparer des scénarios de migration ou de modernisation.
- Générer des dossiers d'architecture et d'impact.

### Développeur COBOL

Objectifs :

- Naviguer rapidement entre programmes, copybooks, JCL et tables. → [[Extension-VSCode]]
- Comprendre un programme ancien. → [[IA-RAG-Agents]]
- Identifier les appelants et appelés.
- Préparer une modification avec moins de risque.

### Responsable applicatif

Objectifs :

- Obtenir une vision macro du patrimoine.
- Identifier les applications critiques.
- Documenter les flux fonctionnels.
- Suivre la progression de la rétro-documentation.

### Équipe DevOps / outillage

Objectifs :

- Intégrer l'indexation dans une chaîne CI/CD. → [[Pipeline-indexation]]
- Publier des rapports.
- Automatiser des contrôles qualité.
- Alimenter des tableaux de bord.

## Périmètre MVP

Le MVP doit être volontairement réduit mais robuste :

- Sources COBOL et copybooks dans un workspace local ou dépôt Git.
- Parsing et extraction de dépendances techniques principales. → [[Pipeline-indexation]]
- Support initial des CALL, COPY, PERFORM, EXEC SQL, EXEC CICS.
- Support initial JCL : JOB, EXEC PGM, PROC, DD.
- Graphe applicatif. → [[Modele-graphe]]
- Visualisation VS Code. → [[Extension-VSCode]]
- Analyse d'impact simple.
- Explication IA d'un programme avec contexte contrôlé. → [[IA-RAG-Agents]]

## Hors périmètre initial

- Transformation automatique COBOL vers Java.
- Modification automatique du code. → [[Decisions-architecture]]
- Exécution de jobs mainframe.
- Refactoring automatique.
- Détection exhaustive de toutes les règles métier.
- Couverture complète de tous les dialectes COBOL dès le départ.

## Critères de succès MVP

- Indexer un périmètre pilote de 50 à 200 programmes.
- Produire un graphe exploitable des dépendances.
- Permettre une analyse d'impact en moins de quelques secondes sur le périmètre pilote.
- Fournir une fiche programme claire et utile.
- Générer une explication IA qui cite les éléments techniques utilisés.
- Permettre l'export de documentation Markdown ou JSON.