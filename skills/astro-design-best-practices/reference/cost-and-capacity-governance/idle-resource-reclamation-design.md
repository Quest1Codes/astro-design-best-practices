# Idle-Resource Reclamation Design

On Astro, workers scale to zero automatically — but the scheduler and webserver continue running 24/7, even when no DAGs are scheduled during off-hours. For non-production environments (dev, staging, feature branches), this constant baseline cost is wasteful. Astro provides **Deployment Hibernation** to address this.

## Deployment Hibernation

Deployment Hibernation is Astro's native mechanism to scale all Deployment components (scheduler, webserver, workers, triggerer) to **zero** on a defined schedule [B1].

**Requirements**:
- The Deployment must be created with **Development Mode** enabled [B1].
- Hibernation is configurable via the Astro UI or programmatically via the Astro API [B1].

**Configuration** (via Astro UI):
- Set a **Wake Schedule** (e.g., `Mon–Fri 09:00–18:00 IST`) so the environment only runs during working hours.
- Outside the wake window, all compute is scaled to zero — no scheduler, no webserver, no workers running [B1].

> **Warning**: Do NOT enable Development Mode on production Deployments. Production SLAs require continuous scheduler uptime. Hibernation is strictly for non-production environments [B1].

## Use Cases

| Scenario | Approach |
|---|---|
| **Dev/staging environments** | Enable hibernation with a business-hours wake schedule. Expected savings: 40–70% vs. always-on [B1]. |
| **Feature-branch ephemeral environments** | Create Deployments via CI/CD on branch open; destroy on merge/close. Use `astro deployment create` / `astro deployment delete` in the pipeline [B1]. |
| **Scheduled batch-only Deployments** (e.g., runs only during nightly batch windows) | Use hibernation with a wake schedule that matches the batch window only. Example: wake from 22:00–06:00, hibernate the rest of the day. |

## Right-Sizing as Reclamation

Idle resource reclamation is not only about hibernation — over-provisioned always-on Deployments also waste resources:
- Use the **Deployment Analytics** dashboard in the Astro UI to identify CPU and memory utilization per pod [B1].
- If scheduler or webserver pods are consistently at < 30% utilization, downsize the AU allocation.
- If workers are frequently at 0 tasks but `min_workers` is set to 1, reduce to 0 and accept the minor cold-start latency of the autoscaler.

## Deferrable Operators as Idle Reduction

For production Deployments that cannot hibernate, Deferrable Operators reduce the "idle worker" problem within the batch window itself: rather than keeping a large worker pod alive while waiting for an API callback (potentially for hours), the worker is released and re-provisioned only when the external event fires [B1]. This directly reduces peak worker-hour costs even without hibernation.

## Sources

[B1] Astronomer Docs — Deployment Hibernation, Development Mode requirement, Wake Schedule configuration, Astro API for programmatic hibernation control, and Deployment Analytics for right-sizing (accessed 2026-08-11)
