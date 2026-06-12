# ADR-02 - Parser COBOL : ANTLR4 Java, dialecte IBM Enterprise COBOL

> Registre : [[ADR-Register]]

**Statut** : Propos�
**Date** : � compl�ter
**D�cideurs** : `architect-reviewer`, `cobol-parser-domain`, `java-architect`

## Contexte

Le parser doit couvrir IBM Enterprise COBOL fixe-format (z/OS) avec EXEC CICS, EXEC SQL et les directives `PROCESS`/`CBL`.
Le corpus cible : Bank-of-Z (38 programmes), puis portfolios clients de 50-500 programmes.

## Options �valu�es

| Option                     | Avantages                                                           | Inconv�nients                                 |
| -------------------------- | ------------------------------------------------------------------- | --------------------------------------------- |
| **ANTLR4 Java**            | Grammaire maintenable, �cosyst�me mature, int�gration Gradle native | Courbe COBOL ambigu�, performances parsing    |
| GnuCOBOL (cobc)            | Compilateur r�el, fid�le au dialecte                                | Pas d'API AST exploitable, d�pendance binaire |
| TreeSitter (COBOL grammar) | Rapide, incremental                                                 | Grammaire COBOL incompl�te pour EXEC CICS/SQL |
| Parser maison              | Contr�le total                                                      | Effort prohibitif, non maintenable            |

## D�cision

**ANTLR4 Java** avec les contraintes suivantes :
- Pr�processeur obligatoire avant le lexer : strip colonnes 1-6 (num�ros de s�quence), gestion des directives `PROCESS`/`CBL`, continuation lines (colonne 7 = `-`).
- Dialecte cible : IBM Enterprise COBOL. Les constructions GnuCOBOL ou MicroFocus hors dialecte IBM sont signal�es en `parse_errors`, pas en exception fatale.
- `CALL 'CBLTDLI'` ? IMS call, confidence 0.8 (non r�solvable statiquement dans tous les cas).

## Cons�quences

- `cobol-parser-domain` est le propri�taire unique de `parser/`.
- Tout nouveau dialecte ou construction d�clenche un ADR ou une sous-t�che dans le backlog.
- Le mod�le interm�diaire JSON est d�fini dans `packages/shared-model/` et versionn� s�par�ment de la grammaire.
- Le parser est invoqu� comme subprocess par le backend Python (pas d'appel gRPC dans le MVP).

## Validation

- [ ] 38/38 programmes Bank-of-Z pars�s sans `parse_errors`
- [ ] 40/40 copybooks r�solus
- [ ] EXEC CICS LINK extrait avec le nom de programme cible