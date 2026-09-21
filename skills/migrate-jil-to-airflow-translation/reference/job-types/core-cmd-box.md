---
topic: core-cmd-box
family: migration
skill: migrate-jil-to-airflow-translation
verified_against:
  airflow: "3.3.1"
  astro_runtime: "3.3-2"
  autosys: "12.0"
  autosys_doc_pages: [2550, 2551, 2422]
last_verified: 2026-09-17
confidence: mixed
signals: [windows]
---

# Core: CMD, BOX, CMDMACHINE

SPLIT ← pre-refactor `mapping.md`'s job-type table (kept: `c`/`b` rows, the Box → DAG boundary
decision tree) + plan §5.1. This family is the bulk of any real estate.

| Code | Default target | Disposition | Attributes consumed | Delta |
|---|---|---|---|---|
| `CMD` (default job type [AS p.2550]) | `@task.bash` / `BashOperator`, or a provider operator if the command is really "call this system" (a wrapped SQL call → `SQLExecuteQueryOperator`) | MECH | `command`, `machine`, `n_retrys`, `term_run_time`, `job_load` | None expected for a plain shell/script command |
| `BOX` | TaskGroup within one DAG, **or** its own DAG linked by an Asset/`TriggerDagRunOperator` | JUDG — decision tree below | `box_name` (children), `box_success`/`box_failure`, `box_terminator` | Box-level alarm/terminator semantics need explicit re-implementation, not assumed to fall out of TaskGroup grouping |
| `CMDMACHINE` | `BashOperator` with the machine chosen at runtime → worker queue / `KubernetesPodOperator` | JUDG | `machine` (list, load-balanced) | PRACTITIONER JUDGMENT — this job type was not found in the ingested 12.0 corpus (`autosys-reference/reference/job-types.md`'s coverage note); confirm its real attribute set against the customer's export before relying on this row |

## Box → DAG boundary decision tree

A box becomes:

1. **A TaskGroup in the parent's DAG** if: same schedule as its parent, same owning team, and
   nothing downstream needs to depend on it independently of the parent box completing.
2. **Its own DAG, linked by an Asset** if: something outside the parent box's condition strings
   needs to know "this box's output is ready" — i.e. the box's completion is itself a signal
   other jobs currently poll for via `success()`/`done()` conditions across box boundaries
   (`manifest.graph.cross_box_condition_edge_count` > 0 for this box is the mechanical signal).
3. **Its own DAG, linked by `TriggerDagRunOperator`** if: the box is explicitly kicked off
   out-of-band today (`sendevent -E FORCE_STARTJOB`, found as a `hidden_control_flow` edge) or by
   a calendar independent of its nominal parent — i.e. it isn't purely schedule-driven.
4. **Flattened into the parent** (no separate grouping) only when the box exists purely as a JIL
   organizational convenience — a single child, no independent alarm/calendar. Rare; confirm
   before flattening, since `alarm_if_fail` on a box is itself meaningful
   (`reference/alerting-and-sla.md`).

Leaf boxes (no nested boxes) are usually TaskGroups; boxes at a scheduling or team boundary are
usually their own DAG. When unsure, default to option 2 (Asset link) — loosest coupling, easiest
to flatten later if wrong. `manifest.stats.box_metrics[box].depth`/`mixed_owners` are the
mechanical inputs to this call.

## Windows options [plan §11.11]

Astro workers are Linux. A `.bat`/`.ps1`/`cmd /c` command, `owner: DOMAIN\user`, or a mapped-drive
path (all flagged by `_lib.autosys_jil.commands.analyze()`'s `os_hint: windows`) needs one of:

1. **Containerize on Linux with PowerShell Core** — the cleanest long-term option when the
   script logic is portable.
2. **Bridge via `SSHOperator`/WinRM to a residual Windows host** — fastest path, defers the real
   re-platforming decision; see `migrate-topology-onprem-distributed` for the bridge-vs-Hybrid
   framing.
3. **Re-platform** — rewrite the logic natively for Linux, when the script is thin enough that
   this is cheaper than maintaining a bridge indefinitely.

State which option was chosen and why per job; never scaffold a `BashOperator` for a
Windows-flagged command and hope it works.

## Worked example (from the fixture estate)

```
insert_job: fetch_bloomberg_eod_prices
job_type: CMD
machine: mktdata-app-01
command: /scripts/mktdata/fetch_bloomberg.sh --type EQUITY --date %%DATE%%
```

→

```python
@task.bash(retries=1)
def fetch_bloomberg_eod_prices():
    return "/scripts/mktdata/fetch_bloomberg.sh --type EQUITY --date {{ ds }}"
```

with `params={"autosys_job_name": "fetch_bloomberg_eod_prices", "autosys_instance": "ACE"}` and
`doc_md` carrying the original JIL block (redacted).

## What the scaffolder emits vs. leaves as TODO

`scaffold_dags.py`'s `_emitters/core.py` emits the full `@task.bash`/`BashOperator` call for a
MECH-scored `CMD` job, including `retries`/`execution_timeout` from `n_retrys`/`term_run_time`.
For a `BOX`, it emits the TaskGroup/DAG-split structure per the disposition already recorded in
`manifest.decisions[]` (a human decision from step 2 above, not re-derived by the scaffolder) and
leaves a `# TODO(JUDG:box-terminator)` wherever `box_terminator`/`box_success`/`box_failure`
semantics need explicit re-implementation.
