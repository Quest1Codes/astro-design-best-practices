---
topic: otto-assisted-translation-workflow
family: knowledge
skill: astro-design-best-practices
verified_against:
  airflow: "3.3.1"
  astro_runtime: "3.3-2"
last_verified: 2026-09-17
confidence: mixed
signals:
  - factory_candidate
---

# Otto-Assisted Translation Workflow

> PRACTITIONER JUDGMENT: Astronomer's Otto is a real AI-assisted migration/operations agent,
> confirmed via astronomer-docs to include "migrate workflows from legacy orchestration systems to
> Airflow on Astro" as a stated capability. **Its current documented status is Labs (early-access)**,
> not GA — factor that into reliability and support expectations before depending on it for a
> production migration timeline. Otto's exact ingestion format, UI flow, and built-in stop
> conditions remain **NEEDS_EXEC_CHECK** against current Astronomer documentation before relying on
> them operationally. What *is* solid, and independently verifiable from this project's own code,
> is the JIL-side half of the workflow — what this estate can hand Otto, and how its output
> reconciles against `traceability.json`.

## What this topic covers

Where an AI-assisted translation tool (Otto, or an equivalent) fits into this project's own
migration pipeline, as a third option alongside this skill's own `scaffold_dags.py` (rule-based,
deterministic, MECH/JUDG-only) and fully manual hand translation (REDESIGN/NONE units). See
`orbiter-vs-otto-vs-hand-translation.md` for the decision table between all three.

## What Otto needs as input

Whatever the exact ingestion mechanism, an AI-assisted translator needs the same three things any
translation approach needs, all of which this project's `estate_manifest.json` already carries:

1. **The source definition** — the JIL block for the unit, already parsed and normalized in
   `manifest.instances[*].jobs`/`boxes` (see `_lib.autosys_jil.parser`).
2. **The conventions to target** — this project's own `manifest.brownfield.conventions` (naming,
   tagging, `default_args` sourcing) rather than whatever generic conventions a general-purpose
   tool would default to; feeding these explicitly is what keeps AI-assisted output consistent
   with the rest of the estate's hand- and rule-translated units.
3. **The disposition/scope boundary** — only `MECH`/`JUDG` units with disposition already recorded
   in `manifest.scores` should go through automated translation at all; see "Where it stops" below.

## Review and traceability workflow

Regardless of translation method, this project's discipline (established in
`migrate-jil-to-airflow-translation`) doesn't change: every unit that goes through Otto still
needs an entry in `traceability.json` mapping `INST:job_name` → the resulting `dag_id.task_id`,
and still needs to pass `dag_quality_gate.py` before being considered translated. An AI-assisted
tool's output is a **draft**, not a shipped translation — the same Human-in-the-loop review this
project already requires of `scaffold_dags.py`'s `# TODO(JUDG:<rule-id>)` markers applies equally
to whatever Otto emits, and arguably more so, since a rule-based emitter's failure modes are
enumerable in a way an AI-assisted tool's are not.

## Where it stops

Consistent with this project's own `scaffold_dags.py` refusal behavior: units scored
`REDESIGN` or `NONE` should not be routed to any automated translator, AI-assisted or rule-based
— `REDESIGN` units need a human to design the actual replacement pattern first (the delta from
AutoSys behavior has to be named, per `assess-assessment-report`'s Risk-section discipline), and
`NONE` units by definition have no Astro-side equivalent to translate into. Feed
automated translation exactly the units `score_estate.py` marked `MECH` or `JUDG` with a resolved
`manifest.decisions[]` entry.

## Mapping from the assessment's `tooling_hint`

`assess-migration-complexity-scoring`'s scoring output can carry a `tooling_hint` per unit (see
`assess-migration-complexity-scoring/reference/translation-tooling-strategy.md`). Where that hint
already recommends AI-assisted translation for a given unit (typically: `MECH` units with
straightforward command-substitution shape and no condition-graph complexity), this is the
workflow it's recommending — not a separate, unrelated tool choice.

## Sources

- [P1] Project-internal — `skills/assess-migration-complexity-scoring/reference/translation-tooling-strategy.md` (tooling_hint field and its scoring inputs)
- [P2] Project-internal — `skills/migrate-jil-to-airflow-translation/scripts/scaffold_dags.py` (refusal behavior for REDESIGN/NONE, `traceability.json` shape)
- [B1] Astronomer Docs — Otto overview and Labs/early-access status: https://www.astronomer.io/docs/astro/otto/otto-overview and https://www.astronomer.io/docs/astro/feature-previews (tier 1, confirmed via astronomer-docs verification)
- NEEDS_EXEC_CHECK — Otto's actual ingestion format, UI flow, and any built-in stop conditions; not independently verified this session.
