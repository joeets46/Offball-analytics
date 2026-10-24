# Sprint 2 Silver Layer Implementation Plan

**Sprint:** 2 - Silver conformance and analytical facts  
**Status:** Approved implementation plan  
**Precondition:** Sprint 1 Bronze ingestion is functionally complete  
**Scope:** Silver Delta tables, Bronze-to-Silver transformations, conformed dimensions, data quality, business rules, jobs, notebooks, and delivery evidence  
**Out of scope:** Architecture redesign, PostgreSQL schema redesign, Bronze contract changes, Gold products, dashboards, model training, and new business domains

## 1. Sprint objective

Build the governed Silver layer that converts immutable Sprint 1 Bronze data into typed, deduplicated, lineage-preserving, repository-aligned Delta tables and approved analytical facts.

Silver must:

- Preserve source lineage to snapshot and ingestion attempt.
- Select one conformed record from duplicate or corrected Bronze versions without deleting Bronze history.
- Resolve cross-domain keys before publishing dependent facts.
- Normalize timestamps to UTC while retaining source-time context where available.
- Make unresolved identity, provider conflicts, and analytical uncertainty visible.
- Prevent quarantined or invalid Bronze records from reaching Silver.
- Write only the approved `silver` schema and Silver operational metadata.

## 2. Frozen constraints

1. Use the existing Bronze tables as the only Sprint 2 source layer.
2. Preserve the approved repository-first table names and grains.
3. Do not introduce `canonical_*` mirrors, club SaaS entities, or unsupported recruitment entities.
4. Do not modify the PostgreSQL schema.
5. Do not write Gold tables.
6. Do not overwrite Bronze records.
7. All Silver rows must carry source lineage and transformation-run metadata.
8. Late or corrected records create a newer Silver conformed version selected by deterministic precedence.
9. Unresolved records remain observable in Silver quarantine/reconciliation outputs.

## 3. Requirement register

| ID | Requirement |
|---|---|
| REQ-001 | Create the approved Silver domain schemas and table locations. |
| REQ-002 | Materialize typed, conformed athlete and event dimensions/facts at approved grains. |
| REQ-003 | Materialize approved football-truth analytical facts: periods, state intervals, possessions, and phases. |
| REQ-004 | Materialize approved opportunity, space, pressing, attribution, and recovery Silver facts. |
| REQ-005 | Apply deterministic source precedence, deduplication, and correction handling. |
| REQ-006 | Resolve athlete, fixture, team/participant, and event references before dependent writes. |
| REQ-007 | Normalize timestamps and preserve source temporal evidence. |
| REQ-008 | Normalize tracking coordinates to the approved pitch convention without mutating Bronze payloads. |
| REQ-009 | Apply source-specific and business-rule data-quality checks. |
| REQ-010 | Quarantine or reconcile invalid, unresolved, and conflicting records with explicit reasons. |
| REQ-011 | Preserve source snapshot, ingestion attempt, calculation run, and transformation lineage. |
| REQ-012 | Support idempotent batch and incremental Silver processing. |
| REQ-013 | Build dependency-ordered Silver jobs with retry-safe task boundaries. |
| REQ-014 | Publish operational metrics for input, output, rejected, unresolved, duplicate, and conflict counts. |
| REQ-015 | Prevent quarantined or failed Bronze records from entering conformed Silver tables. |
| REQ-016 | Validate Silver schemas, keys, referential integrity, temporal validity, and confidence ranges. |
| REQ-017 | Produce reproducible Sprint 2 execution evidence and acceptance results. |

## 4. Approved Silver table inventory

### 4.1 Repository-aligned conformed tables

