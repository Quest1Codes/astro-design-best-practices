---
topic: alerting-and-observability-wiring
family: migration
skill: migrate-astro-platform-buildout
verified_against:
  airflow: "3.3.1"
  astro_runtime: "3.3-2"
last_verified: 2026-09-17
confidence: mixed
signals: [svcdesk]
---

# Alerting and observability wiring

This is the platform-layer half of alerting — the actual integration wiring. Per-job translation
targets (which attribute maps to which callback) are `migrate-jil-to-airflow-translation/reference/alerting-and-sla.md`'s
job; this file is about where those callbacks/Astro Alerts actually route.

## ITSM integration

`manifest.architecture.decisions.alerting_itsm` (from `assess-astro-target-architecture`) names
whether `svcdesk_*` attribute usage was found and what tool to wire to. Get the actual routing
table (who gets paged, through which channel) from the platform team as a separate input — the
JIL export tells you *that* a job alerts, not the current PagerDuty/email/ITSM routing, which
lives in AutoSys's notification configuration or WCC settings.

## Astro Alerts vs. callbacks

Astro Alerts (Deployment-level or DAG-level) are the preferred mechanism for a target on Astro —
prefer them over hand-written `on_failure_callback` wiring where they cover the need, since
they're centrally configurable and don't require a code change per DAG to adjust routing. Fall
back to callbacks for anything Astro Alerts doesn't yet cover (check current capability, this
refactor did not have live MCP access to verify).

## Observability: Astro Observe / OpenLineage

Route estates with existing lineage/observability tooling
(`astro-design-best-practices/reference/observability-and-alerting/openlineage-data-lineage-integration.md`)
per whatever the assessment's `nfr.compliance`/existing-monitoring-stack findings showed. A
customer already invested in a monitoring stack (Prometheus/Datadog/Grafana) should have Astro
metrics/logs integrated into that stack, not stand up a parallel one.

## Validation

Gate P5 (alert fires end-to-end) in `reference/validation.md` is the proof this wiring actually
works — configuring an alert and never testing it fire is not "done."
