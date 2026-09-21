---
topic: wcc-and-web-ui
family: knowledge
skill: autosys-reference
verified_against:
  autosys: "12.0"
  autosys_doc_pages: [1134, 1135, 2146, 2147, 2148, 2895, 2896]
last_verified: 2026-09-17
confidence: cited
signals: []
---

# Web UI (WCC) and AutoSys Web Services (AEWS)

"WCC" (Workload Control Center) is the pre-12.0 product name for what the 12.0 doc calls **Web
UI** — the browser GUI. Both terms appear across real customer estates and older skill content;
this file uses "Web UI" to match the 12.0 corpus, with "WCC" noted where a customer or older
document uses it.

## What Web UI is, architecturally [AS p.2146-2148]

Web UI is a client of the application server, served by Apache Tomcat (port 9443 by default),
which in turn talks to CA EEM (port 5250) for authentication when external security is active
(the default — see `reference/security-eem-and-native.md`). Web UI is not a separate data store:
everything it shows and edits lives in the same event server the CLI and agents use.

## Agent Inventory [AS p.1134-1135]

Web UI periodically polls agent information and displays it under Agent Inventory — **only for
agents in AutoSys-compatible mode**. Requires the Web Services URL to be configured (a Custom,
not Typical, install, since Typical does not install web services) [AS p.1134]. Refresh cadence
is configurable (`Refresh Time (Delta)` vs. `Refresh Time (Full)`, SP7+ delta-only refresh vs.
full refresh on older releases) [AS p.1135] — relevant only to how current the Web UI's own view
of the fleet is, not to anything exportable for discovery.

## What's exportable vs. not

| Artifact | Exportable via CLI? |
|---|---|
| Job/machine/resource/calendar definitions | Yes — JIL export, `autorep`, `autocal_asc` (see `reference/commands.md`) |
| Monitors and reports (`insert_monbro`) | Yes — part of a JIL export, see below |
| Web UI dashboard layouts, Quick Edit groups, saved views | **No standard CLI export** — these are Web UI configuration, not AutoSys objects. Discovery must ask the platform team who uses which dashboards/views and why (`assess-estate-discovery/reference/stakeholder-questions.md`), since this determines the Astro UI/Observe/Grafana dashboard scope, not anything `build_estate_manifest.py` can derive. |
| CA EEM policies (Web UI RBAC) | Yes, via `safex`/`as_safetool` — see `reference/security-eem-and-native.md` |

## Monitors and reports — `insert_monbro` [AS p.2895-2896]

```
insert_monbro: monbro_name
mode: b|r          /* "browser" or "report" -- b shown in the PDF's own example, comment says "browser" */
job_name: ...       /* required for a single job/box */
job_filter: ...
success: y|n
failure: y|n
running: y|n
starting: y|n
terminated: y|n
restart: y|n
all_status: y|n
all_events: y|n
alarm: y|n
alarm_verif: ...    /* monitors only */
after_time: ...      /* reports only */
currun: ...           /* reports only */
```

Defining a `monbro` has **no effect until it is also run** [AS p.2895] — its presence in a JIL
export is evidence of intent, not evidence of an active monitor. `_lib.autosys_jil.models`
captures these as `GenericObject(kind="monbro", ...)`; the discovery checklist's WCC row is
partly satisfied by these blocks, and partly not (dashboard-layer config above is not captured
here at all).

## AutoSys Web Services (AEWS) [AS p.2146-2148]

A REST API for job monitoring and control (status retrieval; start/cancel/hold/etc. actions),
authenticated via CA EEM over HTTPS (Tomcat JAAS realm + EEM LoginModule), standard HTTP/1.1
response codes, ISO 8601 timestamps. This is the inbound-trigger surface discovery must
inventory: anything calling *into* AEWS today (a scheduling wrapper, an ITSM integration, a
custom ops tool) has to be repointed at the Airflow REST API at cutover — see
`assess-estate-discovery/reference/what-jil-cannot-tell-you.md` and
`migrate-parallel-run-and-cutover/reference/cutover-runbook.md`'s inbound-caller repointing step.
AEWS access logs (if retained) are the only way to find these callers mechanically; nothing in a
JIL export names them.
