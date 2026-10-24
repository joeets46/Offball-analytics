# Off-Ball Analytics Platform

Modern football analytics is strongly shaped by on-ball events because event datasets are widely available, structured, and relatively straightforward to count. That focus is valuable, but it leaves a large part of football performance difficult to observe consistently.

Players typically have possession of the ball for only a small fraction of a 90-minute match—often estimated by scouts and analysts at approximately three to five minutes. For the rest of the match, they move, position themselves, create space, press, support teammates, manage defensive distances, and influence play without touching the ball. Much of that value is therefore expressed through actions that traditional statistics do not adequately capture.

Off-Ball exists to make those behaviors more observable, measurable, and actionable. It provides a repository-first football analytics platform for professional clubs, combining football truth, opportunities, space creation, pressing, attribution, governed KPIs, analytics marts, and Power BI decision-support products.

## Why Off-Ball Analytics Matters

Space creation, positioning, movement, pressing, support, and defensive organization are not isolated concepts: they shape the options available to teammates, the pressure applied to opponents, and the quality of subsequent football actions. Opportunity modeling helps distinguish situations in which a player could influence play from situations in which an action was actually observed. Attribution helps connect shared team outcomes to individual contributions without reducing complex football behavior to a single unqualified number.

Better off-ball intelligence can help:

- **Clubs** evaluate performance across more of the match, not only recorded touches and events.
- **Scouts and recruitment teams** compare players using role- and opportunity-aware evidence.
- **Coaches** identify how teams create space, support attacks, press, recover possession, and defend collectively.
- **Analysts** investigate match patterns with explicit coverage, confidence, sample-size, and lineage context.

The platform does not replace professional judgment. Its purpose is to provide a more complete and explainable evidence base for football decisions.

Technically, the platform follows the Databricks Sports & Entertainment MVM methodology and uses a Medallion Architecture across Bronze, Silver, and Gold layers.

## 1. Project Overview

Off-Ball supports:

- Football operations and match analysis
- Coaching and analyst workflows
- Player evaluation and recruitment
- Space-creation and pressing intelligence
- Defensive attribution
- Executive reporting
- Governed KPI and data-quality reporting

The platform preserves source provenance, calculation lineage, metric denominators, confidence, coverage, and sample-size context.

## 2. Objectives

- Centralize approved football data sources.
- Preserve source delivery, snapshot, ingestion, and transformation lineage.
- Conform football entities and events into trusted Silver tables.
- Model football truth, match state, possession, phases, and opportunities.
- Quantify off-ball behaviors such as space creation and pressing.
- Publish versioned Gold KPIs and analytics marts.
- Support fixture, team, athlete, season, and competition analysis.
- Serve governed datasets to Power BI.

## 3. Architecture Overview

```text
Source Providers
      │
      ▼
┌──────────────────────────────┐
│ Bronze: raw immutable Delta  │
│ landing, snapshots, lineage  │
│ quarantine, replay           │
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│ Silver: typed and conformed  │
│ football truth and facts     │
│ quality and reconciliation   │
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│ Gold: KPIs, aggregates,     │
│ team/player/match marts      │
│ executive and dashboard data │
└──────────────┬───────────────┘
               ▼
          Power BI
```

Databricks Unity Catalog governs the Bronze, Silver, and Gold schemas. Delta Lake provides transactional storage and PySpark provides distributed transformations.

## 4. Bronze Layer

The Bronze layer is the immutable source landing and replay layer.

### Responsibilities

- Ingest source deliveries with Auto Loader and Structured Streaming.
- Preserve raw source payloads and delivery identity.
- Register source snapshots and ingestion attempts.
- Apply source schema contracts and source-specific validation.
- Quarantine invalid records idempotently.
- Support retries, replay processing, and deterministic identifiers.
- Capture source metadata, logging, and lineage.
- Write only Bronze Delta tables.

### Bronze domains

- Athlete profile
- Roster
- Performance statistics
- Fixtures
- Participants
- Match results
- Event incidents
- Scoring events

## 5. Silver Layer

The Silver layer provides typed, conformed, repository-aligned data products.

### Conformed entities