| Table | Grain | Bronze inputs | Key business rules |
|---|---|---|---|
| `silver.athlete.athlete_profile` | One athlete | `athlete_profile_raw` | Stable provider identity; latest valid record by source precedence and version. |
| `silver.athlete.roster` | Athlete-team-season affiliation | `roster_raw` | Effective dates; no overlapping active intervals for the same affiliation key. |
| `silver.athlete.performance_stat` | Athlete performance fact | `performance_stat_raw` | Typed value/unit; preserve statistic identity and fixture link. |
| `silver.athlete.contract` | One contract record | `contract_raw` | Preserve source grain; validate effective date ordering. |
| `silver.athlete.eligibility_status` | One eligibility record | `eligibility_status_raw` | Effective/expiry semantics; retain status history. |
| `silver.event.fixture` | One scheduled fixture | `fixture_raw` | Stable fixture identity; UTC timestamps; lifecycle normalization. |
| `silver.event.calendar` | One calendar | `fixture_raw`, `competition_raw` | Conform season/calendar references. |
| `silver.event.tournament` | One tournament | `competition_raw` | Controlled tournament identity and source precedence. |
| `silver.event.competition_round` | One competition round | `competition_raw` | Conform stage/round references. |
| `silver.event.type` | One event type | `competition_raw`, `event_incident_raw` | Controlled event taxonomy with unknown handling. |
| `silver.event.participant` | One fixture participant | `participant_raw` | Resolve athlete/fixture references and participation intervals. |
| `silver.event.match_result` | One fixture result | `match_result_raw` | Reconcile providers; one selected result version. |
| `silver.event.scoring_event` | One scoring event | `scoring_event_raw` | Normalize event time and participant references. |
| `silver.event.event_incident` | One match incident | `event_incident_raw` | Normalize type/time and reconcile provider conflicts. |

### 4.2 Approved analytical Silver tables

| Table | Grain | Main inputs |
|---|---|---|
| `silver.analytics.match_period` | One fixture period | Fixture, tracking/event clocks |
| `silver.analytics.match_state_interval` | One continuous score/game-state interval | Match result, scoring events |
| `silver.analytics.possession_sequence` | One canonical possession | Incidents, scoring events, tracking |
| `silver.analytics.phase_interval` | One phase interval within a possession | Possession sequence, event context |
| `silver.analytics.opportunity` | One eligible analytical situation | Fixture, participant, phase, tracking |
| `silver.analytics.space_opportunity` | One space-creation opportunity | Opportunity, participant, tracking |
| `silver.analytics.space_baseline` | One baseline for a space opportunity | Tracking geometry |
| `silver.analytics.space_counterfactual` | One counterfactual evaluation | Baseline and feature inputs |
| `silver.analytics.space_outcome` | One space outcome | Event, tracking, receiving context |
| `silver.analytics.attribution_ledger` | One participant attribution entry | Space/press outcomes |
| `silver.analytics.pressing_opportunity` | One pressing opportunity | Opportunity, event, tracking |
| `silver.analytics.press_trigger` | One press trigger | Pressing opportunity, event time |
| `silver.analytics.press_action` | One press action | Tracking, participant |
| `silver.analytics.press_support` | One support action | Pressing opportunity, participant |
| `silver.analytics.press_bypass` | One bypass event | Pressing opportunity, possession transition |
| `silver.analytics.press_outcome` | One pressing outcome | Press actions, possession transition |
| `silver.analytics.recovery_action` | One recovery action | Pressing opportunity, participant |

## 5. Silver common contract

Every Silver table must include, where applicable:

```text
<business primary key>
source_system_code
source_record_reference
source_version
source_snapshot_id
ingestion_attempt_id
bronze_payload_hash
silver_record_version
effective_from
effective_to
is_current
quality_status
quality_reason
transformation_run_id
transformed_at
```

Analytical tables additionally include:

```text
confidence
evidence_status
unresolved_reason
calculation_run_id
```

The implementation may use table-specific nullable columns where the approved grain does not support a field. It must not remove the source lineage contract.

## 6. Transformation and business rules

### 6.1 General conformance rules

1. Read only `ingestion_status = 'accepted'` Bronze rows.
2. Exclude Bronze rows with missing mandatory lineage or payload hash to Silver quarantine.
3. Parse typed columns using explicit casts and named parse-failure reasons.
4. Normalize strings using trim and controlled casing only where the source contract permits it.
5. Normalize timestamps to UTC; preserve source timezone or original timestamp in audit columns when supplied.
6. Select the current record using:
   1. valid source identity,
   2. highest source version,
   3. latest source event timestamp,
   4. latest ingestion timestamp,
   5. deterministic payload-hash tie-breaker.
7. Retain superseded records in Silver history where the table supports versioning.
8. Use Delta `MERGE` with deterministic business keys and source lineage.
9. Never use a non-deterministic `dropDuplicates` without an ordering window.

