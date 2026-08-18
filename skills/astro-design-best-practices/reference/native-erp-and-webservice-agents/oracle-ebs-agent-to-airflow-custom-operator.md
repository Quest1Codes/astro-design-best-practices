# Oracle E-Business Suite Agent Migration → Airflow Custom Operator Design

AutoSys's Oracle E-Business Suite (EBS) agent type submits Concurrent Requests directly to the Oracle EBS Concurrent Manager without a wrapper script [B1]. The Concurrent Manager queues and executes EBS programs (Application Engine, PL/SQL programs, reports) on behalf of the scheduler.

There is **no native Airflow Oracle EBS provider** in the Apache Airflow provider ecosystem as of 2026. The migration pattern uses the `OracleHook` (from `apache-airflow-providers-oracle`) to execute PL/SQL directly against the EBS database, calling `fnd_request.submit_request` to queue concurrent programs [B2].

## Architecture

{syn: AutoSys EBS agent → Airflow custom `OracleEBSConcurrentRequestOperator`; EBS Concurrent Manager → `fnd_request.submit_request` via `OracleHook`}

| AutoSys Component | Airflow Equivalent |
|---|---|
| **EBS agent type** | Custom `OracleEBSConcurrentRequestOperator` |
| **Concurrent program submission** | `fnd_request.submit_request` via `OracleHook` |
| **Concurrent Manager queue** | EBS Concurrent Manager (unchanged — Airflow triggers it; CM manages execution) |
| **Completion monitoring** | `OracleSqlSensor` polling `fnd_concurrent_requests` |

## Custom Operator Design

```python
from airflow.models import BaseOperator
from airflow.providers.oracle.hooks.oracle import OracleHook

class OracleEBSConcurrentRequestOperator(BaseOperator):
    def __init__(self, oracle_conn_id, application, program,
                 user_id, resp_id, resp_appl_id, arguments=None, **kwargs):
        super().__init__(**kwargs)
        self.oracle_conn_id = oracle_conn_id
        self.application = application
        self.program = program
        self.user_id = user_id
        self.resp_id = resp_id
        self.resp_appl_id = resp_appl_id
        self.arguments = arguments or []

    def execute(self, context) -> int:
        hook = OracleHook(oracle_conn_id=self.oracle_conn_id)
        args = ", ".join(f"'{a}'" for a in self.arguments)
        pl_sql = f"""
        DECLARE
          l_request_id NUMBER;
        BEGIN
          fnd_global.apps_initialize({self.user_id}, {self.resp_id}, {self.resp_appl_id});
          l_request_id := fnd_request.submit_request(
            application => '{self.application}',
            program     => '{self.program}',
            {f"argument1 => {args}" if self.arguments else ""}
          );
          COMMIT;
          :request_id := l_request_id;
        END;
        """
        result = hook.run(pl_sql, autocommit=True)
        self.log.info("Submitted concurrent request ID: %s", result)
        return result
```

## Polling for Completion

EBS concurrent requests are asynchronous. After submission, poll `fnd_concurrent_requests` for the returned `request_id` until `phase_code = 'C'` (Completed) and `status_code = 'N'` (Normal/Success) [B2]:

```python
from airflow.providers.oracle.sensors.oracle import OracleSqlSensor

wait_for_concurrent_request = OracleSqlSensor(
    task_id="wait_for_ebs_completion",
    oracle_conn_id="oracle_ebs_prod",
    sql="""SELECT COUNT(*) FROM fnd_concurrent_requests
           WHERE request_id = {{ ti.xcom_pull(task_ids='submit_concurrent_request') }}
           AND phase_code = 'C' AND status_code = 'N'""",
    mode="reschedule",
)
```

## Key Design Notes

| Decision | Guidance |
|---|---|
| **`fnd_global.apps_initialize` required** | Must be called before any EBS API calls in the same session to set the application context (user, responsibility) [B2]. |
| **EBS DB user vs. APPS user** | Connect as the `APPS` schema user — not the underlying Oracle DBA user — for `fnd_request.*` API access [B2]. |
| **Long-running programs** | Use Deferrable Operator or `OracleSqlSensor(mode='reschedule')` — never a polling sleep inside the operator. |

## Sources

[B1] Broadcom AutoSys Documentation — Oracle EBS agent job type, Concurrent Manager integration (accessed 2026-08-18)
[B2] Oracle E-Business Suite Technical Reference / Airflow Docs — `fnd_request.submit_request`, `fnd_global.apps_initialize`, `fnd_concurrent_requests` status codes, `OracleHook`, `OracleSqlSensor` (accessed 2026-08-18)
