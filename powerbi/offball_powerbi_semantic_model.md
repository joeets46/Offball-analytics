# Off-Ball Power BI Semantic Model

**Status:** Approved Gold-layer serving design  
**Source:** Sprint 3 Gold products in `offball_sprint_3_gold_layer_implementation_plan.md`  
**Audience:** Executives, coaches, analysts, recruitment staff, and data-platform operators

## 1. Model implementation

Use a Power BI semantic model connected to Unity Catalog Gold Delta tables through the Databricks SQL Warehouse connector.

- Storage mode: Import for dashboard-serving and aggregate tables.
- Incremental refresh: `refreshed_at`, with a rolling 24-month history and a 14-day refresh window.
- Default filter: `publication_status = "published"`.
- Exclude: `quality_status = "quarantined"` and rows with failed publication.
- Preserve: `insufficient_sample`, `not_available`, and `suppressed` rows for explicit display.
- Refresh grain: the Gold calculation run, not an individual visual query.
- Security: apply row-level security on `franchise_id`/club scope and avoid exposing provider identifiers to business users.

The model must not connect directly to Bronze or Silver.

## 2. Star-schema tables

### 2.1 Dimensions

| Power BI table | Gold source | Key | Business attributes |
|---|---|---|---|
| `DimDate` | Date generated in the model | `DateKey` | Date, week, month, quarter, season period |
| `DimFixture` | `gold.match.match_summary` | `fixture_id` | Match date, venue, opponent, home/away, competition |
| `DimAthlete` | `gold.athlete.athlete_profile_metrics` | `athlete_profile_id` | Name, position, preferred foot, active status |
| `DimTeam` | Gold team marts | `franchise_id` | Club, team, squad, current status |
| `DimCompetition` | Gold match/team marts | `competition_id` | Competition, season, competition type |
| `DimParticipant` | `gold.event.participant_metrics` | `participant_id` | Fixture role, team, participation status |
| `DimMetric` | `gold.quality.metric_definition` | `metric_code` + `metric_version` | Name, formula, owner, denominator policy |
| `DimEvaluationWindow` | Gold publication contract | Window key | Window type, start date, end date |
| `DimSpaceType` | Space profiles/detail | `space_type` | Space category and display label |
| `DimPressType` | Press profiles/detail | `press_type` | Press category and display label |
| `DimQualityStatus` | Model-owned static dimension | `quality_status` | Published, warning, insufficient sample, suppressed |

### 2.2 Facts and marts

| Power BI table | Gold source | Grain | Primary use |
|---|---|---|---|
| `FactMetricValue` | `gold.quality.metric_value` | Metric/entity/window/run | Shared KPI cards, trends, governed drill-through |
| `FactAthleteProfile` | `gold.athlete.athlete_profile_metrics` | Athlete/window | Player status and completeness |
| `FactRoster` | `gold.athlete.roster_metrics` | Athlete/team/season/window | Roster continuity and availability |
| `FactTeamMatch` | `gold.team.match_summary` | Team/fixture | Coach match summary |
| `FactTeamWindow` | `gold.team.performance_window` | Team/window | Team trend and performance |
| `FactSpaceTeam` | `gold.team.space_creation_profile` | Team/window/space type | Team space creation |
| `FactPressTeam` | `gold.team.pressing_profile` | Team/window/press type | Team pressing |
| `FactAttributionTeam` | `gold.team.attribution_profile` | Team/window/attribution type | Team contribution |
| `FactMatch` | `gold.match.match_summary` | Fixture | Executive and match views |
| `FactMatchParticipant` | `gold.match.player_summary` / `gold.event.participant_metrics` | Fixture/participant | Player match involvement |
| `FactSpaceOpportunity` | `gold.match.space_opportunity_detail` | Space opportunity | Coach/recruitment drill-through |
| `FactPressOpportunity` | `gold.match.press_opportunity_detail` | Press opportunity | Pressing drill-through |
| `FactTimeline` | `gold.match.timeline` | Fixture/time bucket | Match chronology |
| `FactDataHealth` | `gold.executive.data_health` | Product/reporting period | Executive trust and operations |

## 3. Relationships

All relationships are single-direction, dimension-to-fact, one-to-many. Do not create direct fact-to-fact relationships.

| From dimension | To fact | Join |
|---|---|---|
| `DimDate` | All dated facts | Date key to event/evaluation date |
| `DimFixture` | Match, team-match, participant, space, press, timeline facts | `fixture_id` |
| `DimAthlete` | Athlete, roster, player, opportunity and attribution facts | `athlete_profile_id` |
| `DimTeam` | Team, roster, participant and match-team facts | `franchise_id` |
| `DimCompetition` | Fixture, team and match facts | `competition_id`, `season_id` |
| `DimParticipant` | Participant, player and opportunity facts | `participant_id` |
| `DimMetric` | `FactMetricValue` | `metric_code`, `metric_version` |
| `DimEvaluationWindow` | Window facts and `FactMetricValue` | Window key |
| `DimSpaceType` | Space facts | `space_type` |
| `DimPressType` | Press facts | `press_type` |
| `DimQualityStatus` | All published facts | `quality_status` |

Use inactive alternate date relationships for match date versus evaluation-window end date where both are required. Activate them explicitly in measures with `USERELATIONSHIP`.

## 4. Canonical field groups

Every fact should expose these field groups:

1. **Entity:** fixture, athlete, participant, team, competition, season.
2. **KPI:** `metric_code`, `metric_version`, `numerator`, `denominator`, `metric_value`, `sample_size`.
3. **Evidence:** `coverage_ratio`, `confidence`, `quality_status`, `quality_reason`.
4. **Lineage:** `source_snapshot_id`, `ingestion_attempt_id`, `transformation_run_id`, `calculation_run_id`.
5. **Publication:** `publication_status`, `published_at`, `refreshed_at`.

Hide technical lineage fields from report users but retain them in the model for drill-through and audit pages.

## 5. Filter and interaction rules

- Slicers: season, competition, date range, team, athlete, position/role, opponent, home/away, metric status.
- Global filters must flow from dimensions only.
- Selecting a fixture filters all match, team, player, space, pressing, attribution, and timeline facts.
- Selecting an athlete filters athlete, roster, player-match, space, pressing, and attribution facts.
- KPI cards display a status badge when the denominator is below threshold.
- Tooltips show numerator, denominator, coverage, confidence, metric version, and refresh time.
- Drill-through pages always retain fixture/team/athlete/window context.

## 6. Required model validation

Before publishing the dataset:

- Verify every fact has a unique declared grain.
- Verify no many-to-many dimension relationship exists without an explicit bridge.
- Reconcile every KPI card to Gold numerator/denominator values.
- Verify zero denominators return blank values, never zero performance.
- Verify `metric_value` agrees with numerator/denominator within tolerance.
- Verify hidden lineage fields are populated for published rows.
- Verify row-level security returns only authorized `franchise_id` values.
