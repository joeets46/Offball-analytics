# Business Requirements Document

## Off-Ball Football Intelligence Platform

**Document status:** Frozen discovery baseline  
**Version:** 1.0  
**Audience:** Sporting directors, heads of recruitment, scouts, analysts, coaches, data product teams, and club executives  
**Product type:** Multi-tenant football analytics platform for professional clubs  
**Primary outcome:** Improve player recruitment and scouting decisions by making off-ball contribution measurable, explainable, and comparable.

## 1. Executive Summary

Off-Ball is a football intelligence platform focused on what players do when they do not have possession. It combines event data, tracking data, contextual match information, video evidence, human scouting observations, and explainable analytical models to evaluate off-ball movement, space creation, pressing intelligence, defensive positioning, and scanning-related behaviour.

The platform complements existing providers and human scouting. It does not replace live scouting, video review, medical assessment, contract negotiation, coaching judgement, or the final transfer decision.

The initial release prioritises recruitment and scouting, with supporting first-team performance and academy-development capabilities. Opposition analysis and live match support are future capabilities.

## 2. Business Problem

Traditional football analytics over-indexes on on-ball actions such as passes, shots, goals, assists, and possession events. This creates three business problems:

1. Hidden player contribution is missed when the player does not touch the ball.
2. Analysts lack consistent context for judging whether an off-ball action was valuable, repeatable, and tactically appropriate.
3. Recruitment teams spend excessive time combining provider data, video, and subjective observations before creating a shortlist.

Clubs need a role-aware and evidence-backed way to discover undervalued players, compare tactical fit across competitions, reduce scouting bias, and improve return on transfer investment.

## 3. Product Vision and Objectives

> Make every meaningful off-ball action visible, explainable, and useful for football decisions.

### Business objectives

- Identify players whose off-ball value is not reflected in traditional statistics.
- Improve tactical-fit assessment for recruitment briefs.
- Reduce time from recruitment question to validated shortlist.
- Give analysts and coaches a common language for off-ball behaviours.
- Preserve human accountability while making analysis more repeatable.

### Target scale

- 20-50 competitions.
- 500-1,000 clubs.
- 10,000 or more professional players.
- 100-500 users across scouting, recruitment, performance, coaching, and executive teams.
- Multiple countries, leagues, providers, and data-quality profiles.

## 4. Scope Baseline

### In scope for Release 1

- Recruitment and scouting as the primary use case.
- First-team performance analysis foundations.
- Academy player development foundations.
- Player, team, match, competition, season, and role context.
- Event and tracking data ingestion and normalisation.
- Off-ball run, space creation, pressing, defensive intelligence, and evidence products.
- Role-aware benchmarking and player comparison.
- Recruitment briefs, criteria, watchlists, shortlists, observations, notes, and reports.
- Human review and correction of automated classifications.
- Explainable AI insights with confidence and evidence.
- Multi-tenant club access control and auditability.

### Explicitly out of scope for Release 1

- Real-time or live-match analytics.
- Opposition analysis as a primary workflow.
- Betting, gambling, and fantasy football.
- Automated computer-vision pipelines for scanning.
- Injury forecasting, medical records, and biometric health analysis.
- Contract negotiation or automated player valuation.
- Fully autonomous tactical recommendations.
- Replacement of live scouts, coaches, or decision-makers.

## 5. Stakeholders and Users

| Stakeholder | Responsibility | Primary decisions |
|---|---|---|
| Sporting Director | Final recruitment authority | Which players progress to final recruitment decision |
| Head of Recruitment | Recruitment strategy and approval | Which profiles and shortlists meet club needs |
| Scout | Qualitative validation | Whether data findings are visible in football context |
| Recruitment Analyst | Search, comparison, and evidence review | Which players deserve deeper review |
| Performance Analyst | Match and player diagnosis | Which behaviours require coaching attention |
| Coach / Technical Staff | Tactical and development decisions | Which behaviours should be reinforced or improved |
| Academy Staff | Longitudinal development | Whether player behaviours are progressing |
| Club Administrator | Tenant and access governance | Who may access club data and workflows |
| Data Product Owner | Product and data accountability | Metric definitions, releases, and acceptance |
| Football Analyst / Scouting Expert | Domain ownership | Definitions of behaviours, roles, and validation standards |

