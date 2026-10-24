# Sprint 1 Test Execution Plan

**Scope:** Approved Sprint 1 deployment, snapshot orchestration, Bronze ingestion, quarantine, lineage, and validation  
**Execution target:** Databricks test target (`offball_test`)  
**Source of truth:** `offball_sprint_1_implementation_guide.md`, Databricks Asset Bundle configuration, and deployed Sprint 1 notebooks  
**Out of scope:** Architecture, data-model, PostgreSQL-schema, Silver, and Gold changes

## Execution rules

- Execute test cases in ID order unless a prerequisite is marked `N/A`.
- Use a unique `TEST_RUN_ID` for every execution:

```python
from datetime import datetime, timezone
import uuid

TEST_RUN_ID = "%s-%s" % (
    datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
    uuid.uuid4().hex[:12],
)
print(TEST_RUN_ID)
```

- Replace `${...}` values with the deployed test-target values.
- Each test must record job run IDs, notebook output, SQL results, and pass/fail status.
- Do not use production catalogs, paths, checkpoints, or source deliveries.
- Clean only test data identified by `TEST_RUN_ID`.

## Test data setup

Run once before T-001:

```python
dbutils.fs.mkdirs("${SOURCE_DELIVERY_URI}/sprint1-tests/${TEST_RUN_ID}/athlete_profile")
dbutils.fs.mkdirs("${SOURCE_DELIVERY_URI}/sprint1-tests/${TEST_RUN_ID}/fixture")
dbutils.fs.mkdirs("${SCHEMA_REGISTRY_ROOT_URI}/athlete_profile")
dbutils.fs.mkdirs("${SCHEMA_REGISTRY_ROOT_URI}/fixture")
dbutils.fs.mkdirs("${CHECKPOINT_ROOT_URI}/sprint1-tests/${TEST_RUN_ID}")
dbutils.fs.mkdirs("${QUARANTINE_ROOT_URI}/sprint1-tests/${TEST_RUN_ID}")
```

Create a valid athlete delivery containing two records and one duplicate payload:

```python
athlete_rows = [
    {"athlete_profile_id": f"{TEST_RUN_ID}-athlete-001", "display_name": "Test Player 1"},
    {"athlete_profile_id": f"{TEST_RUN_ID}-athlete-002", "display_name": "Test Player 2"},
    {"athlete_profile_id": f"{TEST_RUN_ID}-athlete-001", "display_name": "Test Player 1"},
]
dbutils.fs.put(
    "${SOURCE_DELIVERY_URI}/sprint1-tests/${TEST_RUN_ID}/athlete_profile/part-000.json",
    "\n".join(json.dumps(row) for row in athlete_rows),
    True,
)
```

Create an invalid record with no provider identity:

```python
invalid_row = {"display_name": "Invalid Player"}
dbutils.fs.put(
    "${SOURCE_DELIVERY_URI}/sprint1-tests/${TEST_RUN_ID}/athlete_profile/invalid.json",
    json.dumps(invalid_row),
    True,
)
```

Create source contracts before ingestion. The contract must contain the exact `source_object_name`, `source_version`, and Spark `StructType.jsonValue()` schema required by the deployed notebook:

```python
from pyspark.sql import types as T

contract = {
    "source_object_name": "athlete_profile",
    "source_version": "1",
    "schema": T.StructType([
        T.StructField("athlete_profile_id", T.StringType(), True),
        T.StructField("display_name", T.StringType(), True),
    ]).jsonValue(),
    "required_column_groups": [["athlete_profile_id", "athlete_id", "provider_athlete_id"]],
}
dbutils.fs.put(
    "${SCHEMA_REGISTRY_ROOT_URI}/athlete_profile/1.json",
    json.dumps(contract),
    True,
)
```

## 1. Deployment validation

### T-001 Bundle deployment validation

**Preconditions:** Databricks CLI authenticated; test target configured.

**Execute:**

```powershell
databricks bundle validate -t test
if ($LASTEXITCODE -ne 0) { throw "Bundle validation failed" }
databricks bundle deploy -t test
if ($LASTEXITCODE -ne 0) { throw "Bundle deployment failed" }
```

**Pass criteria:**

- Bundle validation and deployment exit code is `0`.
- No production target or production path is referenced.
- Deployment output identifies the test workspace and `offball_test` catalog.

