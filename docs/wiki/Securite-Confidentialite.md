> Voir aussi : [[Architecture-technique]] | [[IA-RAG-Agents]] | [[Decisions-architecture]] | [[Home]]

# Sécurité et confidentialité

## Principes

Le patrimoine COBOL peut contenir des règles métier sensibles, des données personnelles, des conventions internes et des informations critiques. La solution doit être conçue avec une posture de sécurité forte dès le MVP.

## Classification des données

Types de données à considérer :

- Code source COBOL.
- Copybooks contenant des structures de données.
- SQL embarqué.
- Noms de tables et colonnes.
- JCL et noms de datasets.
- Documentation fonctionnelle.
- Résumés IA.
- Règles métier candidates.
- Logs d’analyse.

## Modes IA

### Mode local strict

- Aucun code envoyé à un service externe.
- Modèle local ou serveur interne.
- Recommandé pour environnements sensibles.

### Mode entreprise contrôlé

- Modèle hébergé dans un cloud privé ou tenant entreprise.
- Contrats et garanties de non-entraînement.
- Journalisation des appels.

### Mode externe autorisé

- Possible uniquement avec validation explicite.
- Filtrage ou anonymisation recommandée.
- Désactivé par défaut.

## Politique de configuration recommandée

Paramètres :

```json
{
  "security.allowExternalAi": false,
  "security.redactDatasetNames": true,
  "security.redactPersonalData": true,
  "security.auditAiCalls": true,
  "security.storePrompts": false,
  "security.storeModelResponses": true
}
```

## Audit

Tracer :

- Utilisateur.
- Horodatage.
- Action.
- Fichier ou composant concerné.
- Modèle IA utilisé.
- Taille du contexte.
- Statut de l’appel.
- Erreur éventuelle.

Ne pas tracer par défaut :

- Prompts complets contenant du code.
- Secrets.
- Tokens.
- Identifiants de connexion.

## Gestion des secrets

Les clés API et paramètres sensibles doivent être stockés :

- Dans le Secret Storage VS Code côté extension.
- Dans un coffre-fort côté backend.
- Jamais dans les fichiers de configuration versionnés.

## Contrôle d’accès

En mode équipe :

- Authentification SSO.
- Rôles utilisateur.
- Autorisation par application ou domaine.
- Journalisation des exports.

Rôles possibles :

- `reader`
- `developer`
- `architect`
- `admin`

## Risques principaux

### Fuite de code vers un modèle externe

Mesures :

- Désactiver l’externe par défaut.
- Liste blanche des fournisseurs.
- Confirmation explicite.
- Audit.

### Hallucination IA

Mesures :

- RAG basé sur graphe.
- Citations techniques obligatoires.
- Séparation fait / inférence / hypothèse.
- Validation humaine des règles métier.

### Mauvaise analyse d’impact

Mesures :

- Affichage du niveau de confiance.
- Distinction impacts directs, indirects et incertains.
- Tests sur jeux de référence.

### Données obsolètes

Mesures :

- Hash des fichiers.
- Horodatage d’indexation.
- Indexation incrémentale.
- Alerte si graphe plus ancien que le workspace.