## 6. User Scenarios and Acceptance Tests

### US-001: Build a recruitment shortlist — Priority P1

As a recruitment analyst, I want to define an off-ball profile and discover suitable players so that I can create a defensible shortlist faster.

**Acceptance scenarios**

1. Given an approved recruitment brief, when the analyst selects role, competition, date range, and behavioural criteria, then the platform returns eligible players with fit scores, coverage, confidence, and comparison cohort.
2. Given a candidate player, when the analyst opens the profile, then the platform shows component metrics and supporting evidence rather than only an aggregate score.
3. Given a candidate with incomplete data, when the analyst views the result, then missing coverage and provisional status are shown and the player is not presented as fully comparable.

### US-002: Validate a player with evidence — Priority P1

As a scout, I want to review clips, events, and context behind a metric so that I can validate whether the behaviour is football-relevant.

**Acceptance scenarios**

1. Given a metric with video rights, when the scout opens evidence, then the relevant timestamp, frame range, clip, or playlist is available.
2. Given unavailable video, when the scout opens evidence, then the analytical result remains available with an explicit evidence-unavailable status.
3. Given an incorrect classification, when an authorised analyst corrects it, then the correction, author, reason, and model version remain auditable.

### US-003: Compare player fit — Priority P1

As a head of recruitment, I want to compare players under the same role and cohort so that I can distinguish tactical fit from raw volume.

**Acceptance scenarios**

1. Given at least four players, when the user compares them under identical filters, then metrics use the same definitions, denominators, window, and benchmark cohort.
2. Given players from different competitions, when the comparison is displayed, then per-90 values, role percentiles, competition context, and adjustment status are visible.
3. Given a player below the minimum sample threshold, when the comparison is displayed, then the profile is marked provisional.

### US-004: Diagnose a match or team — Priority P2

As a performance analyst, I want to drill from team patterns to player actions so that I can prepare evidence-based coaching feedback.

**Acceptance scenarios**

1. Given a completed match, when the analyst selects phase, zone, scoreline, and possession context, then team-level off-ball patterns are filtered accordingly.
2. Given a team pattern, when the analyst drills down, then the platform identifies contributing players, actions, confidence, and evidence.
3. Given collective defensive responsibility, when attribution is shown, then individual and unit contributions are separated.

### US-005: Track development — Priority P2

As academy staff, I want to compare a player across evaluation windows so that I can monitor repeatable behavioural development.

**Acceptance scenarios**

1. Given a player and rolling or seasonal windows, when staff view trends, then the denominator, minutes, role, coverage, and metric version are shown.
2. Given a role change, when the trend is displayed, then role assignments and effective dates explain the comparison.

### US-006: Govern AI insights — Priority P2

As an analyst, I want to review and approve AI-generated insights so that automated recommendations cannot silently influence professional decisions.

**Acceptance scenarios**

1. Given an AI insight, when it is displayed, then confidence, model version, explanation, contributing metrics, and evidence are visible.
2. Given an insight requiring review, when it is not approved, then it is excluded from approved recruitment reports.
3. Given an override, when it is saved, then the reviewer, reason, timestamp, and original output remain available.

### Edge cases

- Duplicate or conflicting provider player identities.
- Missing date of birth or conflicting identity attributes.
- Postponed, replayed, abandoned, friendly, or incomplete matches.
- Substitutions, extra time, stoppage time, loans, transfers, and dual registration.
- Tracking occlusion, missing frames, identity swaps, calibration errors, and camera changes.
- Conflicting provider events or late-arriving corrections.
- Multiple players contributing to the same space creation or defensive outcome.
- A single movement qualifying for multiple run or pressing labels.
- Low sample size, zero denominator, missing video, expired video rights, and unavailable scanning signals.
- Cross-league comparisons with different providers, pitch dimensions, and playing styles.
- Tenant users attempting to access another club's private briefs, notes, corrections, or reports.

