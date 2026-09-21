---
name: autosys-to-astronomer
description: Router for any AutoSys Workload Automation (CA WA AE, JIL) to Apache Airflow 3 / Astro request. Use when the user mentions migrating, converting, assessing, or porting AutoSys jobs/boxes/JIL to Airflow or Astro, wants an estate assessed before committing to a migration, or asks what a JIL construct maps to in Airflow. Always load this skill FIRST for any AutoSys-to-Astronomer request — it triages assessment-vs-migration, routes to the right assess-*/migrate-* skill(s) and topology companion(s), and points at knowledge skills. Do not load a family skill directly without going through this triage first unless you already know exactly which one you need.
---

# AutoSys → Astronomer: start here

This skill decides **which family** of skills a request needs, then gets out of the way. It has
no scripts of its own and does not translate anything itself.

## Phase 0 — Which engagement?

Two questions, in order:

**1. Is the deliverable a document or a running platform?**

| Deliverable | Family |
|---|---|
| A written assessment / migration-readiness report, a complexity/effort estimate, a target-architecture recommendation — nothing gets written to a target Astro project | **Assessment** — load `assess-estate-discovery` first |
| Actual DAGs, an actual Astro platform buildout, an actual cutover — code and infrastructure get written | **Migration** — see question 2 |

**2. Does `estate_manifest.json` already exist, with `scores{}` and `waves[]` populated?**

