# Sprint 1 Remediation Plan

## Purpose

This plan remediates only the **CRITICAL** and **HIGH** findings from the Sprint 1 Databricks notebook code review.

The plan:

- Preserves the approved Version 2.1 architecture.
- Preserves the approved data model and PostgreSQL schema.
- Keeps Sprint 1 limited to Bronze ingestion and operational metadata.
- Does not address MEDIUM or LOW findings.
- Uses the existing notebook and Asset Bundle structure.

## Production-readiness target

Sprint 1 remediation is complete when every Bronze row and quarantine row can be traced to one source snapshot and ingestion attempt, retries are idempotent, source contracts are explicit and versioned, finalization counts are run-scoped, and the validation job proves these properties on Databricks.

## Priority definitions

| Priority | Meaning |
|---|---|
| P0 | Must be fixed before production; correctness, lineage, or retry safety is compromised |
| P1 | Should be fixed before production; operational reliability or contract enforcement is incomplete |
| P2 | Can be deferred; high-severity hardening that is not required for the first controlled production release |

---

# 1. Remediation backlog

| ID | Priority | Finding addressed | Scope | Dependencies |
|---|---:|---|---|---|
| R-001 | P0 | Snapshot registration creates a new UUID on every retry | Make snapshot registration deterministic and Delta-MERGE based | None |
| R-002 | P0 | Snapshot ID is not persisted into Bronze records | Add snapshot and attempt lineage to accepted and quarantined rows | R-001 |
| R-003 | P0 | Finalization counts all historical Bronze rows | Scope counts by current snapshot/attempt and source domain | R-002 |
| R-004 | P0 | Finalization does not update snapshot status | Finalize the registered snapshot with scoped counts and terminal status | R-001, R-003 |
| R-005 | P0 | Quarantine records are not associated with the current attempt | Persist lineage and rejection reason in quarantine | R-002 |
| R-006 | P0 | Finalization is append-only and not retry-safe | MERGE finalization records by ingestion attempt ID | R-003 |
| R-007 | P0 | Missing task-value publication is downgraded to a warning | Fail fast when required snapshot/attempt task values cannot be published or read | R-001, R-004 |
| R-008 | P1 | Source schemas are inferred | Load explicit versioned source schemas and reject unsupported versions | R-009 |
| R-009 | P1 | Schema registry configuration is unused | Implement schema-registry resolution and validation | None |
| R-010 | P1 | Parse and contract failures are not consistently quarantined | Add controlled read, parse, required-field, and type-validation outcomes | R-008, R-009 |
| R-011 | P1 | Duplicate source rows are not deduplicated before MERGE | Deduplicate by the complete Bronze idempotency key | None |
| R-012 | P1 | Delta MERGE metrics report `inserted_count=-1` | Produce reliable candidate, inserted, duplicate, rejected, and quarantined metrics | R-011 |
| R-013 | P1 | Source-specific required fields are not validated | Add contract requirements for all eight ingestion notebooks | R-008, R-010 |
| R-014 | P1 | Incremental mode uses `spark.read` and ignores checkpoint configuration | Implement the approved incremental ingestion path with Auto Loader/checkpoints | R-009 |
| R-015 | P1 | Delivery completeness and expected counts are not validated | Validate delivery metadata and compare expected versus actual scoped counts | R-003, R-004 |
| R-016 | P1 | Default provider metadata can hide missing deployment configuration | Require source system, object, version, and source path in production jobs | None |
| R-017 | P1 | Job parameters do not pass snapshot/lineage context to ingestion/finalization | Wire task values and required parameters through Bundle jobs | R-001, R-002 |
| R-018 | P1 | No production validation job proves replay, duplicate, quarantine, and metadata behavior | Implement the validation notebooks/jobs already specified by the guide | R-001 through R-017 |
| R-019 | P2 | Source-specific field mappings are not explicit by contract version | Move candidate-field resolution into versioned mappings | R-008, R-013 |
| R-020 | P2 | No automated Databricks integration coverage exists | Add deployed-runtime tests for Delta MERGE, Unity Catalog, permissions, and replay | R-018 |

## Priority summary

| Priority | Items |
|---|---:|
| P0 | 7 |
| P1 | 11 |
| P2 | 2 |

---

# 2. Required code changes

## Phase 1 — Establish lineage and retry identity (P0)

