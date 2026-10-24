# Off-Ball Football Analytics Remediation Sprint

**Sprint focus:** Football Truth Layer, Space Creation Framework, Pressing Intelligence Framework  
**Sprint type:** Data-model remediation and analytical design  
**Status:** Proposed  
**Duration:** 3 weeks, with a design review at the end of each week  
**Primary outcome:** Make off-ball outputs football-valid, explainable, opportunity-adjusted, and reproducible.

## 1. Sprint Objective

Remediate the football analytics weaknesses identified in the senior architecture review without expanding into enterprise security, deployment infrastructure, PostgreSQL hardening, or production operations.

At the end of the sprint, the platform must be able to explain an off-ball action in football terms:

1. What opportunity existed?
2. What tactical state existed?
3. What did the player do?
4. What changed because of the action?
5. Who else contributed?
6. What was the counterfactual or baseline?
7. How reliable is the evidence?
8. Which metric and model version produced the conclusion?

## 2. Scope Priorities

| Priority | Workstream | Outcome |
|---|---|---|
| P0 | Football Truth Layer | A canonical, versioned match context that supports valid denominators and tactical interpretation. |
| P1 | Space Creation Framework | A defensible space opportunity, action, counterfactual, and contribution model. |
| P1 | Pressing Intelligence Framework | An opportunity-adjusted model of pressing triggers, actions, support, bypass, and outcomes. |

## 3. Explicitly Deferred

The sprint will not address:

- Authentication, row-level security, tenant enforcement, or privacy controls.
- PostgreSQL deployment defects, extensions, indexes, or schema execution.
- Databricks cluster sizing, storage policies, orchestration, disaster recovery, or SLOs.
- Contract, transfer-market, valuation, medical, injury, or financial models.
- Live-match streaming.
- Computer-vision implementation for scanning.
- UI implementation or dashboard styling.

Security and infrastructure findings remain open review items and must not be interpreted as resolved by this sprint.

## 4. Design Principles

1. **Football truth before derived intelligence:** No space or pressing score is published without canonical match state.
2. **Opportunity before outcome:** A count is meaningful only when eligible opportunities are modeled.
3. **Context is part of the action:** Score state, phase, formation, pitch zone, support, and tactical responsibility are not optional decorations.
4. **Counterfactuals are explicit:** Incidental vacancy must not be treated as created space.
5. **Attribution is conserved and inspectable:** Positive contributions reconcile to the event value; negative effects are separate.
6. **Separate observation from interpretation:** Provider observations, derived actions, analyst labels, and published metrics remain distinct.
7. **Version every football definition:** Changes to possession, phase, role, action detection, or scoring produce a new analytical version.
8. **Prefer uncertainty to false precision:** Unknown, unavailable, unresolved, and low-confidence states are modeled explicitly.

## 5. Workstream A — Football Truth Layer

### Goal

Create the canonical match-context layer required to interpret movement, space, pressing, and defensive actions consistently across providers and competitions.

### A1. Canonical match state

Define first-class entities and grains for:

- Competition, competition stage, round, season, matchday, and fixture.
- Match occurrence, status, postponement, replay, abandonment, and extra time.
- Home and away team participation.
- Match period, stoppage time, elapsed match seconds, and provider clock alignment.
- Score-state intervals, goal events, numerical advantage, and match importance.
- Field orientation and attacking direction by team and period.

**Required outputs**

- Canonical match-state glossary.
- Match-state entity and relationship specification.
- State-transition rules for kickoff, goal, restart, halftime, substitution, red card, extra time, abandonment, and final whistle.
- Provider mapping and conflict-resolution table.

### A2. Team structure and tactical context

Define:

- Squad and match squad.
- Starting lineup, bench, substitution, and lineup segments.
- Position and tactical role assignment.
- Formation instance and formation changes.
- Team shape snapshots: line height, width, depth, compactness, and defensive block.
- Tactical instruction or game-plan context where available.
- Defensive unit and functional unit membership.

**Required outputs**