- **No** → the estate hasn't been assessed yet. Load the assessment family first
  (`assess-estate-discovery` → ... → `assess-assessment-report`) even if the end goal is
  migration — `migrate-jil-to-airflow-translation` refuses to run without a scored, waved
  manifest (see that skill's Phase 1). The one exception is a deliberately small spike/demo: that
  skill's `SKILL.md` explains how to produce a minimal manifest by hand for that case only.
- **Yes** → go straight to `migrate-jil-to-airflow-translation`.

## Phase 0.5 — Topology companions

Independent of assessment-vs-migration, check the manifest (or, pre-assessment, a quick look at
the JIL export and machine list) for these signals. An estate can match more than one row — load
every companion that matches, alongside whichever family skill from Phase 0 applies.

| Signal | Load companion |
|---|---|
| Any job with `job_type` in `{ZOS, ZOSM, ZOSDST}`, or `unknowns.job_types`/`command_analysis` hits on MFT/Connect:Direct/NDM/dataset-naming patterns (`Instance.unknowns`, `commands.analyze()` hosts/paths) | `migrate-topology-mainframe-boundary` |
| `Machine.opsys`/`command_summary.os_hint` shows a large distributed Unix/Windows agent fleet (dozens to thousands of machines), not containerized | `migrate-topology-onprem-distributed` |
| `manifest.brownfield` or discovery notes show the AutoSys Application Server/agents already running as containers or on Kubernetes | `migrate-topology-k8s` |

Before a manifest exists, these signals aren't computed yet — use the same heuristics the
companion `SKILL.md`s themselves describe (job-type presence, machine-name patterns, "does this
estate already run in a container") as a rough pre-assessment triage, and re-confirm once
`estate_manifest.json` exists.

## Phase 0.7 — Knowledge

- Load `autosys-reference` whenever a question about what AutoSys actually does comes up —
  job types, attributes, condition grammar, states, commands, machine/security facts. **Never
  guess JIL syntax; check the registry or that skill's reference files.**
- Load `astro-design-best-practices` topics **selectively**, via
  `assess-astro-target-architecture/reference/kb-routing.md` (signal → topic list covering 20 of
  the KB's ~26-signal vocabulary; not all 137 topics at once). For a signal with no routed topic,
  or a question the routing table doesn't cover, fall back to the KB's own cluster index in its
  `SKILL.md`.

## Hard rules (apply across every family and companion)

1. **Never stub.** A translated job/box either works through validation or is deferred with a
   written reason.
2. **No silent omissions.** Every unit in every manifest ends in a terminal state or
   `deferred (reason)` — `_lib.autosys_jil.status summary --workflow <name>` must exit 0 before
   any family calls its work done.
3. **Equivalence rows for every condition string** that gets translated. AutoSys's `n()`
   (not-running) and OR-combined conditions have no single stock Airflow equivalent — the sin is
   not the delta, it's the undocumented delta.
4. **Fix classes, not instances.** When a translation pattern fails validation, fix the pattern
   (record it in the relevant `troubleshooting.md`), then re-apply — never hand-patch one job.
5. **Do not invent JIL syntax.** Check `job_types.json`/`attributes.json`
   (`autosys_jil.registry`), then `autosys-reference`'s reference files, then the PDF corpus
   (`research/autosys-12.0/*.txt`, grep for `[p.N]`). If it's in none of those, say so explicitly
   and flag it — never assume from a version you haven't checked.
6. **Assessment scripts never touch live systems.** Every assessment script reads files the
   platform team already exported; nothing in the `assess-*` family makes a live AutoSys or Astro
   call. Anything that would query a live system is a discovery *instruction* for a human, not a
   script action.
7. **Every number in a report traces to a manifest field.** If a reviewer asks "where did this
   come from," the answer is a JSON path and, for an AutoSys fact, a PDF page — never "it seemed
   about right."

## Glossary

| Term | Meaning |
|---|---|
| JIL | Job Information Language — the text DSL used to define AutoSys jobs/boxes/machines/calendars |
| Box job | A container job; other jobs join it via their own `box_name` attribute (membership is declared bottom-up, reconstructed by `_lib.boxes`) |
| Condition | A boolean expression over other jobs' statuses/exit codes/global variables gating when a job is eligible to run (`_lib.conditions`) |
| Calendar | A named, reusable list of eligible/excluded dates managed via `autocal_asc`, referenced by `run_calendar`/`exclude_calendar` |
| Agent | The AutoSys process installed on a target machine that actually executes jobs and reports status back |
| Web UI / WCC | The browser GUI for defining, monitoring, and operating AutoSys jobs (WCC is the pre-12.0 product name; both terms appear in real estates) |
| `autorep` | CLI for reporting job/box/machine/variable status |
| `sendevent` | CLI for sending control events (start, force-start, hold/ice, manual status override) |
| ON_HOLD / ON_ICE | Two different "don't run this" states with **different** effects on dependents — see `autosys-reference/reference/job-states-and-events.md` before using either as a cutover primitive |
| Estate manifest | `estate_manifest.json` — the single typed artifact every assess-*/migrate-* script reads and enriches (`_lib.autosys_jil.manifest`) |
| Disposition | MECH / JUDG / REDESIGN / NONE (+ DECOMMISSION) — how mechanically a job/box translates; see `assess-migration-complexity-scoring/reference/disposition-definitions.md` |

## What can and cannot break

- **Cannot break during assessment or planning**: nothing is written back to AutoSys or to a
  target Astro project; every `assess-*` script and `migrate-jil-to-airflow-translation`'s
  planning phases are read-only against the estate manifest.
- **Can break once scaffolding starts**: the target Astro project is being written to (new DAG
  files, `include/` data). This does not touch AutoSys.
- **Can break starting cutover** (`migrate-parallel-run-and-cutover`): AutoSys job state
  (`ON_ICE`) and Airflow DAG pause state change. This is the only phase with production blast
  radius — always confirm rollback works before flipping the first box, one box/machine-group at
  a time, never the whole estate at once.

## First-session checklist

1. Triage per Phase 0/0.5 above.
2. `pip install -e skills/_lib` (once, per environment) so every script's `from autosys_jil import
   ...` resolves.
3. If starting from nothing: `assess-estate-discovery`'s `discovery_checklist.py` to see what
   artifacts to request.
4. Once artifacts land: `assess-estate-inventory`'s `build_estate_manifest.py`, then
   `inventory_stats.py --top` for a first look at the estate's shape.
