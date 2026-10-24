# Sprint 3 Gold Layer Implementation Plan

**Sprint:** 3 - Gold metrics, marts, and dashboard-serving products  
**Status:** Implementation plan  
**Precondition:** Approved Silver Layer implementation is deployed and producing conformed Silver facts  
**Scope:** Gold Delta tables, KPI aggregates, team/player/match marts, executive datasets, dashboard-serving tables, notebooks, jobs, and acceptance evidence  
**Out of scope:** Audits, reviews, remediation analysis, architecture redesign, Bronze/Silver redesign, PostgreSQL schema changes, and new analytical entities

## 1. Sprint objective

Build the governed Gold layer over the approved Silver tables. Gold publishes stable, denormalized, consumption-ready products for coaches, analysts, recruitment users, executives, and dashboards.

Gold products must:

- Use Silver only as their analytical source.
- Preserve source snapshot, transformation/calculation run, metric version, quality status, and publication status.
- Separate denominators from numerators and expose sample size and coverage.
- Publish both detailed review products and aggregated KPI marts.
- Exclude quarantined, unresolved, and invalid Silver facts according to each metric’s quality policy.
- Be idempotent for batch, incremental, correction, and replay processing.
- Never write Bronze or Silver tables.

## 2. Frozen implementation constraints

1. Use the existing `silver.athlete`, `silver.event`, and `silver.analytics` tables as the only Gold inputs.
2. Preserve approved repository domain boundaries.
3. Do not create new business entities or alter Silver grains.
4. Do not modify the approved PostgreSQL schema.
5. Do not publish a KPI without a metric code, metric version, denominator policy, quality status, and lineage.
6. Do not silently convert missing tracking or unresolved analytical facts into confirmed performance.
7. Do not publish rows with `quality_status = 'quarantined'`.
8. Retain zero-denominator outcomes as explicit `not_available` or `insufficient_sample`, not zero performance.
9. All dashboard-serving tables must be reproducible from Gold detail or aggregate products.
10. All Gold jobs must be retry-safe and use deterministic merge keys.

## 3. Gold requirement register

| ID | Requirement |
|---|---|
| REQ-001 | Create approved Gold schemas, table contracts, and deployment resources. |
| REQ-002 | Publish repository-aligned athlete and event KPI tables. |
| REQ-003 | Publish team analytics marts at fixture, competition, season, and evaluation-window grains. |
| REQ-004 | Publish player analytics marts at athlete, team, season, role, and evaluation-window grains. |
| REQ-005 | Publish match analytics marts at fixture and team-participant grains. |
| REQ-006 | Publish space-creation KPIs with explicit eligible, observed, successful, and coverage denominators. |
| REQ-007 | Publish pressing KPIs with opportunity, action, support, bypass, recovery, and outcome measures. |
| REQ-008 | Publish attribution KPIs with bounded attribution shares and evidence status. |
| REQ-009 | Publish executive reporting datasets with stable business dimensions and trend periods. |
| REQ-010 | Publish dashboard-serving detail and aggregate tables with predictable filters and refresh metadata. |
| REQ-011 | Apply metric definitions, versions, denominator rules, quality filters, and suppression rules consistently. |
| REQ-012 | Preserve source snapshot, ingestion attempt, transformation run, calculation run, and publication lineage. |
| REQ-013 | Support idempotent Gold rebuilds for selected fixtures, windows, teams, and athletes. |
| REQ-014 | Build dependency-ordered Gold jobs with retry-safe task boundaries. |
| REQ-015 | Publish operational metrics for input, output, suppressed, insufficient-sample, and failed calculations. |
| REQ-016 | Validate Gold keys, metric ranges, denominators, quality status, lineage, and freshness. |
| REQ-017 | Produce reproducible Sprint 3 delivery evidence and acceptance results. |

## 4. Gold common publication contract

Every Gold metric or mart row must include, where applicable:

```text
metric_code
metric_version
evaluation_window_type
evaluation_window_start
evaluation_window_end
fixture_id
athlete_profile_id
participant_id
franchise_id
season_id
competition_id
numerator
denominator
metric_value
sample_size
coverage_ratio
confidence
quality_status
quality_reason
source_snapshot_id
ingestion_attempt_id
transformation_run_id
calculation_run_id
publication_status
published_at
refreshed_at
```