- Athlete profile
- Roster
- Fixture
- Calendar
- Competition
- Participant
- Match result
- Scoring event
- Event incident

### Football truth

- Match period
- Match state interval
- Possession sequence
- Phase interval

### Analytical facts

- Opportunity
- Space opportunity
- Space baseline
- Space counterfactual
- Space outcome
- Pressing opportunity
- Press trigger
- Press action
- Press support
- Press bypass
- Press outcome
- Recovery action
- Attribution ledger

Silver also produces quality records, reconciliation conflicts, unresolved references, transformation-run metadata, evidence status, and confidence indicators.

## 6. Gold Layer

The Gold layer contains governed, denormalized, consumption-ready products.

### KPI foundations

- Metric definitions
- Calculation runs
- Metric publications
- Metric values
- Data freshness
- Metric exceptions

### KPI categories

#### Space creation

- Eligible, observed, and successful opportunities
- Observation and conversion rates
- Expected-value delta
- Baseline, counterfactual, and tracking coverage
- Confidence-weighted success
- Attribution share

#### Pressing

- Pressing opportunities and triggers
- Action completion
- Support involvement
- Bypass rate
- Recovery rate
- Positive outcome rate
- Time-to-action
- Tracking coverage and unresolved opportunities

#### Attribution

- Attribution share
- Contribution counts
- Positive-outcome contribution
- Evidence-linked attribution
- Confidence-weighted attribution
- Unresolved attribution

### Analytics marts

- Athlete profile and roster metrics
- Team match and performance-window marts
- Team space, pressing, attribution, and competition profiles
- Player match, performance, off-ball, pressing, and attribution marts
- Match summaries, participant metrics, timelines, and opportunity detail
- Executive reporting datasets
- Dashboard-serving tables

All Gold products preserve metric version, numerator, denominator, sample size, coverage, confidence, quality status, calculation lineage, publication status, and refresh metadata.

## 7. Main Domains and Entities

### Athlete

Athlete profile, roster, performance statistic, contract, eligibility status, and participant.

### Event

Fixture, calendar, tournament, competition round, match result, scoring event, event incident, and event type.

### Football truth

Match period, match state interval, possession sequence, and phase interval.

### Opportunity and off-ball

Opportunity, space opportunity, space baseline, space counterfactual, space outcome, pressing opportunity, press trigger, press action, press support, press bypass, press outcome, recovery action, and attribution ledger.

### Governance and operations

Source snapshot, ingestion attempt, transformation run, calculation run, metric definition, metric publication, metric exception, data freshness, quality record, and reconciliation conflict.

## 8. Technology Stack

| Area | Technology |
|---|---|
| Data platform | Databricks |
| Storage | Delta Lake |
| Governance | Unity Catalog |
| Processing | Apache Spark and PySpark |
| Ingestion | Auto Loader and Structured Streaming |
| Relational contract | PostgreSQL |
| Orchestration | Databricks Asset Bundles and Workflows |
| Visualization | Microsoft Power BI |
| Semantic model | Power BI star schema |
| Measures | DAX |

## 9. Repository Structure

```text
OFF-Ball/
├── README.md
├── football_offball_project.md
├── offball_data_model_design.md
├── offball_postgresql_schema.sql
├── offball_databricks_lakehouse_implementation_roadmap.md
├── offball_sprint_1_implementation_guide.md
├── offball_sprint_1_test_execution_plan.md
├── offball_sprint_2_silver_layer_implementation_plan.md
├── offball_sprint_3_gold_layer_implementation_plan.md
├── archive/
├── databricks/
│   ├── databricks.yml
│   ├── resources/
│   └── notebooks/
│       ├── common/
│       ├── orchestration/
│       ├── bronze/
│       ├── silver/
│       └── gold/
└── powerbi/
    ├── offball_powerbi_semantic_model.md
    ├── offball_powerbi_dashboard_design.md
    └── offball_powerbi_measures.dax
```

## 10. Key Analytics Capabilities

