# Zombie-Task Detection and Handling

AutoSys's `chase` utility periodically reconciles what the Event Server *thinks* is running against what's actually alive on the target machine — a job whose process died without reporting back raises `PROCESS_MIA`. Airflow has a structurally similar reconciliation problem with a different name and mechanism: a **zombie task**.

## Core mechanics

- Airflow defines two distinct failure-detection concepts, not one: a **zombie task** has a heartbeat *absence* and a `running` status in the metadata DB — the worker process died (OOM-killed, node rebooted, network partition) without ever updating its own state [F1]. An **undead task** is the inverse: the process is alive and heartbeating, but the DB doesn't know it should be running (typically because someone manually cleared/deleted the task-instance row) — the task detects this mismatch itself during its own heartbeat routine and self-terminates [F1].
- Zombie detection is scheduler-side, heartbeat-timeout-driven: the scheduler periodically checks for task instances whose last heartbeat is older than a threshold, and kills+reschedules them [F1][F2].
- {syn: F2} On Astro, the relevant threshold is `AIRFLOW__SCHEDULER__TASK_INSTANCE_HEARTBEAT_TIMEOUT` (paired with `AIRFLOW__SCHEDULER__SCHEDULER_ZOMBIE_TASK_THRESHOLD`) — both default to **60 seconds, except on the Astro executor, where the default is 120 seconds** [F2]. This is an Astro-platform-set default, not the generic upstream Airflow default — don't assume the OSS default applies unmodified on Astro.
- Zombie kills are observable two ways: (1) a dedicated metric — `airflow_zombies_killed` on Airflow 2, **replaced by `airflow_task_instances_without_heartbeats_killed` on Airflow 3+** [F3]; (2) as of Airflow 2.8 (scheduler) / 2.10 (executor), zombie-detection information is forwarded into the *task's own logs* when a component error causes the task to fail, so a task with no logs but a "no heartbeat" event in its Event Log is a strong OOM/zombie signal even without checking scheduler logs directly [F4].
- See `reference/ha-and-dr/chaos-and-failure-testing-strategy.md` in this skill for testing this behavior directly (`kubectl delete pod <worker-pod>` and confirming the task is correctly marked `failed` and rescheduled) — that file already covers the chaos-testing angle; this file covers the underlying detection mechanism and Astro-specific defaults it's testing against.

## {syn: F1,F2} What this replaces from AutoSys

`chase`'s `PROCESS_MIA` reconciliation and Airflow's zombie detection are the same shape of problem — periodic, heartbeat-based reconciliation between "what the state store believes" and "what's actually alive" — solved by structurally similar mechanisms (a polling reconciler on the orchestration side, not the job itself, detecting silence and declaring failure). The concrete differences worth calling out when migrating a team used to `chase`:

| AutoSys `chase` model | Airflow equivalent | What's different |
|---|---|---|
| `PROCESS_MIA` is a single named failure state surfaced directly in `autorep` / the AutoSys UI | Zombie detection results in a normal task `failed` state plus (if retries remain) automatic rescheduling — there's no separate "MIA" status to query for; you infer it from the failure reason / Event Log entry [F1][F4]. | Airflow doesn't expose zombie-ness as its own durable state the way AutoSys does — it's a transient detection event, not a queryable status. |
| `chase` interval is a single estate-wide polling cadence | Zombie/heartbeat timeouts are Airflow config (`scheduler_zombie_task_threshold`, `task_instance_heartbeat_timeout`), and on Astro specifically vary by executor (60s standard, 120s on Astro executor) [F2] | The threshold is executor-dependent on Astro, not a single estate-wide constant the way `chase`'s interval was. |

## Sources

- [F1] Apache Airflow docs — Tasks, "Zombie & Undead Tasks" (definitions, detection mechanism, self-termination for undead tasks): https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/tasks.html#zombie-undead-tasks (tier 2)
- [F2] Astronomer Docs — Platform variables, `AIRFLOW__SCHEDULER__SCHEDULER_ZOMBIE_TASK_THRESHOLD` and `AIRFLOW__SCHEDULER__TASK_INSTANCE_HEARTBEAT_TIMEOUT` (default 60, 120 on Astro executor): https://www.astronomer.io/docs/astro/platform-variables#default-changed (tier 1)
- [F3] Astronomer Docs — Export metrics reference, counters (`airflow_zombies_killed` replaced by `airflow_task_instances_without_heartbeats_killed` on Airflow 3+): https://www.astronomer.io/docs/astro/export-metrics-reference#counters (tier 1)
- [F4] Astronomer Docs — Logging, "Containerized Airflow environment" (scheduler 2.8+/executor 2.10+ forward zombie info to task logs; `AIRFLOW__LOGGING__ENABLE_TASK_CONTEXT_LOGGER` to disable) and Best practices, "Logging and Out of Memory on Tasks" (OOM → no logs + missing-heartbeat Event Log entry signal): https://www.astronomer.io/docs/learn/logging#containerized-airflow-environment and https://www.astronomer.io/docs/astro/best-practices/airflow-edge-cases#logging-and-out-of-memory-on-tasks (tier 1)
- [P1] Task-tracker description (AutoSys `chase`/`PROCESS_MIA` background) — this skill's own `tasks/README.md`, topic 023; AutoSys-side mechanics not independently verified via the Astronomer docs MCP (out of scope), taken as given background per the topic brief.
