# Generic and Homegrown ERP Batch-Integration Patterns

AutoSys frequently served as the glue layer between mainframe batch processes and homegrown ERP systems via flat-file drops, database triggers, or proprietary APIs. When migrating to Astro, Airflow becomes the orchestrator — but the external system's behavior does not change. This file covers the architectural patterns for Airflow's side of these integrations.

> **Scope**: This file covers generic/homegrown ERP patterns only. For SAP, PeopleSoft, and Oracle EBS native-agent migrations, see Cluster 18 (Topics 117–119).

## Core Architectural Principle: Airflow as Orchestrator, Not Executor

Airflow should **trigger and monitor** external batch processes, not execute them inline. Running heavy ERP batch logic directly inside a Python task on an Airflow worker ties up worker slots and creates unpredictable resource consumption.

## Pattern 1: Trigger-and-Poll (Async Batch Jobs)

For ERP systems that expose a job submission API and a status endpoint:

1. **Task 1 (Submit)**: Call the ERP API to start the batch job. Return the job ID via XCom.
2. **Task 2 (Sensor/Deferrable Operator)**: Poll the status endpoint using the job ID until the job reaches a terminal state (SUCCESS or FAILED) [B1][B2].
   - Use `mode='reschedule'` on sensors or **Deferrable Operators** to release the worker slot during wait time [B1].
3. **Task 3 (Validate)**: Confirm the ERP processed the expected record count before marking success.

## Pattern 2: File-Based Integration (Flat File Drop)

For legacy ERP systems that consume batch input files (common AutoSys pattern):

1. **Task 1 (Extract)**: Extract and transform data, writing to an S3 landing zone.
2. **Task 2 (Transfer)**: Move the file to the ERP's input location (SFTP server or shared volume) via `SFTPOperator`.
3. **Task 3 (Sensor)**: Use a file-completion sensor (SFTP or S3 `KeySensor`) to detect the ERP's output acknowledgement file before proceeding [B2].

## Key Design Rules

| Rule | Rationale |
|---|---|
| **Use Deferrable Operators for long waits** | Releases worker slot; critical for large ERP batch windows that run for hours [B1]. |
| **Never call ERP APIs in top-level DAG code** | Scheduler parses DAG files frequently — any API call at parse time causes repeated external calls and scheduler performance degradation [B1]. |
| **Use Airflow Connections for API credentials** | Store ERP base URLs and API keys in Connections backed by a Secrets Backend [B2]. |
| **Ensure task idempotency** | If an ERP task fails and retries, it must not submit duplicate batch jobs or create duplicate records [B1][B2]. |
| **Use dedicated worker queues** | Route ERP integration tasks to a dedicated worker queue to prevent long-running ERP calls from starving compute-intensive data pipeline tasks [B1]. |

## Sources

[B1] Apache Airflow Docs — Deferrable Operators, Sensor modes, and top-level code anti-patterns (accessed 2026-08-10)
[B2] Astronomer Docs — Connections, Secrets Backends, and enterprise integration best practices (accessed 2026-08-10)