### 6.2 Conformed dimension rules

- `athlete_profile`: provider identity must resolve to one athlete key; conflicting identity values create a reconciliation record.
- `roster`: athlete identity must resolve; activation cannot be after deactivation; overlapping current affiliations are flagged.
- `fixture`: fixture identity is the event anchor; start/end timestamps must be ordered; event date must be consistent with normalized start time.
- `participant`: fixture must resolve; athlete reference is required for player participation; participation status and lineup position are controlled values.
- `match_result`: fixture must resolve; scores must be non-negative; competing provider records are retained as conflict evidence and selected by precedence.
- `scoring_event` and `event_incident`: fixture must resolve; timestamps must fall within an allowed fixture tolerance window when match timing exists.
- `performance_stat`: athlete must resolve; statistic value must be numeric when required by statistic type; unit must be controlled.

### 6.3 Football truth rules

- Periods are ordered, non-overlapping intervals anchored to a fixture.
- State intervals are derived from initial score and scoring events; score changes occur at normalized scoring timestamps.
- Possession sequences may be `confirmed`, `inferred`, or `unresolved`; unresolved sequences remain visible with a reason.
- Phase intervals must be contained within their possession sequence.
- Confidence is bounded from `0` to `1`.
- Gaps or overlaps in event/tracking time are recorded as quality findings rather than silently filled.

### 6.4 Space and pressing rules

- An opportunity is eligible only when required fixture, participant, phase, and temporal evidence exists.
- `eligible_flag` and `observed_flag` are independent.
- Space baselines and counterfactuals must reference a reproducible transformation/calculation run.
- Press actions, support, bypass, outcomes, and recovery actions must reference a pressing opportunity.
- Attribution shares must be between `0` and `1`; sum checks are emitted where the business rule requires complete attribution.
- Missing tracking coverage lowers quality/confidence and cannot be represented as a confirmed observation.

## 7. Data-quality framework

### 7.1 Rule categories

| Category | Examples | Action |
|---|---|---|
| Schema | Required column, type, contract version | Fail task or quarantine row |
| Identity | Missing/duplicate provider key, unresolved FK | Quarantine or reconciliation output |
| Temporal | Invalid ordering, overlap, impossible timestamp | Quarantine or quality flag |
| Referential | Fixture, athlete, participant, phase lookup failure | Quarantine dependent row |
| Domain | Invalid status, score, unit, event type | Quarantine or controlled unknown |
| Geometry | Invalid coordinates, wrong pitch bounds, tracking gap | Quarantine frame/flag downstream fact |
| Reconciliation | Provider conflict or competing version | Select deterministic winner; retain conflict |
| Completeness | Missing expected source objects or coverage | Mark run quality status and alert |

### 7.2 Required quality outputs

Create:

- `silver._quality_record`
- `silver._quality_run`
- `silver._reconciliation_conflict`
- `silver._unresolved_reference`
- `silver._transformation_run`

These are operational Silver tables, not new business entities. Each output must include rule code, table, source lineage, severity, reason, detected timestamp, and resolution status.

### 7.3 Quality statuses

```text
valid
valid_with_warning
quarantined
unresolved
conflict_selected
superseded
```

No `quarantined` row may be published into a conformed business table.

## 8. Notebook implementation

Create the following notebooks under `databricks/notebooks/silver/`.

### 8.1 Shared notebooks

| Notebook | Responsibility |
|---|---|
| `00_silver_runtime_config.py` | Silver catalog/schema, run mode, input snapshot, transformation-run parameters |
| `01_silver_helpers.py` | Typed parsing, deterministic version selection, Delta merge, lineage, metrics |
| `02_quality_helpers.py` | Rule execution, quality outputs, quarantine and reconciliation writes |
| `03_reference_helpers.py` | Dimension lookup, unresolved-reference handling, controlled value mappings |
| `04_temporal_helpers.py` | UTC normalization, interval validation, overlap/gap detection |

### 8.2 Conformed source notebooks

