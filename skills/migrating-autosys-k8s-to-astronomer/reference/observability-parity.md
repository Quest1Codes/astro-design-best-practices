# Observability parity

## What to inventory

List what the source estate actually monitors today and how operators are alerted, before mapping anything:

- **Pod/infrastructure health** (is the Application Server pod up, is an agent pod crash-looping) — typically Prometheus/Grafana watching Kubernetes-level metrics, or a cloud provider's native monitoring.
- **Job-level status** (did job X succeed, is job Y running long) — typically WCC's own views, `autorep`-based polling, or a custom dashboard querying the AutoSys database directly.
- **Alerting/paging** — see the core skill's `reference/alerting-and-sla.md`; the routing (who gets paged) is organizational, the mechanism here is what triggers it.
- **Lineage/audit** (what ran, what it touched, in what order) — if anything exists here at all in a typical AutoSys estate, it's usually informal (log correlation, manual documentation) rather than a first-class product feature.

## Mapping

| Source concern | Target |
|---|---|
| Pod/infrastructure health | Standard Kubernetes observability (Prometheus/Grafana) continues to apply to the underlying cluster largely unchanged — Astronomer components (scheduler, workers, webserver, triggerer) are just different pods to watch, not a different monitoring paradigm |
| Job-level status | Airflow UI (real-time), plus Astro Observe if the target is Astro-hosted, for the higher-level "is this pipeline healthy, is it on time" view WCC provided |
| Alerting/paging | `on_failure_callback`/`on_success_callback` wired to the existing paging system, or Astro Alerts if migrating the routing itself is in scope (confirm with the platform team before assuming the alert routing changes at all — it may just need a new trigger source pointed at the same downstream system) |
| Lineage/audit | OpenLineage (native to Airflow) / Astro's lineage view — this is usually a genuine capability upgrade over whatever informal lineage tracking existed before; call it out as such in the report rather than treating it as a strict translation |

## What's usually missing from the source and shouldn't be invented for the target

Don't build column-level lineage, cost-per-job accounting, or other capabilities the source AutoSys estate never had, just because Astro Observe or OpenLineage happen to support them — scope observability parity to what operators actually relied on day to day, and note genuinely new capabilities as optional upside in the report, not requirements.

## Validating parity

Before calling observability `complete` for a namespace/environment, confirm: an intentionally-failed test job actually pages the right person through the new path, and a normal successful run is actually visible in the new dashboard/UI to whoever checked WCC for that information before.