### 2.1 Shared Bronze metadata

Update [01_ingestion_helpers.py](C:/Users/ASUS/OFF-Ball/databricks/notebooks/common/01_ingestion_helpers.py) to:

- Carry `source_snapshot_id` and `ingestion_attempt_id`.
- Require those values for production ingestion.
- Add both values to accepted Bronze rows.
- Add both values to quarantine rows.
- Preserve the existing approved common metadata fields.
- Include lineage fields in the idempotency and finalization path.

No new business entity or analytical table is introduced. These are operational ingestion metadata fields required to make the approved snapshot workflow correct.

### 2.2 Deterministic snapshot registration

Update [90_register_source_snapshot.py](C:/Users/ASUS/OFF-Ball/databricks/notebooks/orchestration/90_register_source_snapshot.py) to:

- Derive a deterministic delivery key from source system, source object, source version, delivery URI/reference, and run mode.
- Use Delta MERGE rather than unconditional append.
- Reuse the existing snapshot ID for retries of the same delivery.
- Generate a new attempt ID only for a new ingestion attempt or explicit replay.
- Fail if required task-value publication fails.
- Store the actual source delivery reference rather than the generic Bronze root when available.

### 2.3 Run-scoped finalization

Update [91_finalize_ingestion_attempt.py](C:/Users/ASUS/OFF-Ball/databricks/notebooks/orchestration/91_finalize_ingestion_attempt.py) to:

- Read the registered snapshot ID from the upstream task value or a required parameter.
- Require the snapshot ID before counting records.
- Filter all Bronze and quarantine counts by snapshot/attempt lineage.
- Restrict finalization to the relevant source domain and tables for the job.
- Calculate accepted, rejected, quarantined, duplicate, and actual counts from scoped operational data.
- MERGE finalization by ingestion attempt ID.
- Update the corresponding snapshot status to `completed`, `completed_with_quarantine`, or `failed`.
- Fail when required tables or metadata are missing rather than silently treating them as zero.

### 2.4 Error propagation

Update [00_runtime_config.py](C:/Users/ASUS/OFF-Ball/databricks/notebooks/common/00_runtime_config.py), [01_ingestion_helpers.py](C:/Users/ASUS/OFF-Ball/databricks/notebooks/common/01_ingestion_helpers.py), and both orchestration notebooks to:

- Replace broad exception handling around required runtime behavior with narrow expected-error handling.
- Fail fast when required widgets, task values, source metadata, or lineage values are unavailable.
- Retain warnings only for genuinely optional observability behavior.

## Phase 2 — Enforce source contracts (P1)

### 2.5 Schema registry

Update [01_ingestion_helpers.py](C:/Users/ASUS/OFF-Ball/databricks/notebooks/common/01_ingestion_helpers.py) to:

- Resolve the source schema using `schema_registry_root_uri`, source object name, and source version.
- Read explicit schemas instead of relying on CSV/JSON inference.
- Reject unsupported or missing schema versions.
- Validate required columns before enrichment.
- Preserve rescued or unexpected fields according to the existing Bronze contract without silently changing the table schema.

### 2.6 Controlled parse and quarantine behavior

Update [01_ingestion_helpers.py](C:/Users/ASUS/OFF-Ball/databricks/notebooks/common/01_ingestion_helpers.py) to:

- Distinguish source-read failure, parse failure, contract failure, and row-level validation failure.
- Write row-level failures to quarantine with a reason code and lineage.
- Fail the notebook for delivery-level failures that prevent trustworthy parsing.
- Return accurate rejected and quarantined counts.

### 2.7 Required-field validation

Add source contract definitions or a shared validation configuration for:

- `athlete_profile_raw`
- `roster_raw`
- `performance_stat_raw`
- `fixture_raw`
- `participant_raw`
- `match_result_raw`
- `event_incident_raw`
- `scoring_event_raw`

Update the eight ingestion notebooks to pass the source-specific contract identifier and required field rules to the shared helper. Validation must include stable provider identity and the required fixture/athlete context applicable to each source.

## Phase 3 — Make Delta ingestion deterministic (P1)

### 2.8 Batch deduplication

Update [01_ingestion_helpers.py](C:/Users/ASUS/OFF-Ball/databricks/notebooks/common/01_ingestion_helpers.py) to:

