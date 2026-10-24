# Off-Ball Version 2.1 Sprint 1 Implementation Guide

**Sprint:** 1 - Platform foundation and Bronze ingestion  
**Status:** Execution guide for the approved frozen baseline  
**Authoritative roadmap:** [offball_databricks_lakehouse_implementation_roadmap.md](./offball_databricks_lakehouse_implementation_roadmap.md)  
**Approved model:** [offball_data_model_design.md](./offball_data_model_design.md)  
**Approved PostgreSQL contract:** [offball_postgresql_schema.sql](./offball_postgresql_schema.sql)

## 1. Sprint purpose

Sprint 1 establishes the Databricks foundation and immutable Bronze landing layer. It does not build Silver conformance, match truth, opportunities, space intelligence, pressing intelligence, Gold metrics, or PostgreSQL serving synchronization.

### 1.1 Sprint objectives

1. Create the Unity Catalog catalog and Bronze, Silver, and Gold schemas.
2. Establish governed landing locations and environment configuration.
3. Ingest the repository-aligned athlete and event source products into Bronze Delta tables.
4. Register source snapshots and ingestion attempts.
5. Establish raw tracking, video evidence, and scouting annotation landing contracts.
6. Support replay, idempotency, malformed-record quarantine, and operational observability.

### 1.2 In-scope source families

| Source family | Bronze scope | Downstream approved anchor |
|---|---|---|
| Athlete identity | `athlete_profile_raw` | `athlete.athlete_profile` |
| Roster and registration | `roster_raw` | `athlete.roster` |
| Performance statistics | `performance_stat_raw` | `athlete.performance_stat` |
| Contracts | `contract_raw` | `athlete.contract` |
| Eligibility | `eligibility_status_raw` | `athlete.eligibility_status` |
| Fixtures and calendars | `fixture_raw` | `event.fixture`, `event.calendar` |
| Competition context | `competition_raw` | `event.tournament`, `event.bracket`, `event.competition_round`, `event.type` |
| Participation and lineups | `participant_raw` | `event.participant` |
| Match results | `match_result_raw` | `event.match_result` |
| Scoring events | `scoring_event_raw` | `event.scoring_event` |
| Match incidents | `event_incident_raw` | `event.event_incident` |
| Tracking frames | `tracking_frame_raw` | Silver tracking facts in Sprint 2+ |
| Tracking quality | `tracking_quality_raw` | Silver quality fields in Sprint 2+ |
| Video metadata | `video_evidence_raw` | `analytics.evidence_link` in later sprint |
| Scouting annotations | `scouting_annotation_raw` | Annotation tables in later sprint |

## 2. Databricks setup

### 2.1 Environment configuration

Create separate Databricks workspaces or environment-specific deployment targets for:

```text
dev
test
prod
```

Each environment must have:

- Unity Catalog enabled.
- A workspace identity or service principal for scheduled jobs.
- An external location or managed storage location for Bronze data.
- Secret-backed credentials for source systems.
- A Git-connected repository or workspace source directory for notebooks and deployment definitions.
- Cluster policies limiting uncontrolled compute and enforcing approved runtime settings.
- Job notifications for failure and prolonged inactivity.

Environment-specific values must be configuration-driven:

| Configuration | Example key | Purpose |
|---|---|---|
| Catalog | `offball_catalog` | Environment-specific Unity Catalog catalog |
| Bronze root | `bronze_root_uri` | Immutable Bronze storage location |
| Checkpoint root | `checkpoint_root_uri` | Structured Streaming and Auto Loader checkpoints |
| Schema registry root | `schema_registry_root_uri` | Source schema/version metadata |
| Quarantine root | `quarantine_root_uri` | Invalid and rejected records |
| Source secret scope | `source_secret_scope` | Provider credentials |
| Run mode | `run_mode` | Batch, incremental, or replay execution |

Do not place credentials, tokens, or provider secrets in notebooks, job parameters, or Delta payload columns.

### 2.2 Catalog and schema creation

Create the approved catalog and schemas:

```text
offball_<environment>
offball_<environment>.bronze
offball_<environment>.silver
offball_<environment>.gold
```

Sprint 1 creates all three schemas so later sprints can deploy without changing the namespace. Only Bronze tables and Bronze metadata are populated in this sprint.

Recommended permissions:

| Principal | Bronze | Silver | Gold |
|---|---|---|---|
| Ingestion service principal | Create/write | No write | No write |
| Data engineering group | Read/write | Read/write | Read |
| Analysts | Read approved tables | Read | Read |
| Operations/support | Read metadata and quarantine | Read quality outputs | Read publication status |
| Application serving identity | Read approved exports | Read approved exports | Read approved products |

