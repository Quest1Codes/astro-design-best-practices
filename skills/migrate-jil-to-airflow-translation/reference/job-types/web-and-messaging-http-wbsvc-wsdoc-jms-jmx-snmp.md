---
topic: web-and-messaging-http-wbsvc-wsdoc-jms-jmx-snmp
family: migration
skill: migrate-jil-to-airflow-translation
verified_against:
  airflow: "3.3.1"
  astro_runtime: "3.3-2"
  autosys: "12.0"
  autosys_doc_pages: [2551, 2459, 2469, 2546, 2547]
last_verified: 2026-09-17
confidence: mixed
signals: []
---

# Web and messaging: HTTP, WBSVC, WSDOC, JMS*, JMX*, SNMP*

| Code | Default target | Disposition | Delta |
|---|---|---|---|
| `HTTP` [AS p.2551] | `HttpOperator` / `HttpSensor` (`apache-airflow-providers-http`) | MECH/JUDG | Auth mechanism needs mapping to a Connection |
| `WBSVC` (Web Service RPC/Encoded) [AS p.2459, p.2468-2469] | `@task` using `zeep` for SOAP, or `HttpOperator` if the "web service" is really a REST call underneath | JUDG | SOAP has no dedicated Airflow provider operator; a `@task` wrapping a client library is the honest answer |
| `WSDOC` (Web Service Document/Literal) [AS p.2546-2547] | Same as `WBSVC` | JUDG | Same |
| `JMSPUB` / `JMSSUB` | `@task` with a vendor JMS client (`stomp.py` or similar); `JMSSUB` as a deferrable custom sensor if it needs to wait for a message | REDESIGN | No Airflow provider covers JMS; this is genuinely provider-less territory |
| `JMXMAG`/`JMXMAS`/`JMXMC`/`JMXMOP`/`JMXMREM`/`JMXSUB` | `@task` using `jmxquery`/Jolokia HTTP bridge; **NONE** if the job is monitoring-only | REDESIGN / NONE | Same reasoning as `OM*`: if it's pure monitoring, it moves to the monitoring stack, not Airflow |
| `SNMPGET`/`SNMPSET` | `@task` using `pysnmp`; **NONE** if monitoring-only | REDESIGN / NONE | Same |

## Deciding REDESIGN vs. NONE for the messaging/JMX/SNMP siblings

Check `manifest.graph` for outbound condition edges from the job — if something downstream
depends on its result, it's REDESIGN (needs a real translation); if it's purely informational
(alerts/logs only, no dependents), it's NONE (moves to monitoring), same test as `OMTF`'s
exception in `reference/os-monitors-om.md`.

## What the scaffolder emits vs. leaves as TODO

Emits an `HttpOperator`/`HttpSensor` skeleton for `HTTP` jobs with the endpoint/auth
parameterized. For `WBSVC`/`WSDOC`/`JMS*`/`JMX*`/`SNMP*`, emits a `@task` stub with the vendor
client import and a `# TODO(JUDG:vendor-client)` marker — never a fabricated provider operator
call for a protocol Airflow doesn't natively support.
