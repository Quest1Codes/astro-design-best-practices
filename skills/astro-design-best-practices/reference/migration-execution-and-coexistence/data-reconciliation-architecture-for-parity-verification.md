# Data-Reconciliation Architecture for Parity Verification

During the dual-run phase, the key deliverable is a statistically defensible proof that the Airflow DAG produces the same output as the AutoSys job. This requires a **dedicated reconciliation pipeline** — not manual spot-checks.

## The Reconciliation DAG Pattern

Create a dedicated `reconciliation_<domain>` DAG that runs **after** both the AutoSys job and its shadow Airflow DAG have completed for a given cycle [B1][B2].

### Reconciliation DAG Structure

```
[Wait for AutoSys Output] → [Wait for Airflow Shadow Output] → [Schema Check] → [Row Count Check] → [Hash/Checksum Check] → [Report & Alert]
```

Each check is a separate task, so failures are individually identified:

1. **Schema Comparator**: Validate that column names, data types, and nullability are identical between the AutoSys-produced table and the Airflow-produced shadow table [B2].
2. **Row Count Check**: Compare total record counts for the same time partition. A discrepancy here is a critical finding [B2].
3. **Aggregate Comparator**: Compare `SUM()`, `MIN()`, `MAX()` for key financial or numeric fields. This catches transformation logic errors that a row-count check would miss [B2].
4. **Row-Level Diff (Sampling)**: For full validation, perform a `LEFT ANTI JOIN` between the two datasets to identify records that exist in one but not the other. For large datasets, use a hash-based comparison rather than row-by-row comparison [B2].

## Output: The Parity Report

Each reconciliation cycle should write a structured report to a persistent store (e.g., a `migration_parity_log` database table or an S3 JSON file) [B2]:

```json
{
  "dag_id": "erp_daily_load_shadow",
  "run_date": "2026-08-11",
  "schema_match": true,
  "row_count_autosys": 1204567,
  "row_count_airflow": 1204567,
  "row_count_delta": 0,
  "sum_amount_autosys": 9823456.78,
  "sum_amount_airflow": 9823456.78,
  "hash_mismatch_count": 0,
  "verdict": "PASS"
}
```

If `verdict != "PASS"`, the reconciliation DAG should automatically:
- Alert the migration team (PagerDuty/Slack) [B2].
- **Block** the cutover schedule for this domain until the discrepancy is investigated and resolved.

## Reconciliation Exit Criteria

Define a clear, documented definition of "readiness" before you declare a DAG ready for cutover:

- N consecutive `PASS` cycles (e.g., 5 business days) [B1].
- Zero `CRITICAL` discrepancies (row count delta > 0 on financial data).
- All schema fields match.

## Sources

[B1] Astronomer Migration Guidance — Parity verification during AutoSys-to-Airflow migration (accessed 2026-08-11)
[B2] Enterprise migration community — Reconciliation engine architecture, hash-based comparison, and parity report structure (accessed 2026-08-11)
