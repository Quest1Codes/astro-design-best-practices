# SAP Application Job Agent Migration → Airflow SAP Provider/Operator Design

AutoSys's SAP Application Job type is a native agent that submits ABAP background jobs directly to SAP without requiring a wrapper script. The AutoSys agent communicates with SAP via RFC (Remote Function Call) to trigger ABAP programs, function modules, or variants [B1].

In Airflow, there is no out-of-the-box "SAP job type." The replacement pattern uses the **Apache Airflow SAP RFC provider** (`apache-airflow-providers-sap`) and the `pyrfc` Python library to execute RFC calls against SAP NetWeaver systems [B2].

## Architecture

{syn: AutoSys SAP Application Job → Airflow `SAPRfcOperator`; AutoSys SAP agent connection → Airflow SAP Connection (RFC endpoint)}

| AutoSys Component | Airflow Equivalent |
|---|---|
| **SAP Application Job type** | `SAPRfcOperator` or custom RFC-calling `PythonOperator` |
| **AutoSys SAP agent (RFC connection)** | Airflow SAP Connection (`conn_type="sap_rfc"`) |
| **ABAP program / function module call** | RFC function call via `pyrfc` library |
| **SAP HANA database operations** | `SapHanaOperator` / SAP HANA provider |

## Prerequisites

The SAP RFC provider requires the **SAP NetWeaver RFC SDK** to be installed in the Airflow worker image [B2]. Add to your `Dockerfile`:

```dockerfile
# Add SAP NWRFC SDK libs to the worker image
COPY nwrfcsdk/ /opt/sap/nwrfcsdk/
ENV SAPNWRFC_HOME=/opt/sap/nwrfcsdk
RUN pip install pyrfc apache-airflow-providers-sap
```

## Operator Pattern

```python
from airflow.providers.sap.hooks.sap_rfc import SAPRfcHook

@task
def run_sap_job(function_module: str, parameters: dict) -> dict:
    hook = SAPRfcHook(sap_conn_id="sap_production")
    conn = hook.get_conn()
    result = conn.call(function_module, **parameters)
    return result

run_sap_job.override(task_id="trigger_abap_program")(
    function_module="BAPI_MATERIAL_GETLIST",
    parameters={"MATERIAL_GENERAL_DATA": []},
)
```

## Connection Management

Store SAP connection credentials in Airflow Connections (or a Secrets Backend) — never in DAG code [B2]:
- `conn_type`: `sap_rfc`
- `host`: SAP application server hostname
- `login`: SAP RFC user
- `password`: SAP RFC password (via Secrets Backend)
- `extra`: `{"client": "100", "sysnr": "00"}`

## Key Design Decisions

| Decision | Guidance |
|---|---|
| **Background jobs vs. immediate RFC** | Most AutoSys SAP jobs ran background ABAP programs. Use RFC `JOB_OPEN` / `JOB_SUBMIT` / `JOB_CLOSE` pattern to submit a background job and then poll `JOB_STATUS` for completion [B2]. |
| **SAP HANA vs. SAP NetWeaver** | Different providers: `apache-airflow-providers-sap` for RFC (NetWeaver); SAP HANA provider (`hdbcli`) for HANA DB operations. |
| **Long-running SAP jobs** | Use a Deferrable Operator or a separate `SAPJobStatusSensor` that polls `JOB_STATUS` with `mode='reschedule'` to avoid blocking workers. |

## Sources

[B1] Broadcom AutoSys Documentation — SAP Application Job type, RFC-based agent communication with SAP NetWeaver (accessed 2026-08-18)
[B2] Apache Airflow Docs / SAP Provider Docs — `apache-airflow-providers-sap`, `SAPRfcHook`, `pyrfc` library, SAP NWRFC SDK requirement, SAP Connection configuration (accessed 2026-08-18)
