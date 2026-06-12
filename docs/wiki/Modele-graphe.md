# Modèle graphe applicatif

> Voir aussi : [[Architecture-technique]] | [[Pipeline-indexation]] | [[IA-RAG-Agents]] | [[Decisions-architecture]] | [[Home]]

## Objectif

Le graphe représente les composants du patrimoine COBOL et leurs relations. Il doit permettre la navigation, l'analyse d'impact, la documentation et l'enrichissement IA. → [[IA-RAG-Agents]]

## Nœuds principaux

### Application

Propriétés : `id`, `name`, `domain`, `owner`, `criticality`, `description`

### Program

Propriétés : `id`, `name`, `path`, `language`, `source_format`, `lines_of_code`, `complexity_score`, `last_indexed_at`, `hash`

### Copybook

Propriétés : `id`, `name`, `path`, `hash`, `contains_data_structures`, `last_indexed_at`

### Paragraph

Propriétés : `id`, `program_id`, `name`, `start_line`, `end_line`, `summary`

### Section

Propriétés : `id`, `program_id`, `name`, `start_line`, `end_line`

### JCLJob

Propriétés : `id`, `name`, `path`, `schedule`, `description`

### JCLStep

Propriétés : `id`, `job_id`, `name`, `program_name`, `step_order`

### DB2Table

Propriétés : `id`, `schema`, `name`, `qualified_name`, `business_description`

### DB2Column

Propriétés : `id`, `table_id`, `name`, `datatype`, `nullable`

### File

Propriétés : `id`, `logical_name`, `dataset_pattern`, `record_layout`, `description`

### DDName

Propriétés : `id`, `name`, `job_id`, `step_id`, `dataset`

### CICSTransaction

Propriétés : `id`, `tran_id`, `program_name`, `description`

### BusinessRuleCandidate

Propriétés : `id`, `label`, `description`, `confidence`, `status`, `validated_by`, `validated_at`, `evidence`

Valeurs de `status` : `candidate` | `validated` | `rejected` | `deprecated`

## Relations principales

### Relations code

- `PROGRAM_CONTAINS_SECTION`
- `PROGRAM_CONTAINS_PARAGRAPH`
- `SECTION_CONTAINS_PARAGRAPH`
- `PROGRAM_INCLUDES_COPYBOOK`
- `PROGRAM_CALLS_PROGRAM`
- `PROGRAM_PERFORMS_PARAGRAPH`
- `PARAGRAPH_PERFORMS_PARAGRAPH`

### Relations données

- `PROGRAM_READS_TABLE` / `PROGRAM_WRITES_TABLE` / `PROGRAM_UPDATES_TABLE` / `PROGRAM_DELETES_FROM_TABLE`
- `PROGRAM_READS_FILE` / `PROGRAM_WRITES_FILE`
- `COPYBOOK_DEFINES_RECORD`
- `TABLE_HAS_COLUMN`

### Relations batch

- `JOB_HAS_STEP` / `STEP_EXECUTES_PROGRAM` / `STEP_USES_DDNAME` / `DDNAME_REFERENCES_FILE` / `JOB_CALLS_PROC`

### Relations CICS

- `TRANSACTION_STARTS_PROGRAM` / `PROGRAM_USES_CICS_COMMAND` / `PROGRAM_LINKS_PROGRAM` / `PROGRAM_XCTLS_PROGRAM`

### Relations IA et documentation

- `PROGRAM_IMPLEMENTS_RULE` / `PARAGRAPH_SUPPORTS_RULE` / `RULE_EVIDENCED_BY_CODE`
- `PROGRAM_HAS_SUMMARY` / `APPLICATION_HAS_DOCUMENTATION`

## Niveaux de confiance

Chaque relation porte un attribut `confidence` :

- `1.0` — relation déterministe extraite par parsing
- `0.8` — relation déduite par convention de nommage ou résolution partielle
- `0.5` — relation proposée par IA → [[IA-RAG-Agents]]
- `0.2` — relation incertaine nécessitant validation

## Exemple de requêtes métier

- **Impact d'un copybook** — tous les programmes incluant ce copybook, directement ou indirectement.
- **Impact d'une table DB2** — programmes lecteurs/modificateurs, puis jobs associés.
- **Chaîne batch** — étapes, programmes, fichiers lus et produits depuis un job.
- **Programme critique** — fort nombre d'appelants, de tables modifiées ou complexité élevée.