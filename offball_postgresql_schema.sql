-- Off-Ball Version 2.1 repository-first relational contract
-- Primary source: Databricks Sports Entertainment v1 MVM.
-- Repository-backed tables preserve athlete and event product names.

CREATE SCHEMA IF NOT EXISTS athlete;
CREATE SCHEMA IF NOT EXISTS event;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE athlete.athlete_profile (
    athlete_profile_id bigint PRIMARY KEY,
    preferred_name text NOT NULL,
    legal_name text,
    date_of_birth date,
    nationality_code text,
    career_status text,
    source_system_code text NOT NULL,
    source_record_reference text NOT NULL,
    record_version bigint NOT NULL DEFAULT 1,
    updated_timestamp timestamptz NOT NULL DEFAULT now(),
    UNIQUE (source_system_code, source_record_reference)
);

CREATE TABLE event.fixture (
    fixture_id bigint PRIMARY KEY,
    calendar_id bigint,
    tournament_id bigint,
    competition_round_id bigint,
    type_id bigint,
    season_id bigint,
    fixture_code text,
    event_date date,
    actual_start_timestamp timestamptz,
    actual_end_timestamp timestamptz,
    lifecycle_status text,
    source_system_code text NOT NULL,
    source_record_reference text NOT NULL,
    record_version bigint NOT NULL DEFAULT 1,
    UNIQUE (source_system_code, source_record_reference)
);

CREATE TABLE athlete.roster (
    roster_id bigint PRIMARY KEY,
    athlete_profile_id bigint NOT NULL REFERENCES athlete.athlete_profile(athlete_profile_id),
    franchise_id bigint,
    league_id bigint,
    season_id bigint,
    position_code text,
    activation_date date,
    deactivation_date date,
    eligibility_status text,
    source_system_code text NOT NULL,
    source_record_reference text NOT NULL,
    UNIQUE (source_system_code, source_record_reference)
);

CREATE TABLE event.participant (
    participant_id bigint PRIMARY KEY,
    fixture_id bigint NOT NULL REFERENCES event.fixture(fixture_id),
    athlete_profile_id bigint REFERENCES athlete.athlete_profile(athlete_profile_id),
    franchise_id bigint,
    participant_role text,
    lineup_position text,
    participation_status text,
    source_system_code text NOT NULL,
    source_record_reference text NOT NULL,
    UNIQUE (source_system_code, source_record_reference)
);

CREATE TABLE event.match_result (
    match_result_id bigint PRIMARY KEY,
    fixture_id bigint NOT NULL REFERENCES event.fixture(fixture_id),
    home_score integer,
    away_score integer,
    result_status text,
    result_timestamp timestamptz,
    source_system_code text NOT NULL,
    source_record_reference text NOT NULL,
    UNIQUE (source_system_code, source_record_reference)
);

CREATE TABLE event.event_incident (
    event_incident_id bigint PRIMARY KEY,
    fixture_id bigint NOT NULL REFERENCES event.fixture(fixture_id),
    participant_id bigint REFERENCES event.participant(participant_id),
    incident_type text NOT NULL,
    incident_timestamp timestamptz,
    incident_status text,
    provider_payload jsonb,
    source_system_code text NOT NULL,
    source_record_reference text NOT NULL,
    UNIQUE (source_system_code, source_record_reference)
);

CREATE TABLE event.scoring_event (
    scoring_event_id bigint PRIMARY KEY,
    fixture_id bigint NOT NULL REFERENCES event.fixture(fixture_id),
    participant_id bigint REFERENCES event.participant(participant_id),
    scoring_type text NOT NULL,
    scoring_timestamp timestamptz,
    source_system_code text NOT NULL,
    source_record_reference text NOT NULL,
    UNIQUE (source_system_code, source_record_reference)
);

CREATE TABLE athlete.performance_stat (
    performance_stat_id bigint PRIMARY KEY,
    athlete_profile_id bigint NOT NULL REFERENCES athlete.athlete_profile(athlete_profile_id),
    fixture_id bigint REFERENCES event.fixture(fixture_id),
    statistic_type text NOT NULL,
    statistic_value numeric,
    statistic_unit text,
    source_system_code text NOT NULL,
    source_record_reference text NOT NULL,
    calculation_run_id uuid,
    UNIQUE (source_system_code, source_record_reference)
);

CREATE SEQUENCE analytics.match_period_id_seq;
CREATE SEQUENCE analytics.match_state_interval_id_seq;

CREATE TABLE analytics.match_period (
    match_period_id bigint PRIMARY KEY DEFAULT nextval('analytics.match_period_id_seq'),
    fixture_id bigint NOT NULL REFERENCES event.fixture(fixture_id),
    period_type text NOT NULL,
    period_number integer NOT NULL,
    start_timestamp timestamptz NOT NULL,
    end_timestamp timestamptz,
    UNIQUE (fixture_id, period_number)
);

