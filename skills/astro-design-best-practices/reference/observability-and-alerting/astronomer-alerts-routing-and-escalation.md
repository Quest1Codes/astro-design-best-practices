# Astronomer Alerts Routing and Escalation

AutoSys integrated with enterprise event managers to route alarms based on job criticality. On the Astro platform, alert routing can be handled at two levels: native **Astro Alerts** (platform-level) and **Airflow Callbacks** (code-level).

## The two-tier alerting strategy

| Mechanism | Where it's configured | Best for |
|---|---|---|
| **Astro Alerts** | Astro UI (Deployment/Workspace/Org level) | Baseline monitoring: DAG failures, task duration, DAG SLAs. No code changes required [B1][B2]. |
| **Airflow Callbacks** (`on_failure_callback`) | Python DAG code | Custom logic, task-specific routing (e.g., only paging for one specific task out of 50), or interacting with internal APIs [B2][B6]. |

> **Astronomer's recommendation**: Use Astro Alerts for standard failure and SLA monitoring as it is easier to maintain centrally. Reserve Airflow callbacks for tasks requiring highly custom logic [B1][B2].

## Astro Alerts capabilities

Astro Alerts natively support routing to five channels [B1][B4][B14]:
1. **Email**
2. **Slack**
3. **PagerDuty**
4. **Opsgenie**
5. **Dag Trigger** — the alert itself triggers a DAG run, letting the alert response be automated Airflow logic rather than only a human-facing notification; architecturally distinct from the other four and worth considering for auto-remediation patterns

Supported trigger events include:
- DAG Failure / Success
- DAG Timeliness (SLA)
- DAG / Task Duration anomalies

## Routing and escalation design (Axis B — H rating)

While Astro handles the *delivery* of the alert, the *escalation* logic should reside in the destination platform (e.g., PagerDuty) [B10][B11].

**Best Practice Routing Model:**

1. **Severity classification**:
   - **P1/P2 (Critical)**: Production DAG failures affecting business SLAs.
   - **P3/P4 (Warning)**: Task retries, non-critical pipeline failures.
2. **Channel routing**:
   - Route P1/P2 from Astro Alerts directly to a **PagerDuty integration** [B1][B12]. PagerDuty's Escalation Policies then handle on-call routing and reassignment [B11].
   - Route P3/P4 from Astro Alerts to a **dedicated Slack channel** (e.g., `#data-eng-warnings`) to avoid waking engineers for non-critical issues [B10][B13].

## Email notifications on Astro

If using Airflow's native `EmailOperator` or email callbacks on Astro, you must configure an external SMTP service (e.g., SendGrid, Amazon SES) per Deployment [B6][B7]. Astro does not provide a built-in SMTP relay for custom Airflow code (though native Astro Alerts to email work automatically).

## Sources

[B1, B3, B4] Astronomer Docs — Astro Alerts: https://www.astronomer.io/docs/astro/alerts (accessed 2026-08-08)
[B14] Astronomer Docs — Configure and add alert notification channels (five channels: Slack, PagerDuty, Email, Dag Trigger, Opsgenie): https://www.astronomer.io/docs/astro/alerts#configure-and-add-alert-notification-channels (tier 1, added on doc-verification review — corrects the earlier three-channel claim)
[B2] Astronomer Docs — When to use Airflow or Astro alerts for your pipelines on Astro: https://www.astronomer.io/docs/astro/best-practices/airflow-vs-astro-alerts (tier 1)
[B6, B7] Astronomer Docs — Configure Airflow email notifications on Astro: https://www.astronomer.io/docs/astro/airflow-email-notifications (tier 1)
[B10, B11] PagerDuty / AlertOps — Escalation policy best practices (accessed 2026-08-08)
[B12, B13] Medium — Managing alert fatigue with Slack and PagerDuty (accessed 2026-08-08)
