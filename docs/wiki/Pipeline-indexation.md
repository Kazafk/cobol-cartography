# Pipeline d'indexation

> Voir aussi : [[Architecture-technique]] | [[Modele-graphe]] | [[Plan-Tests-Qualite]] | [[Home]]

## Objectif

Transformer un patrimoine source COBOL en graphe exploitable, index texte et index vectoriel.

## Étapes du pipeline

### Découverte

Entrées : répertoire local, dépôt Git, exports z/OS, JCL, copybooks.

Sorties : inventaire brut, classification initiale par type (COBOL programmes, copybooks, JCL, PROC, SQL DDL, metadata DB2, documentation).

### Normalisation

Actions : détection encodage, conversion EBCDIC→UTF-8, normalisation fins de ligne, identification format fixe/libre, suppression colonnes COBOL, calcul de hash.

### Prétraitement COBOL

Actions : résolution `COPY`, gestion `COPY REPLACING`, gestion bibliothèques multiples, conservation lien source, construction vue prétraitée.

Points d'attention :
- Ne jamais perdre la correspondance avec les lignes originales.
- Conserver les offsets pour la navigation VS Code. → [[Extension-VSCode]]
- Marquer les dépendances non résolues.

### Parsing

Actions : parsing syntaxique COBOL, extraction AST, divisions/sections/paragraphes, Data Division, Procedure Division, EXEC SQL et EXEC CICS.

Résultat : modèle intermédiaire normalisé indépendant du parseur. → [[Decisions-architecture]]

### Analyse sémantique

Actions : résolution des appels, analyse des PERFORM, identification fichiers et tables DB2, variables clés, détection SQL read/write, commandes CICS.

### Construction graphe

Actions : upsert nœuds et relations, suppression relations obsolètes, calcul métriques. → [[Modele-graphe]]

Métriques : lignes, paragraphes, CALL, COPY, tables lues, tables modifiées, complexité approximative, centralité.

### Indexation texte

Indexer : code brut, code prétraité, commentaires, résumés générés, documentation associée.

### Indexation vectorielle

Granularité recommandée : programme entier, paragraphes/sections, copybooks, JCL steps, documentation.

Chaque chunk conserve : `source_type`, `source_id`, `path`, `start_line`, `end_line`, `hash`, `indexed_at`.

## Indexation incrémentale

Détection par hash. Si un fichier change : réindexer le fichier + ses dépendants si copybook, mettre à jour relations et embeddings.

## Gestion des erreurs

Chaque erreur tracée avec : fichier, type, étape, message, gravité, suggestion.

Catégories : `UNSUPPORTED_DIALECT` | `COPY_NOT_FOUND` | `PARSING_ERROR` | `ENCODING_ERROR` | `SQL_EXTRACTION_ERROR` | `JCL_EXTRACTION_ERROR` | `AI_CONTEXT_TOO_LARGE`