Nullable entity keys are permitted according to table grain. A row must not claim a dimension that is unavailable.

### 4.1 Metric status values

```text
published
published_with_warning
insufficient_sample
not_available
suppressed
failed
```

### 4.2 Denominator policy

- `denominator = 0` never produces a numeric `metric_value`.
- Ratios use `metric_value = NULL` and `quality_status = 'insufficient_sample'` when the denominator is below the metric threshold.
- Coverage is calculated as valid observed evidence divided by eligible evidence.
- Missing tracking coverage is reported separately from zero performance.
- Suppressed values retain numerator, denominator, suppression reason, and lineage where policy permits.

## 5. Gold table inventory

### 5.1 KPI foundation tables

| Table | Grain | Main inputs | Purpose |
|---|---|---|---|
| `gold.quality.metric_definition` | One metric definition/version | Configuration and code registry | Metric code, formula, denominator policy, threshold, owner |
| `gold.quality.calculation_run` | One Gold calculation run | Silver transformation metadata | Run status, input scope, code version, timestamps |
| `gold.quality.metric_publication` | One published product/run | Calculation run | Publication state and freshness |
| `gold.quality.metric_value` | One entity/window/metric/run | All Gold KPI calculations | Reusable metric fact |
| `gold.quality.data_freshness` | One product/refresh window | Gold jobs | Last successful refresh, lag, status |
| `gold.quality.metric_exception` | One suppressed or failed metric | KPI calculations | Explicit reason and lineage |

### 5.2 Repository-aligned KPI tables

| Table | Grain | KPI content |
|---|---|---|
| `gold.athlete.athlete_profile_metrics` | Athlete and evaluation window | Active status, roster continuity, source completeness |
| `gold.athlete.roster_metrics` | Athlete-team-season window | Starts, appearances, active days, eligibility coverage |
| `gold.event.match_result_metrics` | Fixture | Score, result state, result completeness, provider agreement |
| `gold.event.participant_metrics` | Fixture participant | Participation duration/status and event involvement |
| `gold.event.scoring_event_metrics` | Fixture/scoring type | Goals or scoring-event counts and rates |
| `gold.event.incident_metrics` | Fixture/incident type | Incident counts, timing, and source quality |

### 5.3 Team analytics marts

| Table | Grain | Main measures |
|---|---|---|
| `gold.team.match_summary` | Team-fixture | Result, score, participation, possession/phase coverage |
| `gold.team.performance_window` | Team-evaluation window | Event rates, opportunity rates, pressing, space, attribution |
| `gold.team.space_creation_profile` | Team-window-space type | Eligible, observed, successful, value delta, coverage |
| `gold.team.pressing_profile` | Team-window-press type | Opportunities, actions, support, bypass, recoveries, outcomes |
| `gold.team.attribution_profile` | Team-window-attribution type | Attributed share, contributors, evidence coverage |
| `gold.team.competition_summary` | Team-competition-season | Fixture totals, trend metrics, quality/freshness |

### 5.4 Player analytics marts

| Table | Grain | Main measures |
|---|---|---|
| `gold.player.match_summary` | Athlete-fixture | Participation, events, opportunities, space, pressing, attribution |
| `gold.player.performance_window` | Athlete-evaluation window | Per-90 and rate metrics with denominator exposure |
| `gold.player.offball_profile` | Athlete-window-role | Movement, space creation, opportunity conversion |
| `gold.player.space_creation_profile` | Athlete-window-space type | Eligible, observed, successful, value delta, confidence |
| `gold.player.pressing_profile` | Athlete-window-press type | Press opportunity conversion, support, bypass, recovery |
| `gold.player.defensive_attribution` | Athlete-window-attribution type | Attribution shares and evidence |
| `gold.player.comparison` | Cohort-window-role | Percentile/rank outputs with cohort definition |

### 5.5 Match analytics marts

| Table | Grain | Main measures |
|---|---|---|
| `gold.match.match_summary` | Fixture | Result, score, periods, state intervals, possessions, phases |
| `gold.match.team_summary` | Fixture-team | Team event, space, pressing, recovery, attribution measures |
| `gold.match.player_summary` | Fixture-participant | Player involvement and contribution measures |
| `gold.match.space_opportunity_detail` | Space opportunity | Evidence, baseline, outcome, attribution, quality |
| `gold.match.press_opportunity_detail` | Press opportunity | Trigger, action, support, bypass, outcome, recovery |
| `gold.match.timeline` | Fixture-time bucket | State, possession, phase, incidents, scoring, KPI events |

