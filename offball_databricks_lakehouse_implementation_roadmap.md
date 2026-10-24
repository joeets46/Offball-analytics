# Off-Ball Version 2.1 Databricks Lakehouse Implementation Blueprint

**Status:** Implementation design for the approved frozen baseline  
**Scope:** Bronze, Silver, Gold, Delta mappings, ingestion, KPI generation, feature engineering, and sprint roadmap  
**Authoritative inputs:**

- [Business Requirements Document](./football_offball_project.md)
- [Repository-first Version 2.1 data model](./offball_data_model_design.md)
- [Version 2.1 PostgreSQL schema](./offball_postgresql_schema.sql)
- [Databricks Sports Entertainment MVM](https://github.com/databricks-industry-solutions/lakehouse-industry-data-models/tree/main/data-models/sports_entertainment/v1/mvm)

This blueprint operationalizes the approved model. It does not add entities, change grains, or redesign the PostgreSQL contract.

## 1. Lakehouse principles

1. Databricks Unity Catalog is the analytical system of record.
2. Bronze preserves immutable source payloads and ingestion metadata.
3. Silver conforms repository-aligned athlete and event products and reconciles the approved analytics extensions.
4. Gold publishes denormalized metric views and player/match data products for dashboards and downstream consumers.
5. PostgreSQL stores the approved relational contract, lineage metadata, evidence/review workflow, and low-volume operational records.
6. High-volume tracking frames and provider observations remain Delta tables.
7. Every published metric is linked to a source snapshot, calculation run, metric version, quality status, and publication record.
8. Late corrections create a new versioned record or run; Bronze data is never overwritten.

## 2. Catalog and schema layout

Recommended Unity Catalog layout:

```text
offball_<environment>/
  bronze/
  silver/
  gold/
```

Logical domain namespaces in Silver and Gold follow the repository:

```text
silver.athlete
silver.event
silver.analytics
gold.athlete
gold.event
gold.offball
gold.pressing
gold.recruitment
gold.quality
```

The PostgreSQL schemas remain `athlete`, `event`, and `analytics` as defined in the approved SQL. Unity Catalog tables and PostgreSQL tables are synchronized through controlled export or serving jobs; they are not independent competing definitions.

## 3. Bronze layer design

### 3.1 Bronze objectives

Bronze is the immutable landing layer for source fidelity, replay, reconciliation, and auditability. Bronze tables retain the original payload, provider identity, source timestamps, ingestion timestamps, schema version, and content hash.

Common Bronze columns:

| Column | Purpose |
|---|---|
| `ingestion_id` | Unique ingestion attempt |
| `source_system_code` | Provider or source application |
| `source_record_reference` | Provider-native record identifier |
| `source_object_name` | Source table, file, feed, or endpoint |
| `source_version` | Provider schema or delivery version |
| `payload_json` | Original record or message |
| `payload_hash` | Idempotency and change detection |
| `source_event_timestamp` | Timestamp supplied by source |
| `ingested_at` | Platform ingestion timestamp |
| `file_uri` | Landing object reference where applicable |
| `rescued_data` | Fields that cannot be parsed into the current contract |
| `ingestion_status` | Accepted, rejected, or quarantined |

### 3.2 Bronze source tables

| Bronze Delta table | Source | Downstream repository anchor |
|---|---|---|
| `bronze.athlete_profile_raw` | Athlete identity feed | `athlete.athlete_profile` |
| `bronze.roster_raw` | Roster and registration feed | `athlete.roster` |
| `bronze.performance_stat_raw` | Provider performance statistics | `athlete.performance_stat` |
| `bronze.contract_raw` | Contract feed | `athlete.contract` |
| `bronze.eligibility_status_raw` | Eligibility and registration feed | `athlete.eligibility_status` |
| `bronze.fixture_raw` | Fixture/calendar feed | `event.fixture`, `event.calendar` |
| `bronze.competition_raw` | Tournament and competition feed | `event.tournament`, `event.bracket`, `event.competition_round`, `event.type` |
| `bronze.participant_raw` | Lineup and participation feed | `event.participant` |
| `bronze.match_result_raw` | Match result feed | `event.match_result` |
| `bronze.scoring_event_raw` | Scoring event feed | `event.scoring_event` |
| `bronze.event_incident_raw` | Event incident feed | `event.event_incident` |
| `bronze.tracking_frame_raw` | Licensed tracking provider | Silver tracking facts and approved analytics extensions |
| `bronze.tracking_quality_raw` | Tracking coverage/alignment metadata | Silver quality fields |
| `bronze.video_evidence_raw` | Licensed video metadata and locators | `analytics.evidence_link` |
| `bronze.scouting_annotation_raw` | Human labels and review actions | Annotation tables |

Bronze tracking data is partitioned by `source_system_code`, `fixture_id` where available, and event date. Raw frame payloads are stored in Delta or referenced through governed object storage when the provider contract requires file preservation.

### 3.3 Bronze ingestion behavior

- Use Auto Loader for file and object-store deliveries.
- Use Structured Streaming or scheduled incremental extraction for provider APIs and relational feeds.
- Enforce idempotency using `source_system_code`, `source_record_reference`, `source_version`, and `payload_hash`.
- Preserve malformed records in `rescued_data`; do not silently discard them.
- Record rejected batches in the operational run log associated with `analytics.source_snapshot`.

## 4. Silver layer design

### 4.1 Silver objectives

Silver converts Bronze payloads into typed, deduplicated, conformed Delta tables at the approved model grains. It applies identity resolution, event reconciliation, temporal normalization, coordinate normalization, and quality gates.

### 4.2 Repository-aligned Silver tables

| Silver Delta table | Grain | PostgreSQL contract | Transformation |
|---|---|---|---|
| `silver.athlete.athlete_profile` | One athlete | `athlete.athlete_profile` | Deduplicate identity records and preserve source/version history |
| `silver.athlete.roster` | One athlete-team-season affiliation | `athlete.roster` | Apply effective dates and roster status |
| `silver.athlete.performance_stat` | One athlete performance fact | `athlete.performance_stat` | Type, standardize, and retain provider statistic identity |
| `silver.athlete.contract` | One contract record | Approved repository entity | Preserve contractual source grain |
| `silver.athlete.eligibility_status` | One eligibility record | Approved repository entity | Apply effective and expiry semantics |
| `silver.event.fixture` | One scheduled event | `event.fixture` | Reconcile fixture references and lifecycle state |
| `silver.event.calendar` | One calendar | Repository MVM entity | Conform season/calendar attributes |
| `silver.event.tournament` | One tournament | Repository MVM entity | Conform tournament and bracket references |
| `silver.event.competition_round` | One competition round | Repository MVM entity | Conform round and stage references |
| `silver.event.type` | One event type | Repository MVM entity | Apply controlled event taxonomy |
| `silver.event.participant` | One fixture participant | `event.participant` | Resolve athlete/team participation and lineup context |
| `silver.event.match_result` | One fixture result | `event.match_result` | Reconcile competing result providers |
| `silver.event.scoring_event` | One scoring event | `event.scoring_event` | Normalize event time and participant references |
| `silver.event.event_incident` | One event incident | `event.event_incident` | Reconcile incident type and provider payload |

### 4.3 Approved analytics Silver tables

| Silver Delta table | Grain | PostgreSQL table | Main inputs |
|---|---|---|---|
| `silver.analytics.match_period` | One match period | `analytics.match_period` | Fixture and provider clock |
| `silver.analytics.match_state_interval` | One continuous score/game-state interval | `analytics.match_state_interval` | Match result and scoring events |
| `silver.analytics.possession_sequence` | One canonical possession | `analytics.possession_sequence` | Incidents, tracking, event transitions |
| `silver.analytics.phase_interval` | One phase interval | `analytics.phase_interval` | Possession sequence and event context |
| `silver.analytics.opportunity` | One eligible analytical situation | `analytics.opportunity` | Fixture, participant, phase, tracking |
| `silver.analytics.space_opportunity` | One space opportunity | `analytics.space_opportunity` | Opportunity and participant |
| `silver.analytics.space_baseline` | One baseline for a space opportunity | `analytics.space_baseline` | Tracking geometry and baseline method |
| `silver.analytics.space_counterfactual` | One counterfactual evaluation | `analytics.space_counterfactual` | Baseline, feature set, model run |
| `silver.analytics.space_outcome` | One space outcome | `analytics.space_outcome` | Event, tracking, and receiving context |
| `silver.analytics.attribution_ledger` | One participant attribution entry | `analytics.attribution_ledger` | Space/press outcome and participant |
| `silver.analytics.pressing_opportunity` | One pressing opportunity | `analytics.pressing_opportunity` | Opportunity, target participant, event/tracking |
| `silver.analytics.press_trigger` | One press trigger | `analytics.press_trigger` | Press opportunity and event timestamp |
| `silver.analytics.press_action` | One press action | `analytics.press_action` | Tracking and participant |
| `silver.analytics.press_support` | One support action | `analytics.press_support` | Press opportunity and participant |
| `silver.analytics.press_bypass` | One bypass event | `analytics.press_bypass` | Press opportunity and event transition |
| `silver.analytics.press_outcome` | One pressing outcome | `analytics.press_outcome` | Press actions and possession transition |
| `silver.analytics.recovery_action` | One recovery action | `analytics.recovery_action` | Press opportunity and participant |

### 4.4 Silver quality rules

- Every athlete and event foreign key resolves to a repository-aligned Silver key.
- Duplicate source records are retained in Bronze but only the selected conformed version is promoted.
- Fixture clocks are normalized to UTC while preserving source timezone metadata.
- Tracking coordinates are transformed into the approved pitch coordinate convention.
- Possession and phase records carry status and confidence; unresolved intervals remain visible.
- Opportunity records distinguish eligible from observed situations.
- Provider conflicts are retained as evidence and resolved through deterministic precedence and reconciliation output.
- Quarantined records cannot flow into Gold publication.

## 5. Gold layer design

Gold is organized around the repository metric-view pattern and the approved off-ball analytical products. Gold tables are denormalized for dashboards, player comparison, recruitment workflows, and analyst review.

### 5.1 Repository-aligned Gold products

| Gold product | Grain | Source pattern |
|---|---|---|
| `gold.athlete.athlete_profile_metrics` | Athlete and evaluation window | Repository athlete metric view |
| `gold.athlete.roster_metrics` | Athlete-team-season window | Repository athlete/roster metric view |
| `gold.event.match_result_metrics` | Fixture | Repository event metric view |
| `gold.event.participant_metrics` | Fixture participant | Repository event metric view |
| `gold.event.scoring_event_metrics` | Scoring-event aggregation | Repository event metric view |
| `gold.event.incident_metrics` | Fixture incident aggregation | Repository event metric view |

### 5.2 Off-ball Gold products

| Gold product | Grain | Consumers |
|---|---|---|
| `gold.offball.player_offball_profile` | Athlete, window, role/position context | Recruitment and player dashboards |
| `gold.offball.space_creation_profile` | Athlete, window, space type | Coaches, analysts, recruitment |
| `gold.offball.space_opportunity_detail` | Space opportunity | Analyst review and evidence |
| `gold.pressing.player_pressing_profile` | Athlete, window, press type | Coaches and performance analysts |
| `gold.pressing.press_opportunity_detail` | Pressing opportunity | Match analysis and annotation |
| `gold.offball.player_defensive_attribution` | Athlete, window, attribution type | Defensive intelligence |
| `gold.offball.match_offball_summary` | Fixture and team | Match dashboards |
| `gold.offball.player_comparison` | Cohort and evaluation window | Scouting and recruitment |

### 5.3 Gold publication contract

Every published Gold metric row includes or can join to:

- `athlete_profile_id` or `fixture_id`
- Evaluation window
- Metric code and metric version
- Numerator and denominator where applicable
- Sample size and coverage
- Confidence and quality status
- `source_snapshot_id`
- `calculation_run_id`
- Feature-set and model-artifact references when modeled
- Publication status
- Evidence linkage for reviewable outputs

## 6. Delta Lake table mapping

| PostgreSQL object | Delta implementation | Layer | Notes |
|---|---|---|---|
| `athlete.athlete_profile` | `silver.athlete.athlete_profile` | Silver | Repository-aligned identity |
| `athlete.roster` | `silver.athlete.roster` | Silver | Effective-dated affiliation |
| `athlete.performance_stat` | `silver.athlete.performance_stat` | Silver | Repository performance fact |
| `event.fixture` | `silver.event.fixture` | Silver | Scheduled event anchor |
| `event.participant` | `silver.event.participant` | Silver | Participation anchor |
| `event.match_result` | `silver.event.match_result` | Silver | Recorded result |
| `event.event_incident` | `silver.event.event_incident` | Silver | Incident fact |
| `event.scoring_event` | `silver.event.scoring_event` | Silver | Scoring fact |
| `analytics.match_period` | `silver.analytics.match_period` | Silver | Approved analytical extension |
| `analytics.match_state_interval` | `silver.analytics.match_state_interval` | Silver | Score/game-state intervals |
| `analytics.possession_sequence` | `silver.analytics.possession_sequence` | Silver | Canonical possession |
| `analytics.phase_interval` | `silver.analytics.phase_interval` | Silver | Phase semantics |
| `analytics.opportunity` | `silver.analytics.opportunity` | Silver | Denominator grain |
| Space and pressing tables | Corresponding `silver.analytics.*` tables | Silver | Curated analytical facts |
| `analytics.source_snapshot` | `silver.analytics.source_snapshot` | Silver metadata | Run and input manifest |
| `analytics.calculation_run` | `silver.analytics.calculation_run` | Silver metadata | Execution state |
| `analytics.feature_set` | `silver.analytics.feature_set` | Silver metadata | Feature definition |
| `analytics.model_artifact` | `silver.analytics.model_artifact` | Silver metadata | Model reference |
| `analytics.metric_publication` | `gold.quality.metric_publication` | Gold metadata | Publication gate |
| `analytics.metric_value` | `gold.*` metric products | Gold | Serving metric fact |
| `analytics.evidence_link` | `gold.quality.evidence_link` | Gold | Reviewable evidence |
| Annotation tables | `silver.analytics.annotation_*` | Silver | Human validation workflow |

Delta tables are the high-volume analytical implementation. PostgreSQL receives governed low-volume copies or references for application workflows and contract validation, as specified by the frozen schema.

## 7. Source-to-target mapping

| Source | Target | Key mapping | Transformation |
|---|---|---|---|
| Athlete identity provider | `bronze.athlete_profile_raw` | Provider record reference | Preserve payload and hash |
| Athlete identity Bronze | `silver.athlete.athlete_profile` | `athlete_profile_id` | Deduplicate and standardize identity |
| Roster provider | `bronze.roster_raw` | Provider roster reference | Normalize effective dates and status |
| Roster Bronze | `silver.athlete.roster` | Athlete plus season/team keys | Resolve athlete identity and affiliation |
| Performance provider | `bronze.performance_stat_raw` | Provider statistic reference | Normalize statistic type/unit |
| Performance Bronze | `silver.athlete.performance_stat` | Athlete and fixture | Attach calculation run when derived |
| Fixture provider | `bronze.fixture_raw` | Provider fixture reference | Resolve fixture lifecycle and event date |
| Fixture Bronze | `silver.event.fixture` | `fixture_id` | Conform event anchor |
| Lineup provider | `bronze.participant_raw` | Fixture plus provider participant | Resolve player to `athlete_profile_id` |
| Result provider | `bronze.match_result_raw` | Fixture plus result reference | Reconcile scores and result status |
| Event provider | `bronze.event_incident_raw` | Fixture plus provider event | Canonicalize incident type and time |
| Scoring provider | `bronze.scoring_event_raw` | Fixture plus scorer/participant | Link scoring event to participant |
| Tracking provider | `bronze.tracking_frame_raw` | Fixture, period, frame | Normalize coordinates and frame time |
| Event plus tracking Silver | `silver.analytics.possession_sequence` | Fixture and time interval | Reconcile control and confidence |
| Possession plus match state | `silver.analytics.phase_interval` | Possession and interval | Assign approved phase type |
| Tracking plus participant context | `silver.analytics.opportunity` | Fixture, participant, interval | Determine eligibility and observability |
| Opportunity plus tracking | `silver.analytics.space_opportunity` | Opportunity and participant | Classify space opportunity |
| Space opportunity plus baseline | `silver.analytics.space_baseline` | Space opportunity | Calculate baseline state |
| Baseline plus feature/model run | `silver.analytics.space_counterfactual` | Space opportunity and run | Compute approved counterfactual |
| Space/press observations | `silver.analytics.attribution_ledger` | Participant and outcome | Allocate approved contribution |
| Opportunity plus defensive event/tracking | `silver.analytics.pressing_opportunity` | Opportunity and target | Classify pressing situation |
| Pressing observations | Pressing child Silver tables | Press opportunity | Capture trigger, action, support, bypass, outcome, recovery |
| Silver facts plus metric definition | Gold metric products | Entity/window/run | Aggregate numerator, denominator, confidence, coverage |
| Gold metric products | PostgreSQL `analytics.metric_value` | Run and entity keys | Publish serving copy/reference |

## 8. Data ingestion workflow

### 8.1 Batch sequence

1. Register delivery and create `source_snapshot`.
2. Land raw files/messages into Bronze.
3. Validate file completeness, schema compatibility, hash, and source timestamps.
4. Quarantine invalid records and expose ingestion status.
5. Merge valid Bronze records into repository-aligned Silver athlete and event tables.
6. Reconcile identity, fixture, participant, incident, result, and scoring references.
7. Normalize tracking timestamps and pitch coordinates.
8. Build match periods, state intervals, possession, phase, and opportunity facts.
9. Build space and pressing analytical facts.
10. Run quality checks and create the `calculation_run` record.
11. Generate Gold metric products.
12. Publish only approved Gold partitions and register `metric_publication`.
13. Export required low-volume records to PostgreSQL.

### 8.2 Triggering and dependencies

| Job | Trigger | Dependency | Output |
|---|---|---|---|
| `ingest_reference_and_athlete` | Source delivery | Bronze availability | Athlete Silver |
| `ingest_event_context` | Fixture/event delivery | Athlete keys available | Event Silver |
| `ingest_tracking` | Tracking delivery | Fixture and participant resolution | Tracking Silver |
| `reconcile_match_truth` | Event and tracking completion | Event Silver | Period, state, possession, phase |
| `build_opportunities` | Match truth completion | Tracking and participant Silver | Opportunity facts |
| `build_space_intelligence` | Opportunity completion | Tracking and event facts | Space facts |
| `build_pressing_intelligence` | Opportunity completion | Tracking and event facts | Pressing facts |
| `publish_metrics` | Analytical facts complete | Quality and lineage gates | Gold products |
| `sync_postgresql_contract` | Gold publication | Publication approval | PostgreSQL serving records |

## 9. KPI generation workflow

### 9.1 KPI calculation stages

1. Select the evaluation window and comparison cohort.
2. Select the approved metric version.
3. Resolve eligible opportunities, not only observed actions.
4. Calculate numerator and denominator from Silver facts.
5. Apply minutes, coverage, phase, position, role/roster, and match filters.
6. Calculate confidence, sample size, coverage, and quality status.
7. Persist run metadata and feature/model references.
8. Write Gold metric products.
9. Validate publication thresholds.
10. Publish to dashboards and PostgreSQL serving tables.

### 9.2 KPI families

| KPI family | Example measures | Primary facts |
|---|---|---|
| Player profile | Minutes, starts, participation, role context | Athlete, roster, participant |
| Space creation | Space opportunities, successful creation rate, displacement, receiving benefit, expected-value delta | Opportunity, space, outcome, attribution |
| Pressing | Press opportunities, trigger response, action rate, support rate, bypass rate, recovery rate | Pressing opportunity and child facts |
| Defensive intelligence | Defensive opportunity response, protected-space impact, attribution share | Opportunity, attribution, event/tracking |
| Match analysis | Team opportunity rates, phase distribution, score-state splits, pressing waves | Fixture, state, phase, space, pressing |
| Data quality | Coverage, alignment, reconciliation, evidence-link validity | Quality metadata and source snapshots |

## 10. Feature engineering layer

Feature engineering is implemented as versioned Delta feature sets tied to `analytics.feature_set` and `analytics.calculation_run`. Features are derived only from approved Silver facts.

### 10.1 Feature groups

| Feature group | Example features | Source |
|---|---|---|
| Match context | Period, score state, numerical state, phase, minute, home/away | Match period, state, phase, fixture |
| Player context | Age at fixture, roster status, position, participation duration | Athlete profile, roster, participant |
| Tracking quality | Coverage ratio, frame continuity, coordinate validity | Tracking Bronze/Silver |
| Space geometry | Distance to target zone, open-space area, lane width, defender displacement | Tracking, space baseline |
| Movement | Run duration, speed profile, acceleration, direction change, separation | Tracking and opportunity |
| Space impact | Baseline-to-outcome delta, receiving benefit, expected-value delta | Space baseline, counterfactual, outcome |
| Pressing context | Target participant, approach distance, trigger type, support count, cover relation | Press tables and tracking |
| Pressing outcome | Bypass type, possession change, recovery time, outcome value | Press outcome and possession |
| Event context | Incident proximity, scoring-event proximity, restart state | Event incident and scoring event |
| Evidence | Video availability, locator validity, annotation agreement | Evidence and annotation tables |

### 10.2 Feature engineering controls

- Each feature set has a stable identifier and definition payload.
- Feature values are generated with a calculation run.
- Training and scoring partitions use the same feature definitions and exclusions.
- Missing tracking coverage is represented explicitly; it is not imputed as positive behavior.
- Features derived from unresolved possession or phase intervals retain the uncertainty state.
- Feature publication is blocked when quality thresholds in the BRD are not met.

## 11. Sprint-by-sprint implementation roadmap

The roadmap implements the frozen model and does not introduce redesign work.

### Sprint 1 - Platform foundation and Bronze ingestion

**Deliverables**

- Unity Catalog catalogs and schemas for Bronze, Silver, and Gold.
- Bronze ingestion for athlete and event repository products.
- Source snapshot registration and idempotent ingestion.
- Raw tracking, evidence, and annotation landing contracts.

**Exit criteria**

- Raw source replay works for a representative fixture and athlete cohort.
- Malformed records are quarantined and visible.
- Source snapshot metadata is complete.

### Sprint 2 - Repository-aligned Silver

**Deliverables**

- Silver `athlete` domain tables.
- Silver `event` domain tables.
- Identity and fixture reconciliation.
- Participant, result, incident, and scoring-event conformance.
- PostgreSQL contract synchronization for repository-backed tables.

**Exit criteria**

- All analytical foreign keys resolve to Silver repository-backed keys.
- Duplicate and late-arriving source records are versioned.
- Athlete and event metric-view inputs are queryable.

### Sprint 3 - Match truth and opportunity layer

**Deliverables**

- Match periods and state intervals.
- Possession and phase construction.
- Coordinate/time normalization for tracking.
- Opportunity eligibility and observability facts.

**Exit criteria**

- A complete fixture can be reconstructed by period, score state, possession, and phase.
- Eligible and observed opportunities are separately measurable.
- Unresolved state intervals remain explicitly flagged.

### Sprint 4 - Space intelligence

**Deliverables**

- Space opportunities.
- Space baselines and counterfactuals.
- Space outcomes and attribution ledger.
- Space detail and player profile Gold products.

**Exit criteria**

- Space metrics are calculated from opportunity denominators.
- Counterfactual and baseline references are linked to calculation runs.
- Analyst-facing space records retain evidence references where licensed.

### Sprint 5 - Pressing intelligence

**Deliverables**

- Pressing opportunities.
- Trigger, action, support, bypass, outcome, and recovery facts.
- Pressing player and match Gold products.

**Exit criteria**

- Pressing is measured at opportunity grain, not only distance-to-ball.
- Team and individual pressing outputs can be traced to participant and fixture keys.
- Bypass and recovery outcomes are represented separately.

### Sprint 6 - KPI, feature, and publication layer

**Deliverables**

- Repository-aligned athlete/event metric products.
- Off-ball and pressing KPI products.
- Versioned feature sets.
- Calculation runs, model artifacts, publication gates, and PostgreSQL metric synchronization.

**Exit criteria**

- Published metrics expose numerator, denominator, quality, confidence, coverage, and lineage.
- Re-running a calculation with the same inputs and versions produces the same result.
- Gold products support player, match, recruitment, coach, analyst, and executive dashboard needs.

### Sprint 7 - Evidence, annotation, and operational hardening

**Deliverables**

- Evidence-link serving.
- Annotation task, label, and adjudication workflows.
- Data quality dashboards and replay procedures.
- End-to-end acceptance testing against the BRD thresholds.

**Exit criteria**

- Human validation is linked to analytical targets.
- Evidence links meet the approved alignment threshold.
- The MVM quality thresholds are measured before production publication.

## 12. Frozen-baseline compliance

This implementation blueprint preserves:

- Repository-backed `athlete` and `event` product names and grains.
- Approved `analytics` extension entities.
- PostgreSQL schemas, keys, and lineage objects.
- Delta as the high-volume analytical store.
- Bronze/Silver/Gold separation.
- The approved distinction between repository reuse and review-required additions.

No new PostgreSQL table, entity, relationship, metric family, or domain is introduced by this document.