- Versioned position and role taxonomy.
- Role assignment precedence and confidence rules.
- Formation and shape snapshot specification.
- Lineup-segment rules for substitutions and role changes.

### A3. Possession and phase engine

Define canonical rules for:

- Possession owner and possession confidence.
- Possession start, continuation, loss, contest, and unresolved interval.
- Possession sequence.
- Attacking phase, defensive phase, attacking transition, defensive transition.
- Set piece, restart, dead ball, second ball, and duel contest.
- Pressing and defensive opportunities during uncertain possession.

**Required outputs**

- Versioned possession-state machine.
- Phase classification rules.
- Maximum unresolved interval and confidence treatment.
- Provider reconciliation examples for duels, tackles, deflections, rebounds, goalkeeper claims, and loose balls.

### A4. Opportunity denominators

Define reusable opportunity facts for:

- Off-ball run opportunity.
- Receiving-space opportunity.
- Space-creation opportunity.
- Pressing opportunity.
- Cover and lane-protection opportunity.
- Runner-tracking opportunity.
- Scan opportunity.

Each opportunity must include:

- Match and time interval.
- Team and player eligibility.
- Tactical phase.
- Role and assignment.
- Location and target zone or lane.
- Eligibility reason.
- Opportunity confidence.
- Whether the player acted, declined, failed, or was not observable.

### Football Truth Layer exit criteria

- A replayed example match produces one canonical match timeline.
- Possession and phase assignments are deterministic for all published examples.
- Substitution, extra-time, score-state, formation, and field-orientation cases are represented.
- Every downstream space and pressing action can reference a canonical phase, tactical state, and opportunity.
- Analysts approve at least 90% of sampled state transitions and opportunity labels.

## 6. Workstream B — Space Creation Framework

### Goal

Replace the current high-level space score with an auditable framework that separates opportunity, movement, spatial change, teammate benefit, opponent response, and attribution.

### B1. Space ontology

Define the controlled vocabulary for:

- Space type: depth, width, half-space, central, channel, box, between-lines, behind-line, exit space, and defensive cover space.
- Spatial object: zone, lane, corridor, polygon, receiving radius, passing window, or defensive gap.
- Space state: occupied, available, constrained, opened, closed, or contested.
- Space creator, beneficiary, affected defender, supporting teammate, and team-structure contributor.

### B2. Space opportunity and baseline

Create a `space_opportunity` concept at the smallest meaningful tactical interval. It must describe:

- Pre-action spatial state.
- Candidate target zone or passing lane.
- Eligible teammate or ball-receiver.
- Relevant defenders and defensive line.
- Team shape and possession phase.
- Baseline availability without the candidate movement.
- Opportunity confidence and observability.

The baseline must support one of these versioned methods:

1. Matched historical situations.
2. Defender-trajectory baseline.
3. Rule-based spatial baseline.
4. Analyst-labeled baseline.

The selected method must be stored with the result.

### B3. Movement-to-space causal chain

Model the chain:

`space opportunity -> candidate movement -> movement classification -> defender response -> spatial change -> teammate opportunity -> football outcome`

A space event must be able to reference:

- One or more runs or movements.
- One or more affected defenders.
- The target zone or lane.
- Before and after geometry.
- Teammate receiving or progression opportunity.
- Opponent response.
- Resulting possession-value or progression change.

### B4. Space measurement

Define measurable components, with units and sign conventions:

- Defender displacement.
- Increase in teammate receiving radius.
- Passing-lane opening duration.
- Zone vacancy duration.
- Defensive-line distortion.
- Separation from marker.
- Expected progression or possession-value delta.
- Outcome contribution.

Do not combine these into one score until component-level quality is available.

### B5. Attribution ledger

Define a contribution ledger with:

- Primary creator.
- Supporting creators.
- Beneficiary.
- Affected defenders.
- Team-structure contribution.
- Positive contribution share.
- Negative impact.
- Attribution method.
- Attribution confidence.