- Validate every configured merge-key column exists.
- Deduplicate incoming rows by the complete merge key before MERGE.
- Detect duplicate source keys within the batch.
- Classify duplicate rows separately from accepted rows.
- Preserve immutable payload history when the payload hash changes.

### 2.9 Delta metrics

Replace the current unknown `inserted_count=-1` behavior with deterministic metrics. The result contract must report:

- Input candidate count.
- In-batch duplicate count.
- Existing duplicate count.
- Inserted count.
- Rejected count.
- Quarantined count.

Metrics must be scoped to the current snapshot and attempt.

### 2.10 Incremental ingestion

Update [read_source](C:/Users/ASUS/OFF-Ball/databricks/notebooks/common/01_ingestion_helpers.py) and the ingestion orchestration to honor `run_mode`:

- `batch`: deterministic bounded batch read.
- `incremental`: Auto Loader/checkpoint-based file discovery.
- `replay`: explicit snapshot/attempt replay without overwriting prior Bronze records.

Use the configured `checkpoint_root_uri`. Do not introduce a new architecture or change the approved Bronze table targets.

## Phase 4 — Harden production configuration and validation (P1/P2)

Update [databricks.yml](C:/Users/ASUS/OFF-Ball/databricks/databricks.yml) and [jobs.yml](C:/Users/ASUS/OFF-Ball/databricks/resources/jobs.yml) to:

- Require source metadata in production rather than relying on `configured-provider`, generic object names, or default version values.
- Pass delivery URI/reference, snapshot ID, source domain, run mode, and attempt context consistently.
- Configure checkpoint and schema-registry paths for the relevant ingestion jobs.
- Ensure finalization depends on all source tasks and receives the registered snapshot context.
- Add the Bronze validation job as a required downstream gate.

P2 integration-test work may be deferred only after the P1 validation job exists and passes in a deployed test workspace.

---

# 3. Notebook changes

| Notebook | Required changes | Priority |
|---|---|---:|
| [00_runtime_config.py](C:/Users/ASUS/OFF-Ball/databricks/notebooks/common/00_runtime_config.py) | Narrow exception handling; require production metadata; expose run/snapshot/attempt context; validate checkpoint and schema registry configuration | P0/P1 |
| [01_ingestion_helpers.py](C:/Users/ASUS/OFF-Ball/databricks/notebooks/common/01_ingestion_helpers.py) | Add lineage columns; explicit schema loading; contract validation; controlled quarantine; deduplication; accurate Delta metrics; run-mode handling | P0/P1 |
| [90_register_source_snapshot.py](C:/Users/ASUS/OFF-Ball/databricks/notebooks/orchestration/90_register_source_snapshot.py) | Deterministic delivery identity; Delta MERGE; retry-safe task value publication; actual delivery URI; new-attempt/replay semantics | P0 |
| [91_finalize_ingestion_attempt.py](C:/Users/ASUS/OFF-Ball/databricks/notebooks/orchestration/91_finalize_ingestion_attempt.py) | Snapshot-scoped counts; domain-scoped counts; quarantine/rejection/duplicate metrics; snapshot status update; retry-safe MERGE | P0 |
| [10_ingest_athlete_profile.py](C:/Users/ASUS/OFF-Ball/databricks/notebooks/bronze/10_ingest_athlete_profile.py) | Pass explicit contract and lineage context; enforce athlete identity requirements; remove infer-schema defaults | P1 |
| [11_ingest_roster.py](C:/Users/ASUS/OFF-Ball/databricks/notebooks/bronze/11_ingest_roster.py) | Pass explicit contract and lineage context; validate roster and season identity; remove infer-schema defaults | P1 |
| [12_ingest_performance_stat.py](C:/Users/ASUS/OFF-Ball/databricks/notebooks/bronze/12_ingest_performance_stat.py) | Validate statistic, athlete, and fixture context; pass explicit contract and lineage context | P1 |
| [20_ingest_fixture.py](C:/Users/ASUS/OFF-Ball/databricks/notebooks/bronze/20_ingest_fixture.py) | Validate fixture identity/date; pass explicit contract and lineage context | P1 |
| [22_ingest_participant.py](C:/Users/ASUS/OFF-Ball/databricks/notebooks/bronze/22_ingest_participant.py) | Validate fixture and participant identity; pass explicit contract and lineage context | P1 |
| [23_ingest_match_result.py](C:/Users/ASUS/OFF-Ball/databricks/notebooks/bronze/23_ingest_match_result.py) | Validate fixture, score, and result status; pass explicit contract and lineage context | P1 |
| [24_ingest_scoring_event.py](C:/Users/ASUS/OFF-Ball/databricks/notebooks/bronze/24_ingest_scoring_event.py) | Validate scoring event and fixture/participant identity; pass explicit contract and lineage context | P1 |
| [25_ingest_event_incident.py](C:/Users/ASUS/OFF-Ball/databricks/notebooks/bronze/25_ingest_event_incident.py) | Validate incident identity, fixture, type, and timestamp; pass explicit contract and lineage context | P1 |
| `95_validate_bronze_contracts.py` | Add table existence, required-column, metadata, contract, lineage, quarantine, and count checks | P1 |
| `96_validate_bronze_replay.py` | Verify replay produces the same accepted payload-hash set without overwriting original rows | P1 |