Permission implementation must follow the organization’s Unity Catalog policy. This sprint does not change the approved business data model.

### 2.3 Storage layout

Use environment-specific managed or external locations with the following logical layout:

```text
<bronze_root_uri>/
  athlete/
    athlete_profile_raw/
    roster_raw/
    performance_stat_raw/
    contract_raw/
    eligibility_status_raw/
  event/
    fixture_raw/
    competition_raw/
    participant_raw/
    match_result_raw/
    scoring_event_raw/
    event_incident_raw/
  tracking/
    tracking_frame_raw/
    tracking_quality_raw/
  evidence/
    video_evidence_raw/
  annotation/
    scouting_annotation_raw/
  _metadata/
    source_snapshot/
    ingestion_attempt/
  _quarantine/
```

The storage paths are implementation locations, not additional domain entities.

## 3. Repository folder structure

Store implementation assets in a repository-connected project directory:

```text
offball/
  databricks/
    resources/
      catalogs.yml
      schemas.yml
      bronze_tables.yml
      jobs.yml
    notebooks/
      common/
        00_runtime_config
        01_ingestion_helpers
        02_quality_helpers
        03_snapshot_helpers
      bronze/
        10_ingest_athlete_profile
        11_ingest_roster
        12_ingest_performance_stat
        13_ingest_contract
        14_ingest_eligibility_status
        20_ingest_fixture
        21_ingest_competition
        22_ingest_participant
        23_ingest_match_result
        24_ingest_scoring_event
        25_ingest_event_incident
        30_ingest_tracking_frame
        31_ingest_tracking_quality
        32_ingest_video_evidence
        33_ingest_scouting_annotation
      orchestration/
        90_register_source_snapshot
        91_finalize_ingestion_attempt
        92_bronze_replay
      validation/
        95_validate_bronze_contracts
        96_validate_bronze_replay
    schemas/
      bronze_contracts/
        athlete_profile.json
        roster.json
        performance_stat.json
        contract.json
        eligibility_status.json
        fixture.json
        competition.json
        participant.json
        match_result.json
        scoring_event.json
        event_incident.json
        tracking_frame.json
        tracking_quality.json
        video_evidence.json
        scouting_annotation.json
    tests/
      bronze/
      orchestration/
      replay/
    configuration/
      dev.yml
      test.yml
      prod.yml
```

Notebook names are illustrative implementation names for the approved table set. They do not create new model entities.

## 4. Bronze Delta table contract

### 4.1 Common columns

Every Bronze Delta table must contain the following ingestion columns:

| Column | Type | Required | Rule |
|---|---|---:|---|
| `ingestion_id` | `string` | Yes | Unique for the ingestion attempt |
| `source_system_code` | `string` | Yes | Stable source/provider code |
| `source_record_reference` | `string` | Yes where source provides one | Provider-native record identifier |
| `source_object_name` | `string` | Yes | Source object or feed name |
| `source_version` | `string` | Yes | Provider schema or delivery version |
| `payload_json` | `string` | Yes | Original serialized payload |
| `payload_hash` | `string` | Yes | Deterministic content hash |
| `source_event_timestamp` | `timestamp` | No | Source-provided event timestamp |
| `ingested_at` | `timestamp` | Yes | Platform ingestion timestamp |
| `file_uri` | `string` | No | Source file or object location |
| `rescued_data` | `string` or `variant` | No | Unparsed fields |
| `ingestion_status` | `string` | Yes | `accepted`, `rejected`, or `quarantined` |

Source-specific fields may be added according to the source contract. Bronze does not silently drop fields that are not yet promoted to Silver.

### 4.2 Source-specific Bronze tables