| Notebook | Target |
|---|---|
| `10_conform_athlete_profile.py` | `silver.athlete.athlete_profile` |
| `11_conform_roster.py` | `silver.athlete.roster` |
| `12_conform_performance_stat.py` | `silver.athlete.performance_stat` |
| `13_conform_contract.py` | `silver.athlete.contract` |
| `14_conform_eligibility_status.py` | `silver.athlete.eligibility_status` |
| `20_conform_fixture.py` | `silver.event.fixture` |
| `21_conform_calendar_competition.py` | Calendar, tournament, round, and type tables |
| `22_conform_participant.py` | `silver.event.participant` |
| `23_conform_match_result.py` | `silver.event.match_result` |
| `24_conform_scoring_event.py` | `silver.event.scoring_event` |
| `25_conform_event_incident.py` | `silver.event.event_incident` |

### 8.3 Analytical fact notebooks

| Notebook | Targets |
|---|---|
| `30_build_match_period.py` | Match periods |
| `31_build_match_state_interval.py` | Match state intervals |
| `32_build_possession_sequence.py` | Possession sequences |
| `33_build_phase_interval.py` | Phase intervals |
| `34_build_opportunity.py` | Opportunity denominator |
| `35_build_space_facts.py` | Space opportunity, baseline, counterfactual, outcome |
| `36_build_pressing_facts.py` | Press opportunity, trigger, action, support, bypass, outcome, recovery |
| `37_build_attribution_ledger.py` | Attribution entries and validation |

### 8.4 Validation notebook

| Notebook | Responsibility |
|---|---|
| `95_validate_silver_contracts.py` | Schema, row-count, lineage, key, referential, temporal, quality, and no-Gold-write checks |

## 9. Silver jobs

Create `databricks/resources/silver_jobs.yml`.

### Job 1: `offball_s2_silver_conformed_dimensions`

Order:

```text
create_silver_operational_tables
  -> conform_athlete_profile
  -> conform_roster
  -> conform_contract
  -> conform_eligibility_status
  -> conform_fixture
  -> conform_calendar_competition
  -> conform_participant
  -> conform_match_result
  -> conform_scoring_event
  -> conform_event_incident
  -> conform_performance_stat
  -> validate_silver_dimensions
```

### Job 2: `offball_s2_silver_football_truth`

Depends on the conformed-dimensions job:

```text
build_match_period
  -> build_match_state_interval
  -> build_possession_sequence
  -> build_phase_interval
  -> validate_silver_truth
```

### Job 3: `offball_s2_silver_space_pressing`

Depends on football-truth completion:

```text
build_opportunity
  -> build_space_facts
  -> build_pressing_facts
  -> build_attribution_ledger
  -> validate_silver_analytics
```

### Job 4: `offball_s2_validate_silver`

Runs all Silver validation suites and publishes the Sprint 2 execution report. It must fail the job when critical schema, lineage, referential, or data-quality gates fail.

All jobs must:

- Use the existing Bundle target variables and Unity Catalog.
- Be retry-safe and idempotent.
- Pass `source_snapshot_id`, `ingestion_attempt_id`, and `transformation_run_id`.
- Publish task-level input/output/duplicate/quarantine/conflict/unresolved metrics.
- Never write Bronze, Gold, or PostgreSQL.

## 10. Implementation phases and task breakdown

### Phase 1 - Setup

- [ ] T001 [Plan:1.1] Add Silver schemas, operational table contracts, and deployment variables in `databricks/resources/silver_tables.yml`.
- [ ] T002 [P] [Plan:1.1] Add Silver job definitions and task dependencies in `databricks/resources/silver_jobs.yml`.
- [ ] T003 [P] [Plan:1.1] Add Silver notebook folder structure under `databricks/notebooks/silver/`.
- [ ] T004 [Plan:1.1] Add `databricks/configuration/silver_test.yml` with test-target paths, quality thresholds, and run parameters.

### Phase 2 - Foundational Silver framework

- [ ] T005 [Plan:2.1,2.2] Implement `databricks/notebooks/silver/00_silver_runtime_config.py`.
- [ ] T006 [P] [Plan:2.1,2.2] Implement `databricks/notebooks/silver/01_silver_helpers.py` with deterministic selection, typed projection, Delta MERGE, and task metrics.
- [ ] T007 [P] [Plan:2.2] Implement `databricks/notebooks/silver/02_quality_helpers.py` and operational quality tables.
- [ ] T008 [P] [Plan:2.2] Implement `databricks/notebooks/silver/03_reference_helpers.py` for conformed-key lookup and unresolved references.
- [ ] T009 [P] [Plan:2.2] Implement `databricks/notebooks/silver/04_temporal_helpers.py` for UTC and interval rules.
- [ ] T010 [Plan:2.1,2.2] Implement transformation-run registration and finalization with deterministic retry behavior.