### 5.6 Executive reporting datasets

| Table | Grain | Consumer |
|---|---|---|
| `gold.executive.club_overview` | Club/season/reporting period | Executive dashboard |
| `gold.executive.performance_trends` | Club/team/period/metric | Trend reporting |
| `gold.executive.player_pipeline` | Athlete/cohort/reporting period | Recruitment and leadership |
| `gold.executive.match_outcomes` | Fixture/reporting period | Executive match reporting |
| `gold.executive.data_health` | Product/reporting period | Operational leadership |

### 5.7 Dashboard-serving tables

| Table | Grain | Serving behavior |
|---|---|---|
| `gold.dashboard.player_overview` | Athlete/window | One-row player summary for filters and cards |
| `gold.dashboard.team_overview` | Team/window | One-row team summary |
| `gold.dashboard.match_overview` | Fixture | One-row match summary |
| `gold.dashboard.space_pressing_overview` | Fixture/team/player/window | Combined off-ball KPI cards |
| `gold.dashboard.kpi_timeseries` | Dimension/metric/time bucket | Chart-ready time series |
| `gold.dashboard.filter_dimensions` | Dimension/value | Stable dashboard filters and labels |

## 6. KPI definitions

### 6.1 Space-creation KPIs

Compute from `silver.analytics.opportunity`, `space_opportunity`, `space_baseline`, `space_counterfactual`, `space_outcome`, and `attribution_ledger`.

Required measures:

- Eligible opportunities
- Observed opportunities
- Observation rate
- Successful space outcomes
- Space conversion rate
- Mean and total expected-value delta
- Baseline coverage
- Counterfactual coverage
- Tracking coverage
- Attribution share
- Confidence-weighted success
- Insufficient-sample indicator

### 6.2 Pressing KPIs

Compute from `pressing_opportunity`, `press_trigger`, `press_action`, `press_support`, `press_bypass`, `press_outcome`, and `recovery_action`.

Required measures:

- Pressing opportunities
- Triggered opportunities
- Action completion rate
- Support involvement rate
- Bypass rate
- Recovery rate
- Positive outcome rate
- Time-to-action where timestamps exist
- Confidence and tracking coverage
- Unresolved opportunity rate
- Per-90 and per-opportunity rates where exposure exists

### 6.3 Attribution KPIs

Compute from `attribution_ledger` joined to space and pressing outcomes.

Required measures:

- Total attribution share
- Mean attribution share
- Opportunity contribution count
- Positive-outcome contribution share
- Attribution completeness
- Evidence-linked attribution ratio
- Confidence-weighted attribution
- Unresolved attribution count

### 6.4 Normalization rules

- Per-90 uses valid participation minutes as the exposure denominator.
- Per-opportunity uses eligible opportunity count.
- Team totals are calculated from detail facts, not sums of already rounded player rates.
- Percentiles use a declared cohort, role, season, and minimum sample threshold.
- Aggregates retain raw numerator and denominator for reproducibility.
- All KPI code is versioned through `metric_code`, `metric_version`, and `calculation_run_id`.

## 7. Gold notebook structure

Create notebooks under `databricks/notebooks/gold/`.

### 7.1 Shared Gold notebooks

| Notebook | Responsibility |
|---|---|
| `00_gold_runtime_config.py` | Gold scope, run mode, evaluation windows, catalog/schema, publication controls |
| `01_gold_helpers.py` | Metric projection, safe ratios, deterministic MERGE, lineage, refresh metadata |
| `02_metric_registry_helpers.py` | Metric definitions, versions, thresholds, denominator policies |
| `03_publication_helpers.py` | Calculation-run lifecycle, publication status, freshness, exceptions |
| `04_aggregate_helpers.py` | Windowing, per-90 normalization, percentiles, cohort filters |

### 7.2 KPI foundation notebooks

| Notebook | Targets |
|---|---|
| `05_register_calculation_run.py` | `gold.quality.calculation_run` |
| `06_publish_metric_definitions.py` | `gold.quality.metric_definition` |
| `07_finalize_metric_publication.py` | `gold.quality.metric_publication`, freshness, exceptions |