CREATE TABLE analytics.match_state_interval (
    match_state_interval_id bigint PRIMARY KEY DEFAULT nextval('analytics.match_state_interval_id_seq'),
    match_period_id bigint NOT NULL REFERENCES analytics.match_period(match_period_id),
    home_score integer NOT NULL,
    away_score integer NOT NULL,
    numerical_state text,
    start_timestamp timestamptz NOT NULL,
    end_timestamp timestamptz,
    confidence numeric CHECK (confidence >= 0 AND confidence <= 1)
);

CREATE TABLE analytics.possession_sequence (
    possession_sequence_id bigint PRIMARY KEY,
    fixture_id bigint NOT NULL REFERENCES event.fixture(fixture_id),
    controlling_franchise_id bigint,
    start_timestamp timestamptz NOT NULL,
    end_timestamp timestamptz,
    status text NOT NULL,
    confidence numeric CHECK (confidence >= 0 AND confidence <= 1),
    phase_version text NOT NULL,
    unresolved_reason text
);

CREATE TABLE analytics.phase_interval (
    phase_interval_id bigint PRIMARY KEY,
    possession_sequence_id bigint REFERENCES analytics.possession_sequence(possession_sequence_id),
    fixture_id bigint NOT NULL REFERENCES event.fixture(fixture_id),
    phase_type text NOT NULL,
    start_timestamp timestamptz NOT NULL,
    end_timestamp timestamptz,
    confidence numeric CHECK (confidence >= 0 AND confidence <= 1)
);

CREATE TABLE analytics.opportunity (
    opportunity_id bigint PRIMARY KEY,
    fixture_id bigint NOT NULL REFERENCES event.fixture(fixture_id),
    participant_id bigint REFERENCES event.participant(participant_id),
    phase_interval_id bigint REFERENCES analytics.phase_interval(phase_interval_id),
    opportunity_type text NOT NULL,
    eligible_flag boolean NOT NULL,
    observed_flag boolean NOT NULL,
    start_timestamp timestamptz NOT NULL,
    end_timestamp timestamptz,
    evidence_status text NOT NULL
);

CREATE TABLE analytics.space_opportunity (
    space_opportunity_id bigint PRIMARY KEY,
    opportunity_id bigint NOT NULL REFERENCES analytics.opportunity(opportunity_id),
    participant_id bigint REFERENCES event.participant(participant_id),
    space_type text NOT NULL,
    target_zone text,
    expected_value_delta numeric,
    outcome_status text
);

CREATE TABLE analytics.pressing_opportunity (
    pressing_opportunity_id bigint PRIMARY KEY,
    opportunity_id bigint NOT NULL REFERENCES analytics.opportunity(opportunity_id),
    participant_id bigint REFERENCES event.participant(participant_id),
    press_type text NOT NULL,
    target_participant_id bigint REFERENCES event.participant(participant_id),
    trigger_type text,
    outcome_status text
);

CREATE TABLE analytics.space_baseline (
    space_baseline_id bigint PRIMARY KEY,
    space_opportunity_id bigint NOT NULL REFERENCES analytics.space_opportunity(space_opportunity_id),
    baseline_method text NOT NULL,
    baseline_value jsonb NOT NULL,
    counterfactual_reference text
);

CREATE TABLE analytics.space_counterfactual (
    space_counterfactual_id bigint PRIMARY KEY,
    space_opportunity_id bigint NOT NULL REFERENCES analytics.space_opportunity(space_opportunity_id),
    counterfactual_type text NOT NULL,
    expected_value_delta numeric,
    calculation_run_id uuid NOT NULL
);

CREATE TABLE analytics.space_outcome (
    space_outcome_id bigint PRIMARY KEY,
    space_opportunity_id bigint NOT NULL REFERENCES analytics.space_opportunity(space_opportunity_id),
    outcome_type text NOT NULL,
    outcome_value numeric,
    outcome_timestamp timestamptz
);

CREATE TABLE analytics.attribution_ledger (
    attribution_id bigint PRIMARY KEY,
    space_opportunity_id bigint REFERENCES analytics.space_opportunity(space_opportunity_id),
    pressing_opportunity_id bigint REFERENCES analytics.pressing_opportunity(pressing_opportunity_id),
    participant_id bigint NOT NULL REFERENCES event.participant(participant_id),
    attribution_type text NOT NULL,
    attribution_share numeric CHECK (attribution_share >= 0 AND attribution_share <= 1),
    evidence_link_id bigint
);

CREATE TABLE analytics.press_trigger (
    press_trigger_id bigint PRIMARY KEY,
    pressing_opportunity_id bigint NOT NULL REFERENCES analytics.pressing_opportunity(pressing_opportunity_id),
    trigger_type text NOT NULL,
    trigger_timestamp timestamptz NOT NULL
);

CREATE TABLE analytics.press_action (
    press_action_id bigint PRIMARY KEY,
    pressing_opportunity_id bigint NOT NULL REFERENCES analytics.pressing_opportunity(pressing_opportunity_id),
    participant_id bigint NOT NULL REFERENCES event.participant(participant_id),
    action_type text NOT NULL,
    action_timestamp timestamptz NOT NULL,
    intensity numeric
);

