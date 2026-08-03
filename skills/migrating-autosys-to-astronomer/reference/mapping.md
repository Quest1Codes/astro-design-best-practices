# JIL construct → Airflow 3 concept map

Classify every job/box record with one of four dispositions before translating:

- **MECH** (mechanical) — direct, deterministic translation. No design decision required.
- **JUDG** (judgment) — a design decision is required (which DAG boundary, which trigger mechanism); the mapping exists but isn't 1:1.
- **REDESIGN** — the AutoSys pattern has no direct Airflow shape; a different implementation approach is needed.
- **NONE** — no equivalent; document the operational alternative and move on. Not a blocker by itself.

## Job types

| JIL `job_type` | What it is | Airflow 3 target | Disposition |
|---|---|---|---|
| `c` (command) | Runs a shell command / script on a `machine` | `@task.bash` / `BashOperator`, or a provider operator if the command is really "call this system" (e.g. a wrapped SQL call → `SQLExecuteQueryOperator`) | MECH |
| `b` (box) | Container job; children declare membership via `box_name` | TaskGroup within one DAG (same schedule, same team) **or** its own DAG linked by Dataset/`TriggerDagRunOperator` (different schedule, different team, or cross-machine-pool ownership) | JUDG — see decision tree below |
| `f` (file watcher) | Watches for a file's arrival (`watch_file`, `watch_interval`) | `FileSensor` (if literally polling a filesystem) — but if the file is produced by another Airflow-owned DAG, redesign as a Dataset-triggered schedule instead of polling | JUDG |
| `FT` (file transfer) | Moves a file between hosts; attributes vary the most across AutoSys/WA AE versions | Provider transfer operator matching the actual protocol (SFTP/FTP/Connect:Direct-adjacent) — **verify the JIL attribute names against the customer's export**, do not assume a fixed attribute set | JUDG (mechanics of the transfer are usually mechanical once the protocol is confirmed; the protocol confirmation itself is the judgment step) |

If the export contains a `job_type` not listed here, record it as `pending` with the raw attributes captured — do not guess its Airflow shape from the name alone.

## Box → DAG boundary decision tree

A box becomes:

1. **A TaskGroup in the parent's DAG** if: same schedule as its parent, same owning team, and nothing downstream needs to depend on it independently of the parent box completing.
2. **Its own DAG, linked by a Dataset** if: something outside the parent box's condition strings needs to know "this box's output is ready" (i.e., the box's completion is itself a signal other jobs currently poll for via `d()`/`s()` conditions across box boundaries).
3. **Its own DAG, linked by `TriggerDagRunOperator`** if: the box is explicitly kicked off out-of-band today (via `sendevent -E FORCE_STARTJOB` or a calendar independent of its nominal parent), i.e., it isn't purely schedule-driven.
4. **Flattened into the parent** (no separate grouping) only when the box exists purely as a JIL organizational convenience with a single child and no independent alarm/calendar — rare; confirm before flattening, since `alarm_if_fail` on a box is itself meaningful (see `reference/alerting-and-sla.md`).

Leaf boxes (no nested boxes) are usually TaskGroups; boxes that sit at a scheduling or team boundary are usually their own DAG. When unsure, default to option 2 (Dataset link) — it preserves the loosest coupling and is the easiest to later flatten if wrong.

## Other constructs

| JIL construct | Airflow 3 target | Disposition |
|---|---|---|
| `machine:` | Executor/queue/pool assignment — see the relevant companion skill (mainframe-boundary / on-prem-distributed / k8s) for the actual infrastructure mapping; this skill only records the intent | JUDG |
| `owner:` | DAG `owner` in `default_args`, or an Astro RBAC/team tag | MECH |
| `permission:` | Airflow/Astro RBAC — rarely 1:1, since AutoSys permission bits (`gx`, `wx`, etc.) are per-job ACLs and Airflow's are role-based | JUDG |
| `std_out_file` / `std_err_file` | Airflow captures task logs natively (UI + configured remote logging); explicit file redirection is usually dropped, not translated | NONE (documented alternative: task logs) |
| `description:` | Docstring / `doc_md` on the DAG or task | MECH |
| `box_terminator: 1` | Marks that the box's success/fail state should propagate as its own terminal signal — matches Airflow's default DAG-level success/failure state; usually a no-op to note, not translate | MECH |
| `date_conditions: 1` + `days_of_week`/`start_times` | See `reference/calendars-and-scheduling.md` | JUDG |
| `condition:` | See `reference/conditions-and-dependencies.md` | JUDG/REDESIGN depending on complexity |
| `%%variable%%` substitution | See `reference/global-variables-and-templating.md` | MECH/JUDG |
| `alarm_if_fail`, `term_run_time`, notifications | See `reference/alerting-and-sla.md` | MECH/JUDG |

## A note on confidence

The job-type table above (`c`, `b`, `f`, `FT`) and the well-known attributes (`condition`, `box_name`, `days_of_week`, `start_times`, `run_calendar`, `exclude_calendar`, `alarm_if_fail`, `term_run_time`, `machine`, `owner`) are stable across recent AutoSys/WA AE releases and safe to rely on. Anything else encountered in a real export — additional job types, newer container/agent-related attributes, version-specific FT syntax — is a "verify before using" item, not a "look it up in this file" item. Say so in the manifest rather than guessing.