### 7.3 Repository KPI notebooks

| Notebook | Targets |
|---|---|
| `10_build_athlete_profile_metrics.py` | `gold.athlete.athlete_profile_metrics` |
| `11_build_roster_metrics.py` | `gold.athlete.roster_metrics` |
| `20_build_match_result_metrics.py` | `gold.event.match_result_metrics` |
| `21_build_participant_metrics.py` | `gold.event.participant_metrics` |
| `22_build_scoring_event_metrics.py` | `gold.event.scoring_event_metrics` |
| `23_build_incident_metrics.py` | `gold.event.incident_metrics` |

### 7.4 Team, player, and match marts

| Notebook | Targets |
|---|---|
| `30_build_team_match_summary.py` | `gold.team.match_summary` |
| `31_build_team_performance_window.py` | `gold.team.performance_window` |
| `32_build_team_space_creation_profile.py` | `gold.team.space_creation_profile` |
| `33_build_team_pressing_profile.py` | `gold.team.pressing_profile` |
| `34_build_team_attribution_profile.py` | `gold.team.attribution_profile` |
| `35_build_team_competition_summary.py` | `gold.team.competition_summary` |
| `40_build_player_match_summary.py` | `gold.player.match_summary` |
| `41_build_player_performance_window.py` | `gold.player.performance_window` |
| `42_build_player_offball_profile.py` | `gold.player.offball_profile` |
| `43_build_player_space_creation_profile.py` | `gold.player.space_creation_profile` |
| `44_build_player_pressing_profile.py` | `gold.player.pressing_profile` |
| `45_build_player_defensive_attribution.py` | `gold.player.defensive_attribution` |
| `46_build_player_comparison.py` | `gold.player.comparison` |
| `50_build_match_summary.py` | `gold.match.match_summary` |
| `51_build_match_team_summary.py` | `gold.match.team_summary` |
| `52_build_match_player_summary.py` | `gold.match.player_summary` |
| `53_build_space_opportunity_detail.py` | `gold.match.space_opportunity_detail` |
| `54_build_press_opportunity_detail.py` | `gold.match.press_opportunity_detail` |
| `55_build_match_timeline.py` | `gold.match.timeline` |

### 7.5 Executive and dashboard notebooks

| Notebook | Targets |
|---|---|
| `60_build_club_overview.py` | `gold.executive.club_overview` |
| `61_build_performance_trends.py` | `gold.executive.performance_trends` |
| `62_build_player_pipeline.py` | `gold.executive.player_pipeline` |
| `63_build_match_outcomes.py` | `gold.executive.match_outcomes` |
| `64_build_data_health.py` | `gold.executive.data_health` |
| `70_build_player_overview.py` | `gold.dashboard.player_overview` |
| `71_build_team_overview.py` | `gold.dashboard.team_overview` |
| `72_build_match_overview.py` | `gold.dashboard.match_overview` |
| `73_build_space_pressing_overview.py` | `gold.dashboard.space_pressing_overview` |
| `74_build_kpi_timeseries.py` | `gold.dashboard.kpi_timeseries` |
| `75_build_filter_dimensions.py` | `gold.dashboard.filter_dimensions` |

### 7.6 Validation notebook

| Notebook | Responsibility |
|---|---|
| `95_validate_gold_contracts.py` | Schema, metric, denominator, range, lineage, freshness, publication, and no-Silver-write checks |

## 8. Gold job definitions

Create `databricks/resources/gold_jobs.yml`.

### Job 1: `offball_s3_gold_kpi_foundation`

```text
create_gold_operational_tables
  -> register_calculation_run
  -> publish_metric_definitions
```

### Job 2: `offball_s3_gold_repository_kpis`

Depends on KPI foundation:

```text
athlete_profile_metrics
roster_metrics
match_result_metrics
participant_metrics
scoring_event_metrics
incident_metrics
  -> finalize_repository_publication
```

### Job 3: `offball_s3_gold_team_marts`

Depends on repository KPI completion:

```text
team_match_summary
  -> team_performance_window
  -> team_space_creation_profile
  -> team_pressing_profile
  -> team_attribution_profile
  -> team_competition_summary
```

