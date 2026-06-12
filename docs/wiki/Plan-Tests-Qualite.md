> Voir aussi : [[Cadrage-produit]] | [[Pipeline-indexation]] | [[IA-RAG-Agents]] | [[Backlog-MVP]] | [[Home]]

# Plan de tests et qualité

## Objectif

Garantir que la cartographie produite est fiable, traçable et utile avant d’ajouter des fonctions IA avancées.

## Stratégie de tests

### Tests unitaires

À couvrir :

- Classification de fichiers.
- Résolution copybooks.
- Extraction CALL.
- Extraction PERFORM.
- Extraction EXEC SQL.
- Extraction EXEC CICS.
- Extraction JCL.
- Construction de nœuds graphe.
- Construction de relations graphe.

### Tests d’intégration

À couvrir :

- Indexation complète d’un mini-patrimoine.
- Mise à jour incrémentale.
- Requête dépendances programme.
- Analyse d’impact copybook.
- Analyse d’impact table.
- Génération fiche programme.

### Tests extension VS Code

À couvrir :

- Activation extension.
- Commandes.
- TreeView.
- Webview.
- Navigation vers source.
- Gestion backend indisponible.

### Tests IA

À couvrir :

- Construction du contexte.
- Respect du format de réponse.
- Absence de dépendance inventée.
- Présence des incertitudes.
- Gestion contexte trop long.
- Désactivation IA externe.

## Jeux de test

### Mini patrimoine synthétique

Contenu :

- 5 programmes COBOL.
- 3 copybooks.
- 2 JCL.
- 3 tables DB2.
- 2 fichiers.
- 1 transaction CICS.

Objectif :

- Tests rapides.
- CI/CD.
- Non-régression.

### Patrimoine pilote

Contenu :

- 50 à 200 programmes réels.
- Copybooks réels.
- JCL réels.
- DB2 si possible.

Objectif :

- Validation terrain.
- Mesure performance.
- Validation utilité.

## Métriques qualité

### Parsing

- Taux de fichiers parsés avec succès.
- Nombre d’erreurs par type.
- Nombre de copybooks non résolus.

### Graphe

- Nombre de nœuds par type.
- Nombre de relations par type.
- Taux de relations incertaines.
- Nombre de composants orphelins.

### Performance

- Temps d’indexation complet.
- Temps d’indexation incrémental.
- Temps de réponse analyse d’impact.
- Temps de génération explication IA.

### IA

- Pourcentage de réponses conformes au schéma.
- Nombre d’hypothèses non sourcées.
- Taux de règles métier validées.
- Taux de règles métier rejetées.

## Critères de passage MVP

- 90 % des fichiers du périmètre pilote classifiés.
- 80 % des programmes COBOL parsés ou partiellement analysés.
- 95 % des copybooks résolus sur le périmètre configuré.
- Analyse d’impact copybook exploitable.
- Fiche programme générée sans erreur bloquante.
- IA désactivable complètement.
- Aucune fuite de code dans les logs par défaut.