### T-002 Unity Catalog and schema validation

**Execute in a Databricks SQL or notebook cell:**

```sql
SHOW CATALOGS LIKE 'offball_test';
SHOW SCHEMAS IN offball_test;
```

```python
assert spark.catalog.databaseExists("offball_test.bronze")
assert spark.catalog.databaseExists("offball_test.silver")
assert spark.catalog.databaseExists("offball_test.gold")
```

**Pass criteria:** Catalog and all three approved schemas exist.

### T-003 Bronze table inventory validation

**Execute:**

```python
expected = {
    "athlete_profile_raw", "roster_raw", "performance_stat_raw",
    "contract_raw", "eligibility_status_raw", "fixture_raw",
    "competition_raw", "participant_raw", "match_result_raw",
    "scoring_event_raw", "event_incident_raw", "tracking_frame_raw",
    "tracking_quality_raw", "video_evidence_raw", "scouting_annotation_raw",
}
actual = {
    row.tableName
    for row in spark.sql("SHOW TABLES IN offball_test.bronze").collect()
    if not row.isTemporary
}
assert expected.issubset(actual), sorted(expected - actual)
```

**Pass criteria:** All 15 approved Bronze table names are deployed.

### T-004 Common Bronze metadata contract validation

**Execute:**

```python
required = {
    "ingestion_id", "source_snapshot_id", "ingestion_attempt_id",
    "source_system_code", "source_record_reference", "source_object_name",
    "source_version", "payload_json", "payload_hash",
    "source_event_timestamp", "ingested_at", "file_uri",
    "rescued_data", "ingestion_status",
}
for table in sorted(expected):
    if spark.catalog.tableExists(f"offball_test.bronze.{table}"):
        columns = set(spark.table(f"offball_test.bronze.{table}").columns)
        assert required.issubset(columns), (table, sorted(required - columns))
```

**Pass criteria:** Every deployed Bronze table contains the approved common metadata columns.

### T-005 No Silver or Gold writes validation

**Execute:**

```python
assert spark.catalog.listTables("offball_test.silver") == []
assert spark.catalog.listTables("offball_test.gold") == []
```

**Pass criteria:** Sprint 1 deployment has not populated Silver or Gold tables.

## 2. Snapshot registration tests

### T-010 Initial snapshot registration

**Execute:**

```text
Run notebook:
  databricks/notebooks/orchestration/90_register_source_snapshot.py

Parameters:
  catalog=offball_test
  bronze_schema=bronze
  source_system_code=test-provider
  source_object_name=athlete_delivery
  source_version=1
  source_delivery_uri=${SOURCE_DELIVERY_URI}/sprint1-tests/${TEST_RUN_ID}/athlete_profile
  source_domain=athlete
  run_mode=batch
```

**Assert:**

```sql
SELECT delivery_key, source_snapshot_id, ingestion_attempt_id,
       source_system_code, source_version, object_uri, snapshot_status
FROM offball_test.bronze._source_snapshot
WHERE object_uri = '${SOURCE_DELIVERY_URI}/sprint1-tests/${TEST_RUN_ID}/athlete_profile';
```

**Pass criteria:**

- Exactly one row exists.
- `snapshot_status = 'registered'`.
- Source system, version, and delivery URI match the parameters.
- Notebook publishes `source_snapshot_id` and `ingestion_attempt_id` task values.

### T-011 Missing required snapshot parameter

**Execute:** Run registration with `source_delivery_uri=""`.

**Pass criteria:** Notebook fails before writing a snapshot row; error identifies `source_delivery_uri`.

### T-012 Invalid source provider rejection

**Execute:** Run registration with `source_system_code=configured-provider`.

**Pass criteria:** Notebook fails before registration with the configured-provider validation error.

### T-013 Invalid run mode rejection

**Execute:** Run registration with `run_mode=unsupported`.

**Pass criteria:** Notebook fails before registration and does not write a new snapshot row.

### T-014 Replay ID requirement

**Execute:** Run registration with `run_mode=replay` and no `replay_id`.

**Pass criteria:** Notebook fails before registration and identifies missing `replay_id`.

## 3. Retry and idempotency tests

### T-020 Registration retry determinism

**Execute:**

1. Run registration twice with identical source system, object, version, delivery URI, domain, and run mode.
2. Query the snapshot table.