| Table | Minimum source-specific fields | Partition or clustering guidance |
|---|---|---|
| `bronze.athlete_profile_raw` | provider athlete ID, name fields, date of birth, nationality, career status | Source and ingestion date |
| `bronze.roster_raw` | provider roster ID, athlete ID, team/franchise ID, season ID, activation/deactivation dates | Season and ingestion date |
| `bronze.performance_stat_raw` | athlete ID, fixture ID, statistic type, value, unit | Fixture and ingestion date |
| `bronze.contract_raw` | athlete ID, team ID, contract reference, effective dates, status | Effective year and ingestion date |
| `bronze.eligibility_status_raw` | athlete ID, eligibility type, status, effective/expiry dates | Effective date and ingestion date |
| `bronze.fixture_raw` | fixture ID, calendar ID, competition references, event date, lifecycle status | Event date and source |
| `bronze.competition_raw` | tournament, bracket, round, event type identifiers and labels | Season and source |
| `bronze.participant_raw` | fixture ID, athlete/team ID, participant role, lineup position, status | Fixture and event date |
| `bronze.match_result_raw` | fixture ID, home/away score, result status, result timestamp | Event date and source |
| `bronze.scoring_event_raw` | fixture ID, participant ID, scoring type, event timestamp | Fixture and event date |
| `bronze.event_incident_raw` | fixture ID, participant ID, incident type, timestamp, provider payload | Fixture and event date |
| `bronze.tracking_frame_raw` | fixture ID, frame timestamp, object ID, x/y coordinates, provider frame ID | Source, fixture, event date |
| `bronze.tracking_quality_raw` | fixture ID, coverage interval, alignment status, quality measurements | Source, fixture, event date |
| `bronze.video_evidence_raw` | fixture ID, source reference, locator, rights/access metadata | Fixture and ingestion date |
| `bronze.scouting_annotation_raw` | fixture ID, target reference, reviewer reference, label, confidence | Fixture and ingestion date |

Tracking-frame partitioning must avoid creating a partition for every frame or player. Use fixture and event date as the primary partitioning dimensions, with source/provider clustering where available.

## 5. Ingestion notebook guide

### 5.1 Common notebook responsibilities

`00_runtime_config`

- Resolve environment and catalog parameters.
- Load secret references without exposing values.
- Validate required parameters.
- Set run identifiers and replay mode.

`01_ingestion_helpers`

- Build common Bronze metadata columns.
- Serialize and hash source payloads.
- Normalize timestamps to UTC.
- Apply idempotency keys.
- Write accepted and rejected records.

`02_quality_helpers`

- Validate required metadata.
- Validate source schema version.
- Validate file completeness and parseability.
- Count malformed records.
- Write quarantine records.

`03_snapshot_helpers`

- Register a source delivery.
- Create the `source_snapshot` metadata record for the run.
- Associate all ingestion attempts with the snapshot.
- Finalize status and counts.

### 5.2 Athlete ingestion notebooks

| Notebook | Input | Output | Required behavior |
|---|---|---|---|
| `10_ingest_athlete_profile` | Identity delivery | `bronze.athlete_profile_raw` | Preserve identity payload and provider reference |
| `11_ingest_roster` | Roster delivery | `bronze.roster_raw` | Preserve registration and effective-date fields |
| `12_ingest_performance_stat` | Performance delivery | `bronze.performance_stat_raw` | Preserve provider statistic type/value/unit |
| `13_ingest_contract` | Contract delivery | `bronze.contract_raw` | Preserve contract source record and lifecycle |
| `14_ingest_eligibility_status` | Eligibility delivery | `bronze.eligibility_status_raw` | Preserve eligibility status and dates |

### 5.3 Event ingestion notebooks

| Notebook | Input | Output | Required behavior |
|---|---|---|---|
| `20_ingest_fixture` | Fixture/calendar delivery | `bronze.fixture_raw` | Preserve fixture identity and lifecycle |
| `21_ingest_competition` | Tournament/round/type delivery | `bronze.competition_raw` | Preserve competition hierarchy payload |
| `22_ingest_participant` | Lineup/participant delivery | `bronze.participant_raw` | Preserve player/team participation |
| `23_ingest_match_result` | Result delivery | `bronze.match_result_raw` | Preserve score and result status |
| `24_ingest_scoring_event` | Scoring delivery | `bronze.scoring_event_raw` | Preserve scoring event and timestamp |
| `25_ingest_event_incident` | Incident delivery | `bronze.event_incident_raw` | Preserve incident type, timestamp, and provider payload |

### 5.4 Additional landing notebooks

| Notebook | Input | Output | Required behavior |
|---|---|---|---|
| `30_ingest_tracking_frame` | Licensed tracking files/feed | `bronze.tracking_frame_raw` | Preserve frames, coordinates, provider frame ID, and quality metadata |
| `31_ingest_tracking_quality` | Tracking quality feed | `bronze.tracking_quality_raw` | Preserve coverage and alignment observations |
| `32_ingest_video_evidence` | Video metadata/locator feed | `bronze.video_evidence_raw` | Preserve source locator and rights/access fields |
| `33_ingest_scouting_annotation` | Human annotation export | `bronze.scouting_annotation_raw` | Preserve reviewer, label, target, confidence, and timestamps |

### 5.5 Finalization notebooks

`90_register_source_snapshot`

- Accept source delivery parameters.
- Create the snapshot identifier.
- Record source object, source version, delivery time, and expected record count if available.

`91_finalize_ingestion_attempt`