## 7. Functional Requirements

### Product and access

- **REQ-001:** The platform MUST support isolated club workspaces within a shared global football dataset.
- **REQ-002:** The platform MUST enforce role-based access for administrators, scouts, recruitment analysts, performance analysts, coaches, executives, and approved partners.
- **REQ-003:** The platform MUST keep club briefs, shortlists, notes, corrections, custom weights, reports, and overrides private by default.
- **REQ-004:** The platform MUST record audit events for access-sensitive changes, approvals, overrides, identity merges, metric configuration, and published reports.

### Football universe and identity

- **REQ-005:** The platform MUST maintain canonical organisations, clubs, teams, competitions, seasons, competition-seasons, fixtures, matches, venues, and match participants.
- **REQ-006:** The platform MUST maintain a canonical Off-Ball Player ID and preserve provider-specific identities and source attributes.
- **REQ-007:** The platform MUST support effective-dated registrations, loans, transfers, academy promotion, and team attribution without rewriting historical performance.
- **REQ-008:** The platform MUST retain merge, unmerge, conflict, confidence, and reviewer history for identity resolution.
- **REQ-009:** The platform MUST represent role profiles and assignments by player, team, season, match segment, source, confidence, and approval state.
- **REQ-010:** The platform MUST apply role source precedence: analyst override, lineup evidence, provider role, rules inference, then AI inference.

### Recruitment workflow

- **REQ-011:** Users MUST be able to create versioned recruitment briefs with position or position group, squad need, target profile, tactical role, optional age, budget, competition, contract, physical, development, and behavioural criteria.
- **REQ-012:** Users MUST be able to assign weights, targets, minimums, maximums, direction, and required status to brief criteria.
- **REQ-013:** The platform MUST calculate brief-fit scores on a 0-100 scale using normalised component metrics.
- **REQ-014:** The platform MUST require at least 80% component coverage and medium confidence before publishing a brief-fit score as decision-ready.
- **REQ-015:** Users MUST be able to create watchlists and shortlists with statuses from discovered through signed, rejected, or archived.
- **REQ-016:** Status changes MUST support reasons, assignees, timestamps, and audit history.
- **REQ-017:** Users MUST be able to record scouting observations with match context, time, rating, tags, evidence, confidence, recommendation, author, visibility, and revisions.
- **REQ-018:** Users MUST be able to compare at least four players under identical filters and metric versions.

### Match, event, and tracking data

- **REQ-019:** The platform MUST preserve provider-native event and tracking data before canonicalisation.
- **REQ-020:** The platform MUST map source events to a canonical taxonomy while retaining source observations and reconciliation status.
- **REQ-021:** The platform MUST support canonical event versioning, late arrivals, soft deletion, recalculation timestamps, and historical metric vintages.
- **REQ-022:** The platform MUST retain provider time, elapsed match seconds, period, period clock, wall-clock time where available, and frame number where available.
- **REQ-023:** The platform MUST represent possession sequences, attacking phases, defensive phases, transitions, set pieces, and dead-ball periods.
- **REQ-024:** The platform MUST retain tracking positions, ball positions where available, velocity, acceleration, orientation where available, visibility, coverage, and quality flags.
- **REQ-025:** The platform MUST represent continuous player-track segments and explicit quality intervals for substitutions, gaps, occlusion, identity swaps, and off-pitch periods.
- **REQ-026:** Tracking-derived metrics MUST be withheld or marked provisional when coverage is below 95%, gaps exceed the configured tolerance, or coordinate validity fails.

### Off-ball intelligence

