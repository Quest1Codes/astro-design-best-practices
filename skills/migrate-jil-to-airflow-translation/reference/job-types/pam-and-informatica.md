---
topic: pam-and-informatica
family: migration
skill: migrate-jil-to-airflow-translation
verified_against:
  airflow: "3.3.1"
  astro_runtime: "3.3-2"
  autosys: "12.0"
  autosys_doc_pages: [2551]
last_verified: 2026-09-17
confidence: mixed
signals: []
---

# Process Automation (PAM) and Informatica: PAPROC, PAREQ, INFORMATICA

| Code | Default target | Disposition |
|---|---|---|
| `PAPROC` (Process Automation Process Execution) [AS p.2551] | `HttpOperator` to the CA PAM REST API | JUDG |
| `PAREQ` (Process Automation Start Request Form) [AS p.2551] | Needs a human-facing request-form equivalent — a HITL operator, not a simple `HttpOperator` call, since a request form implies manual input | JUDG (borders REDESIGN if the form logic is complex) |
| `INFORMATICA` [AS p.2551] | `@task.bash pmcmd startworkflow ...`, or `HttpOperator` if targeting Informatica's REST API instead | JUDG |

## `PAREQ` and human-in-the-loop

`PAREQ` shares the same fundamental shape as `WAIT_REPLY` states
(`reference/job-states-to-task-states.md`) — a workflow step expecting manual input. Check
whether the "request form" is genuinely interactive (needs a human-in-the-loop operator or an
external approval-system integration) before assuming a bare `HttpOperator` call captures its
actual behavior.

## CA PAM / Informatica platform continuity

If CA PAM itself is being retired as part of this migration (not just the AutoSys orchestration
around it), `PAPROC`/`PAREQ` become REDESIGN regardless of the table above — the target isn't a
REST call to a system that still exists, it's a genuine re-implementation. Confirm PAM's own
fate with the customer before finalizing this family's disposition.

## What the scaffolder emits vs. leaves as TODO

Emits an `HttpOperator`/`@task.bash` skeleton for `PAPROC`/`INFORMATICA` with the endpoint/command
parameterized; leaves `# TODO(JUDG:hitl-or-api)` on every `PAREQ` job for the
manual-vs-automated-approval decision.