CREATE TABLE analytics.press_support (
    press_support_id bigint PRIMARY KEY,
    pressing_opportunity_id bigint NOT NULL REFERENCES analytics.pressing_opportunity(pressing_opportunity_id),
    participant_id bigint NOT NULL REFERENCES event.participant(participant_id),
    support_type text NOT NULL
);

CREATE TABLE analytics.press_bypass (
    press_bypass_id bigint PRIMARY KEY,
    pressing_opportunity_id bigint NOT NULL REFERENCES analytics.pressing_opportunity(pressing_opportunity_id),
    bypass_type text NOT NULL,
    bypass_timestamp timestamptz
);

CREATE TABLE analytics.press_outcome (
    press_outcome_id bigint PRIMARY KEY,
    pressing_opportunity_id bigint NOT NULL REFERENCES analytics.pressing_opportunity(pressing_opportunity_id),
    outcome_type text NOT NULL,
    outcome_value numeric
);

CREATE TABLE analytics.recovery_action (
    recovery_action_id bigint PRIMARY KEY,
    pressing_opportunity_id bigint NOT NULL REFERENCES analytics.pressing_opportunity(pressing_opportunity_id),
    participant_id bigint NOT NULL REFERENCES event.participant(participant_id),
    action_type text NOT NULL,
    action_timestamp timestamptz NOT NULL
);

CREATE TABLE analytics.source_snapshot (
    source_snapshot_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    source_system_code text NOT NULL,
    source_object_name text NOT NULL,
    source_version text NOT NULL,
    captured_at timestamptz NOT NULL DEFAULT now(),
    object_uri text
);

CREATE TABLE analytics.calculation_run (
    calculation_run_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    source_snapshot_id uuid NOT NULL REFERENCES analytics.source_snapshot(source_snapshot_id),
    metric_version text NOT NULL,
    started_at timestamptz NOT NULL,
    completed_at timestamptz,
    status text NOT NULL
);

ALTER TABLE athlete.performance_stat
    ADD CONSTRAINT performance_stat_calculation_run_fk
    FOREIGN KEY (calculation_run_id) REFERENCES analytics.calculation_run(calculation_run_id);

CREATE TABLE analytics.feature_set (
    feature_set_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    calculation_run_id uuid NOT NULL REFERENCES analytics.calculation_run(calculation_run_id),
    feature_definition jsonb NOT NULL
);

CREATE TABLE analytics.model_artifact (
    model_artifact_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    calculation_run_id uuid NOT NULL REFERENCES analytics.calculation_run(calculation_run_id),
    model_name text NOT NULL,
    model_version text NOT NULL,
    artifact_uri text
);

CREATE TABLE analytics.metric_publication (
    metric_publication_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    calculation_run_id uuid NOT NULL REFERENCES analytics.calculation_run(calculation_run_id),
    published_at timestamptz,
    publication_status text NOT NULL
);

CREATE TABLE analytics.metric_value (
    metric_value_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    athlete_profile_id bigint REFERENCES athlete.athlete_profile(athlete_profile_id),
    fixture_id bigint REFERENCES event.fixture(fixture_id),
    metric_code text NOT NULL,
    metric_value numeric,
    numerator numeric,
    denominator numeric,
    calculation_run_id uuid NOT NULL REFERENCES analytics.calculation_run(calculation_run_id),
    quality_status text NOT NULL
);

CREATE TABLE analytics.evidence_link (
    evidence_link_id bigint PRIMARY KEY,
    fixture_id bigint NOT NULL REFERENCES event.fixture(fixture_id),
    source_type text NOT NULL,
    source_reference text NOT NULL,
    locator jsonb,
    access_status text
);

CREATE TABLE analytics.annotation_task (
    annotation_task_id bigint PRIMARY KEY,
    fixture_id bigint NOT NULL REFERENCES event.fixture(fixture_id),
    target_type text NOT NULL,
    target_id bigint NOT NULL,
    status text NOT NULL
);

CREATE TABLE analytics.annotation_label (
    annotation_label_id bigint PRIMARY KEY,
    annotation_task_id bigint NOT NULL REFERENCES analytics.annotation_task(annotation_task_id),
    reviewer_reference text NOT NULL,
    label_code text NOT NULL,
    confidence numeric CHECK (confidence >= 0 AND confidence <= 1)
);

CREATE TABLE analytics.annotation_adjudication (
    annotation_adjudication_id bigint PRIMARY KEY,
    annotation_task_id bigint NOT NULL REFERENCES analytics.annotation_task(annotation_task_id),
    adjudication_status text NOT NULL,
    agreement_score numeric CHECK (agreement_score >= 0 AND agreement_score <= 1),
    adjudicated_at timestamptz
);

CREATE INDEX fixture_event_date_idx ON event.fixture(event_date);
CREATE INDEX participant_fixture_idx ON event.participant(fixture_id);
CREATE INDEX performance_stat_athlete_fixture_idx ON athlete.performance_stat(athlete_profile_id, fixture_id);
CREATE INDEX opportunity_fixture_time_idx ON analytics.opportunity(fixture_id, start_timestamp);
CREATE INDEX metric_value_run_idx ON analytics.metric_value(calculation_run_id);
