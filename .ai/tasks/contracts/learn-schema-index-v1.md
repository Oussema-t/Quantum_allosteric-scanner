# Learn Schema Index v1

## Purpose

Define the minimum canonical schema and index keys for /learn.

## Record Shape

Each learned record uses the following fields:

- `record_id`: stable unique ID for the learned record
- `family`: test family key (example: `006`)
- `case_id`: optional case key
- `fact_type`: type of fact (mapping, naming-convention, constraint, policy)
- `fact_value`: normalized payload for retrieval
- `source_refs`: list of provenance references (task path, file path, csv excerpt id)
- `lookup_path`: authoritative retrieval path for output metadata (`schema-index`)
- `confidence`: `high|medium|low`
- `status`: `active|stale|unknown`
- `updated_at`: ISO-8601 UTC timestamp
- `updated_by`: actor identifier (agent or HITL)

## Required Index Keys

Primary index:

- `family`
- `case_id`
- `fact_type`

Secondary index:

- `status`
- `confidence`
- `updated_at`

## Retrieval Rules

- Retrieval mode reads canonical records through schema-index keys.
- Output ordering for identical queries is deterministic:
  1. `family`
  2. `case_id`
  3. `fact_type`
  4. `record_id`
- Output must include `lookup_path=schema-index` metadata.
- Source grep may be used for bootstrap or reconciliation, but not as authoritative learned-fact retrieval.
