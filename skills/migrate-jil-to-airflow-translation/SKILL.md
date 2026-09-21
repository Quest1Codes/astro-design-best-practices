---
name: migrate-jil-to-airflow-translation
description: Core AutoSys JIL to Airflow 3 (Astro) job/box translation. Use once the assess-* family has produced a scored, waved estate_manifest.json — this skill scaffolds DAGs for MECH units, translates condition/calendar strings with recorded equivalence rows, and runs the quality gates. Does not handle topology (see migrate-topology-*), platform buildout (migrate-astro-platform-buildout), or cutover (migrate-parallel-run-and-cutover) — this skill's scope is job/box semantics only.
---

# JIL → Airflow 3 translation

Translate AutoSys jobs and boxes into Airflow 3 DAGs. This is the core of the migration family:
job-type mapping, condition-string translation, calendar-to-Timetable translation, and the
quality gate that proves a scaffolded DAG actually parses and runs. Topology (where things run),
platform buildout (Workspaces/Deployments/RBAC/secrets), and cutover mechanics are separate
skills — this one is job/box semantics only.

## Requirements

- `estate_manifest.json` with `scores{}` **and** `waves[]` populated (the whole `assess-*`
  family has run). **This skill refuses to scaffold anything without a scored, waved manifest** —
  translating an unscored job means translating without knowing its disposition, which is
  exactly the "don't stub, don't guess" failure mode the hard rules below forbid.
  - **Exception for a spike/demo**: to try this skill against a small hand-picked JIL file
    without running the full assessment pipeline, produce a minimal manifest by hand:
    `build_estate_manifest.py --instance X=file.jil --out m.json`, then
    `score_estate.py --manifest m.json` (scores every job MECH/JUDG/etc. from the rules alone,
    with no history/schedule context — fine for a spike, not for a real engagement).
- Target **Astro Runtime 3.3+** (Airflow 3.3+).
- `astro` CLI for the target project.

## Hard rules

1. **Never stub.** A translated job/box either works through the quality gate or is deferred
   with a written reason. Fake-success bodies and workaround code with long justifying comments
   are failures.
2. **No silent omissions.** Every unit in the wave being translated ends `complete` or
   `deferred (reason)` — `_lib.autosys_jil.status summary --workflow translation` exits nonzero
   otherwise; run it before claiming a wave done.
3. **Equivalence rows for every condition string.** Each `condition:` attribute gets a report
   row: source expression, target implementation, delta in one sentence — even when the delta is
   "none expected." AutoSys's `notrunning()` and OR-combined conditions have no single stock
   Airflow equivalent; the sin is not the delta, it is the undocumented delta.
4. **Fix classes, not instances.** When a translation pattern fails the quality gate, fix the
   pattern (and record it in `reference/troubleshooting.md`), then re-apply — never hand-patch
   one job.
5. **Do not invent JIL syntax.** Check `job_types.json`/`attributes.json`
   (`autosys_jil.registry`), then `autosys-reference`'s reference files, then the PDF corpus.
   Never assume from a version you haven't checked.
6. **Never scaffold a REDESIGN/NONE unit as if it were MECH/JUDG.** `scaffold_dags.py` refuses
   outright — these need a human-designed approach, not a generated skeleton with `# TODO`s
   papering over a fundamentally different shape.

## Workflow

### Phase 1: Load the assessment manifest

Confirm `estate_manifest.json` has `scores{}` and `waves[]` (see Requirements above). Pick the
wave to translate — normally the pilot wave first (`assess-migration-complexity-scoring/reference/wave-planning.md`).

### Phase 2: Scaffold MECH units

```
python3 scripts/scaffold_dags.py --manifest estate_manifest.json --wave 0 --out dags/ --include include/
```

Emits one DAG file per top-level box (or bare job) in the wave, using Airflow 3.3 idioms
(`@dag`, `@task.bash`, TaskGroups, Assets), with `# TODO(JUDG:<rule-id>)` markers at every
judgment point a JUDG-scored child needs, `params`/`tags`/`doc_md` carrying traceability back to
the AutoSys job (`autosys_job_name`/`instance`/`box`), and a `traceability.json` mapping
`job -> dag_id.task_id`. Refuses REDESIGN/NONE units outright (lists them instead of a skeleton).

### Phase 2.5: Translate conditions and calendars

```
python3 scripts/translate_conditions.py --manifest estate_manifest.json --out equivalence_rows.json --md equivalence_rows.md
python3 scripts/translate_calendars.py --manifest estate_manifest.json --out include/calendars/ --md calendar_decisions.md
```

Each produces a first-draft recommendation per condition/schedule with a confidence and
`needs_decision` flag — the human accepts or edits each row
(`_lib.autosys_jil.status advance <unit> --workflow translation ...`), per
`reference/conditions-and-dependencies.md` and `reference/calendars-and-scheduling.md`.

### Phase 3: Trial

Migrate 2-3 representative units end-to-end before fanning out to the rest of the wave: one MECH
command-job box, one box with a nontrivial condition string, one calendar-driven box (the same
three-kind rule `propose_waves.py`'s pilot pick already used). What the trial teaches goes into
`reference/troubleshooting.md` before scaling.

### Phase 4: Quality gate

```
python3 scripts/dag_quality_gate.py --project-dir . --traceability traceability.json
```

Runs `astro dev parse`, `ruff check`, and `pytest tests/dags/` (DAG-integrity tests shipped in
`_lib/fixtures/astro_project/tests/dags/test_dag_integrity.py`: no import errors,
owner/tags/`doc_md` present, no top-level `Variable.get`/DB calls, `catchup` explicit, `retries`
set, every task traceable via `traceability.json`). See `reference/validation.md` for gates
beyond what this script automates (output parity, safe re-run).

### Phase 5: Advance and repeat

Per unit: `_lib.autosys_jil.status --manifest estate_manifest.json advance <unit> --workflow
translation --status <state>`. States: `pending → translate → fix-import → fix-lint → fix-tests
→ verify-parity → complete | deferred(reason)`.

## Reference routing

| Question | Read |
|---|---|
| Job-type default target, disposition, worked example | `reference/job-types/*.md` (11 family files) |
| Condition-string translation, including OR/lookback/cross-instance | `reference/conditions-and-dependencies.md` |
| Calendar/schedule translation, cron vs. Timetable | `reference/calendars-and-scheduling.md` |
| `%%variable%%` and global-variable translation | `reference/global-variables-and-templating.md` |
| Alerting/SLA translation | `reference/alerting-and-sla.md` |
| AutoSys state → Airflow TaskInstance state | `reference/job-states-to-task-states.md` |
| The validation gates | `reference/validation.md` |
| Known failure classes | `reference/troubleshooting.md` |

## Scripts

| Script | Purpose |
|---|---|
| `scripts/scaffold_dags.py` | Emit DAG skeletons for a wave's MECH/JUDG units; `_emitters/<family>.py` per job-type family |
| `scripts/translate_conditions.py` | Condition AST → recommended implementation + equivalence row |
| `scripts/translate_calendars.py` | Calendar → cron (if provably equivalent) or a Timetable data file |
| `scripts/parity_check.py` | AutoSys run history vs. Airflow run history, joined on `traceability.json` |
| `scripts/dag_quality_gate.py` | `astro dev parse` + `ruff` + DAG-integrity `pytest` |
