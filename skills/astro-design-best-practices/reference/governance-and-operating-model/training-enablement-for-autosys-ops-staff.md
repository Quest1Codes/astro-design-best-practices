# Training and Enablement Design for AutoSys Ops Staff

AutoSys operators and admins have deep expertise in JIL, box job semantics, calendar scheduling, and event rules — but almost no exposure to Python, Git, or Kubernetes. A training program that ignores this starting point and jumps straight to "Airflow concepts" will lose people. The curriculum must explicitly map the known mental model to the new one.

## Mental Model Translation First

Before any Airflow syntax, the curriculum must resolve the question every AutoSys operator is silently asking: *"Where did MY thing go?"*

{syn: JIL concepts → Airflow equivalents}

| AutoSys Concept | Airflow Equivalent | Key Difference |
|---|---|---|
| **Box job** | DAG (or `TaskGroup`) | DAG is code in a Python file, not a UI form |
| **Job (command type)** | Operator (BashOperator, PythonOperator, etc.) | Many specialized operators replace command strings |
| **`condition:` / `box_success`** | `trigger_rule` | More flexible; can handle ANY_FAILED, ONE_SUCCESS, etc. |
| **Calendar / time condition** | `schedule` parameter (cron or timetable) | Cron syntax is the same; advanced timetables offer more |
| **Event-based start (file trigger)** | `FileSensor`, `S3KeySensor` | Event-driven, not polling the same database |
| **`max_run_alarm`** | `execution_timeout` + SLA callback | Declarative timeout per task |
| **AutoSys GUI (WCCOE)** | Airflow UI (web browser) | No client install; web-based |
| **JIL file** | Python DAG file | Requires Python basics; versioned in Git |

## Training Track by Role

| Audience | Core Topics | Hands-On Exercises |
|---|---|---|
| **Ops / Monitoring staff** | Airflow UI navigation, task states, log inspection, clearing/re-running tasks | Monitor a failing pipeline; diagnose and clear a zombie task |
| **JIL authors / job builders** | Python basics, DAG authoring, TaskGroups, trigger_rules, Sensors | Convert a 10-job AutoSys box to a DAG |
| **AutoSys admins** | Astro deployment management, RBAC, resource sizing, Terraform IaC | Create and manage a Workspace; right-size a Deployment |

## Program Structure

1. **Week 1–2**: Conceptual mapping + Airflow UI familiarization. No coding required. Goal: every operator can navigate and monitor pipelines independently.
2. **Week 3–4**: Python fundamentals + first DAG authoring (BashOperator-only to start). Goal: every former JIL author writes and deploys a simple DAG.
3. **Week 5–6**: CI/CD basics (Git, PRs, `astro dev start`), testing (`astro dev parse`, `dag.test()`), and Secrets management. Goal: full self-serve DAG development lifecycle.
4. **Ongoing**: Quarterly deep-dives (Deferrable Operators, dynamic DAG mapping, performance optimization) as the team matures.

## Key Principle: Pilot Before Broad Rollout

Run a **pilot migration of 50–100 non-critical jobs** with the enablement program before broad rollout [B1]. This validates the training content against real-world complexity and builds champion engineers who become internal mentors for the broader ops staff.

## Sources

[B1] Astronomer migration guidance & enterprise migration community — Training curriculum design, JIL-to-DAG mental model mapping, and pilot program structure (accessed 2026-08-11)
