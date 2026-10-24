# Off-Ball Data Architecture Design Review

**Reviewer:** Senior Football Data Architect  
**Review status:** Design review only; no implementation changes made  
**Artifacts reviewed:**

- [Business Requirements Document](C:/Users/ASUS/OFF-Ball/football_offball_project.md)
- [Lakehouse data model design](C:/Users/ASUS/OFF-Ball/offball_data_model_design.md)
- [PostgreSQL application schema](C:/Users/ASUS/OFF-Ball/offball_postgresql_schema.sql)

## 1. Executive Assessment

The artifacts establish a strong product intent and a credible first-pass lakehouse shape. The separation between global football data, club-private workflow data, immutable source data, canonical Silver entities, and Gold decision products is directionally correct.

The design is **not yet implementation-ready for professional-club use**. The most important weaknesses are:

1. The PostgreSQL schema is not executable as written because it uses `citext` without enabling the `citext` extension.
2. PostgreSQL workflow rows use free-text player and match IDs with no foreign-key or synchronization contract to the canonical lakehouse.
3. The model describes off-ball actions, but does not yet model the football opportunities, tactical state, counterfactual baseline, target space, and attribution evidence required to defend those actions analytically.
4. Match context is too thin for professional analysis: formations, phases, game state, score timeline, substitutions, set-piece state, field orientation, and tactical instructions are not first-class modeled concepts.
5. The tracking strategy is potentially prohibitively large and expensive at frame-player grain with indefinite retention, and it lacks an explicit hot/cold serving strategy.
6. Tenant isolation, audit immutability, workflow history, and row-level security are requirements but are not enforced by the PostgreSQL artifact.

**Overall verdict:** Conceptually promising, but **conditional fail** for production design approval. Approve as a product-domain baseline only after the Critical and High findings below are resolved.

## 2. Severity Summary

| Severity | Count | Meaning |
|---|---:|---|
| Critical | 5 | Blocks execution, correctness, or production safety |
| High | 10 | Likely to cause incorrect football conclusions, data leakage, or material scale failure |
| Medium | 10 | Important completeness, maintainability, or operating-model gaps |
| Low | 4 | Useful hardening and documentation improvements |

## 3. Critical Findings

### CR-001 — PostgreSQL schema fails on a clean database

**Evidence:** [offball_postgresql_schema.sql](C:/Users/ASUS/OFF-Ball/offball_postgresql_schema.sql:25) uses `citext`, while the schema only creates `pgcrypto` at [line 3](C:/Users/ASUS/OFF-Ball/offball_postgresql_schema.sql:3).

**Impact:** A clean deployment fails before `app.app_user` can be created. This is a release blocker.

**Required decision:** Either explicitly provision `citext` or use a portable case-normalised email strategy. The extension must be part of the controlled database bootstrap, not an undocumented prerequisite.

### CR-002 — Application records are disconnected from canonical football data

**Evidence:** `shortlist_item.offball_player_id` is free text at [line 99](C:/Users/ASUS/OFF-Ball/offball_postgresql_schema.sql:99), and `scouting_observation.offball_player_id` and `match_id` are also free text at [lines 113-114](C:/Users/ASUS/OFF-Ball/offball_postgresql_schema.sql:113). The design states that PostgreSQL owns workflow metadata while Delta owns analytical facts at [line 63](C:/Users/ASUS/OFF-Ball/offball_data_model_design.md:63), but does not define an identity registry, referential contract, or synchronization mechanism.

**Impact:** Deleted, merged, or incorrectly typed players can remain in active shortlists. A report may reference a player or match that does not exist, has been superseded, or belongs to a different global identity. This directly undermines the stated referential-integrity target.

**Required decision:** Define a canonical-ID contract: immutable IDs, registry snapshot/version, existence validation, merge/unmerge propagation, tombstone behavior, and whether PostgreSQL stores a local mirror of global player/match dimensions.

### CR-003 — Tenant isolation is specified but not enforced

**Evidence:** Tenant isolation is a requirement at [REQ-001 to REQ-004](C:/Users/ASUS/OFF-Ball/football_offball_project.md:170), while the PostgreSQL schema contains no row-level security policies, security-definer access boundary, organisation-level membership checks, or append-only audit controls. Several tables have `club_id`, but `app_user` and membership administration do not establish a complete authorization model.

**Impact:** A query or service defect can expose another club's briefs, observations, reports, metric configurations, or shortlist decisions. This is a material confidentiality and commercial-risk issue.

