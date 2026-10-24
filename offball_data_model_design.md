# Off-Ball Football Intelligence Data Model - Version 2

**Status:** Repository-first refactor  
**Version:** 2.1  
**Primary source:** [Databricks Sports Entertainment MVM](https://github.com/databricks-industry-solutions/lakehouse-industry-data-models/tree/main/data-models/sports_entertainment/v1/mvm)  
**Secondary sources:** [Design Review Report](./archive/offball_design_review_report.md), [Remediation Sprint](./archive/offball_football_analytics_remediation_sprint.md)  
**Scope:** Football analytics extensions over the repository's `athlete` and `event` domains.

## 1. Repository evidence

The repository is a Databricks Unity Catalog MVM organized as domain schemas, metric views, DBML, ontology, and documentation. Its relevant source files are:

| Repository artifact | Evidence used |
|---|---|
| `schemas/sports_entertainment_athlete_schema_v1_mvm.sql` | `athlete_profile`, `roster`, `performance_stat`, `contract`, `eligibility_status`, and related athlete lifecycle entities |
| `schemas/sports_entertainment_event_schema_v1_mvm.sql` | `fixture`, `calendar`, `tournament`, `bracket`, `match_result`, `scoring_event`, `participant`, `event_incident`, `competition_round`, and `type` |
| `metrics/sports_entertainment_athlete_metrics_v1_mvm.sql` | Athlete profile and roster metric-view patterns |
| `metrics/sports_entertainment_event_metrics_v1_mvm.sql` | Match-result, participant, scoring-event, and incident metric-view patterns |
| `diagram/sports_entertainment_dbml_v1_mvm.txt` | Keys, domains, and relationships for the MVM entities |
| `readme.md` | Domain/product inventory, MVM scope, denormalized data-product approach, and output layout |

The repository does **not** explicitly contain football tracking, possession, pressing, off-ball movement, or space-creation entities. Those are therefore retained only where they directly implement an enumerated review finding.

## 2. Repository-first design rules

1. `event.fixture` is the scheduled match anchor; `event.match_result` is the recorded outcome.
2. `athlete.athlete_profile` is the player identity anchor; `athlete.roster` is the time-bounded athlete-team affiliation.
3. `event.participant` links people or teams to an event and is reused for match participation.
4. `event.scoring_event` and `event.event_incident` remain the repository-backed event facts.
5. `athlete.performance_stat` remains the repository-backed performance fact and is extended only with review-backed analytical references.
6. Repository tables are not duplicated as `canonical_*` mirrors.
7. Football-specific truth, space, and pressing objects are remediation additions, not claimed repository entities.
8. Databricks Delta data products remain authoritative for high-volume analytical facts; PostgreSQL contains the relational application and curated extension contract.

## 3. Component traceability matrix

| Component | Repository Based | Repository Extended | New Remediation Addition |
|---|---|---|---|
| Athlete identity | `athlete.athlete_profile` | Add stable source-record/version metadata only | No |
| Player-team affiliation | `athlete.roster` | Add football position/role references only where required by HR-005 | No |
| Player performance | `athlete.performance_stat` | Add metric-definition/run references for CR-005 | No |
| Contract and eligibility | `athlete.contract`, `athlete.eligibility_status` | Preserve repository grain; no new recruitment-market model | No |
| Scheduled match | `event.fixture` | Add analytical match key and source version | No |
| Match outcome | `event.match_result` | Add score-state linkage required by HR-001 | No |
| Match participants | `event.participant` | Add lineup interval and team/player role context | No |
| Match incidents | `event.event_incident` | Add event-provider reconciliation metadata for HR-002 | No |
| Scoring events | `event.scoring_event` | Link to possession/phase where available | No |
| Competition context | `event.calendar`, `event.tournament`, `event.competition_round`, `event.type` | No duplicate competition hierarchy | No |
| Athlete/event metrics | Repository metric views | Add reproducible calculation-run and source-snapshot references | No |
| Football truth layer | No direct repository entity | Reuses fixture, result, participant, incident, scoring event | Yes - HR-001/HR-002 |
| Possession and phase | No direct repository entity | Uses event facts as evidence | Yes - HR-002 |
| Space opportunities | No direct repository entity | Uses participant, event, and performance facts as anchors | Yes - CR-004 |
| Pressing intelligence | No direct repository entity | Uses participant, event, and performance facts as anchors | Yes - HR-003 |
| Defensive attribution | No direct repository entity | Uses participant and tactical evidence | Yes - HR-004 |
| Metric lineage | Metric views are repository based | Adds run, source snapshot, feature-set, and publication objects | Yes - CR-005 |
| Annotation governance | No direct repository entity | Links labels to repository-backed events | Yes - HR-007 |
| Video lifecycle | No direct repository entity | Evidence link is limited to review-backed analytical evidence | Yes - HR-008 |

## 4. Domain model

### Repository domains

- **Athlete:** `athlete_profile`, `roster`, `performance_stat`, `contract`, and `eligibility_status`.
- **Event:** `fixture`, `calendar`, `tournament`, `bracket`, `competition_round`, `type`, `participant`, `match_result`, `scoring_event`, and `event_incident`.
- **Metrics:** repository metric views over athlete and event data.

### Remediation extensions

The extensions are deliberately narrow:

- **Football truth:** `match_period`, `match_state_interval`, `possession_sequence`, `phase_interval`, `lineup_segment`, and `field_orientation`.
- **Space:** `opportunity`, `space_opportunity`, `space_baseline`, `space_counterfactual`, `space_outcome`, and `attribution_ledger`.
- **Pressing:** `pressing_opportunity`, `press_trigger`, `press_action`, `press_support`, `press_bypass`, `press_outcome`, and `recovery_action`.
- **Reproducibility:** `source_snapshot`, `calculation_run`, `feature_set`, `model_artifact`, and `metric_publication`.
- **Evidence and review:** `evidence_link`, `annotation_task`, `annotation_label`, and `annotation_adjudication`.

No V2 entity is retained solely because it was present in the prior generated design. Unsupported `canonical_*` mirrors, organisation/club SaaS tables, and speculative recruitment-market objects are removed from the repository-first model.

## 5. Logical model and grains

| Entity | Grain | Repository anchor | Purpose |
|---|---|---|---|
| `fixture` | One scheduled event | `event.fixture` | Match identity and schedule |
| `match_result` | One recorded fixture result | `event.match_result` | Outcome and score |
| `participant` | One entity participating in a fixture | `event.participant` | Team/player/event participation |
| `athlete_profile` | One athlete | `athlete.athlete_profile` | Player identity |
| `roster` | One athlete-team-season affiliation | `athlete.roster` | Eligibility and team context |
| `performance_stat` | One athlete performance record | `athlete.performance_stat` | Repository performance fact |
| `match_period` | One period within a fixture | `fixture` | Review-backed temporal context |
| `match_state_interval` | One continuous score/game-state interval | `fixture`, `match_result` | HR-001 |
| `possession_sequence` | One canonical possession sequence | `fixture`, `event_incident` | HR-002 |
| `phase_interval` | One phase interval | `possession_sequence` | HR-002 |
| `opportunity` | One eligible analytical situation | `fixture`, `participant` | CR-004 and HR-003 |
| `space_opportunity` | One space-creation opportunity | `opportunity`, `participant` | CR-004 |
| `pressing_opportunity` | One pressing opportunity | `opportunity`, `participant` | HR-003 |
| `metric_value` | One metric for one entity/window/run | `performance_stat`, `calculation_run` | CR-005 |

## 6. Physical and lakehouse architecture

The repository's physical pattern is retained: domain schemas and denormalized metric views in Databricks Unity Catalog.

- **Bronze:** immutable source extracts for repository-aligned `event` and `athlete` products plus tracking/event-provider feeds.
- **Silver:** repository-shaped `athlete` and `event` tables, then remediation extension tables reconciled to fixture, athlete, roster, participant, incident, and scoring-event keys.
- **Gold:** denormalized athlete/event metric views and new off-ball/pressing data products. Gold products must expose source snapshot, calculation run, metric version, quality status, and publication status.

High-volume tracking frames and event observations remain Delta tables. PostgreSQL stores the curated contract, review workflow, lineage metadata, and low-volume operational records.

## 7. Repository-aligned ERD

<!-- mermaid-checked: every attribute is `<type> <name> [<key>] ["<description>"]` with at most one of PK/FK/UK, no \n in descriptions, no {} in descriptions, every relationship label is double-quoted -->
~~~mermaid
erDiagram
    ATHLETE_PROFILE ||--o{ ROSTER : "has roster records"
    ATHLETE_PROFILE ||--o{ PERFORMANCE_STAT : "has performance facts"
    FIXTURE ||--o{ PARTICIPANT : "has participants"
    FIXTURE ||--|| MATCH_RESULT : "has result"
    FIXTURE ||--o{ EVENT_INCIDENT : "has incidents"
    FIXTURE ||--o{ SCORING_EVENT : "has scoring events"
    FIXTURE ||--o{ OPPORTUNITY : "anchors opportunities"
    PARTICIPANT }o--|| ATHLETE_PROFILE : "identifies athlete"
    OPPORTUNITY ||--o{ SPACE_OPPORTUNITY : "classifies space"
    OPPORTUNITY ||--o{ PRESSING_OPPORTUNITY : "classifies pressing"
    FIXTURE ||--o{ MATCH_PERIOD : "has periods"
    MATCH_PERIOD ||--o{ MATCH_STATE_INTERVAL : "contains states"
    ATHLETE_PROFILE {
        bigint athlete_profile_id PK
        string preferred_name
        date date_of_birth
    }
    ROSTER {
        bigint roster_id PK
        bigint athlete_profile_id FK
        bigint season_id FK
        bigint franchise_id FK
    }
    PERFORMANCE_STAT {
        bigint performance_stat_id PK
        bigint athlete_profile_id FK
        bigint fixture_id FK
        string statistic_type
    }
    FIXTURE {
        bigint fixture_id PK
        bigint season_id FK
        bigint competition_round_id FK
        timestamp actual_start_timestamp
    }
    PARTICIPANT {
        bigint participant_id PK
        bigint fixture_id FK
        bigint athlete_profile_id FK
        string participant_role
    }
    MATCH_RESULT {
        bigint match_result_id PK
        bigint fixture_id FK
        string result_status
    }
    EVENT_INCIDENT {
        bigint event_incident_id PK
        bigint fixture_id FK
        string incident_type
    }
    SCORING_EVENT {
        bigint scoring_event_id PK
        bigint fixture_id FK
        bigint participant_id FK
        string scoring_type
    }
    OPPORTUNITY {
        bigint opportunity_id PK
        bigint fixture_id FK
        bigint participant_id FK
        string opportunity_type
    }
    SPACE_OPPORTUNITY {
        bigint space_opportunity_id PK
        bigint opportunity_id FK
        bigint participant_id FK
        string space_type
    }
    PRESSING_OPPORTUNITY {
        bigint pressing_opportunity_id PK
        bigint opportunity_id FK
        bigint participant_id FK
        string press_type
    }
    MATCH_PERIOD {
        bigint match_period_id PK
        bigint fixture_id FK
        string period_type
    }
    MATCH_STATE_INTERVAL {
        bigint match_state_interval_id PK
        bigint match_period_id FK
        string score_state
    }
~~~

## 8. MVM acceptance gates

1. Every V2 athlete and event foreign key resolves to a repository-backed key.
2. No `canonical_*` mirror duplicates a repository entity.
3. Every space and pressing record has a fixture and participant/opportunity anchor.
4. Every published metric has a source snapshot, calculation run, metric version, and publication record.
5. Repository-backed tables preserve the repository names and domain boundaries.
6. Unsupported prior V2 objects are absent or explicitly documented as deferred.