Positive contribution shares must sum to 100% for each published space event. Negative impact must be represented separately and must not erase source provenance.

### B6. Space action lifecycle

Every candidate must support:

`candidate -> classified -> analyst reviewed -> approved -> rejected -> superseded`

Store:

- Detection method.
- Feature snapshot.
- Model/rule version.
- Analyst label.
- Rejection reason.
- Evidence references.
- Review agreement.

### Space Creation Framework exit criteria

- Analysts can distinguish created space from incidental or pre-existing space in labeled examples.
- Every published space event has an opportunity, baseline method, target geometry, affected players, and evidence.
- Contribution shares reconcile to 100% for positive value.
- A space event can be traced to movement, tracking interval, phase, and resulting teammate opportunity.
- A metric can separately report opportunity rate, action rate, space change, and outcome value.
- At least 80% of sampled classifications reach analyst agreement, with disagreement reasons captured.

## 7. Workstream C — Pressing Intelligence Framework

### Goal

Model pressing as a contextual defensive decision, not merely a distance-to-ball event.

### C1. Pressing opportunity

Define a `pressing_opportunity` for situations where a player could reasonably apply pressure, screen, close a lane, or coordinate a press.

Required context:

- Opponent possession and ball-carrier identity.
- Trigger type.
- Ball zone and direction of play.
- Player role and tactical assignment.
- Team line height and defensive block.
- Teammate support and cover.
- Available passing options.
- Opponent body orientation where available.
- Score state, fatigue proxy, and transition state where available.

### C2. Press trigger ontology

Support controlled trigger types:

- Poor first touch.
- Backward pass.
- Sideways pass.
- Isolated receiver.
- Receiver facing own goal.
- Slow or exposed build-up.
- Transition after loss.
- Predictable passing lane.
- Goalkeeper distribution.
- Tactical instruction trigger.

Each trigger requires:

- Trigger event or time interval.
- Trigger confidence.
- Provider evidence or derived rationale.
- Whether the trigger was available to the player.

### C3. Press action

Define a pressing action with:

- Pressing player.
- Ball carrier.
- Start and end time.
- Start and end location.
- Closing distance and speed.
- Approach angle.
- Cover-shadow lane.
- Supporting teammates.
- Player role and responsibility.
- Tactical phase.
- Pass options before and after the action.
- Action classification and confidence.

### C4. Press outcome and bypass

Model outcome as potentially multi-valued, with one primary outcome:

- Turnover.
- Forced backward pass.
- Forced long ball.
- Passing-lane closure.
- Delayed progression.
- Reduced receiving options.
- Foul won or conceded.
- Press bypassed.
- Press resisted.
- No observable outcome.

For bypassed presses, capture:

- Bypass location.
- Bypassing action.
- Which lane or support failed.
- Recovery action.
- Subsequent threat or progression.

### C5. Coordinated pressing

Add team-level coordination concepts:

- Press unit.
- Press wave.
- Trigger synchronisation.
- Supporting player.
- Cover-shadow responsibility.
- Rest-defence state.
- Pressing chain.

This prevents assigning the entire result to the nearest player when the value came from coordinated pressure.

### C6. Opportunity-adjusted metrics

Define separate measures for:

- Pressing opportunity rate.
- Press initiation rate.
- Trigger recognition rate.
- Pressure execution rate.
- Lane closure rate.
- Support availability rate.
- Successful press rate.
- Bypass rate.
- Recovery effectiveness.
- Team coordination value.

Do not publish a single pressing score without exposing these components.

### Pressing Intelligence Framework exit criteria

- A press can be traced from trigger to action to outcome.
- The model distinguishes opportunity, initiation, execution, support, and outcome.
- Presses are not rewarded solely for distance or speed toward the ball.
- Bypassed and unsupported presses are visible.
- Individual and coordinated team contributions are separately reportable.
- Analysts reach at least 80% agreement on sampled opportunity, action, and outcome labels.

## 8. Cross-Workstream Model Changes

The three workstreams must share the following canonical concepts:

| Shared concept | Purpose |
|---|---|
| `match_state_interval` | Score, period, numerical state, field orientation, and match status. |
| `phase_interval` | Possession, attacking/defensive phase, transition, set piece, and confidence. |
| `lineup_segment` | Player participation, role, position, and effective interval. |
| `team_shape_snapshot` | Formation, line height, width, depth, compactness, and unit state. |
| `opportunity` | Eligibility, tactical assignment, target, observability, and confidence. |
| `action_instance` | Candidate/approved derived behaviour with version and evidence. |
| `spatial_object` | Zone, lane, corridor, polygon, or receiving area. |
| `attribution_ledger` | Positive shares, negative impact, contributors, and method. |
| `evidence_link` | Events, tracking intervals, video, features, labels, and model outputs. |
| `quality_assertion` | Rule, result, threshold, affected records, and publication status. |

## 9. Sprint Plan and Tasks

### Week 1 — Football Truth Layer

- [ ] T001 Freeze the canonical football glossary and define entity grains for match, match state, phase, lineup segment, formation, team shape, role, and opportunity.
- [ ] T002 Document match-state transition rules for kickoff, goals, restarts, halftime, substitutions, cards, extra time, abandonment, and final whistle.
- [ ] T003 Define the possession and phase state machine, including uncertain intervals and provider conflict resolution.
- [ ] T004 Define the role taxonomy, role versions, position mappings, assignment precedence, and role confidence.
- [ ] T005 Define formation, team-shape, defensive-unit, field-orientation, and tactical-assignment snapshots.
- [ ] T006 Define opportunity grains and eligibility rules for runs, space creation, pressing, cover, tracking, and scanning.
- [ ] T007 Produce worked examples for normal time, extra time, substitution, red card, set piece, transition, duel, and incomplete-data matches.
- [ ] T008 Run a football analyst review of the Football Truth Layer and record unresolved semantic conflicts.

### Week 2 — Space Creation Framework

- [ ] T009 Define the space ontology, spatial-object types, target-zone vocabulary, and space-state transitions.
- [ ] T010 Define `space_opportunity` and its pre-action baseline, target, eligible beneficiaries, affected defenders, and confidence.
- [ ] T011 Define the movement-to-space causal chain and the action lifecycle from candidate to approved or rejected.
- [ ] T012 Define geometric and outcome features for defender displacement, receiving space, lane opening, vacancy, separation, and value delta.
- [ ] T013 Define counterfactual methods, method versioning, minimum evidence, and fallback behavior when a baseline cannot be estimated.
- [ ] T014 Define the attribution ledger and reconciliation rules for primary, supporting, beneficiary, defender, team-structure, positive, and negative contributions.
- [ ] T015 Define space-specific opportunity-adjusted metrics and reporting components.
- [ ] T016 Produce annotated examples for depth run, decoy run, width run, underlap, overload, accidental vacancy, and failed movement.
- [ ] T017 Run analyst adjudication and record classification agreement and disagreement categories.

### Week 3 — Pressing Intelligence Framework

- [ ] T018 Define the pressing opportunity ontology and eligibility rules by phase, role, ball zone, trigger, and support context.
- [ ] T019 Define the trigger taxonomy and source/evidence requirements.
- [ ] T020 Define pressing action grain, start/end rules, distance/speed/angle features, cover shadow, support, and assignment.
- [ ] T021 Define outcome and bypass taxonomy, including primary outcome selection and unknown outcome handling.
- [ ] T022 Define coordinated pressing entities: press unit, press wave, support chain, rest-defence state, and recovery action.
- [ ] T023 Define opportunity-adjusted pressing metrics and component-level reporting.
- [ ] T024 Produce annotated examples for backward-pass trigger, isolated receiver, goalkeeper press, coordinated press, unsupported press, bypassed press, and resisted press.
- [ ] T025 Run analyst adjudication and record classification agreement and disagreement categories.

### Final integration and approval