- Aggregate accepted, rejected, and quarantined counts.
- Record payload hash counts and duplicate counts.
- Mark the snapshot as `completed`, `completed_with_quarantine`, or `failed`.

`92_bronze_replay`

- Replay a selected snapshot or ingestion ID.
- Write a new ingestion attempt.
- Never overwrite the original Bronze records.
- Confirm that the replay produces the same accepted payload hash set.

## 6. Job definitions

### 6.1 Job: `offball_s1_register_snapshot`

| Property | Definition |
|---|---|
| Trigger | Manual, API, or upstream delivery event |
| Tasks | `90_register_source_snapshot` |
| Parameters | environment, source system, source object, source version, delivery URI, replay flag |
| Output | Snapshot identifier and expected delivery metadata |
| Failure behavior | Fail fast if source metadata is incomplete |

### 6.2 Job: `offball_s1_ingest_athlete_bronze`

| Property | Definition |
|---|---|
| Trigger | Source delivery or scheduled incremental run |
| Tasks | Snapshot registration, athlete ingestion notebooks, finalization |
| Dependencies | Source credentials and Bronze schema available |
| Output | Athlete Bronze tables and ingestion counts |
| Retry | Retry transient source/storage failures; do not duplicate accepted records |
| Failure behavior | Quarantine malformed records and fail if the source contract cannot be parsed |

### 6.3 Job: `offball_s1_ingest_event_bronze`

| Property | Definition |
|---|---|
| Trigger | Source delivery or scheduled incremental run |
| Tasks | Snapshot registration, fixture/competition/participant/result/scoring/incident ingestion, finalization |
| Dependencies | Bronze schema available |
| Output | Event Bronze tables and ingestion counts |
| Retry | Idempotent retry using source reference and payload hash |
| Failure behavior | Do not publish a successful run if fixture identity or source version is absent |

### 6.4 Job: `offball_s1_ingest_tracking_bronze`

| Property | Definition |
|---|---|
| Trigger | Tracking delivery |
| Tasks | Snapshot registration, tracking frame ingestion, tracking quality ingestion, finalization |
| Dependencies | Fixture delivery or resolvable provider fixture reference |
| Output | Tracking Bronze tables and coverage metadata |
| Retry | Retry delivery and storage failures; preserve original payloads |
| Failure behavior | Quarantine invalid frames and report coverage gaps |

### 6.5 Job: `offball_s1_ingest_evidence_annotation_bronze`

| Property | Definition |
|---|---|
| Trigger | Video or annotation delivery |
| Tasks | Snapshot registration, evidence ingestion, annotation ingestion, finalization |
| Dependencies | Bronze schemas and source contract |
| Output | Evidence and annotation Bronze tables |
| Failure behavior | Preserve records with invalid locators or labels as quarantined; do not silently discard |

### 6.6 Job: `offball_s1_validate_bronze`

| Property | Definition |
|---|---|
| Trigger | Completion of any Bronze ingestion job |
| Tasks | `95_validate_bronze_contracts`, `96_validate_bronze_replay` |
| Checks | Table existence, required columns, metadata completeness, duplicate handling, quarantine visibility, replay consistency |
| Output | Validation report and job status |
| Gate | Required before Sprint 1 sign-off |

### 6.7 Dependency graph

```text
offball_s1_register_snapshot
  ├── offball_s1_ingest_athlete_bronze
  ├── offball_s1_ingest_event_bronze
  ├── offball_s1_ingest_tracking_bronze
  └── offball_s1_ingest_evidence_annotation_bronze
          └── offball_s1_validate_bronze
```

No Sprint 1 job writes Silver or Gold tables.

## 7. Source snapshot and ingestion metadata

The approved schema defines `analytics.source_snapshot` as the source snapshot contract. Sprint 1 registers the corresponding metadata in Bronze operational storage and prepares the contract for later synchronization.

Minimum snapshot attributes:

| Attribute | Required |
|---|---:|
| Snapshot identifier | Yes |
| Source system code | Yes |
| Source object name | Yes |
| Source version | Yes |
| Capture/delivery timestamp | Yes |
| Object URI or delivery reference | Yes |
| Expected record count, when supplied | No |
| Actual record count | Yes after finalization |
| Accepted count | Yes after finalization |
| Rejected count | Yes after finalization |
| Quarantined count | Yes after finalization |
| Snapshot status | Yes |

The snapshot status must distinguish successful ingestion from successful ingestion with quarantined records.

## 8. Idempotency, replay, and quarantine

### 8.1 Idempotency key

Use the following logical key:

```text
source_system_code
+ source_record_reference
+ source_version
+ payload_hash
```