### Job 4: `offball_s3_gold_player_marts`

Depends on repository KPI completion:

```text
player_match_summary
  -> player_performance_window
  -> player_offball_profile
  -> player_space_creation_profile
  -> player_pressing_profile
  -> player_defensive_attribution
  -> player_comparison
```

### Job 5: `offball_s3_gold_match_marts`

Depends on repository KPI completion and Silver analytical facts:

```text
match_summary
  -> match_team_summary
  -> match_player_summary
  -> space_opportunity_detail
  -> press_opportunity_detail
  -> match_timeline
```

### Job 6: `offball_s3_gold_executive_dashboard`

Depends on team, player, and match marts:

```text
club_overview
performance_trends
player_pipeline
match_outcomes
data_health
  -> player_overview
  -> team_overview
  -> match_overview
  -> space_pressing_overview
  -> kpi_timeseries
  -> filter_dimensions
  -> finalize_metric_publication
  -> validate_gold_contracts
```

All Gold jobs must:

- Use the existing Bundle target variables and Unity Catalog.
- Pass `source_snapshot_id`, `transformation_run_id`, `calculation_run_id`, evaluation window, and metric version.
- Use deterministic merge keys.
- Publish task-level input, output, suppression, insufficient-sample, and exception metrics.
- Fail the publication gate when critical validation fails.
- Never write Bronze, Silver, or PostgreSQL.

## 9. Business and publication rules

### 9.1 Quality filters

Include only Silver rows with:

- `quality_status IN ('valid', 'valid_with_warning', 'conflict_selected')`
- `is_current = true` where the Silver table supports versioning
- Required fixture, athlete, participant, and opportunity references resolved
- Confidence and coverage meeting the metric’s declared threshold

Keep excluded rows in metric exceptions or data-health outputs with explicit reasons.

### 9.2 Freshness

Every published product records:

- Latest input Silver transformation timestamp
- Gold calculation start/completion
- Data lag
- Expected refresh interval
- Freshness status

### 9.3 Rebuild scope

Every Gold notebook accepts:

```text
run_mode
source_snapshot_id
transformation_run_id
evaluation_window_start
evaluation_window_end
fixture_id
athlete_profile_id
franchise_id
season_id
metric_version
```

Unspecified filters process the configured default evaluation window.

## 10. Implementation phases and tasks

### Phase 1 - Gold foundation

- [ ] T001 [Plan:1.1] Add Gold table contracts, schema metadata, and product properties in `databricks/resources/gold_tables.yml`.
- [ ] T002 [P] [Plan:1.1] Add Gold job definitions in `databricks/resources/gold_jobs.yml`.
- [ ] T003 [P] [Plan:1.1] Add Gold notebook folder structure under `databricks/notebooks/gold/`.
- [ ] T004 [Plan:1.1] Add Gold configuration in `databricks/configuration/gold_test.yml`.
- [ ] T005 [Plan:1.2] Implement `databricks/notebooks/gold/00_gold_runtime_config.py`.
- [ ] T006 [P] [Plan:1.2] Implement `databricks/notebooks/gold/01_gold_helpers.py` with safe ratios, deterministic keys, Delta MERGE, and lineage.
- [ ] T007 [P] [Plan:1.2] Implement `databricks/notebooks/gold/02_metric_registry_helpers.py`.
- [ ] T008 [P] [Plan:1.2] Implement `databricks/notebooks/gold/03_publication_helpers.py`.
- [ ] T009 [P] [Plan:1.2] Implement `databricks/notebooks/gold/04_aggregate_helpers.py`.
- [ ] T010 [Plan:1.2] Implement `05_register_calculation_run.py`, `06_publish_metric_definitions.py`, and `07_finalize_metric_publication.py`.

### Phase 2 - Repository KPI products

- [ ] T011 [P] [Plan:2.1] Implement `10_build_athlete_profile_metrics.py` and `11_build_roster_metrics.py`.
- [ ] T012 [P] [Plan:2.1] Implement `20_build_match_result_metrics.py`, `21_build_participant_metrics.py`, `22_build_scoring_event_metrics.py`, and `23_build_incident_metrics.py`.
- [ ] T013 [Plan:2.2] Add repository KPI metric definitions, thresholds, denominator rules, and publication lineage.

