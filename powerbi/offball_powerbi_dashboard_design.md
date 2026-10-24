# Off-Ball Power BI Dashboard Design

## 1. Report navigation

1. Executive Overview
2. Club Performance
3. Match Centre
4. Team Off-Ball
5. Player Performance
6. Recruitment Pipeline
7. Space Creation Explorer
8. Pressing Explorer
9. Data Health

Global slicers are season, competition, date window, team, opponent, home/away, athlete, role, and quality status. The report landing page defaults to the latest published calculation run.

## 2. Executive views

### Executive Overview

**Purpose:** Give leadership a concise view of results, performance direction, player pipeline, and data trust.

Top cards:

- Points per Match
- Goal Difference
- Fixtures
- Space Observation Rate
- Press Recovery Rate
- Player Pipeline Count
- Data Coverage Status
- Last Published Refresh

Visuals:

- Results and points trend by reporting period.
- Space creation and pressing rates versus previous period.
- Top five positive and bottom five negative KPI movements.
- Player pipeline by position, age band, contract status, and recruitment status.
- Data-health tile showing stale, insufficient-sample, and warning products.

Drill-through: Club Performance, Recruitment Pipeline, Data Health.

### Club Performance

**Purpose:** Compare team and competition performance without exposing unsupported precision.

Visuals:

- Team KPI scorecards with numerator, denominator, coverage, and confidence tooltip.
- Team trend lines for space conversion, press recovery, and positive press outcomes.
- Competition/season matrix for fixtures, points, goals, and KPI rates.
- Home versus away comparison.
- Quality-status indicator beside every rate.

## 3. Coach views

### Match Centre

**Purpose:** Review one fixture from outcome to event timeline and actionable off-ball patterns.

Visuals:

- Match header: opponent, venue, result, score, competition, match date.
- Team summary cards: phase coverage, possession/phase exposure, pressing, space creation.
- Timeline of score events, incidents, phase changes, pressing opportunities, and recoveries.
- Team comparison matrix for opportunities, actions, support, bypass, recoveries, and outcomes.
- Player contribution table with participation minutes, space outcomes, pressing actions, and attribution.

Drill-through: Space Creation Explorer, Pressing Explorer, Player Performance.

### Team Off-Ball

**Purpose:** Support weekly coaching review at team and evaluation-window grain.

Visuals:

- Eligible, observed, and successful space opportunities.
- Space conversion by space type and phase.
- Pressing funnel: opportunities → triggers → actions → support → recovery → positive outcome.
- Attribution contribution by player and outcome type.
- Confidence/coverage scatter plot, with low-coverage points visibly marked.
- Fixture selector for match-level comparison.

### Space Creation Explorer

**Purpose:** Inspect evidence-backed space creation without treating missing tracking as zero performance.

Visuals:

- Opportunity detail table with baseline, counterfactual, outcome, attribution, evidence, and quality.
- Space funnel and conversion rate by player/team.
- Expected-value delta distribution.
- Tracking, baseline, and counterfactual coverage cards.
- Detail drill-through to fixture timeline.

### Pressing Explorer

**Purpose:** Identify pressing execution and failure modes.

Visuals:

- Press funnel with opportunity, trigger, action, support, bypass, recovery, and positive outcome.
- Time-to-action distribution.
- Press type matrix by team, player, and opponent.
- Recovery map/table with evidence status and confidence.
- Unresolved opportunity count and coverage warning.

## 4. Recruitment views

### Player Performance

**Purpose:** Compare a player against a declared peer cohort while preserving sample and exposure context.

Visuals:

- Player identity and availability card.
- Participation minutes and appearances.
- Per-90 event and pressing measures.
- Space observation, conversion, expected-value delta, and attribution share.
- Radar or bar comparison against cohort median, only when minimum sample is met.
- Evidence and coverage panel.

Required controls:

- Cohort definition.
- Role/position.
- Season.
- Minimum minutes.
- Minimum opportunities.

### Recruitment Pipeline

**Purpose:** Prioritize candidates for deeper analyst review, not automate signing decisions.

Visuals:

- Candidate table: athlete, age, role, club, contract status, minutes, opportunity exposure, space conversion, press recovery, attribution share, confidence, and coverage.
- Scatter plot: performance value versus evidence coverage.
- Shortlist trend by evaluation period.
- Flags for insufficient sample, unresolved attribution, and stale data.

Rules:

- Never rank a candidate solely on a rounded rate.
- Show numerator and denominator beside every rate.
- Suppress ranking when the declared cohort or minimum sample is missing.
- Keep scouting notes and external recruitment decisions outside the governed KPI facts.

## 5. Data Health

**Purpose:** Make model trust visible to business users and operators.

Visuals:

- Last successful refresh by Gold product.
- Product freshness lag versus SLA.
- Published, warning, insufficient-sample, suppressed, and failed row counts.
- Missing lineage count by source snapshot and calculation run.
- Coverage trend for tracking, baseline, counterfactual, and evidence-linked attribution.

## 6. UX and visual standards

- Green: published and coverage at least 80%.
- Amber: warning or coverage from 50% to 79%.
- Red: failed, suppressed, or coverage below 50%.
- Gray: not available or insufficient sample.
- Never use red for a genuinely poor football result and data-quality failure simultaneously; use separate result and trust indicators.
- Every KPI tooltip contains: definition, metric version, numerator, denominator, sample size, coverage, confidence, quality reason, and refresh time.

## 7. Required drill-through and export actions

- Fixture drill-through from every match/team visual.
- Athlete drill-through from every player visual.
- Space and pressing detail drill-through from KPI cards.
- Export detail must include calculation run and metric version.
- Executive pages export only published aggregate rows.
- Analyst pages may export warning and insufficient-sample rows with visible status labels.
