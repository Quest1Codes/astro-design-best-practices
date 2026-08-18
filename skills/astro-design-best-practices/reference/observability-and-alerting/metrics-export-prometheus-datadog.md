# Metrics Export (Prometheus / Datadog)

AutoSys exposed operational metrics via proprietary SNMP traps or database queries. Astro provides native, cloud-standard observability by emitting metrics in standard formats that can be routed to enterprise monitoring systems.

## Native Airflow metrics architecture

Apache Airflow natively emits metrics using the StatsD protocol. In the Astro platform architecture, these StatsD metrics are automatically collected, normalized by an internal `statsd_exporter`, and funneled into the platform's Prometheus instance [B7][B8].

## Export options on Astro

To send metrics to your own enterprise observability stack, Astro offers two primary methods:

### 1. Universal Metrics Exporter (Recommended for Prometheus/Grafana)

The Universal Metrics Exporter (UME) is the most robust way to export metrics from Astro [B1][B2].
- **Format**: Uses the Prometheus data model and supports `remote-write` [B1][B3].
- **Scope**: Exports both Airflow application-level metrics (e.g., DAG duration, task failures) AND Kubernetes infrastructure-level metrics (e.g., Pod CPU/Memory) [B1][B4].
- **Configuration**: Can be configured at the Workspace or Deployment level via the Astro UI [B1][B3].
- **Best for**: Teams using Prometheus, Grafana Cloud, or any system that accepts Prometheus `remote-write`.

### 2. Native Datadog Integration

Astro has built-in, streamlined support for exporting logs and metrics directly to Datadog [B1][B5].
- **Scope**: Focuses on standard Airflow metrics and logs [B5]. It does not provide the same depth of Kubernetes infrastructure metrics as the UME.
- **Configuration**: Enabled by setting `DATADOG_API_KEY` as a secret environment variable in the Astro Deployment [B6].
- **Best for**: Organizations heavily invested in Datadog wanting a zero-friction setup.

## Selection guidance (Axis A — H rating)

| Environment | Recommended Exporter | Notes |
|---|---|---|
| **Astro Hosted + Prometheus** | Universal Metrics Exporter | Provides the most comprehensive dataset |
| **Astro Hosted + Datadog** | Datadog Integration | Fastest setup; use UME if deeper infra metrics are needed |
| **Self-managed (Astronomer Software)** | Custom Prometheus scrape config | Software includes built-in Grafana; users can modify the scrape targets directly [B9] |

> **Design principle**: If you have a choice, prefer the Universal Metrics Exporter. It provides a richer dataset (combining application and infrastructure metrics) and uses an open standard (`remote-write`) that prevents vendor lock-in.

## Sources

[B1, B3, B4] Astronomer Docs — Universal Metrics Exporter: https://www.astronomer.io/docs/astro/export-metrics (accessed 2026-08-08)
[B5, B6] Astronomer Docs — Datadog integration (accessed 2026-08-08)
[B7, B8] Medium — Airflow and StatsD architecture (accessed 2026-08-08)
[B9] Astronomer Docs — Astronomer Software Grafana integration (accessed 2026-08-08)