```sql
SELECT COUNT(*) AS row_count,
       COUNT(DISTINCT source_snapshot_id) AS snapshot_count,
       COUNT(DISTINCT ingestion_attempt_id) AS attempt_count
FROM offball_test.bronze._source_snapshot
WHERE object_uri = '${SOURCE_DELIVERY_URI}/sprint1-tests/${TEST_RUN_ID}/athlete_profile';
```

**Pass criteria:** `row_count = 1`, `snapshot_count = 1`, and `attempt_count = 1`.

### T-021 Delivery identity isolation

**Execute:** Register two deliveries differing only by `source_delivery_uri`.

```sql
SELECT COUNT(DISTINCT source_snapshot_id) AS snapshots,
       COUNT(DISTINCT ingestion_attempt_id) AS attempts
FROM offball_test.bronze._source_snapshot
WHERE source_system_code = 'test-provider'
  AND source_object_name = 'athlete_delivery'
  AND source_version = '1'
  AND object_uri LIKE '%/sprint1-tests/%';
```

**Pass criteria:** Two distinct delivery URIs produce two distinct snapshot IDs and attempt IDs.

### T-022 Accepted Bronze retry idempotency

**Execute:**

1. Run athlete ingestion successfully.
2. Rerun the same ingestion with the same delivery and registered task values.
3. Query rows for the test snapshot and attempt.

```sql
SELECT COUNT(*) AS rows,
       COUNT(DISTINCT payload_hash) AS payloads
FROM offball_test.bronze.athlete_profile_raw
WHERE source_snapshot_id = '${SOURCE_SNAPSHOT_ID}'
  AND ingestion_attempt_id = '${INGESTION_ATTEMPT_ID}'
  AND file_uri LIKE '%${TEST_RUN_ID}%';
```

**Pass criteria:** Retry does not create duplicate accepted rows for the same merge keys and payload hashes.

### T-023 Task-value authority

**Execute:** Run Bronze ingestion with `snapshot_id` or `ingestion_id` different from the values published by `register_snapshot`.

**Pass criteria:** Ingestion fails before writing Bronze or quarantine records and identifies the mismatch.

## 4. Replay tests

### T-030 Explicit replay creates a distinct attempt

**Execute:**

1. Register and ingest the original delivery in `batch` mode.
2. Register the same delivery in `replay` mode with `replay_id=${TEST_RUN_ID}-replay-001`.
3. Run ingestion.

```sql
SELECT delivery_key, source_snapshot_id, ingestion_attempt_id, run_mode, snapshot_status
FROM offball_test.bronze._source_snapshot
WHERE object_uri LIKE '%${TEST_RUN_ID}%'
ORDER BY created_at;
```

**Pass criteria:**

- Replay has a distinct delivery key, snapshot ID, and attempt ID.
- Original accepted Bronze rows remain unchanged.
- Replay rows retain the new attempt lineage.

### T-031 Terminal status protection

**Execute:**

1. Complete an original snapshot.
2. Rerun ordinary registration with identical delivery parameters and `run_mode=batch`.
3. Query the original row.

**Pass criteria:** Terminal status and finalized counts are not reset by ordinary registration.

### T-032 Replay status behavior

**Execute:** Register a completed delivery with an explicit replay ID and `run_mode=replay`.

**Pass criteria:** Replay is accepted as a separate deterministic delivery identity and does not mutate original Bronze payload rows.

## 5. Auto Loader tests

### T-040 Incremental Auto Loader ingestion

**Execute:**

1. Register an athlete delivery with `run_mode=incremental`.
2. Run the athlete ingestion notebook.
3. Query the target and inspect the checkpoint path.

```python
checkpoint_entries = dbutils.fs.ls(
    "${CHECKPOINT_ROOT_URI}/athlete_profile"
)
assert checkpoint_entries, "Auto Loader checkpoint directory is empty"
```

**Pass criteria:**

- Job succeeds using `cloudFiles`, explicit schema, `availableNow=True`, and `foreachBatch`.
- Accepted rows contain the registered snapshot and attempt IDs.
- Checkpoint state exists under the configured checkpoint root.

### T-041 Auto Loader second-run no-new-files

**Execute:** Rerun the same incremental ingestion without adding files.

