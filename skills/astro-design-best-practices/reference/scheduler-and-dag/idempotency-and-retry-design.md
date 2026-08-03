# Idempotency and Retry Design for Translated Tasks

AutoSys's `n_retrys` attribute is a count with no built-in idempotency guarantee of its own — a retried AutoSys job simply re-runs the same command, and whether that's safe depends entirely on what the command does. The same is true after translation; Airflow's retry mechanism does not make a task idempotent, it just re-invokes it.

## Core mechanics

- The primary retry parameters are `retries`, `retry_delay`, and `retry_exponential_backoff` [F1].
- Setting `retry_exponential_backoff=True` doubles the delay between each successive retry until `max_retry_delay` is reached, which caps runaway growth [F1].
- Task idempotency is a design requirement for retries to be *safe*, not just functional: if a task inserts rows, a naive retry duplicates them; the fix is a MERGE/upsert, a DELETE+INSERT within a transaction, or writing to a date-partitioned path and overwriting the partition rather than appending [F2]. This is described as general Airflow/data-engineering practice rather than a single authoritative spec — treat the specific technique choice (MERGE vs. partition-overwrite) as a per-task design decision, not a fixed rule.
- Only idempotent tasks should have retries enabled at all; retrying a non-idempotent task (one that duplicates data on re-run) converts a transient failure into a data-correctness bug [F2].

## {syn: F1,F2} Design guidance, migrating from `n_retrys`

`n_retrys` alone told AutoSys *how many times* to retry — it said nothing about whether the underlying command was safe to run twice. Migrating it to Airflow's `retries` without addressing idempotency just carries the original risk forward unexamined. For every translated job with `n_retrys > 0`:

1. Classify the task's side effect: does it insert/append (duplication risk on retry), upsert/overwrite (safe), or have no persistent side effect (safe)? This classification did not exist in JIL and has to be done fresh per job during translation, not inferred from `n_retrys`'s presence.
2. If the classification is "insert/append, unsafe" — either fix the underlying operation to be idempotent (preferred: upsert or partition-overwrite) [F2], or set `retries=0` and treat failures as requiring manual intervention rather than silently re-attempting a duplicating operation.
3. Only once step 1-2 are resolved, set `retries=`(the original `n_retrys` value) and `retry_delay`, with `retry_exponential_backoff=True` for anything calling an external system that could benefit from backing off rather than hammering it at a fixed interval [F1].

## Resolved during Critic review

The float-multiplier form of `retry_exponential_backoff` (originally flagged here as `NEEDS_EXEC_CHECK`, pending confirmation) is in fact already stated on [F1] — the same Astronomer doc already cited for the boolean form: "In Airflow 3.2+ you can set `retry_exponential_backoff` to a float to directly specify the factor by which the retry delay should be multiplied between retries." No further execution check is needed for this specific claim; the original flag was appropriately cautious but the corroboration was sitting in an already-cited source.

## Sources

- [F1] Astronomer Docs — Rerun Airflow Dags and tasks (`retries`/`retry_delay`/`retry_exponential_backoff` mechanics): https://www.astronomer.io/docs/learn/rerunning-dags (tier 1)
- [F2] General Airflow/data-engineering practice — idempotency patterns for retry safety (upsert/partition-overwrite, classify-before-retrying). Sourced from a third-party engineering blog during this research pass, not an Astronomer/Apache primary source — treat the *principle* (idempotency is required for safe retries) as solid, standard practice, but treat any specific numeric guidance (e.g. suggested retry counts per operation type) as **`PRACTITIONER JUDGMENT — not independently verified from tier 1/2 sources`**, not a citable fact.