The last two validation notebooks are required by the approved Sprint 1 guide and are implementation-quality validation only; they do not add Silver/Gold processing.

---

# 4. Bundle changes

File: [jobs.yml](C:/Users/ASUS/OFF-Ball/databricks/resources/jobs.yml)

Required changes:

1. Pass `source_delivery_uri` or an equivalent delivery reference to snapshot registration.
2. Pass `checkpoint_root_uri` and `schema_registry_root_uri` to ingestion tasks.
3. Ensure registration publishes the snapshot ID as a required upstream task value.
4. Ensure every ingestion task receives the snapshot context.
5. Ensure finalization receives the snapshot ID, source domain, and ingestion attempt context.
6. Set production source metadata as required inputs instead of allowing placeholder defaults.
7. Add `95_validate_bronze_contracts` and `96_validate_bronze_replay` to `offball_s1_validate_bronze`.
8. Make validation depend on successful finalization.
9. Configure retries so deterministic snapshot/attempt keys prevent duplicate writes.
10. Preserve the current job boundaries and Bronze-only outputs.

File: [databricks.yml](C:/Users/ASUS/OFF-Ball/databricks/databricks.yml)

Required changes:

1. Retain the existing checkpoint and schema-registry variables.
2. Add explicit delivery-reference variables only if they are not supplied through job parameters.
3. Remove or override the generic `configured-provider` default for the production target.
4. Keep catalog, schema, root URI, runtime, cluster, and target structure unchanged.

File: [bronze_tables.yml](C:/Users/ASUS/OFF-Ball/databricks/resources/bronze_tables.yml)

Required changes:

- Ensure the bootstrap job creates the operational metadata tables used by snapshot registration and finalization, or ensure those notebooks create them with the same controlled schema.
- Do not add new business tables or alter the approved 15 Bronze source-table list.

---

# 5. Validation tests

## Unit and static tests

| Test | Expected result | Priority |
|---|---|---:|
| Missing required source metadata | Notebook fails with a specific validation error | P0 |
| Missing snapshot task value | Ingestion/finalization fails rather than continuing unscoped | P0 |
| Repeated snapshot registration for the same delivery | Same snapshot ID is reused | P0 |
| Snapshot registration for a new replay attempt | New attempt is created without overwriting original Bronze rows | P0 |
| Bronze row lineage | Every accepted row contains the current snapshot and attempt identifiers | P0 |
| Quarantine row lineage | Every quarantine row contains the current snapshot and attempt identifiers | P0 |
| Finalization scope | Counts include only the current snapshot/attempt and source domain | P0 |
| Finalization retry | Existing attempt record is updated, not duplicated | P0 |
| Snapshot status transition | Registration and finalization produce the correct terminal status | P0 |
| Required merge key missing | Helper fails before Delta MERGE | P1 |
| Duplicate rows within input batch | Only one row per complete idempotency key is inserted; duplicate count is reported | P1 |
| Existing payload replay | No new Bronze row is inserted | P1 |
| Changed payload with same source reference | New immutable payload version is retained according to current Bronze semantics | P1 |
| Unsupported source version | Delivery fails before table write | P1 |
| Missing required source field | Record is quarantined with a reason code | P1 |
| Malformed source record | Row is quarantined or delivery fails according to failure class; no silent drop | P1 |
| Explicit schema loading | CSV/JSON ingestion does not infer production schema | P1 |
| Batch mode | Bounded source read succeeds without checkpoint state | P1 |
| Incremental mode | Auto Loader/checkpoint state prevents reprocessing of already discovered files | P1 |
| Replay mode | Replay produces identical accepted payload-hash set without overwriting original rows | P1 |
| Expected record count mismatch | Finalization reports failure or completed-with-quarantine according to the approved contract | P1 |
| Production placeholder metadata | Production job rejects placeholder source system/object/version values | P1 |

