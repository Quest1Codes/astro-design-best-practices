# Native Web Services Job Type (job_type: WS) → Airflow HttpOperator/SimpleHttpOperator Design

AutoSys's `job_type: WS` (Web Services) is a native job type that submits SOAP or REST web service calls **without a wrapper script** — the JIL definition contains the endpoint URL, method, headers, and payload directly [B1]. This is AutoSys's built-in HTTP client; no shell script or third-party tool is needed.

In Airflow, there is no "WS job type." Every HTTP call is expressed as an operator using the `HTTP provider` (`apache-airflow-providers-http`) [B2]. The equivalent is `HttpOperator` (Airflow 2.4+) or the older `SimpleHttpOperator`.

## Concept Mapping

{syn: AutoSys `job_type: WS` → Airflow `HttpOperator`; AutoSys WS endpoint URL → Airflow HTTP Connection `host`}

| AutoSys WS JIL Attribute | Airflow Equivalent |
|---|---|
| `web_service_url` | Airflow Connection `host` + `HttpOperator(endpoint=...)` |
| HTTP method (GET/POST) | `HttpOperator(method="POST")` |
| Request body / payload | `HttpOperator(data=...)` |
| Request headers | `HttpOperator(headers={...})` |
| Response check condition | `HttpOperator(response_check=lambda resp: resp.status_code == 200)` |
| SOAP envelope | Custom operator using `zeep` library (no native SOAP operator) |

## REST Pattern

```python
from airflow.providers.http.operators.http import HttpOperator
import json

call_rest_api = HttpOperator(
    task_id="call_payment_api",
    http_conn_id="payment_service",   # Connection stores base URL + auth
    endpoint="/api/v2/payments/process",
    method="POST",
    headers={"Content-Type": "application/json"},
    data=json.dumps({"amount": 100.00, "currency": "USD"}),
    response_check=lambda response: response.json().get("status") == "accepted",
    response_filter=lambda response: response.json().get("transaction_id"),
    log_response=True,
)
```

## SOAP Pattern

AutoSys WS also supported SOAP (`job_type: WS, soap_action: ...`). Airflow has no native SOAP operator. Use the `zeep` library in a `PythonOperator`:

```python
from airflow.decorators import task
from zeep import Client

@task
def call_soap_service(wsdl_url: str, operation: str, **kwargs) -> dict:
    client = Client(wsdl_url)
    result = client.service[operation](**kwargs)
    return dict(result)
```

Add `zeep` to `requirements.txt`.

## HTTP Sensor (Polling Pattern)

For AutoSys WS jobs that polled an endpoint until a condition was met:

```python
from airflow.providers.http.sensors.http import HttpSensor

wait_for_job_completion = HttpSensor(
    task_id="wait_for_api_completion",
    http_conn_id="batch_api",
    endpoint="/api/v1/jobs/{{ ti.xcom_pull(task_ids='submit_job') }}/status",
    response_check=lambda response: response.json().get("state") == "COMPLETED",
    mode="reschedule",   # Do not block worker slot while polling
    poke_interval=60,
    timeout=3600,
)
```

## Credential Management

Store all API credentials in **Airflow Connections** — never in DAG code [B2]:
- `conn_type`: `http`
- `host`: `https://api.payment-service.internal`
- `login` / `password`: API key (or use `extra` for Bearer tokens)

For OAuth2 APIs, use the `airflow-providers-http` with a token refresh wrapper in a custom Hook.

## Sources

[B1] Broadcom AutoSys Documentation — `job_type: WS`, Web Services job type (SOAP and REST, no wrapper script required), JIL `web_service_url` and `soap_action` attributes (accessed 2026-08-18)
[B2] Apache Airflow Docs — `HttpOperator`, `SimpleHttpOperator`, `HttpSensor`, `apache-airflow-providers-http`, `response_check`, `response_filter`, HTTP Connection (accessed 2026-08-18)
