# Architecture technique

> Voir aussi : [[Cadrage-produit]] | [[Modele-graphe]] | [[Pipeline-indexation]] | [[Extension-VSCode]] | [[IA-RAG-Agents]] | [[API-Backend]] | [[Decisions-architecture]] | [[Home]]

## Vue d'ensemble

La solution est composée de quatre blocs principaux :

1. Extension VS Code. → [[Extension-VSCode]]
2. Backend d'analyse COBOL. → [[API-Backend]]
3. Stockage graphe, texte et vecteur. → [[Modele-graphe]]
4. Services IA et agents spécialisés. → [[IA-RAG-Agents]]

L'extension VS Code communique avec le backend via HTTP, WebSocket ou gRPC. Le backend orchestre le parsing, l'indexation, les requêtes graphe et les appels IA.

## Composants

### Extension VS Code

Responsabilités :

- Commandes utilisateur.
- Tree views.
- Webviews de cartographie.
- Navigation vers les sources.
- Affichage des fiches programme.
- Interaction avec le backend.
- Gestion de configuration locale.

### Backend API

Responsabilités :

- Exposer les API consommées par VS Code. → [[API-Backend]]
- Lancer les jobs d'indexation.
- Interroger le graphe.
- Construire les contextes RAG. → [[IA-RAG-Agents]]
- Appeler les modèles IA.
- Gérer la sécurité, les logs et les traces. → [[Securite-Confidentialite]]

### Analyseur COBOL

Responsabilités :

- Prétraitement COBOL.
- Résolution COPY et COPY REPLACING.
- Parsing syntaxique.
- Extraction des sections, paragraphes, variables, fichiers, SQL, CICS, CALL, PERFORM.
- Calcul des relations techniques. → [[Pipeline-indexation]]

### Moteur graphe

Responsabilités :

- Stocker les nœuds applicatifs.
- Stocker les relations.
- Répondre aux requêtes d'impact.
- Fournir les sous-graphes utiles aux vues VS Code et au RAG. → [[Modele-graphe]]

### Index texte et vectoriel

Responsabilités :

- Recherche plein texte.
- Recherche sémantique.
- Embeddings de code, commentaires, documentation et règles métier candidates.
- Construction de contextes pour les modèles IA. → [[IA-RAG-Agents]]

### Couche IA

Responsabilités :

- Explication de programmes.
- Synthèse de flux.
- Documentation assistée.
- Identification de règles métier candidates.
- Regroupement fonctionnel.
- Assistance à l'analyse d'impact.

## Flux principal d'indexation

1. L'utilisateur lance `COBOL Cartography: Index Workspace`.
2. L'extension envoie au backend la racine du workspace et la configuration.
3. Le backend découvre les fichiers.
4. Le backend résout les copybooks et dépendances de compilation.
5. L'analyseur extrait les métadonnées. → [[Pipeline-indexation]]
6. Le backend écrit les nœuds et relations dans le graphe. → [[Modele-graphe]]
7. Le backend crée les index texte et vecteur.
8. L'extension rafraîchit les vues. → [[Extension-VSCode]]

## Flux principal d'analyse d'impact

1. L'utilisateur sélectionne un copybook, programme, table ou fichier.
2. L'extension appelle l'API d'impact. → [[API-Backend]]
3. Le backend interroge le graphe.
4. Le backend classe les impacts directs, indirects et incertains.
5. L'extension affiche la carte d'impact et la liste des composants concernés.

## Flux principal d'explication IA

1. L'utilisateur ouvre un programme.
2. L'extension demande une explication.
3. Le backend récupère le programme, les copybooks, les appels, les tables, les fichiers et les paragraphes clés.
4. Le backend construit un contexte court et traçable.
5. Le modèle IA produit une explication structurée. → [[IA-RAG-Agents]]
6. L'explication est affichée avec les références techniques utilisées.

## Déploiements possibles

### Mode local développeur

- Backend lancé localement.
- Base locale SQLite, LanceDB ou fichiers JSON.
- Adapté au MVP et aux démonstrateurs. → [[Decisions-architecture]]

### Mode équipe

- Backend partagé.
- Graphe Neo4j ou PostgreSQL.
- Index vectoriel centralisé.
- Authentification d'entreprise. → [[Securite-Confidentialite]]

### Mode on-premise sécurisé

- Aucun code envoyé à des services externes.
- Modèle IA interne ou modèle hébergé dans un cloud privé.
- Logs d'audit. → [[Securite-Confidentialite]]
- Politique de rétention stricte.