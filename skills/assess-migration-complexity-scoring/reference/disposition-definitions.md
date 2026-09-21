---
topic: disposition-definitions
family: assessment
skill: assess-migration-complexity-scoring
verified_against:
  airflow: "3.3.1"
  astro_runtime: "3.3-2"
  autosys: "12.0"
last_verified: 2026-09-17
confidence: mixed
signals: []
---

# Disposition definitions

REWRITE ← the pre-refactor `migrating-autosys-to-astronomer/reference/mapping.md`'s
classification section, tightened with precise tests and examples. Five outcomes, not four — see
`DECOMMISSION` below, added this refactor from `history_stats.py`'s dead-job detection.

## MECH (mechanical)

**Test**: a direct, deterministic translation exists — given the same JIL and the same registry,
two competent engineers would produce byte-identical target code (the same test the whole
refactor uses for "is this deterministic" per plan §0). No design decision required.

Examples:
- `CMD` job with a plain shell/script command and no complex condition → `@task.bash` /
  `BashOperator`.
- `owner:` → `owner` in `default_args`.
- `FTP`/`SCP` job once the protocol is confirmed → the matching provider transfer operator
  1:1, since the attribute set maps directly.

## JUDG (judgment)

**Test**: a mapping exists, but it isn't 1:1 — a design decision determines which of several
valid target shapes applies. The decision is bounded (a fixed decision tree exists in the
relevant `job-types/*.md` or `conditions-and-dependencies.md` file), not open-ended.

Examples:
- `BOX` job → TaskGroup within one DAG, or its own DAG linked by an Asset/`TriggerDagRunOperator`
  — depends on schedule/team/ownership per `migrate-jil-to-airflow-translation/reference/job-types/core-cmd-box.md`'s
  decision tree.
- `FW` (file watcher) → `FileSensor` if genuinely polling a filesystem, or an Asset-triggered
  schedule if the file is produced by another Airflow-owned DAG.
- A `condition:` with a look-back value → `ExternalTaskSensor(execution_date_fn=...)` vs. an
  Asset with a time window — the mechanics are known, which one applies is a per-job call.

## REDESIGN

**Test**: the AutoSys pattern has no direct Airflow shape at all — a genuinely different
implementation approach is needed, not a variant of an existing one.

Examples:
- An OR-combined condition spanning several jobs — no single stock `trigger_rule` expresses OR
  semantics across arbitrary predecessors; needs decomposition or a custom evaluator task.
- A hidden `sendevent` call embedded in a job's command — the dependency it creates has no JIL
  representation to translate at all; it has to be made explicit as a new
  `TriggerDagRunOperator`/Asset edge, or deliberately removed.
- `JMS*`/`JMX*`/`SNMP*` job types — no Airflow provider covers these; a custom `@task` using a
  vendor client library is the honest answer, not a fabricated provider operator.

## NONE

**Test**: no orchestration equivalent exists, and that's fine — the right answer is "this
doesn't belong in Airflow," with a documented alternative. Not a blocker; the smallest possible
scope reduction.

Examples:
- `OM*` (OS monitor) job types — infrastructure monitoring belongs in Prometheus/Datadog, not
  the orchestrator.
- `std_out_file`/`std_err_file` explicit redirection — Airflow captures task logs natively; the
  attribute is dropped, with "task logs" as the documented alternative.
- `WOL` (Wake on LAN) — no orchestration equivalent; document and move on.

## DECOMMISSION

**Test**: `history_stats.py`'s `dead_jobs()` flags the job (no run in the configured window, and
no calendar/condition eligibility that would explain the silence) — the cheapest possible
migration outcome, because there's no migration work at all, only a confirm-and-drop step.

**Always confirm with the platform team before finalizing** — "no run in window" can also mean
"runs only on a rare trigger this assessment's history window didn't capture." A `DECOMMISSION`
disposition that turns out to be wrong is worse than a `MECH` one that turns out to be easy.

## Choosing between adjacent dispositions

When a job could plausibly be scored two ways, prefer the *more conservative* (higher-severity)
one and let a human override with a recorded reason once actually reviewed — this mirrors
`score_estate.py`'s own aggregation rule (box disposition = most severe among itself and
children) and the same "undercounting is the real risk" principle behind the additive modifiers
in `reference/scoring-rules.md`.