**Required decision:** Make tenant enforcement a database and serving-layer invariant. Add explicit organisation/club scope, authorization policy semantics, RLS policy tests, external-partner sharing rules, and deny-by-default behavior.

### CR-004 — Space creation is not analytically defensible without opportunity and counterfactual entities

**Evidence:** The design says space creation combines defender displacement, passing-lane creation, receiving space, zone vacancy, possession value, and defensive disruption at [REQ-030](C:/Users/ASUS/OFF-Ball/football_offball_project.md:202), but the entity model contains only `space_creation_event` and `space_contribution` and does not model the target space, affected defenders, receiver opportunity, baseline state, or counterfactual at [lines 134 and 303](C:/Users/ASUS/OFF-Ball/offball_data_model_design.md:134).

**Impact:** The platform cannot distinguish intentional space creation from incidental vacancy, teammate movement, opponent error, or a team-shape consequence. Scores become difficult to validate and vulnerable to double counting.

**Required decision:** Add explicit opportunity/baseline structures: pre-action state, post-action state, target zone or lane geometry, affected player(s), receiving opportunity, expected value delta, counterfactual method, and contribution ledger.

### CR-005 — The MVM cannot reproduce or audit metric calculations end to end

**Evidence:** The model requires metric version and lineage at [line 116](C:/Users/ASUS/OFF-Ball/offball_data_model_design.md:116) and [REQ-037](C:/Users/ASUS/OFF-Ball/football_offball_project.md:213), but there is no first-class ingestion run, transformation run, feature set, source snapshot, label set, metric execution, or calculation input manifest.

**Impact:** A historical score can be tagged with a version but still cannot be reproduced from a deterministic set of source records, code/model artifact, parameters, and quality results.

**Required decision:** Model a run/lineage graph covering source snapshot, pipeline run, feature set, model artifact, metric version, output partition, and publication. Preserve the exact input snapshot used by each published metric.

## 4. High Findings

### HR-001 — Football match context is materially incomplete

**Evidence:** The BRD requires filtering by phase, zone, scoreline, minute, formation, possession, and opponent strength at [REQ-047](C:/Users/ASUS/OFF-Ball/football_offball_project.md:222), but the design only names match, match team, lineup, event, and possession sequence at [lines 108-130](C:/Users/ASUS/OFF-Ball/offball_data_model_design.md:108).

**Missing concepts:** Match period and stoppage, score-state intervals, game-state timeline, formations, tactical shape, field orientation, starting XI, substitutions, bench, set-piece state, referee decisions, and match status/abandonment reason.

**Impact:** Filters and denominators cannot be computed consistently, and an action cannot be judged against the tactical state in which it occurred.

### HR-002 — Possession and phase semantics are under-modeled

**Evidence:** The design lists `possession_sequence` and canonical phases but provides no event-level ownership transitions, uncertainty interval, phase boundaries, attack direction, or set-piece restart model.

**Impact:** Pressing, defensive, transition, and attacking denominators can disagree across providers. The same event may be assigned to the wrong team phase or possession.

**Required decision:** Define a versioned possession/phase engine with explicit start/end events, confidence, unresolved intervals, restart semantics, attacking direction, and provider evidence.

### HR-003 — Pressing intelligence lacks the target and opportunity grain

**Evidence:** Pressing requirements include triggers, approach context, teammate support, lane closure, outcomes, and confidence at [REQ-032 and REQ-033](C:/Users/ASUS/OFF-Ball/football_offball_project.md:204), but `pressing_action` in the ERD has only player, outcome, distance, and confidence at [lines 232-237](C:/Users/ASUS/OFF-Ball/offball_data_model_design.md:232).

**Missing concepts:** Pressed ball carrier, target event, trigger event, press start/end, approach angle, cover shadow geometry, passing options before/after, supporting players, press resistance, bypass point, and tactical instruction.

**Impact:** A player can be rewarded for running toward the ball even when the press was unsupported, tactically wrong, or easily bypassed.

### HR-004 — Defensive attribution lacks responsibility context

**Evidence:** The BRD requires individual, supporting, defensive-unit, and team-structure contribution at [REQ-035](C:/Users/ASUS/OFF-Ball/football_offball_project.md:207), but the model has only `defensive_intelligence_action` and no first-class defensive unit, assignment, target opponent, danger zone, or responsibility state.

**Impact:** The system cannot distinguish a player failing an assigned responsibility from a teammate or system failure. This creates unfair player evaluation.

**Required decision:** Add defensive assignment and unit snapshots, target opponent/runner, protected zone/lane, expected responsibility, actual response, and attribution evidence.

