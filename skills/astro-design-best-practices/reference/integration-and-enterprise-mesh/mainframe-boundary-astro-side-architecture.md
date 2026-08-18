# Mainframe-Boundary Astro-Side Architecture

Mainframe (z/OS) batch workloads present a unique integration challenge: Airflow runs on Kubernetes in the cloud; the mainframe runs JCL in JES2/JES3 on z/OS. This file covers the Airflow side of that boundary — how to trigger, monitor, and receive output from mainframe jobs without requiring Airflow to execute JCL natively.

> **Important**: Airflow cannot execute JCL directly [B1]. The design choices below cover how Airflow acts as the orchestrator while z/OS remains the runtime for mainframe workloads.

## Two Architectural Patterns at the Boundary

### Pattern 1: Orchestration Swap (Mainframe Runtime Preserved)

Replace the legacy batch scheduler (e.g., CA7, Control-M) with Airflow while keeping all JCL and COBOL execution on z/OS.

**How Airflow triggers z/OS jobs**:
- **Zowe CLI**: Open-source framework providing a CLI and REST API that allows Airflow to submit JCL to z/OS, query JES job status, and retrieve spool output — from a Linux/Kubernetes environment [B1][B2].
- **SSH-based submission**: If Zowe is not available, use `SSHOperator` to connect to a z/OS USS (Unix System Services) shell and invoke a Rexx/shell script that submits JCL via `SUBMIT` command [B1].

**Monitoring and completion detection**:
- After submitting a job, use a custom sensor (polling the Zowe REST API or JES query endpoint) to wait for the job to enter `CC` (Condition Code) terminal status [B1].
- Check the return code (`RC=0000`) before proceeding. Non-zero RC should fail the Airflow task and trigger alerts.

### Pattern 2: Replatformed Runtime (COBOL on Linux)

If COBOL programs have been rehosted to a distributed runtime (e.g., Micro Focus Enterprise Server, AWS Mainframe Modernization):
- Rehosted COBOL programs run as Linux processes. Airflow treats them as native tasks [B1].
- Use `BashOperator` for direct invocation, or `KubernetesPodOperator` for isolated, resource-controlled execution.
- This enables granular task decomposition: each JCL step becomes a separate Airflow task with independent retry and monitoring.

## JCL Concept → Airflow Concept Mapping

{syn: JCL concepts → Airflow orchestration equivalents}

| JCL / z/OS Concept | Airflow Equivalent |
|---|---|
| JCL `COND=` parameter | `trigger_rule` (e.g., `TriggerRule.ALL_SUCCESS`, `ONE_FAILED`) |
| Step restart (RESTART= parameter) | Idempotent tasks + `depends_on_past=True` or task retry |
| GDG (Generation Data Group) file dependency | `S3KeySensor` or Airflow Assets/Datasets for event-driven triggers |
| Spool output capture | Fetch spool via Zowe API; write to S3 for log retention |
| `MAXCC=0` check | Custom sensor validating job Condition Code before downstream tasks |

## Design Recommendations

- **Incremental migration**: Start with non-critical batch streams to validate the connectivity pattern (Zowe/SSH) before migrating mission-critical payroll or financial close batches [B1].
- **Hidden dependency discovery**: Mainframe batch often has undocumented dataset dependencies (file X written by Job A consumed by Job B with no explicit dependency). Use lineage discovery tools during migration assessment to surface these before DAG construction [B1].

## Sources

[B1] BatchFoundry / Airflow mainframe integration community guidance — Orchestration Swap vs. Replatforming patterns, Zowe CLI integration, JCL concept mapping (accessed 2026-08-10)
[B2] Zowe.org — Zowe CLI and REST API for z/OS job submission, JES queue query, and dataset access (accessed 2026-08-10)