If a source does not provide a record reference, use the deterministic hash of the provider payload plus source object and source event timestamp.

### 8.2 Replay rules

- Replay uses a new `ingestion_id`.
- Original Bronze rows remain unchanged.
- Accepted payload hashes must match the original run unless the source delivery changed.
- Replay differences are reported, not silently merged.
- Replaying a quarantined record is permitted after the parser or source contract is corrected.

### 8.3 Quarantine rules

Quarantine records when:

- Required source metadata is missing.
- Payload parsing fails.
- Source version is unsupported.
- Timestamp cannot be normalized.
- Payload hash cannot be calculated.
- Required provider identity is absent where the source contract requires it.
- Tracking frame coordinates are malformed.

Quarantine records retain the original payload and an explicit rejection reason.

## 9. Acceptance criteria

Sprint 1 is accepted only when all criteria pass:

| ID | Acceptance criterion | Evidence |
|---|---|---|
| S1-AC-01 | Environment-specific Unity Catalog catalog exists | Catalog and schema deployment output |
| S1-AC-02 | `bronze`, `silver`, and `gold` schemas exist | Unity Catalog metadata query |
| S1-AC-03 | All 15 approved Bronze source tables exist | Table inventory report |
| S1-AC-04 | Every Bronze table contains the common ingestion metadata columns | Automated schema test |
| S1-AC-05 | Athlete source replay succeeds for a representative athlete cohort | Replay run report |
| S1-AC-06 | Event source replay succeeds for a representative fixture | Replay run report |
| S1-AC-07 | Tracking frames and tracking quality data land without overwriting source payloads | Delta history and row-count report |
| S1-AC-08 | Video evidence and scouting annotation landing contracts accept valid records | Contract test output |
| S1-AC-09 | Duplicate deliveries are idempotent | Duplicate/replay test |
| S1-AC-10 | Malformed records are quarantined with a reason and original payload | Quarantine sample and counts |
| S1-AC-11 | Source snapshot metadata records source, version, URI, counts, and status | Snapshot metadata report |
| S1-AC-12 | Failed and completed-with-quarantine runs are distinguishable | Job run output |
| S1-AC-13 | Bronze tables can be replayed from a selected ingestion ID | Replay demonstration |
| S1-AC-14 | Ingestion jobs retry transient failures without duplicate accepted rows | Job history and idempotency test |
| S1-AC-15 | No Sprint 1 job writes Silver or Gold data | Unity Catalog audit and job configuration |

## 10. Sprint 1 deliverables

### Databricks platform

- Catalog and schema deployment definitions.
- Managed or external location configuration.
- Service principal and job identity configuration.
- Environment configuration files for dev, test, and prod.

### Bronze data products

- Fifteen Bronze Delta tables.
- Common ingestion metadata contract.
- Source-specific schema contracts.
- Tracking, video, and annotation landing contracts.

### Notebooks

- Common configuration, hashing, quality, and snapshot helpers.
- Athlete ingestion notebooks.
- Event ingestion notebooks.
- Tracking, evidence, and annotation ingestion notebooks.
- Snapshot registration, finalization, replay, and validation notebooks.

### Jobs

- Snapshot registration job.
- Athlete Bronze ingestion job.
- Event Bronze ingestion job.
- Tracking Bronze ingestion job.
- Evidence and annotation Bronze ingestion job.
- Bronze validation job.

### Testing and evidence

- Bronze schema test results.
- Source replay results.
- Idempotency test results.
- Quarantine test results.
- Snapshot and ingestion-count report.
- Job dependency and failure-handling evidence.

## 11. Sprint completion checklist

- [ ] Catalog and schemas deployed in the target environment.
- [ ] Storage locations and checkpoints configured.
- [ ] Secrets referenced through the approved secret manager.
- [ ] Bronze table contracts reviewed against the roadmap.
- [ ] Athlete ingestion completed.
- [ ] Event ingestion completed.
- [ ] Tracking ingestion completed.
- [ ] Evidence and annotation landing completed.
- [ ] Snapshot registration and finalization completed.
- [ ] Replay and idempotency tests passed.
- [ ] Quarantine behavior passed.
- [ ] Bronze validation job passed.
- [ ] No Silver or Gold writes occurred.
- [ ] Sprint evidence attached to the release record.

## 12. Out of scope

The following are explicitly deferred to later roadmap sprints:

- Silver identity resolution and conformance.
- Fixture and participant reconciliation.
- Match periods, score-state intervals, possession, and phase.
- Opportunity, space, and pressing facts.
- Gold metric products and dashboards.
- Feature engineering.
- PostgreSQL serving synchronization.
- Model training and scoring.

