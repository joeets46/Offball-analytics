# Off-Ball Version 2.1 Repository-First Traceability

**Primary source:** [Databricks Sports Entertainment MVM](https://github.com/databricks-industry-solutions/lakehouse-industry-data-models/tree/main/data-models/sports_entertainment/v1/mvm)  
**Review date:** 2026-10-24  
**Purpose:** Refactor V2 against repository evidence before further remediation or redesign.

## Repository evidence

The relevant source artifacts are:

- [`sports_entertainment_athlete_schema_v1_mvm.sql`](https://github.com/databricks-industry-solutions/lakehouse-industry-data-models/blob/main/data-models/sports_entertainment/v1/mvm/schemas/sports_entertainment_athlete_schema_v1_mvm.sql): `athlete_profile`, `roster`, `performance_stat`, `contract`, `eligibility_status`.
- [`sports_entertainment_event_schema_v1_mvm.sql`](https://github.com/databricks-industry-solutions/lakehouse-industry-data-models/blob/main/data-models/sports_entertainment/v1/mvm/schemas/sports_entertainment_event_schema_v1_mvm.sql): `fixture`, `calendar`, `tournament`, `bracket`, `match_result`, `scoring_event`, `participant`, `event_incident`, `competition_round`, `type`.
- [`sports_entertainment_athlete_metrics_v1_mvm.sql`](https://github.com/databricks-industry-solutions/lakehouse-industry-data-models/blob/main/data-models/sports_entertainment/v1/mvm/metrics/sports_entertainment_athlete_metrics_v1_mvm.sql): athlete and roster metric views.
- [`sports_entertainment_event_metrics_v1_mvm.sql`](https://github.com/databricks-industry-solutions/lakehouse-industry-data-models/blob/main/data-models/sports_entertainment/v1/mvm/metrics/sports_entertainment_event_metrics_v1_mvm.sql): match-result, participant, scoring-event, and incident metric views.
- [`sports_entertainment_dbml_v1_mvm.txt`](https://github.com/databricks-industry-solutions/lakehouse-industry-data-models/blob/main/data-models/sports_entertainment/v1/mvm/diagram/sports_entertainment_dbml_v1_mvm.txt): repository keys and relationships.

## Traceability matrix

| Component | Repository Based | Repository Extended | New Remediation Addition |
|---|---|---|---|
| `athlete.athlete_profile` | Yes - exact repository product | Source/version metadata only | No |
| `athlete.roster` | Yes - exact repository product | Football position context | No |
| `athlete.performance_stat` | Yes - exact repository product | Calculation-run reference | No |
| `athlete.contract` | Yes - exact repository product | None | No |
| `athlete.eligibility_status` | Yes - exact repository product | None | No |
| `event.fixture` | Yes - exact repository product | Analytical timestamps/version | No |
| `event.match_result` | Yes - exact repository product | Score-state linkage | No |
| `event.participant` | Yes - exact repository product | Lineup and analytical participant context | No |
| `event.event_incident` | Yes - exact repository product | Reconciliation payload | No |
| `event.scoring_event` | Yes - exact repository product | Phase/possession linkage | No |
| `event.calendar`, `tournament`, `bracket`, `competition_round`, `type` | Yes - exact repository products | None | No |
| Athlete/event metric-view pattern | Yes - repository metric SQL | Run and publication lineage | No |
| Match state and periods | No direct equivalent | Anchored to `event.fixture` and `event.match_result` | Yes - HR-001 |
| Possession and phase | No direct equivalent | Evidence anchored to `event_incident` and `scoring_event` | Yes - HR-002 |
| Space opportunity and counterfactual | No direct equivalent | Anchored to `participant` and `performance_stat` | Yes - CR-004 |
| Pressing opportunity and outcome | No direct equivalent | Anchored to `participant` and `event_incident` | Yes - HR-003 |
| Defensive attribution | No direct equivalent | Uses repository participant identity | Yes - HR-004 |
| Metric lineage objects | No direct equivalent | Extends repository metric-view pattern | Yes - CR-005 |
| Annotation objects | No direct equivalent | Targets repository-backed event/participant records | Yes - HR-007 |
| Evidence links | No direct equivalent | Fixture-scoped evidence contract | Yes - HR-008 |

## Major component evidence

| Major component | Repository status | Evidence and conclusion |
|---|---|---|
| Football Truth Layer | Repository extended plus remediation addition | The repository supplies fixture, result, participant, incident, scoring event, season/calendar, tournament, and competition-round anchors. Match periods, score intervals, possession, and phase are not explicit repository products and are added only for HR-001/HR-002. |
| Match State Model | Remediation addition | `event.match_result` supplies final score; no interval state entity exists in the repository. `match_state_interval` is therefore a review-backed extension, not a repository claim. |
| Possession Engine | Remediation addition | Repository event facts can evidence transitions, but no possession table or possession metric is present. |
| Formation and Tactical Shape Model | Not retained as a repository claim | No explicit formation or shape product was found. Only participant and roster position fields support a limited lineup context. |
| Pressing Intelligence Framework | Remediation addition | No pressing product exists in the repository. It remains only because HR-003 explicitly requires pressing opportunity, trigger, action, support, bypass, and outcome context. |
| Space Creation Framework | Remediation addition | No space product exists in the repository. It remains only because CR-004 explicitly requires opportunity, baseline, counterfactual, outcome, and attribution. |
| Role Taxonomy and Versioning | Repository extended, bounded | Repository roster and participant products expose position/role context, but no role taxonomy product exists. No standalone role framework is retained. |
| Confidence and Evidence Framework | Remediation addition | Repository products contain source and status metadata, but no generalized evidence/quality framework exists. It is retained only for CR-005, HR-007, and HR-008. |

## Removed or bounded from the prior V2

- Removed generated `canonical_*` mirror entities because the repository already provides the source domain products.
- Removed platform SaaS organisation, club-membership, and tenant application entities from the football model because they are not in the repository MVM and were not part of the focused remediation.
- Removed standalone formation, functional-unit, tactical-assignment, role-definition, recruitment-market, and AI-governance frameworks unless an explicit review finding requires a bounded field or extension.
- Kept no claim that tracking data, video rights, or off-ball metrics are repository-native.

## Assessment

The refactored V2 is repository-first: repository entity names and domain boundaries are preserved, repository-backed keys anchor every remediation fact, and unsupported prior abstractions are removed or explicitly classified as remediation additions. The model is repository-faithful at its base layer, while the football intelligence extensions remain clearly identified as review-backed additions rather than repository evidence.