### Phase 3 - Team analytics marts

- [ ] T014 [P] [Plan:3.1] Implement `30_build_team_match_summary.py` and `31_build_team_performance_window.py`.
- [ ] T015 [P] [Plan:3.1] Implement `32_build_team_space_creation_profile.py`, `33_build_team_pressing_profile.py`, and `34_build_team_attribution_profile.py`.
- [ ] T016 [Plan:3.1] Implement `35_build_team_competition_summary.py`.

### Phase 4 - Player analytics marts

- [ ] T017 [P] [Plan:4.1] Implement `40_build_player_match_summary.py` and `41_build_player_performance_window.py`.
- [ ] T018 [P] [Plan:4.1,4.2] Implement `42_build_player_offball_profile.py` and `43_build_player_space_creation_profile.py`.
- [ ] T019 [P] [Plan:4.1,4.2] Implement `44_build_player_pressing_profile.py` and `45_build_player_defensive_attribution.py`.
- [ ] T020 [Plan:4.2] Implement `46_build_player_comparison.py` with declared cohort, role, and minimum-sample rules.

### Phase 5 - Match marts and off-ball KPIs

- [ ] T021 [P] [Plan:5.1] Implement `50_build_match_summary.py`, `51_build_match_team_summary.py`, and `52_build_match_player_summary.py`.
- [ ] T022 [P] [Plan:5.2] Implement `53_build_space_opportunity_detail.py` and `54_build_press_opportunity_detail.py`.
- [ ] T023 [Plan:5.2] Implement `55_build_match_timeline.py`.
- [ ] T024 [Plan:5.3] Validate space KPIs, pressing KPIs, attribution KPIs, coverage, confidence, and denominator behavior.

### Phase 6 - Executive and dashboard products

- [ ] T025 [P] [Plan:6.1] Implement `60_build_club_overview.py`, `61_build_performance_trends.py`, and `62_build_player_pipeline.py`.
- [ ] T026 [P] [Plan:6.1] Implement `63_build_match_outcomes.py` and `64_build_data_health.py`.
- [ ] T027 [P] [Plan:6.2] Implement `70_build_player_overview.py`, `71_build_team_overview.py`, and `72_build_match_overview.py`.
- [ ] T028 [P] [Plan:6.2] Implement `73_build_space_pressing_overview.py`, `74_build_kpi_timeseries.py`, and `75_build_filter_dimensions.py`.

### Phase 7 - Jobs, validation, and delivery

- [ ] T029 [Plan:7.1] Implement `95_validate_gold_contracts.py`.
- [ ] T030 [Plan:7.1] Wire all Gold notebooks into dependency-ordered Asset Bundle jobs.
- [ ] T031 [Plan:7.2] Execute full-window, fixture-scoped, athlete-scoped, retry, replay, correction, and insufficient-sample runs.
- [ ] T032 [Plan:7.2,7.3] Produce Gold row-count, KPI, denominator, lineage, freshness, publication, and exception evidence.
- [ ] T033 [Plan:7.3] Complete Sprint 3 acceptance sign-off without deploying later-sprint features.

## 11. Sprint deliverables

### Configuration and resources

- `databricks/resources/gold_tables.yml`
- `databricks/resources/gold_jobs.yml`
- `databricks/configuration/gold_test.yml`
- Gold Bundle target variables and publication controls

### Gold notebooks

- Shared runtime, metric, publication, and aggregation helpers
- Calculation-run and metric-definition notebooks
- Repository KPI notebooks
- Team, player, and match mart notebooks
- Space, pressing, and attribution KPI notebooks
- Executive reporting notebooks
- Dashboard-serving notebooks
- Gold contract validation notebook

### Gold data products

- Repository-aligned KPI tables
- Team analytics marts
- Player analytics marts
- Match analytics marts
- Space-creation KPI products
- Pressing KPI products
- Attribution KPI products
- Executive reporting datasets
- Dashboard-serving tables
- Metric, publication, freshness, and exception outputs

### Delivery evidence

- Gold schema and table inventory
- Source-to-Gold lineage report
- KPI definition/version registry
- Numerator/denominator validation report
- Quality and suppression report
- Freshness and publication report
- Retry/rebuild evidence
- Sprint 3 acceptance report

## 12. Acceptance criteria

