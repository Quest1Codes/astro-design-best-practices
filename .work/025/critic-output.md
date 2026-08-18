# Critic Output — 025

*(Critic note: this review is conducted without referencing the Generator's reasoning process — only the draft and the fact-sheet.)*

## Verdict: **PASS with minor flags**

## Unsourced claims
- **Cleared**: The table rows citing [A1-1], [A1-2], [B5], [B6], [B-S4] are all traceable to the researcher fact-sheet rows; the `{syn: ...}` tag on B-S3 is correctly applied and the caveating NOTE block directly below it is present and accurate.
- **Flag — `B7` row** (AutoSys vs. Airflow metadata DB comparison in the intro paragraph): the intro states "AutoSys stored job state in its Event Server RDBMS" without a citation marker. This claim maps to researcher row `B4` which is correctly flagged as `PRACTITIONER JUDGMENT`. The Generator omitted the citation marker. **Severity: Low** — the practitioner judgment is still transparent in the researcher-output; the generated text is directionally correct and the NOTE on B-S3 sets the tone. Recommend adding `{syn: B4-practitioner-judgment}` inline or adding a brief annotation at the intro.

## Execution-check-required items
- **A1-4** (BYOD `skipAirflowDatabaseProvisioning` exact setup steps): correctly flagged `NEEDS_EXEC_CHECK` in the researcher; the draft references this note. ✓
- **B-S3** (memory-optimized instance class preference for large estates): correctly caveated with a NOTE block referencing the practitioner judgment. ✓

## Papered-over gaps
- **Specific numeric sizing thresholds** (e.g., "use `db.r6g.large` for estates > 5,000 DAG runs/day"): the draft correctly states there is no tier-1/2 source for these and uses `PRACTITIONER JUDGMENT`. ✓ Not papered over.

## Consistency conflicts with shipped files
- `reference/executor-and-worker/autoscaling-design-for-bursty-batch-workloads.md`: references sizing for worker resources; the 50–75% utilization target range cited in Topic 025 is consistent with the general Astro rightsizing guidance. ✓
- `reference/scheduler-and-dag/dag-factory-pattern-for-large-estates.md`: no conflicts detected.

## Axis coverage check
- **Deployment model (H)**: ✓ Full decision table present; Hosted vs. self-managed vs. BYOD covered
- **Estate scale (H)**: ✓ Small / mid / large sizing table present
- **Vertical/compliance (M)**: ✗ **Missing** — the researcher flagged `E1` (BYOD may be required for data residency in regulated verticals), but the draft has no callout for this. **Severity: Medium** — should add a 1–2 sentence callout noting that regulated verticals may need BYOD for data residency compliance, and that BYOD requires the user to own all DB security controls. This is an axis callout gap, not a fabricated fact.

## Recommendation
**PASS with two changes before shipping:**
1. Add a `{syn: intro-practitioner-judgment}` or brief annotation to the intro AutoSys comparison sentence.
2. Add a compliance callout (Axis E, M rating) noting that regulated verticals may require BYOD for data residency, and that BYOD transfers all DB security controls (encryption-at-rest, RBAC, audit logging) to the user.
