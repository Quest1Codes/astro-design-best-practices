---
name: autosys-reference
description: Authoritative facts about AutoSys Workload Automation 12.0 (CA WA AE / Broadcom) — job types, JIL attributes, condition grammar, states, commands, architecture, security, WCC — every row cited to the Broadcom 12.0 documentation page. Load when any other skill (assessment or migration) needs to check what AutoSys actually does; never guess JIL syntax or semantics. Not a migration or assessment skill itself — it has no phases, no scripts that mutate anything, only facts and their machine-readable twins in `_lib/autosys_jil/registry/`.
---

# AutoSys 12.0 reference

Every fact in this skill traces to a page in the Broadcom *AutoSys Workload Automation 12.0*
documentation (`ca-workload-automation-ae-amp-workload-control-center-validate-source.pdf`,
3,731 pages, generated 2022-08-19) or, for the two generated files, to
`skills/_lib/autosys_jil/registry/*.json` — which was itself extracted from that PDF by
`skills/_lib/autosys_jil/registry/build_registry.py`.

## How to cite

- An AutoSys fact: `[AS p.2549]`.
- A synthesis built from two or more cited facts with no independent source of its own: `{syn: B1+B3}`.
- Something that cannot be verified against the ingested corpus: `PRACTITIONER JUDGMENT — not
  independently verifiable as of 2026-09-17`, and the file's front-matter `confidence` must say
  `practitioner-judgment` or `mixed`.

Never invent JIL syntax. If an attribute or job type isn't in `job_types.json` /
`attributes.json` (queryable via `autosys_jil.registry`) and isn't in this skill's reference
files, grep `research/autosys-12.0/*.txt` before writing anything down as fact. If it's in
neither, say so explicitly and flag it — don't guess a plausible-sounding syntax.

## Version caveat

This corpus is the AutoSys **12.0** documentation. AutoSys 12.1 introduced additional job types
(most relevantly a Kubernetes container job type, which `astro-design-best-practices`'s
`container-native-and-legacy-precision` cluster already assumes exists) that are **not** covered
by this 12.0 PDF and therefore not in `job_types.json`. Any 12.1-specific claim in another skill
must carry `confidence: mixed` and say so explicitly (plan §10 decision #5). If a 12.1 source is
ever ingested, add it as its own corpus subdirectory (`research/autosys-12.1/`) rather than
overwriting the 12.0 one — estates on 12.0 are still real and this skill must keep serving them.

## The registries: machine-readable twins of these pages

| Registry | Generated from | Consumers |
|---|---|---|
| `registry/job_types.json` (64 entries incl. aliases) | `jil-job-definitions.txt` p.2549-2551 + hand overlay `job_type_families.yaml` | `_lib.parser`, `score_estate.py`, `scaffold_dags.py` |
| `registry/attributes.json` (423 entries) | Every `<name> Attribute --` heading p.2400-2854 + hand overlay `attribute_families.yaml` | `_lib.parser` (typed normalization), `inventory_stats.py`, `reference/attributes.md` (generated below) |
| `registry/object_attributes.json` (46 entries) | Same heading pattern, non-job objects (machines, resources, xinsts, monitors) | `_lib.parser` |
| `registry/states.json` (18 entries) | Hand-built from `system-states.txt` p.2912-2928 | `_lib.history`, `reference/job-states-and-events.md` |
| `registry/events.json` (31 entries) | `sendevent -E` reference, `commands.txt` | `_lib.commands` (hidden control-flow detection), `_lib.history` (event archive parsing) |
| `registry/config_params.json` (hand-curated subset) | `administration.txt` p.851-1132; which params matter is itself judgment, see that file's header | `_lib.config`, `astro-target-architecture` |

Regenerate after any overlay edit: `cd skills/_lib && python3 -m autosys_jil.registry.build_registry --corpus ../../research/autosys-12.0`. `--check` exits nonzero if the committed JSON is stale (CI runs this).

## Routing table

| Question | Read |
|---|---|
| What are the AutoSys components and how do they fit together? | `reference/architecture.md` |
| What job types exist, and which family is a given type in? | `reference/job-types.md` |
| What does attribute X do, what job types support it, what's its default? | `reference/attributes.md` |
| How does the `condition:` grammar work? | `reference/conditions-grammar.md` |
| How does scheduling work — calendars, run windows, timezones? | `reference/scheduling-attributes.md` |
| What are the job states, and what events move between them? | `reference/job-states-and-events.md` |
| Machine types, `max_load`/`factor`/`job_load` arithmetic, virtual resources | `reference/machines-load-and-resources.md` |
| `autorep`/`sendevent`/`jil`/other CLI commands — flags, output shape | `reference/commands.md` |
| Native security vs. EEM, permissions, `safex` export format | `reference/security-eem-and-native.md` |
| WCC (Web UI) — what's there, what's exportable | `reference/wcc-and-web-ui.md` |

## Reference files

| File | Content |
|---|---|
| `reference/architecture.md` | Components, instance model, HA, event flow, job lifecycle |
| `reference/job-types.md` | All ~60 canonical job types + aliases, grouped by family; custom job types |
| `reference/attributes.md` | **Generated** by `tools/gen_attributes_md.py` from `attributes.json` — do not hand-edit below the marker |
| `reference/conditions-grammar.md` | Full `condition:` grammar, PDF-example-per-production, case rule, look-back, cross-instance |
| `reference/scheduling-attributes.md` | `date_conditions`, `days_of_week`, `start_times`/`start_mins`, `run_window`, calendars, timezone |
| `reference/job-states-and-events.md` | Every state with terminal flag, transition table, `ON_ICE` vs `ON_HOLD` vs `ON_NOEXEC` |
| `reference/machines-load-and-resources.md` | Machine types, load arithmetic, virtual resources, `QUE_WAIT`/`PEND_MACH`/`RESWAIT` |
| `reference/commands.md` | `autorep`, `sendevent`, `jil`, `autocal_asc`, `chase`, others — the export recipe discovery uses |
| `reference/security-eem-and-native.md` | Native vs. EEM, permission bits, `safex`, encryption |
| `reference/wcc-and-web-ui.md` | WCC applications, monitors/reports, AEWS surface |