### HR-005 — Role model is described but role taxonomy is absent

**Evidence:** Role precedence and effective-dated role assignments are specified at [lines 49-50](C:/Users/ASUS/OFF-Ball/offball_data_model_design.md:49), but there is no role definition, role version, role-to-position mapping, club role profile, or role evidence entity.

**Impact:** Role-based benchmarking is not reproducible. A role label can change meaning across clubs, seasons, or metric versions.

**Required decision:** Add controlled role taxonomy, role version, role attributes, club aliases, position mappings, assignment evidence, and role model version.

### HR-006 — Recruitment domain omits market and squad realities

**Evidence:** Recruitment briefs include budget, contract, physical, and development criteria at [REQ-011](C:/Users/ASUS/OFF-Ball/football_offball_project.md:186), but the MVM excludes contract and does not model market availability, transfer window, valuation snapshot, registration eligibility, work permit, squad slot, agent, or recruitment decision history.

**Impact:** A player may be a perfect behavioural fit but unavailable, ineligible, unaffordable, or incompatible with squad registration. The product cannot support a professional recruitment decision end to end.

**Required decision:** Either explicitly narrow Release 1 to behavioural discovery or add a separate recruitment-market integration boundary with effective-dated snapshots and provenance.

### HR-007 — Human validation is not modeled as a governed annotation process

**Evidence:** Analysts must correct classifications at [REQ-044](C:/Users/ASUS/OFF-Ball/football_offball_project.md:218), while the MVM lists `scouting_observation` and `audit_event` but no annotation task, label schema, adjudication, reviewer agreement, or ground-truth dataset.

**Impact:** The 80% classification acceptance target cannot be measured consistently, and corrections cannot be safely used for model evaluation or retraining.

**Required decision:** Add annotation task, label, reviewer, adjudication, disagreement, sampling, and benchmark-set entities separate from ordinary scouting notes.

### HR-008 — Video rights and asset lifecycle are incomplete

**Evidence:** Video evidence is described as timestamps, frame ranges, clips, playlists, and external links, but the model lacks asset ownership, rights window, territory, expiry, access status, rendition, provider asset ID, and deletion behavior.

**Impact:** A report may retain broken or unauthorised links, and evidence availability cannot be governed when rights expire.

**Required decision:** Add video asset, rights entitlement, evidence locator, derived clip, playlist membership, and access-status concepts.

### HR-009 — Data quality is represented as a few output fields rather than a quality system

**Evidence:** Products carry `data_quality_status`, `coverage_ratio`, `confidence_score`, and `source_count` at [line 411](C:/Users/ASUS/OFF-Ball/offball_data_model_design.md:411), while requirements call for many dimensions and thresholds at [REQ-045 and REQ-046](C:/Users/ASUS/OFF-Ball/football_offball_project.md:220).

**Impact:** There is no per-rule result, measurement window, threshold version, quarantine record, owner, resolution, or quality trend. A single status cannot explain why a profile was downgraded.

**Required decision:** Model quality rule, check execution, result, affected record/partition, quarantine reason, remediation status, and publication gate.

### HR-010 — Tracking scale and retention plan is not viable as currently stated

**Evidence:** The design stores one Silver row per match-frame-player and retains source/canonical/derived data indefinitely at [lines 54, 64, and 346](C:/Users/ASUS/OFF-Ball/offball_data_model_design.md:54).

**Impact:** At 20 Hz, a 90-minute match produces roughly 2.4 million player-position rows for 22 players before ball, quality, metadata, and substitutes. At thousands of matches, this becomes billions of rows. Indefinite full-resolution retention creates storage, compaction, governance, and query-cost risk.

**Required decision:** Define raw retention tiers, derived-feature retention, compaction strategy, file sizing, clustering/Z-order or liquid clustering, match-level isolation, hot versus cold serving, and explicit query patterns. Do not use an unbounded high-cardinality partition scheme without benchmarks.

## 5. Medium Findings

### MR-001 — Squads are in assumptions but not modeled consistently

The design states `organisation -> club -> team -> squad` at [line 45](C:/Users/ASUS/OFF-Ball/offball_data_model_design.md:45), but squad is absent from the ERD and MVM entity list at [line 303](C:/Users/ASUS/OFF-Ball/offball_data_model_design.md:303). A squad is needed for recruitment gaps, roster planning, academy pathways, and squad-role context.

### MR-002 — Contracts and registrations are conflated or incomplete