| ID | Acceptance criterion | Evidence |
|---|---|---|
| S3-AC-01 | Gold schemas, contracts, and jobs are deployed in the test target | Bundle deployment output and table inventory |
| S3-AC-02 | Every Gold product contains metric version, quality status, refresh timestamp, and lineage | Automated Gold schema report |
| S3-AC-03 | Repository-aligned athlete and event KPI tables match their approved grains | KPI grain and row-count report |
| S3-AC-04 | Team marts publish fixture, competition, season, and evaluation-window aggregates | Team mart samples and aggregate reconciliation |
| S3-AC-05 | Player marts publish match, window, role, comparison, space, pressing, and attribution outputs | Player mart report |
| S3-AC-06 | Match marts publish fixture, team, player, timeline, space-detail, and press-detail products | Match mart report |
| S3-AC-07 | Space KPIs expose eligible, observed, successful, coverage, confidence, and denominator fields | Space KPI validation |
| S3-AC-08 | Pressing KPIs expose opportunity, action, support, bypass, recovery, outcome, and coverage fields | Pressing KPI validation |
| S3-AC-09 | Attribution KPIs enforce share bounds and expose evidence-linked coverage | Attribution validation |
| S3-AC-10 | Executive datasets provide stable reporting-period dimensions and freshness status | Executive dataset report |
| S3-AC-11 | Dashboard-serving tables support declared filter dimensions and time-series queries | Dashboard query samples |
| S3-AC-12 | Zero denominators produce explicit non-published or insufficient-sample status, never false zero performance | Denominator test output |
| S3-AC-13 | Quarantined, unresolved, and below-threshold Silver facts are excluded or explicitly represented in exceptions | Quality filter report |
| S3-AC-14 | Fixture-, athlete-, team-, and window-scoped rebuilds are deterministic and idempotent | Rebuild comparison |
| S3-AC-15 | Every published metric is linked to source snapshot, transformation run, calculation run, metric version, and publication record | Lineage query |
| S3-AC-16 | Gold jobs publish input, output, suppression, insufficient-sample, exception, and freshness metrics | Job evidence |
| S3-AC-17 | No Sprint 3 job writes Bronze, Silver, or PostgreSQL | Bundle configuration and catalog audit |
| S3-AC-18 | Gold validation passes all critical schema, metric, denominator, lineage, freshness, and publication gates | `95_validate_gold_contracts.py` output |

## 13. Requirement mapping

| REQ ID | Description | Plan items | Implementation evidence |
|---|---|---|---|
| REQ-001 | Gold schemas, contracts, and resources | 1.1 | `gold_tables.yml`, Bundle resources |
| REQ-002 | Repository KPI tables | 2.1, 2.2 | Notebooks 10-23 |
| REQ-003 | Team marts | 3.1 | Notebooks 30-35 |
| REQ-004 | Player marts | 4.1, 4.2 | Notebooks 40-46 |
| REQ-005 | Match marts | 5.1, 5.2 | Notebooks 50-55 |
| REQ-006 | Space KPIs | 5.2, 5.3 | Space profile/detail notebooks |
| REQ-007 | Pressing KPIs | 5.2, 5.3 | Pressing profile/detail notebooks |
| REQ-008 | Attribution KPIs | 3.1, 4.2, 5.3 | Attribution profile and validation |
| REQ-009 | Executive datasets | 6.1 | Notebooks 60-64 |
| REQ-010 | Dashboard-serving tables | 6.2 | Notebooks 70-75 |
| REQ-011 | Metric definitions and denominator rules | 1.2, 2.2, 5.3 | Metric registry and aggregation helpers |
| REQ-012 | Gold lineage and publication contract | 1.2, 7.1 | Publication helpers and validation |
| REQ-013 | Idempotent scoped rebuilds | 1.2, 7.2 | Gold merge helpers and rebuild evidence |
| REQ-014 | Gold jobs | 1.1, 7.1 | `gold_jobs.yml` |
| REQ-015 | Operational metrics | 1.2, 7.1 | Calculation-run, freshness, and exception outputs |
| REQ-016 | Gold validation | 7.1 | `95_validate_gold_contracts.py` |
| REQ-017 | Delivery evidence | 7.2, 7.3 | Sprint 3 acceptance report |
