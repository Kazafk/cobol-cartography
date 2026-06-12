# ADR-04 - Mode IA par d�faut : local_strict

> Registre : [[ADR-Register]]

**Statut** : Propos�
**Date** : � compl�ter
**D�cideurs** : `security-confidentiality-guard`, `architect-reviewer`

## Contexte

Bank-of-Z et les portfolios COBOL clients contiennent des r�gles m�tier propri�taires, des noms de tables et de datasets internes, et potentiellement des informations personnelles (dans les structures de donn�es).
La configuration IA par d�faut doit prot�ger ces donn�es sans n�cessiter d'action de l'utilisateur.

R�f�rence s�curit� : [[Securite-Confidentialite]].

## Options �valu�es

| Option | Protection | Fonctionnalit� IA |
|--------|-----------|-------------------|
| **local_strict** | Maximale - aucun code ne quitte le processus | Mod�le local requis (Ollama) |
| enterprise_controlled | Bonne - mod�le cloud priv� | N�cessite contrat fournisseur |
| external_authorized | Faible par d�faut | Mod�le public (OpenAI, etc.) |

## D�cision

**`local_strict` est le mode par d�faut.**
`external_authorized` est d�sactiv� (`security.allowExternalAi: false`) et ne peut �tre activ� que par confirmation explicite de l'utilisateur dans les settings VS Code.

## Cons�quences

- `security-confidentiality-guard` v�rifie `ai_mode` avant toute invocation LLM.
- Le backend rejette tout appel LLM si `allowExternalAi: false` et que l'URL du mod�le est externe.
- Epic 6 utilise Ollama en local (service Docker ou processus natif).
- `GET /capabilities` retourne toujours l'`ai_mode` actif.
- Les logs d'audit ne contiennent jamais le contenu des prompts.

## Validation

- [ ] Audit `security-confidentiality-guard` : 0 BLOCK avant merge Epic 6
- [ ] Test : tentative d'appel externe avec `allowExternalAi: false` ? `403 Forbidden`
- [ ] `GET /capabilities` retourne `"ai_mode": "local_strict"` sans configuration