### Phase 3 - Conformed athlete and event products

- [ ] T011 [P] [Plan:3.1,3.2] Implement athlete conformance notebooks `10_conform_athlete_profile.py`, `11_conform_roster.py`, `12_conform_performance_stat.py`, `13_conform_contract.py`, and `14_conform_eligibility_status.py`.
- [ ] T012 [P] [Plan:3.1,3.2] Implement event conformance notebooks `20_conform_fixture.py` and `21_conform_calendar_competition.py`.
- [ ] T013 [P] [Plan:3.1,3.2] Implement `22_conform_participant.py` with fixture and athlete reference resolution.
- [ ] T014 [P] [Plan:3.1,3.2] Implement `23_conform_match_result.py`, `24_conform_scoring_event.py`, and `25_conform_event_incident.py`.
- [ ] T015 [Plan:3.1,3.2] Add deterministic provider precedence and conflict output for competing fixture/result/incident records.
- [ ] T016 [Plan:3.3] Add dimension validation tests for keys, effective dates, types, lineage, and idempotency.

### Phase 4 - Football truth facts

- [ ] T017 [Plan:4.1,4.2] Implement `30_build_match_period.py` from fixture clocks and provider period evidence.
- [ ] T018 [Plan:4.1,4.2] Implement `31_build_match_state_interval.py` from initial state and scoring events.
- [ ] T019 [Plan:4.1,4.2] Implement `32_build_possession_sequence.py` with confirmed, inferred, and unresolved statuses.
- [ ] T020 [Plan:4.1,4.2] Implement `33_build_phase_interval.py` with containment and temporal validation.
- [ ] T021 [Plan:4.3] Add football-truth validation for overlap, gaps, score transitions, confidence, and lineage.

### Phase 5 - Space, pressing, and attribution facts

- [ ] T022 [Plan:5.1,5.2] Implement `34_build_opportunity.py` as the eligible/observed analytical denominator.
- [ ] T023 [P] [Plan:5.1,5.2] Implement `35_build_space_facts.py` for opportunities, baselines, counterfactuals, and outcomes.
- [ ] T024 [P] [Plan:5.1,5.2] Implement `36_build_pressing_facts.py` for opportunities, triggers, actions, support, bypass, outcomes, and recovery.
- [ ] T025 [Plan:5.1,5.2] Implement `37_build_attribution_ledger.py` with share bounds and evidence linkage.
- [ ] T026 [Plan:5.3] Add analytical validation for tracking coverage, coordinate bounds, confidence, evidence, and unresolved states.

### Phase 6 - Jobs, validation, and delivery

- [ ] T027 [Plan:6.1,6.2] Implement `95_validate_silver_contracts.py` with schema, lineage, referential, temporal, quality, and no-Gold-write assertions.
- [ ] T028 [Plan:6.1] Wire all Silver notebooks into dependency-ordered Asset Bundle jobs.
- [ ] T029 [Plan:6.2] Execute batch, incremental, retry, correction, and replay validation against isolated test deliveries.
- [ ] T030 [Plan:6.2,6.3] Produce Silver row-count, quality, reconciliation, lineage, and acceptance evidence.
- [ ] T031 [Plan:6.3] Complete Sprint 2 acceptance sign-off; do not deploy Gold jobs as part of this sprint.

## 11. Sprint deliverables

### Code and configuration

- `databricks/resources/silver_tables.yml`
- `databricks/resources/silver_jobs.yml`
- `databricks/configuration/silver_test.yml`
- Shared Silver notebooks `00` through `04`
- Conformed source notebooks `10` through `25`
- Football truth notebooks `30` through `33`
- Space/pressing notebooks `34` through `37`
- Silver validation notebook `95_validate_silver_contracts.py`

### Data products

- Approved conformed athlete and event Silver tables.
- Approved football-truth Silver tables.
- Approved opportunity, space, pressing, attribution, and recovery Silver tables.
- Operational transformation, quality, reconciliation, and unresolved-reference outputs.