- **REQ-027:** The platform MUST detect or store off-ball movements using a minimum default of 1 second and 3 metres while the player is not controlling the ball.
- **REQ-028:** The platform MUST support depth, width, support, check-to, overlap, underlap, decoy, counter-movement, recovery, cover, pressing, box-entry, and channel run types.
- **REQ-029:** Run labels MUST preserve multi-label classifications or document precedence when labels overlap.
- **REQ-030:** The platform MUST calculate space creation from defender displacement, passing-lane creation, teammate receiving space, zone vacancy, possession value, and defensive disruption features.
- **REQ-031:** Space-creation attribution MUST support primary, supporting, team-structure, and negative contributions, with positive shares conserved to 100%.
- **REQ-032:** The platform MUST represent pressing triggers, pressure attempts, approach context, teammate support, passing-lane closure, outcome, and confidence.
- **REQ-033:** The platform MUST support pressing outcomes including turnover, backward pass, forced long ball, lane closure, delayed progression, bypassed, foul, failed, and unknown.
- **REQ-034:** The platform MUST represent defensive lane protection, tracking, screening, cover, compactness, transition recovery, rest defence, and box protection.
- **REQ-035:** Defensive attribution MUST separate primary player, supporting defenders, defensive unit, and team-structure contribution.
- **REQ-036:** Scanning MUST distinguish unavailable, manual, and proxy signals and MUST NOT claim computer-vision certainty in Release 1.

### Metrics, benchmarks, evidence, and AI

- **REQ-037:** Every published metric MUST include definition, version, window, role, denominator, sample size, coverage, confidence, calculation time, and lineage.
- **REQ-038:** Player rates MUST use player minutes; team rates team minutes; attacking off-ball rates possession minutes; pressing and defensive rates opposition-possession minutes.
- **REQ-039:** Profiles under 900 player minutes MUST be marked provisional.
- **REQ-040:** Cross-league products MUST publish per-90 or per-opportunity values and role percentiles within competition-season; strength adjustments MUST be separately versioned.
- **REQ-041:** Every insight MUST link to source events, tracking intervals, video evidence where available, and the relevant metric or model version.
- **REQ-042:** AI insights MUST include confidence, explanation, contributing metrics, evidence, model version, approval status, reviewer, and override reason.
- **REQ-043:** AI outputs MUST require human review before inclusion in an approved recruitment or coaching report.
- **REQ-044:** Users MUST be able to correct classifications and provide feedback without deleting the original output.

### Data quality and reporting

- **REQ-045:** The platform MUST monitor completeness, timeliness, accuracy, uniqueness, referential integrity, coordinate validity, identity match rate, event reconciliation, and video alignment.
- **REQ-046:** Data-quality failures MUST be quarantined or explicitly marked; the platform MUST NOT silently publish incomplete profiles.
- **REQ-047:** Users MUST be able to filter by phase, zone, possession, scoreline, minute, formation, opponent strength, competition, date, and role where data supports the filter.
- **REQ-048:** Users MUST be able to export player, team, match, and shortlist reports containing definitions, context, findings, evidence links, confidence, and data-quality warnings.
- **REQ-049:** The platform MUST provide recruitment, player, match, team, development, and executive dashboard views.
- **REQ-050:** The platform MUST meet the stated MVM quality thresholds before a product is marked production-ready.

## 8. Non-Functional Requirements

- **NFR-001:** Standard player and match views SHOULD load within 3 seconds for 95% of requests at pilot scale.
- **NFR-002:** Production service availability SHOULD target 99.5% monthly availability excluding planned maintenance.
- **NFR-003:** Metric results MUST be reproducible from versioned source, transformation, metric, and model inputs.
- **NFR-004:** Data MUST be encrypted in transit and at rest with least-privilege access and tenant isolation.
- **NFR-005:** The platform MUST support data retention, deletion, access, and residency controls appropriate to the deployment jurisdiction.
- **NFR-006:** The system MUST scale to at least the target 1,000 clubs, 10,000 players, and 500 users without changing business definitions.
- **NFR-007:** Errors MUST be visible to users and operators with actionable status; the system MUST not return success-shaped fallbacks for missing or invalid data.

## 9. Key Entities

