# Critic Report — Topics 011-020

Full output of the fresh-context Critic subagent pass run against these 10 shipped files (live-fetched sources via WebFetch/WebSearch/`gh api`, not just trusted at face value). All findings were addressed directly in the shipped files (see `topics-011-020-fact-sheet.md`'s summary). Preserved here verbatim as the permanent audit-trail record.

---

## Overall verdict per file (as originally submitted, before fixes)

| File | Verdict |
|---|---|
| `concurrency-controls-pools-and-max-active-runs.md` | PASS WITH NOTES |
| `naming-and-tagging-conventions-at-scale.md` | PASS |
| `one-off-and-ad-hoc-job-design.md` | PASS WITH NOTES |
| `celeryexecutor-vs-kubernetesexecutor-decision-framework.md` | PASS WITH NOTES |
| `worker-queue-segregation-mirroring-machine-groups.md` | PASS |
| `autoscaling-design-for-bursty-batch-workloads.md` | PASS WITH NOTES |
| `per-task-resource-requests-and-limits.md` | **FAIL** |
| `node-affinity-and-taints-for-specialized-jobs.md` | PASS |
| `keda-based-autoscaling.md` | **FAIL** |
| `hybrid-executor-strategy.md` | PASS |

2 of 10 FAIL, 4 PASS WITH NOTES, 4 clean PASS.

## Unsourced or misattributed claims (quoted, all fixed post-review)

**1. `keda-based-autoscaling.md` — most serious finding in the batch.** Original text claimed a "10 second" polling interval and "5-minute cool-down," both cited to `astronomer.io/blog/the-keda-autoscaler/`. That post was fetched three separate ways (targeted queries for the numbers, then a full paragraph transcription) and confirmed to contain the worker-count formula but zero mentions of any interval or cool-down duration. The actual Apache Airflow Helm chart source (`chart/values.yaml`, fetched via `gh api`) gives `pollingInterval: 5` / `cooldownPeriod: 30` (seconds) as defaults — a different pair of numbers entirely, and the one real, directly-sourced data point available. The file's design-guidance section then built further confident advice ("it's a deliberate anti-thrashing design choice, not a tuning bug") on top of the fabricated number.

**2. `per-task-resource-requests-and-limits.md` — both sharp-edge claims fail citation support.** Both claims ("requests must not exceed limits... can leave pods stuck rather than failing cleanly," and "executor_config resource settings... sometimes bleeding into another task's pod") were cited to `github.com/apache/airflow/discussions/22717`. The full discussion body and all 8 comments (pulled via `gh api repos/apache/airflow/discussions/22717/comments`) contain neither claim — the thread is three people posting working `pod_override` code snippets and asking what `200m` CPU means. The second claim was at least correctly hedged (`NEEDS_EXEC_CHECK`) per the AGENTS.md escalation path, but the citation attached to it was still wrong, and it could not be independently located anywhere else via search either.

**3. `concurrency-controls-pools-and-max-active-runs.md` — misattributed but low-severity.** The `core.max_active_runs_per_dag` claim cited `F3` (`pools.html`, which live-fetch confirms covers only `pool_slots` and contains no mention of `max_active_runs` at all); the claim is real and is actually supported by `F1` (`astronomer.io/docs/learn/airflow-pools`, verified verbatim), just not the citation attached to it.

**4. `celeryexecutor-vs-kubernetesexecutor-decision-framework.md` — overstated citation on a real but unsupported comparison.** The "KubernetesExecutor showed a resource-utilization advantage... on bursty workloads" claim, cited to `[F2]` (`astronomer.io/blog/the-new-kubernetesexecutor/`), was fetched twice hunting for burst/idle/utilization language; the post discusses per-pod startup overhead and in one place argues the *opposite* emphasis — "the CeleryExecutor will be more efficient at super high volume since it can run multiple tasks on a single worker." The reasoning itself is sound and derivable from the file's own F1-cited executor mechanics, but F2 doesn't say it — this should have been `{syn: F1}`, not `[F2]`. The identical pattern, softer, recurred in `autoscaling-design-for-bursty-batch-workloads.md`'s citation of the same blog for "scales down conservatively... to avoid thrashing."

## Smuggled facts inside `{syn: ...}` tags

None found across all 10 files — every synthesis block checked against its listed row IDs, all logically constructible from cited facts alone. Same clean result as the previous batch.

## NEEDS_EXEC_CHECK / PRACTITIONER JUDGMENT flag review

- `naming-and-tagging-conventions-at-scale.md` `F1` — correctly labeled `PRACTITIONER JUDGMENT`, precisely scoped to the naming shape only, not the underlying `tags` feature.
- `one-off-and-ad-hoc-job-design.md` `F2` — correctly `NEEDS_EXEC_CHECK`'d; independently re-confirmed still-current by the Critic's own search, closed.
- `per-task-resource-requests-and-limits.md` — the cross-task-bleed bullet was appropriately *hedged* in tone, but that didn't rescue the *citation*, which was a separate defect.
- `keda-based-autoscaling.md` — clear **under-hedging**: two specific numbers stated as plain "Core mechanics" fact with no flag at all, despite being exactly the kind of thing that should have triggered `NEEDS_EXEC_CHECK`.
- `celeryexecutor-vs-kubernetesexecutor-decision-framework.md`'s bursty-workload claim — also arguably under-hedged; read as direct citation when it was closer to synthesis.

## Cross-file consistency

- The `astronomer.io/blog/the-new-kubernetesexecutor/` sourcing gap appeared in **two** files — fixed in both together, not just one.
- `CeleryKubernetesExecutor` described consistently between `celeryexecutor-vs-kubernetesexecutor-decision-framework.md` and `hybrid-executor-strategy.md` — independently verified against Airflow's own source (`celery_kubernetes_executor.py` docstring: queue named `kubernetes_queue`, default value `kubernetes`, routes to KubernetesExecutor; otherwise CeleryExecutor).
- `hybrid-executor-strategy.md`'s claim that `CeleryKubernetesExecutor` and `KubernetesPodOperator` are two genuinely independent mechanisms confirmed directly from Airflow docs: "`KubernetesPodOperator` can be used to similar effect, no matter what executor you are using."
- `node-affinity-and-taints-for-specialized-jobs.md` correctly defers pure resource-isolation questions to `per-task-resource-requests-and-limits.md` rather than re-explaining — no contradiction, good factoring.
- `worker-queue-segregation-mirroring-machine-groups.md`'s `F2` claims verified essentially verbatim against `astronomer.io/docs/astro/configure-worker-queues`, including the specific example categories reused in its guidance table.
- No contradictions found between DAG-run-level controls (`max_active_runs`) and task/pod-level controls (`pool_slots`, `executor_config`) across the scheduler-and-dag vs. executor-and-worker clusters.

## Final recommendation (as given, before fixes were applied)

8 of 10 files ready for sign-off as-is or with only a trivial citation-swap. 2 of 10 needed a named fix before sign-off — both fixed: `keda-based-autoscaling.md` (RETURN TO RESEARCHER — locate real numbers or soften/flag) and `per-task-resource-requests-and-limits.md` (RETURN TO RESEARCHER — re-source or remove unsupported claims).