### Evidence

- Deployment output for Silver schemas and jobs.
- Silver schema inventory.
- Source-to-Silver row-count and lineage report.
- Data-quality rule execution report.
- Referential-integrity and temporal-validation report.
- Retry/idempotency and correction-handling report.
- Sprint 2 acceptance report.

## 12. Acceptance criteria

| ID | Acceptance criterion | Evidence |
|---|---|---|
| S2-AC-01 | Silver schemas and approved tables are deployed in the test target | Bundle deployment output and table inventory |
| S2-AC-02 | All conformed athlete/event tables contain typed columns, approved keys, and lineage | Automated Silver schema report |
| S2-AC-03 | Duplicate Bronze records select one deterministic current Silver version | Deduplication and replay evidence |
| S2-AC-04 | Athlete, fixture, participant, result, scoring, and incident references resolve or are explicitly unresolved | Referential-quality report |
| S2-AC-05 | UTC normalization and source temporal evidence are preserved | Temporal validation report |
| S2-AC-06 | Match periods and state intervals are ordered, non-overlapping, and score-consistent | Football-truth validation report |
| S2-AC-07 | Possession and phase facts expose confidence and unresolved reasons | Football-truth output samples |
| S2-AC-08 | Opportunity records distinguish eligible from observed situations | Opportunity validation report |
| S2-AC-09 | Space and pressing facts retain required opportunity, participant, evidence, and run references | Analytical Silver schema report |
| S2-AC-10 | Invalid coordinates, timestamps, identities, domain values, and references are quarantined or flagged with reasons | Quality and quarantine report |
| S2-AC-11 | Silver processing is idempotent across retry, incremental, and correction runs | Job history and row-count comparison |
| S2-AC-12 | Every Silver output is traceable to Bronze snapshot, ingestion attempt, and transformation run | Lineage query evidence |
| S2-AC-13 | Quality, conflict, unresolved, duplicate, input, and output metrics are published per task | Job task-value and quality-run evidence |
| S2-AC-14 | No Sprint 2 task writes Bronze, Gold, or PostgreSQL | Bundle review and catalog audit |
| S2-AC-15 | Silver validation job passes all critical gates | Validation job output |

## 13. Requirement mapping

| REQ ID | Description | Plan items | Implementation evidence |
|---|---|---|---|
| REQ-001 | Silver schemas and locations | 1.1 | `silver_tables.yml`, deployment output |
| REQ-002 | Conformed athlete/event products | 3.1, 3.2 | Notebooks 10-25 and Silver tables |
| REQ-003 | Football truth facts | 4.1, 4.2 | Notebooks 30-33 |
| REQ-004 | Space, pressing, attribution facts | 5.1, 5.2 | Notebooks 34-37 |
| REQ-005 | Deterministic version selection | 2.1, 3.2 | `01_silver_helpers.py`, conformance outputs |
| REQ-006 | Reference resolution | 2.2, 3.2, 4.2 | `03_reference_helpers.py`, unresolved outputs |
| REQ-007 | UTC and temporal normalization | 2.2, 3.2, 4.2 | `04_temporal_helpers.py`, temporal report |
| REQ-008 | Coordinate normalization | 5.2 | `35_build_space_facts.py`, tracking quality rules |
| REQ-009 | Business/data-quality rules | 2.2, 3.3, 4.3, 5.3 | `02_quality_helpers.py`, quality outputs |
| REQ-010 | Quarantine and reconciliation | 2.2, 3.2, 6.1 | Quality and conflict tables |
| REQ-011 | Transformation and source lineage | 2.1, 6.2 | Transformation-run and lineage columns |
| REQ-012 | Idempotent processing | 2.1, 6.2 | Retry and correction test evidence |
| REQ-013 | Silver jobs | 1.1, 6.1 | `silver_jobs.yml` |
| REQ-014 | Operational metrics | 2.1, 6.1 | Task values and quality-run report |
| REQ-015 | Exclude invalid Bronze | 2.2, 3.3 | Accepted-only filters and validation |
| REQ-016 | Silver validation | 3.3, 4.3, 5.3, 6.1 | `95_validate_silver_contracts.py` |
| REQ-017 | Delivery evidence | 6.2, 6.3 | Sprint 2 acceptance report |
