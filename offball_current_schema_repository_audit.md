# Current PostgreSQL Schema Repository Audit

**Reviewer:** Independent Repository Auditor  
**Review date:** 2026-10-24  
**Primary source:** [Databricks Sports Entertainment MVM](https://github.com/databricks-industry-solutions/lakehouse-industry-data-models/tree/main/data-models/sports_entertainment/v1/mvm)  
**Audited artifact:** [Current PostgreSQL schema](./offball_postgresql_schema.sql)  
**Review findings register:** [Design Review Report](./archive/offball_design_review_report.md)

## 1. Method

Every `CREATE TABLE` in the current PostgreSQL schema was compared with:

1. The repository MVM schema SQL and DBML.
2. The repository athlete and event metric-view patterns.
3. The 25 explicitly enumerated findings in the Design Review Report.

Statuses are assigned at table level:

- **Direct Repository Reuse:** The table corresponds to an explicit repository product with the same business grain and repository name.
- **Repository Extension:** The table extends or materializes a repository product or metric-view pattern without being an exact repository table.
- **Review-Required Addition:** The table is not present in the repository and exists only because an explicit review finding requires the capability.

## 2. Table traceability matrix

| Table Name | Repository Source Table | Repository File | Status |
|---|---|---|---|
| `athlete.athlete_profile` | `athlete.athlete_profile` | `schemas/sports_entertainment_athlete_schema_v1_mvm.sql` | Direct Repository Reuse |
| `event.fixture` | `event.fixture` | `schemas/sports_entertainment_event_schema_v1_mvm.sql` | Direct Repository Reuse |
| `athlete.roster` | `athlete.roster` | `schemas/sports_entertainment_athlete_schema_v1_mvm.sql` | Direct Repository Reuse |
| `event.participant` | `event.participant` | `schemas/sports_entertainment_event_schema_v1_mvm.sql` | Direct Repository Reuse |
| `event.match_result` | `event.match_result` | `schemas/sports_entertainment_event_schema_v1_mvm.sql` | Direct Repository Reuse |
| `event.event_incident` | `event.event_incident` | `schemas/sports_entertainment_event_schema_v1_mvm.sql` | Direct Repository Reuse |
| `event.scoring_event` | `event.scoring_event` | `schemas/sports_entertainment_event_schema_v1_mvm.sql` | Direct Repository Reuse |
| `athlete.performance_stat` | `athlete.performance_stat` | `schemas/sports_entertainment_athlete_schema_v1_mvm.sql` | Direct Repository Reuse |
| `analytics.match_period` | None | Design Review HR-001 | Review-Required Addition |
| `analytics.match_state_interval` | None | Design Review HR-001 | Review-Required Addition |
| `analytics.possession_sequence` | None | Design Review HR-002 | Review-Required Addition |
| `analytics.phase_interval` | None | Design Review HR-002 | Review-Required Addition |
| `analytics.opportunity` | None | Design Review CR-004, MR-004 | Review-Required Addition |
| `analytics.space_opportunity` | None | Design Review CR-004 | Review-Required Addition |
| `analytics.pressing_opportunity` | None | Design Review HR-003 | Review-Required Addition |
| `analytics.space_baseline` | None | Design Review CR-004 | Review-Required Addition |
| `analytics.space_counterfactual` | None | Design Review CR-004 | Review-Required Addition |
| `analytics.space_outcome` | None | Design Review CR-004 | Review-Required Addition |
| `analytics.attribution_ledger` | None | Design Review CR-004, HR-004 | Review-Required Addition |
| `analytics.press_trigger` | None | Design Review HR-003 | Review-Required Addition |
| `analytics.press_action` | None | Design Review HR-003 | Review-Required Addition |
| `analytics.press_support` | None | Design Review HR-003 | Review-Required Addition |
| `analytics.press_bypass` | None | Design Review HR-003 | Review-Required Addition |
| `analytics.press_outcome` | None | Design Review HR-003 | Review-Required Addition |
| `analytics.recovery_action` | None | Design Review HR-003 | Review-Required Addition |
| `analytics.source_snapshot` | None | Design Review CR-005 | Review-Required Addition |
| `analytics.calculation_run` | None | Design Review CR-005 | Review-Required Addition |
| `analytics.feature_set` | None | Design Review CR-005 | Review-Required Addition |
| `analytics.model_artifact` | None | Design Review CR-005 | Review-Required Addition |
| `analytics.metric_publication` | None | Design Review CR-005 | Review-Required Addition |
| `analytics.metric_value` | Repository metric-view pattern, not a repository table | `metrics/sports_entertainment_athlete_metrics_v1_mvm.sql`; `metrics/sports_entertainment_event_metrics_v1_mvm.sql`; Design Review CR-005 | Review-Required Addition |
| `analytics.evidence_link` | None | Design Review HR-008, MR-008 | Review-Required Addition |
| `analytics.annotation_task` | None | Design Review HR-007 | Review-Required Addition |
| `analytics.annotation_label` | None | Design Review HR-007 | Review-Required Addition |
| `analytics.annotation_adjudication` | None | Design Review HR-007 | Review-Required Addition |

## 3. Counts and percentages

Total audited tables: **35**

| Status | Count | Percentage |
|---|---:|---:|
| Direct Repository Reuse | 8 | 22.86% |
| Repository Extension | 0 | 0.00% |
| Review-Required Addition | 27 | 77.14% |
| **Total** | **35** | **100.00%** |

Percentages are calculated as `count / 35 * 100`, rounded to two decimal places.

## 4. Tables without repository or review traceability

**None.**

Every non-repository table in the current schema maps to at least one explicit review finding:

- HR-001: match periods and state intervals.
- HR-002: possession and phase intervals.
- CR-004/MR-004: opportunity, space, counterfactual, outcome, and attribution structures.
- HR-003: pressing opportunity, trigger, action, support, bypass, outcome, and recovery structures.
- HR-004: attribution ledger.
- CR-005: source snapshots, calculation runs, feature sets, model artifacts, publications, and metric values.
- HR-007: annotation task, label, and adjudication.
- HR-008/MR-008: evidence links.

No current table is unsupported by both the repository and the explicit review register.

## 5. Repository alignment score

The repository-alignment score is calculated as:

`(Direct Repository Reuse + Repository Extension) / Total Tables * 100`

Therefore:

`(8 + 0) / 35 * 100 = 22.86%`

### Final score: **22.86% direct repository alignment**

This score measures table-level repository reuse only. It does not treat review-required additions as repository-aligned merely because they are justified by the design review.

## 6. Final assessment

The schema has a clearly traceable repository base consisting of the eight athlete and event tables reused from the Databricks MVM. However, most current tables are analytical remediation additions rather than repository tables. They are traceable to explicit review findings, so they are not unsupported, but they must not be represented as native Databricks MVM entities.

The current schema is therefore:

- **Repository-aligned at the base-domain layer:** Yes.
- **Fully repository-derived:** No.
- **Unsupported by both repository and review findings:** No.
- **Repository-alignment score:** **22.86%**.
