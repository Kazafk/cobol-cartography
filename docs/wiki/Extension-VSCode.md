> Voir aussi : [[Cadrage-produit]] | [[Architecture-technique]] | [[API-Backend]] | [[Backlog-MVP]] | [[Home]]

# Extension VS Code

## Objectif

Fournir une expérience développeur intégrée pour explorer le patrimoine COBOL, visualiser les dépendances, demander des explications IA et générer de la documentation.

## Commandes VS Code

Commandes recommandées :

- `COBOL Cartography: Index Workspace`
- `COBOL Cartography: Open Application Map`
- `COBOL Cartography: Show Program Card`
- `COBOL Cartography: Analyze Impact`
- `COBOL Cartography: Explain Current Program`
- `COBOL Cartography: Explain Selection`
- `COBOL Cartography: Generate Documentation`
- `COBOL Cartography: Validate Business Rule`
- `COBOL Cartography: Open Settings`

## Vues latérales

### Application Explorer

Arborescence :

- Applications.
- Programmes.
- Copybooks.
- Jobs.
- Tables.
- Fichiers.
- Transactions.

### Impact Explorer

Affiche :

- Composant source.
- Impacts directs.
- Impacts indirects.
- Incertitudes.
- Chemins d’impact.

### AI Insights

Affiche :

- Résumé programme.
- Règles métier candidates.
- Points de risque.
- Questions suggérées.
- Historique des explications.

## Webviews

### Carte applicative

Fonctions :

- Graphe interactif.
- Filtrage par type de nœud.
- Filtrage par application ou domaine.
- Zoom sur un sous-graphe.
- Ouverture du code au clic.

### Fiche programme

Sections :

- Résumé.
- Métadonnées.
- Dépendances entrantes.
- Dépendances sortantes.
- Tables DB2.
- Fichiers.
- Transactions CICS.
- Paragraphes clés.
- Règles métier candidates.
- Boutons d’action.

### Chaîne batch

Sections :

- Job.
- Steps.
- Programmes.
- DD names.
- Fichiers consommés et produits.
- Tables impactées.

## Intégration éditeur

Fonctions :

- CodeLens au-dessus des programmes et paragraphes.
- Hover sur CALL, COPY, EXEC SQL.
- Go to definition pour copybooks et programmes appelés.
- Find references pour copybooks, tables et programmes.
- Décoration des zones à risque.

## Configuration utilisateur

Exemple de configuration :

```json
{
  "cobolCartography.backendUrl": "http://localhost:8080",
  "cobolCartography.copybookPaths": [
    "copybooks",
    "includes"
  ],
  "cobolCartography.sourceFormat": "fixed",
  "cobolCartography.ai.enabled": true,
  "cobolCartography.ai.provider": "local",
  "cobolCartography.security.allowExternalAi": false
}
```

## Événements

Événements extension vers backend :

- `workspace.index.requested`
- `program.explain.requested`
- `impact.analysis.requested`
- `documentation.generate.requested`
- `businessRule.validation.submitted`

Événements backend vers extension :

- `indexing.started`
- `indexing.progress`
- `indexing.completed`
- `indexing.failed`
- `ai.response.completed`
- `graph.updated`