**Pass criteria:** Job succeeds, processes zero new source files, and does not add accepted or quarantine rows.

### T-042 Auto Loader new-file discovery

**Execute:**

1. Add one valid JSON file to the same delivery path.
2. Run the incremental ingestion again.

**Pass criteria:** Only the newly discovered record is added; existing records are not duplicated.

### T-043 Explicit schema enforcement

**Execute:** Add a delivery file containing a field not declared in the registered source contract.

**Pass criteria:** The ingestion follows the configured contract behavior; no schema inference occurs, and the result is either contract-compliant rescued data or an explicit failure recorded in job output.

## 6. Quarantine tests

### T-050 Missing identity quarantine

**Execute:** Ingest the invalid athlete record created during setup.

```sql
SELECT source_snapshot_id, ingestion_attempt_id,
       source_record_reference, payload_json,
       payload_hash, rejection_reason, ingestion_status
FROM delta.`${QUARANTINE_ROOT_URI}/athlete_profile_raw`
WHERE file_uri LIKE '%${TEST_RUN_ID}%';
```

**Pass criteria:**

- Invalid record is not inserted into `offball_test.bronze.athlete_profile_raw`.
- Exactly one quarantine row exists.
- Original payload and non-null rejection reason are retained.
- `ingestion_status = 'quarantined'`.

### T-051 Quarantine retry idempotency

**Execute:** Rerun the same invalid delivery twice.

```sql
SELECT COUNT(*) AS quarantine_rows,
       COUNT(DISTINCT payload_hash) AS payloads
FROM delta.`${QUARANTINE_ROOT_URI}/athlete_profile_raw`
WHERE source_snapshot_id = '${SOURCE_SNAPSHOT_ID}'
  AND ingestion_attempt_id = '${INGESTION_ATTEMPT_ID}'
  AND file_uri LIKE '%${TEST_RUN_ID}%';
```

**Pass criteria:** One quarantine row exists per idempotency key; retries do not append duplicates.

### T-052 Quarantine count determinism

**Execute:** Compare quarantine count after the first run and after two identical retries.

```sql
SELECT COUNT(*) AS distinct_quarantine_records
FROM (
  SELECT DISTINCT source_snapshot_id, ingestion_attempt_id,
                  source_system_code, source_object_name,
                  source_record_reference, payload_hash,
                  rejection_reason
  FROM delta.`${QUARANTINE_ROOT_URI}/athlete_profile_raw`
  WHERE source_snapshot_id = '${SOURCE_SNAPSHOT_ID}'
    AND ingestion_attempt_id = '${INGESTION_ATTEMPT_ID}'
);
```

**Pass criteria:** Count is stable across retries and equals the finalization `quarantined_count`.

## 7. Lineage validation tests

### T-060 Bronze lineage completeness

**Execute:**

```sql
SELECT COUNT(*) AS invalid_rows
FROM offball_test.bronze.athlete_profile_raw
WHERE file_uri LIKE '%${TEST_RUN_ID}%'
  AND (
    source_snapshot_id IS NULL OR
    ingestion_attempt_id IS NULL OR
    ingestion_id IS NULL OR
    source_system_code IS NULL OR
    source_object_name IS NULL OR
    source_version IS NULL OR
    payload_hash IS NULL
  );
```

**Pass criteria:** `invalid_rows = 0`.

### T-061 Cross-delivery lineage isolation

**Execute:**

```sql
SELECT source_snapshot_id, ingestion_attempt_id,
       COUNT(*) AS row_count
FROM offball_test.bronze.athlete_profile_raw
WHERE file_uri LIKE '%${TEST_RUN_ID}%'
GROUP BY source_snapshot_id, ingestion_attempt_id;
```

**Pass criteria:** Rows from separate delivery URIs never share a snapshot/attempt lineage pair.

### T-062 Finalization lineage scope

**Execute:** Finalize the test attempt, then query `_ingestion_attempt`.

```sql
SELECT ingestion_attempt_id, source_snapshot_id,
       actual_record_count, accepted_count,
       rejected_count, quarantined_count,
       duplicate_count, snapshot_status
FROM offball_test.bronze._ingestion_attempt
WHERE ingestion_attempt_id = '${INGESTION_ATTEMPT_ID}';
```

**Pass criteria:** Counts include only rows for the registered snapshot and attempt.

