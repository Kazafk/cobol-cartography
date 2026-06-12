# Plugin VS Code de cartographie COBOL avec IA

Ce dossier contient les �l�ments de conception technique n�cessaires au d�marrage d'un projet de plugin VS Code destin� � cartographier un patrimoine COBOL important avec des capacit�s d'IA.

## Objectif du projet

L'objectif est de fournir aux architectes, d�veloppeurs et responsables de modernisation mainframe une extension VS Code permettant de comprendre, explorer, documenter et analyser l'impact d'un patrimoine COBOL volumineux.

Le principe directeur est de construire d'abord une cartographie d�terministe fiable, puis d'ajouter l'IA comme couche d'explication, d'enrichissement et d'assistance. L'IA ne doit pas remplacer le parsing, la r�solution des d�pendances ou l'analyse statique.

## Documents de conception

- [[Cadrage-produit]] - Vision produit, personas, p�rim�tre MVP, crit�res de succ�s
- [[Architecture-technique]] - Architecture cible, composants, flux principaux, modes de d�ploiement
- [[Modele-graphe]] - Mod�le de graphe applicatif COBOL : nouds, relations, niveaux de confiance
- [[Pipeline-indexation]] - Pipeline d'ingestion, parsing, r�solution, indexation texte et vectorielle
- [[Extension-VSCode]] - Commandes VS Code, vues lat�rales, webviews, int�gration �diteur
- [[IA-RAG-Agents]] - Cas d'usage IA, architecture RAG, agents sp�cialis�s, garde-fous
- [[API-Backend]] - Endpoints API entre l'extension et le serveur d'analyse
- [[Securite-Confidentialite]] - S�curit�, modes IA, audit, contr�le d'acc�s, risques
- [[Backlog-MVP]] - Backlog MVP prioris� par epic et user stories
- [[Plan-Tests-Qualite]] - Strat�gie de tests, jeux de test, m�triques qualit�, crit�res MVP
- [[Structure-projet]] - Structure de repository recommand�e, conventions de branches
- [[Decisions-architecture]] - ADR : graphe, parser, IA, backend, modification automatique

## Hypoth�ses de d�part

- Patrimoine COBOL important, potentiellement issu de z/OS, avec COBOL, COPYBOOK, JCL, PROC, SQL embarqu�, CICS et DB2.
- Besoin d'une approche industrialisable et compatible avec des contraintes de confidentialit� fortes.
- Besoin d'un outil utilisable par des �quipes mainframe, modernisation, architecture et DevOps.
- D�ploiement possible en local d�veloppeur, en serveur d'�quipe ou dans un environnement on-premise.

## Architecture en deux ensembles

1. Une extension VS Code pour la navigation, la visualisation, les commandes et l'exp�rience d�veloppeur. ? [[Extension-VSCode]]
2. Un serveur d'analyse COBOL et IA pour le parsing, le graphe, les embeddings, le RAG, les analyses d'impact et la g�n�ration documentaire. ? [[Architecture-technique]]

## Livrable MVP recommand�

- Scan d'un workspace ou d'un r�pertoire de sources. ? [[Pipeline-indexation]]
- R�solution des COPYBOOK.
- Extraction des d�pendances principales : CALL, PERFORM, COPY, EXEC SQL, EXEC CICS, fichiers, JCL. ? [[Modele-graphe]]
- Construction d'un graphe technique.
- Fiche programme dans VS Code. ? [[Extension-VSCode]]
- Analyse d'impact � partir d'un programme, copybook, table DB2 ou fichier.
- Premi�re fonction IA : explication contextualis�e d'un programme. ? [[IA-RAG-Agents]]
## Documentation d'impl�mentation

- [[Strategie-documentation]] - o� et comment documenter, conventions
- [[Journal-developpement]] - log de d�veloppement par �tape (mis � jour en continu)
- [[Contrats-API]] - contrats HTTP finalis�s entre extension et backend
- [[Runbook]] - installation, configuration, lancement, troubleshooting
- [[ADR-Register]] - registre des d�cisions d'architecture
  - [[ADR-01-Stockage-graphe]] - SQLite pour le MVP
  - [[ADR-02-Parser-COBOL]] - ANTLR4 Java, IBM Enterprise COBOL
  - [[ADR-03-Backend-Python]] - Python / FastAPI
  - [[ADR-04-Mode-IA-par-defaut]] - local_strict par d�faut