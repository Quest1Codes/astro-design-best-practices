# PeopleSoft Agent Migration → Airflow Custom Operator Design

AutoSys's PeopleSoft agent type submits requests directly to the PeopleSoft Process Scheduler without a wrapper script, using PeopleSoft's proprietary API [B1]. PeopleSoft Process Scheduler runs batch processes (Application Engine programs, SQR reports, Crystal Reports, etc.) on behalf of the scheduler.

There is **no native Airflow PeopleSoft provider** in the Apache Airflow provider ecosystem as of 2026. The migration pattern is a custom Hook + Operator built against the PeopleSoft Integration Broker REST API or the Process Scheduler web service.

## Architecture

{syn: AutoSys PeopleSoft agent → Airflow custom `PeopleSoftProcessOperator`; PeopleSoft Process Scheduler → HTTP target via Integration Broker}

| AutoSys Component | Airflow Equivalent |
|---|---|
| **PeopleSoft agent type** | Custom `PeopleSoftProcessOperator` |
| **Process Scheduler invocation** | HTTP POST to PeopleSoft Integration Broker REST endpoint |
| **Process completion monitoring** | Custom `PeopleSoftProcessSensor` polling `FND_CONCURRENT_REQUESTS` equivalent |
| **Credentials** | Airflow Connection with HTTP base URL + PeopleSoft user/password |

## Custom Hook Design

```python
from airflow.hooks.base import BaseHook
import requests

class PeopleSoftHook(BaseHook):
    conn_name_attr = "peoplesoft_conn_id"
    default_conn_name = "peoplesoft_default"

    def __init__(self, peoplesoft_conn_id: str = default_conn_name):
        super().__init__()
        self.peoplesoft_conn_id = peoplesoft_conn_id

    def get_conn(self):
        conn = self.get_connection(self.peoplesoft_conn_id)
        self.base_url = f"https://{conn.host}"
        self.session = requests.Session()
        self.session.auth = (conn.login, conn.password)
        return self.session

    def submit_process(self, process_type: str, process_name: str, run_control_id: str) -> str:
        """Submit a PeopleSoft process via Integration Broker and return instance ID."""
        ...
```

## Custom Operator Pattern

```python
from airflow.models import BaseOperator

class PeopleSoftProcessOperator(BaseOperator):
    def __init__(self, process_type, process_name, run_control_id,
                 peoplesoft_conn_id="peoplesoft_default", **kwargs):
        super().__init__(**kwargs)
        self.process_type = process_type
        self.process_name = process_name
        self.run_control_id = run_control_id
        self.peoplesoft_conn_id = peoplesoft_conn_id

    def execute(self, context):
        hook = PeopleSoftHook(self.peoplesoft_conn_id)
        instance_id = hook.submit_process(
            self.process_type, self.process_name, self.run_control_id
        )
        self.log.info("Submitted PeopleSoft process, instance: %s", instance_id)
        return instance_id
```

## Polling for Completion

PeopleSoft processes are asynchronous. Implement a separate `PeopleSoftProcessSensor` that polls the process status endpoint (or queries the `PS_PMN_PRCSLIST` view) until the process status reaches `9` (Success) or `3` (Error) [B2].

Use `mode='reschedule'` on the sensor to avoid blocking a worker slot during the wait.

## Sources

[B1] Broadcom AutoSys Documentation — PeopleSoft agent job type, Process Scheduler integration (accessed 2026-08-18)
[B2] PeopleSoft Integration Broker documentation & Airflow Docs — Custom Hook/Operator design pattern, `PS_PMN_PRCSLIST` process status codes, HTTP sensor with `mode='reschedule'` (accessed 2026-08-18)