- Match-state reconstruction and scoreline analysis
- Possession and phase analysis
- Event and incident timelines
- Space-creation opportunities and conversion
- Defender displacement and receiving-space analysis
- Baseline and counterfactual comparisons
- Press triggers, actions, support, bypasses, and recoveries
- Player attribution and contribution analysis
- Per-90 and opportunity-adjusted measures
- Role and cohort comparisons
- Recruitment pipeline analysis
- Executive results, trends, data coverage, and freshness reporting

## 11. Current Project Status

| Area | Status |
|---|---|
| Bronze implementation | Complete |
| Silver implementation | Complete |
| Gold implementation | Complete |
| Power BI semantic model design | Complete |
| Power BI dashboard design | Complete |
| Deployment validation | Pending |

Sprint 1 Bronze, Sprint 2 Silver, and Sprint 3 Gold artifacts are implemented. Deployment validation is pending in the target Databricks and Power BI environments, including Unity Catalog deployment, Delta runtime execution, Asset Bundle validation, and Power BI dataset deployment.

## 12. Future Enhancements

- Native Power BI project and deployment artifacts
- Automated Power BI dataset refresh orchestration
- Expanded tracking-data ingestion
- Advanced spatial and geometric features
- Detailed defensive-unit modeling
- Real-time match monitoring and KPI alerting
- Advanced player similarity models
- Explainable machine-learning features
- Scenario and counterfactual simulation
- Automated metric certification
- Expanded provider data contracts
- End-to-end automated acceptance testing

## 13. Getting Started

### Prerequisites

- Databricks workspace and SQL Warehouse
- Databricks Runtime with Delta Lake
- Unity Catalog
- Databricks CLI
- Python 3.x
- PostgreSQL
- Power BI Desktop or Power BI Service
- Approved source-provider credentials and delivery locations

### Review the documentation

Start with:

1. [Business requirements](football_offball_project.md)
2. [Data model](offball_data_model_design.md)
3. [PostgreSQL schema](offball_postgresql_schema.sql)
4. [Lakehouse roadmap](offball_databricks_lakehouse_implementation_roadmap.md)
5. [Silver implementation plan](offball_sprint_2_silver_layer_implementation_plan.md)
6. [Gold implementation plan](offball_sprint_3_gold_layer_implementation_plan.md)

### Configure and deploy Databricks

Review `databricks/databricks.yml` and the resource files under `databricks/resources/`. Configure catalog names, storage paths, checkpoints, schema registry paths, quarantine paths, secret scopes, source delivery locations, compute, and alert recipients.

```bash
databricks bundle validate -t dev
databricks bundle deploy -t dev
```

After environment approval:

```bash
databricks bundle validate -t test
databricks bundle deploy -t test

databricks bundle validate -t prod
databricks bundle deploy -t prod
```

### Execute the pipeline

```text
1. Catalog and schema bootstrap
2. Bronze table bootstrap
3. Source snapshot registration
4. Bronze ingestion and finalization
5. Silver conformance
6. Silver football truth
7. Silver analytical facts
8. Gold calculation run
9. Gold metric publication
10. Gold marts and validation
```

### Connect Power BI

Connect Power BI to the Gold schema through the Databricks SQL Warehouse connector. Use:

- `powerbi/offball_powerbi_semantic_model.md`
- `powerbi/offball_powerbi_measures.dax`
- `powerbi/offball_powerbi_dashboard_design.md`

Configure relationships, DAX measures, incremental refresh, row-level security, slicers, drill-through pages, and scheduled refresh.

### Validate before production use

Validate Unity Catalog objects, Delta tables, data contracts, lineage fields, KPI numerator and denominator behavior, minimum-sample rules, freshness, Power BI relationships, row-level security, and dashboard refresh behavior.

## 14. Disclaimer

Off-Ball Analytics is a decision-support platform. Its outputs are intended to support professional analysis by coaches, analysts, recruitment staff, and executives.

Metrics must be interpreted alongside sample size, coverage, tracking availability, evidence status, confidence, role, tactical context, opposition strength, match state, competition level, source quality, and metric version.

The platform does not replace professional football judgment, medical assessment, safeguarding processes, contractual review, legal advice, or recruitment governance.

Production deployment, security configuration, data access, provider licensing, Power BI publishing, and operational validation must be completed by the responsible organization before live football use.