Organisation, Club, Team, Competition, Season, Competition Season, Fixture, Match, Venue, Match Team, Player, Provider Player Identity, Player Registration, Player Role Assignment, Lineup Segment, Provider Event Observation, Canonical Event, Possession Sequence, Tracking Provider, Track Segment, Tracking Frame Position, Tracking Quality Interval, Off-Ball Run, Space Creation Event, Space Contribution, Pressing Action, Defensive Intelligence Action, Scan Observation, Video Evidence, Recruitment Brief, Recruitment Brief Version, Brief Criterion, Shortlist, Shortlist Item, Scouting Observation, Metric Definition, Metric Version, Player Metric Value, Benchmark Value, Brief Fit, AI Insight, Insight Evidence, User, Club Membership, Audit Event, and Report.

## 10. Success Criteria

- **SC-001:** Recruitment analysts reduce time from an off-ball recruitment question to a validated shortlist by at least 50% versus the baseline workflow.
- **SC-002:** At least 80% of sampled automated action classifications are judged relevant and correct by qualified analysts.
- **SC-003:** At least 95% of published tracking-derived profiles meet the configured coverage and alignment gates.
- **SC-004:** Identity resolution reaches at least 99% accuracy, with unresolved conflicts visible in a review queue.
- **SC-005:** Completeness reaches at least 98%; referential integrity reaches at least 99.9%; coordinate validity reaches at least 99.5%.
- **SC-006:** At least 95% of reconciled events map to the canonical taxonomy.
- **SC-007:** At least 95% of licensed evidence links align to the relevant event or action.
- **SC-008:** 90% of pilot users can complete player search, comparison, and evidence review without assistance.
- **SC-009:** Every approved score and report can be reproduced from its historical data and model versions.
- **SC-010:** No cross-tenant access test exposes private club notes, briefs, corrections, or reports.
- **SC-011:** At least 70% of pilot clubs use the product weekly during the pilot period.

## 11. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Provider differences make metrics incomparable | Preserve provider data, canonicalise explicitly, expose provenance, and version calibrations. |
| Off-ball classifications are subjective | Use transparent definitions, analyst review, confidence gates, and feedback loops. |
| Small samples create unstable rankings | Minimum-minute thresholds, provisional labels, cohort benchmarks, and confidence intervals. |
| Tactical roles differ by club | Support global role vocabulary plus club-configurable role profiles and weights. |
| Video rights or timestamps are unavailable | Keep analytical products independent of video and expose evidence availability. |
| AI creates false authority | Require human approval, explanations, evidence, model versions, and override history. |
| Tracking quality varies | Store quality intervals and quarantine or downgrade insufficient data. |
| Multi-tenant leakage | Enforce organisation and club policies in application and analytical serving layers. |

## 12. Assumptions and Frozen Decisions

- Discovery is complete; this document is the frozen business baseline.
- Unresolved implementation choices use the enterprise defaults recorded in the companion [offball data model design](C:/Users/ASUS/OFF-Ball/offball_data_model_design.md).
- PostgreSQL stores application workflow and access metadata; Databricks stores source, canonical, derived, and analytical data.
- Release 1 is batch-first and does not require streaming or live-match latency.
- Scanning is unavailable, manual, or proxy-based until an approved computer-vision source is added.
- Positive contribution shares are conserved to 100%; negative impact is separately represented.
- Historical data and published outputs are versioned and not physically overwritten.
- Global canonical football data is shared read-only; club workflows and corrections are private by default.
- A model governance board consisting of the Lead Football Analyst, Head of Recruitment, Data Product Owner, and Data Architecture owner approves metric changes.

## 13. Delivery Phases

1. **Foundation:** tenant governance, football universe, player registry, provider ingestion, and quality framework.
2. **Canonical intelligence:** event reconciliation, tracking normalisation, match phases, and evidence linkage.
3. **MVM analytics:** runs, space creation, pressing, defensive intelligence, role benchmarks, and player profiles.
4. **Recruitment workflow:** briefs, criteria, shortlists, observations, reports, and human review.
5. **Pilot validation:** quality gates, analyst agreement, user acceptance, and reproducibility testing.
6. **Expansion:** custom club models, additional providers, academy workflows, opposition analysis, and future near-live capabilities.
