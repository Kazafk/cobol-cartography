# IA, RAG et agents

> Voir aussi : [[Architecture-technique]] | [[Modele-graphe]] | [[API-Backend]] | [[Securite-Confidentialite]] | [[Home]]

## Principes

L'IA doit être utilisée comme couche d'assistance, pas comme source de vérité unique. Les faits techniques doivent provenir du graphe → [[Modele-graphe]], du code source, des métadonnées extraites et des documents indexés.

## Cas d'usage IA prioritaires

### Explication de programme

Entrées : code programme, copybooks, tables DB2, fichiers, CALL/PERFORM, JCL exécutant le programme.

Sortie : rôle probable, entrées, sorties, traitements principaux, dépendances, règles métier candidates, incertitudes.

### Explication de sélection

Entrées : fragment sélectionné, contexte local, variables, paragraphes appelants/appelés.

Sortie : explication fragment, effets sur données, risques, suggestions de questions.

### Analyse d'impact assistée

Entrées : sous-graphe d'impact, composant source, types de relations, historique de validation.

Sortie : synthèse des impacts, classement par criticité, chemins d'impact, points à vérifier manuellement.

### Rétro-documentation métier

Entrées : programmes, paragraphes clés, SQL, copybooks, noms de données, documentation existante.

Sortie : règles métier candidates, niveau de confiance, éléments de preuve, statut de validation.

## Architecture RAG

### Retrieval hybride

Combiner : requête graphe + recherche plein texte + recherche vectorielle + heuristiques COBOL.

### Construction du contexte

Le contexte envoyé au modèle doit être limité et traçable :

- Métadonnées programme
- Extraits de code pertinents
- Dépendances directes
- Résultats SQL / CICS extraits
- Extraits JCL
- Documentation existante

Chaque extrait porte : source, chemin, début/fin de ligne, type de contenu.

## Agents proposés

### Agent Inventaire

Responsabilités : identifier composants, classifier fichiers, signaler incohérences.

### Agent Analyse COBOL

Responsabilités : interpréter résultats de parsing, détecter dépendances incertaines, proposer corrections de configuration. → [[Pipeline-indexation]]

### Agent Documentation

Responsabilités : générer fiches programme, fiches application, synthèses de flux.

### Agent Impact

Responsabilités : synthétiser impacts, classer composants touchés, identifier tests de non-régression. → [[Plan-Tests-Qualite]]

### Agent Modernisation

Responsabilités : identifier candidats API, candidats événementiels, programmes fortement couplés, axes de découpage.

## Garde-fous IA

- Ne jamais inventer une dépendance absente du graphe.
- Distinguer clairement fait, inférence et hypothèse.
- Citer les extraits de code ou relations utilisés.
- Marquer les incertitudes.
- Ne jamais proposer de modification automatique sans validation humaine. → [[Decisions-architecture]]
- Ne jamais envoyer de code à un fournisseur externe si la configuration l'interdit. → [[Securite-Confidentialite]]

## Exemple de structure de réponse IA

```json
{
  "summary": "Résumé du programme",
  "inputs": [],
  "outputs": [],
  "main_processing_steps": [],
  "dependencies": [],
  "business_rule_candidates": [
    {
      "label": "Nom de règle",
      "description": "Description",
      "confidence": 0.72,
      "evidence": []
    }
  ],
  "risks": [],
  "uncertainties": []
}
```