- [ ] T026 Link every space and pressing action to canonical match state, phase, lineup segment, role, opportunity, evidence, and quality result.
- [ ] T027 Define shared versioning rules for football truth, derived actions, counterfactuals, attribution, and metrics.
- [ ] T028 Produce the revised conceptual model, logical model, ERD, and MVM entity inventory.
- [ ] T029 Produce a metric dictionary with numerator, denominator, opportunity definition, exclusions, confidence gate, and interpretation for each approved metric.
- [ ] T030 Execute the Football Analytics Design Review and obtain sign-off from the Lead Football Analyst, Head of Recruitment, Performance Analyst, and Data Product Owner.

## 10. Dependencies

```text
Football glossary
  -> Match state and possession/phase rules
  -> Role, formation, shape, and opportunity definitions
  -> Space opportunity and counterfactual design
  -> Pressing opportunity and outcome design
  -> Shared metric dictionary
  -> Revised models and MVM
```

Space and pressing work may proceed in parallel after the shared football glossary, phase model, role model, and opportunity pattern are approved. Their final metrics cannot be approved independently of the Football Truth Layer.

## 11. Required Sprint Deliverables

1. Football Truth Layer glossary and state-machine specification.
2. Canonical match-state, phase, role, formation, shape, and opportunity model.
3. Space Creation Framework ontology and attribution specification.
4. Pressing Intelligence Framework ontology and attribution specification.
5. Shared evidence, quality, lifecycle, and versioning specification.
6. Worked match examples and annotated analyst labels.
7. Metric dictionary with denominators and publication gates.
8. Revised conceptual model and logical model.
9. Revised ERD and MVM inventory.
10. Decision log containing rejected alternatives and unresolved issues.

## 12. Sprint Acceptance Criteria

- **AC-001:** Every published off-ball action references a canonical match state, phase, player participation interval, role context, opportunity, evidence set, quality result, and model version.
- **AC-002:** Possession and phase rules produce deterministic results for the approved worked examples, including uncertain intervals.
- **AC-003:** Space creation distinguishes pre-existing, incidental, created, and contested space.
- **AC-004:** Space creation includes target geometry, affected defenders, beneficiary opportunity, baseline/counterfactual method, and contribution ledger.
- **AC-005:** Positive space contribution shares reconcile to 100% per approved event.
- **AC-006:** Pressing distinguishes opportunity, trigger, initiation, execution, support, bypass, and outcome.
- **AC-007:** Pressing reports opportunity-adjusted components rather than relying on distance-to-ball alone.
- **AC-008:** Defensive and pressing responsibility can be attributed to an individual, support player, unit, and team structure.
- **AC-009:** All derived actions support candidate, reviewed, approved, rejected, and superseded states.
- **AC-010:** Analyst agreement reaches at least 80% for sampled space and pressing classifications, with disagreements categorized.
- **AC-011:** Every approved metric has a defined numerator, denominator, eligibility rule, exclusions, confidence gate, and interpretation.
- **AC-012:** The revised model contains no unexplained score that cannot be traced to opportunity, observation, transformation, and evidence.

## 13. Review Questions for the Final Gate

The final review must explicitly answer:

1. Can two analysts classify the same opportunity using the same rule?
2. Can the model distinguish opportunity from action?
3. Can the model distinguish action from outcome?
4. Can the model distinguish individual contribution from team structure?
5. Can every score be recalculated from versioned evidence?
6. Can a club explain why a player ranked highly or poorly?
7. Can the model represent “not observable” without treating it as failure?
8. Can the same metric be compared across leagues without hiding provider or tactical differences?

## 14. Deferred Review Items

The following findings from the architecture review remain open and are intentionally excluded from this sprint:

- PostgreSQL `citext` bootstrap failure.
- PostgreSQL-to-Delta referential integration.
- Tenant isolation and row-level security.
- Immutable audit enforcement.
- Video rights and asset lifecycle implementation.
- Tracking storage cost, retention, and serving strategy.
- Pipeline SLOs, disaster recovery, and production infrastructure.