The domain table lists contract at [line 71](C:/Users/ASUS/OFF-Ball/offball_data_model_design.md:71), but only registration appears in the MVM. Registration, employment contract, loan, transfer, and eligibility are distinct temporal concepts and should not be inferred from one another.

### MR-003 — Formation and tactical instruction are missing

The product promises tactical fit and contextual evaluation, but there is no formation instance, team shape snapshot, tactical instruction, rest-defence configuration, or coach game-plan version. This limits explanation of whether a run or press was correct.

### MR-004 — Opportunity denominators are not first-class entities

The model stores rates but not the opportunities from which rates are calculated: eligible pressing opportunities, possible runs, receiving opportunities, defendable lanes, or defensive assignments. Without opportunity facts, a low count is indistinguishable from low opportunity.

### MR-005 — Negative actions and failed actions lack a common ledger

Space creation has separate negative-impact language, but no generic action-value ledger links positive, negative, neutral, and unknown outcomes to a common event, player, team, and counterfactual. This risks inconsistent scoring across domains.

### MR-006 — Metric configuration cannot safely express the stated governance

`metric_configuration.configuration` is untyped JSON, there is no effective interval, approval state constraint, owner, dependency list, or environment promotion record. The PostgreSQL boundary therefore cannot guarantee that a club-specific configuration is compatible with a Gold metric version.

### MR-007 — Workflow history is incomplete

`shortlist_item` stores only current status and reason. There is no status-transition history, shortlist membership history, assignment history, comments, tasks, approvals, or decision outcome. This weakens auditability and retrospective recruitment analysis.

### MR-008 — Report and evidence references are weakly typed

Reports use `subject_key` and a JSON payload, while observation evidence uses `evidence_ids` JSON. This makes referential integrity, evidence expiry, selective access, and impact analysis difficult.

### MR-009 — AI governance lacks model lifecycle and risk classification

The artifacts store model version and approval fields, but not model registry identity, training-data lineage, evaluation set, bias evaluation, intended use, risk tier, prompt/version for generative outputs, or rollback status.

### MR-010 — Operational SLOs omit data pipeline and recovery objectives

The design includes application availability and general disaster recovery, but not ingestion freshness by provider, metric publication SLA, RPO/RTO values, replay time, backfill behavior, or provider outage handling.

## 6. Missing Football Concepts

The following concepts should be added or explicitly declared out of scope:

- Competition format, stage, round, group, playoff, matchday, and promotion/relegation context.
- Match period, stoppage, extra time, abandonment reason, replay, and reschedule lineage.
- Starting XI, bench, substitution event, lineup segment, shirt number, captain, and goalkeeper role.
- Formation instance, tactical shape, team width/depth, line height, field orientation, and game-plan version.
- Score-state timeline, numerical superiority, red-card state, goal difference, and match importance.
- Possession owner, possession uncertainty, restart, duel contest, second ball, and transition boundary.
- Set-piece type, taker, marking scheme, restart location, and dead-ball state.
- Squad, roster eligibility, contract, loan, transfer, registration, transfer window, and squad slot.
- Competition strength, provider calibration, pitch surface/dimensions, weather, altitude, and venue context where relevant.
- Official, referee decision, foul advantage, card state, and stoppage cause where event interpretation depends on them.

## 7. Missing Off-Ball Concepts

- Eligible opportunity: the situation in which a player could have run, pressed, covered, scanned, or protected a lane.
- Action intent versus observed movement.
- Action lifecycle: candidate, classified, reviewed, approved, rejected, superseded.
- Run start/end reason, trigger, objective, target zone, target teammate, and defensive response.
- Receiving opportunity and teammate benefit for space creation.
- Counterfactual baseline and expected-value delta.
- Space geometry: zone, lane, polygon, defender displacement, occupation interval, and vacancy ownership.
- Press target, trigger, start/end, approach angle, cover shadow, support, bypass, resistance, and outcome timing.
- Defensive assignment, target opponent, protected zone, expected responsibility, unit snapshot, and failure mode.
- Scan observation provenance and observability status.
- Negative/neutral action value and opportunity-adjusted denominators.
- Human label, adjudicated truth, reviewer agreement, and model-error category.

## 8. Scalability and Performance Concerns

### 8.1 Tracking fact volume

Frame-player data is the largest table by orders of magnitude. It should not be treated like ordinary dimensional data. The design needs:

- Immutable raw file/object retention separate from query-optimised derived tables.
- Match-level or date-level clustering rather than uncontrolled high-cardinality partitions.
- Compact encodings and predictable file sizes.
- Separate high-resolution replay store from feature-level analytical store.
- Precomputed windows and action intervals for dashboards.
- Benchmarks for match query, player-season query, and backfill workloads.

### 8.2 Reprocessing blast radius

Late events, identity merges, metric changes, and model changes can invalidate historical outputs. The design needs dependency-aware incremental recomputation, affected-match/player partition tracking, and publication snapshots. Full historical recomputation should not be the default.

### 8.3 Gold serving

Gold products are described as broad views but lack explicit serving grains and cardinality limits. Player-season profiles, player-match profiles, evidence joins, and comparison queries should be materialised separately from raw action exploration. Evidence and tracking joins should never be performed ad hoc for every dashboard request.

### 8.4 Multi-tenant scale

Row filtering by `club_id` is necessary but not sufficient. Shared global data and private overlays need separate physical and logical access paths. The design should define whether club customisations are overlay tables, cloned products, or parameterised views, and how a global metric version is promoted without breaking club-published reports.

### 8.5 PostgreSQL workload boundary

PostgreSQL is appropriate for workflow state, but JSON-heavy reports, audit events, and outbox rows require partitioning, retention, indexing, and idempotency policies. PostgreSQL should not become the analytical store or the authoritative copy of large evidence payloads.

## 9. Model Integrity Issues

1. The ERD includes only a subset of the entities named in the logical and MVM descriptions, so it is not a complete authoritative relationship model.
2. The ERD shows `SpaceCreationEvent.primaryRunId` but not the required contributor and target entities.
3. `PlayerMetricValue.windowKey` is an untyped string rather than a relationship to an evaluation window with dates, competition, role, and denominator.
4. `MetricVersion.calculationSpec` is an opaque string; it needs structured dependencies and an immutable artifact reference.
5. The PostgreSQL schema allows a global `metric_configuration` with nullable `club_id`, but does not distinguish global approved configuration from a club override.
6. `brief_criterion` does not enforce that weights sum to 1 or that required criteria are present before approval.
7. `scouting_observation.revision` implies versioning but does not preserve prior revisions.
8. `audit_event` is not protected against update/delete and has no hash chain or append-only enforcement.
9. `outbox_event` has no idempotency key, deduplication constraint, dead-letter state, or retry scheduling fields.
10. No schema-level policy prevents a shortlist item from referencing a player that is not resolvable in the lakehouse registry.

## 10. Recommended Remediation Sequence

### Gate 1 — Production safety

- Resolve `citext` deployment.
- Define canonical ID synchronization between PostgreSQL and Delta.
- Implement tenant isolation and test deny-by-default access.
- Make audit and correction history append-only and queryable.
- Define operational RPO, RTO, freshness, replay, and backfill behavior.

### Gate 2 — Football truth

- Add match state, lineup, formation, tactical shape, score timeline, substitutions, and set-piece context.
- Formalise possession and phase semantics.
- Define opportunity denominators.
- Add role taxonomy and effective role evidence.

### Gate 3 — Off-ball validity

- Add action lifecycle and annotation entities.
- Add space target, baseline/counterfactual, affected defenders, receiving opportunity, and attribution ledger.
- Add press target, trigger, support, bypass, and outcome context.
- Add defensive assignment, unit state, responsibility, and failure mode.

### Gate 4 — Analytical reproducibility

- Add source manifests, ingestion runs, quality checks, feature sets, model artifacts, metric executions, and publication snapshots.
- Replace opaque metric strings with structured versioned specifications.
- Define correction propagation and selective recomputation.

### Gate 5 — Scale and serving

- Benchmark frame-player storage and query patterns.
- Separate high-resolution tracking retention from analytical features.
- Add clustering/compaction and hot/cold retention tiers.
- Materialise dashboard products at explicit grains.
- Load-test multi-tenant serving and report/evidence access.

## 11. Approval Recommendation

**Recommendation: Do not approve for production implementation yet.**

Approve the current artifacts as a **domain discovery baseline** and proceed only with a remediation design sprint covering the five critical findings and the football-truth gate. The product vision is sound, but professional-club credibility depends on being able to answer, for every off-ball score:

1. What was the player's opportunity?
2. What tactical state existed?
3. What exactly changed?
4. What was the counterfactual?
5. Who else contributed?
6. How reliable is the evidence?
7. Can the result be reproduced and securely shown to the right club?

Until those questions are represented as first-class data and governance concepts, the platform risks producing attractive but non-defensible player rankings.