## Deployed Databricks validation

Run in the test target after Bundle deployment:

1. Register a fixture delivery.
2. Run the event Bronze job.
3. Retry the same job.
4. Confirm no duplicate accepted rows.
5. Inspect snapshot, ingestion-attempt, Bronze, and quarantine metadata.
6. Inject malformed and contract-invalid records.
7. Confirm quarantine counts are scoped to the run.
8. Run finalization twice and confirm one logical attempt record.
9. Replay the snapshot.
10. Confirm the accepted payload-hash set is unchanged and original rows remain intact.
11. Run the Bronze contract and replay validation jobs.
12. Confirm the validation job blocks sign-off on any lineage, count, schema, or idempotency failure.

---

# 6. Acceptance criteria

## P0 acceptance criteria

1. A source delivery retry reuses the original logical snapshot ID.
2. Every accepted Bronze row contains the snapshot and ingestion-attempt identifiers.
3. Every quarantined row contains the snapshot and ingestion-attempt identifiers.
4. Finalization counts only rows belonging to the current snapshot/attempt and source domain.
5. Snapshot status is updated to `completed`, `completed_with_quarantine`, or `failed`.
6. Finalization retries update the existing attempt record rather than append duplicate summaries.
7. Missing required task values or required metadata fail the job explicitly.
8. No successful finalization is possible when lineage is absent or unscoped.

## P1 acceptance criteria

9. Production ingestion uses explicit source schemas selected by source version.
10. Unsupported schema versions fail before Bronze writes.
11. Invalid source rows are quarantined with a reason and correct lineage.
12. Delivery-level parse or contract failures fail the job and are visible in the final status.
13. Incoming duplicates are removed before MERGE and reported separately.
14. Delta ingestion reports deterministic candidate, inserted, duplicate, rejected, and quarantined counts.
15. Required source identity and football context fields are validated for all eight ingestion notebooks.
16. Batch, incremental, and replay modes execute their approved behavior.
17. Incremental ingestion uses the configured checkpoint root.
18. Expected record counts are compared with scoped actual counts when supplied.
19. Production jobs reject placeholder provider metadata.
20. The validation job runs after finalization and blocks Sprint 1 sign-off on failure.

## P2 acceptance criteria

21. Version-specific source field mappings are externalized and tested.
22. Deployed Databricks integration tests cover Delta concurrency, Unity Catalog permissions, and source replay.

---

# 7. Implementation order

1. Implement R-001 deterministic snapshot registration.
2. Implement R-002 and R-005 lineage propagation to Bronze and quarantine.
3. Implement R-003 scoped finalization counts.
4. Implement R-004 and R-006 snapshot/attempt terminal updates.
5. Implement R-007 fail-fast task-value and runtime handling.
6. Implement R-009 schema-registry resolution.
7. Implement R-008 explicit schema loading.
8. Implement R-010 and R-013 validation/quarantine behavior.
9. Implement R-011 duplicate detection and R-012 Delta metrics.
10. Implement R-014 batch/incremental/replay behavior.
11. Implement R-015 delivery completeness and expected-count checks.
12. Implement R-016 and R-017 production Bundle parameter enforcement.
13. Implement R-018 Bronze contract and replay validation jobs.
14. Implement R-019 versioned field mappings if retained in Sprint 1.
15. Implement R-020 deployed integration tests before production approval.

## Out of scope

- Silver or Gold transformations.
- Football truth, space creation, pressing, or feature-engineering redesign.
- PostgreSQL schema changes.
- New business entities or analytical tables.
- Medium-severity performance, security, or style findings.
- Low-severity cleanup and refactoring.

## Final readiness gate

Sprint 1 remediation may be marked ready for production only when all P0 and P1 acceptance criteria pass in the deployed test target. P2 items must either pass or have an explicit production-release waiver.