## 8. Data quality tests

### T-070 Source contract mismatch

**Execute:** Change the contract `source_object_name` or `source_version` without changing notebook parameters, then run ingestion.

**Pass criteria:** Ingestion fails before Bronze writes with a contract identity mismatch.

### T-071 Required source column group

**Execute:** Register a contract without any athlete identity column and run ingestion.

**Pass criteria:** Ingestion fails before accepted writes and identifies the missing required column group.

### T-072 Metadata non-null validation

**Execute:**

```sql
SELECT COUNT(*) AS invalid_rows
FROM offball_test.bronze.athlete_profile_raw
WHERE file_uri LIKE '%${TEST_RUN_ID}%'
  AND (
    ingestion_id IS NULL OR source_snapshot_id IS NULL OR
    ingestion_attempt_id IS NULL OR source_system_code IS NULL OR
    source_object_name IS NULL OR source_version IS NULL OR
    payload_json IS NULL OR payload_hash IS NULL OR
    ingested_at IS NULL OR ingestion_status IS NULL
  );
```

**Pass criteria:** `invalid_rows = 0`.

### T-073 Payload hash determinism

**Execute:**

```python
import hashlib

rows = (
    spark.table("offball_test.bronze.athlete_profile_raw")
    .where("file_uri LIKE '%" + TEST_RUN_ID + "%'")
    .select("payload_json", "payload_hash")
    .collect()
)
for row in rows:
    assert row.payload_hash == hashlib.sha256(
        row.payload_json.encode("utf-8")
    ).hexdigest()
```

**Pass criteria:** Every accepted payload hash matches its canonical payload JSON.

### T-074 Finalization status and counts

**Execute:** Finalize both a clean delivery and a delivery containing the invalid record.

**Pass criteria:**

- Clean delivery status is `completed`.
- Delivery with quarantine status is `completed_with_quarantine`.
- `actual_record_count = accepted_count + rejected_count + quarantined_count`.
- `duplicate_count` equals the sum of ingestion task duplicate metrics.

## 9. Acceptance tests

### T-080 S1-AC-01 through S1-AC-04

**Execute:** Run T-001 through T-004.

**Pass criteria:** All four deployment and contract tests pass.

### T-081 S1-AC-05 and S1-AC-06

**Execute:**

1. Run an athlete representative delivery through registration, ingestion, retry, and finalization.
2. Run an event representative fixture delivery through registration, ingestion, retry, and finalization.

**Pass criteria:** Both domains complete successfully with deterministic lineage and no duplicate accepted rows.

### T-082 S1-AC-07 and S1-AC-08

**Execute:** Run tracking, video evidence, and scouting annotation jobs against valid contract-conforming fixtures.

**Pass criteria:** Valid records land in their approved Bronze tables without overwriting source payloads.

### T-083 S1-AC-09 through S1-AC-12

**Execute:** Run T-020, T-022, T-050, T-051, T-052, and T-074.

**Pass criteria:** Duplicate deliveries are idempotent, malformed records are quarantined, metadata is complete, and terminal statuses distinguish clean and quarantined completion.

### T-084 S1-AC-13 and S1-AC-14

**Execute:**

1. Run T-030 through T-032.
2. Configure a transient test failure or retryable task interruption.
3. Re-run the job with the same delivery identity.

**Pass criteria:** Replay is selectable by delivery/attempt identity, retries do not duplicate accepted rows, and original Bronze rows remain unchanged.

### T-085 S1-AC-15

**Execute:**

```sql
SHOW TABLES IN offball_test.silver;
SHOW TABLES IN offball_test.gold;
```

Review the deployed job task paths and write operations:

```powershell
Select-String -Path .\databricks\resources\jobs.yml -Pattern 'silver|gold' -CaseSensitive:$false
```

**Pass criteria:** No Sprint 1 task writes Silver or Gold data.

## Final execution record

Record one row per test case:

| Test ID | Run ID | Job/notebook run | Result | Evidence location | Defect |
|---|---|---|---|---|---|
| T-001 | `${TEST_RUN_ID}` | `<run-id>` | PASS/FAIL | `<path or URL>` | `<none or defect ID>` |

Sprint 1 acceptance is **PASS** only when T-080 through T-085 pass and every prerequisite test has executable evidence.
