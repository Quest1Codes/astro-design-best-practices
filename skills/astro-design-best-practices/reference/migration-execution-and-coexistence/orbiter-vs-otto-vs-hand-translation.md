---
topic: orbiter-vs-otto-vs-hand-translation
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

# Orbiter vs. Otto vs. Hand Translation

> PRACTITIONER JUDGMENT: Astronomer's Orbiter is a real, open-source, rule-based workflow
> converter (source-format parser → Airflow DAG code, extensible per source system) that
> Astronomer has published; Otto is Astronomer's separately marketed AI-assisted migration agent
> (see `otto-assisted-translation-workflow.md`). Neither has a documented, out-of-the-box JIL/AutoSys
> plugin as of this session's training-data knowledge, and this claim was not re-verified against
> live Astronomer documentation this session — confirm current plugin/source-format support before
> committing to either tool for a real engagement. This project's own `scaffold_dags.py` (rule-based,
> JIL-native) is the one option in this table that is independently verified, since it was written
> and tested against the real 297-job fixture estate this session.

## The three options for a given unit

| Option | Mechanism | JIL-native? |
|---|---|---|
| **This project's `scaffold_dags.py`** | Rule-based, per-job-family emitters (`_emitters/<family>.py`) reading the parsed `estate_manifest.json` directly | Yes — built for this estate's JIL shape specifically |
| **Orbiter** | Rule-based, general-purpose workflow-to-DAG converter with a source-format plugin model | No known out-of-the-box JIL plugin (NEEDS_EXEC_CHECK) — would require writing a custom Orbiter source-format plugin from JIL, which is itself a nontrivial undertaking given `_lib.autosys_jil.parser`'s own AST complexity |
| **Otto** | AI-assisted translation, drafts DAG code from source input + conventions | No documented stop-condition guarantees as strict as this project's own REDESIGN/NONE refusal (see `otto-assisted-translation-workflow.md`) |
| **Hand translation** | A human writes the DAG directly | Always available; the only option for REDESIGN units by definition |

## Decision table

| Signal | Recommendation |
|---|---|
| Unit is `MECH`, high `factory_candidate` volume (many structurally-similar boxes) | `scaffold_dags.py` — already JIL-native, deterministic, and this project's own emitters are the closest fit to the estate's actual JIL shapes; no translation-tool licensing/access question to resolve |
| Unit is `JUDG` with a resolved `manifest.decisions[]` entry, moderate volume, low condition-graph complexity | Either `scaffold_dags.py` (if the family already has an emitter) or Otto as a drafting aid, always followed by the same `dag_quality_gate.py`/human-review pass either way |
| Unit is `JUDG`, condition-graph complexity is high (deep boxes, `or_conditions`, cross-instance edges) | Hand translation — this is exactly the case where an automated translator's draft needs the most rework, and the time saved by automation is smallest relative to review cost |
| Unit is `REDESIGN` or `NONE` | Hand translation only — see `otto-assisted-translation-workflow.md`'s "Where it stops" section; no automated tool should be pointed at these |
| Orbiter or Otto licensing/access is not already provisioned for this engagement | Default to `scaffold_dags.py` plus hand translation for the remainder — don't add a new tool-procurement dependency to a migration's critical path unless the estate's scale genuinely justifies it (see `factory_candidate` volume threshold in `assess-migration-complexity-scoring`) |

## Why `scaffold_dags.py` is the default, not a third-place option

Unlike Orbiter or Otto, this project's own emitter is verified against this specific estate's real
JIL corpus, requires no separate tool licensing, and its failure mode is enumerable: every
judgment point it can't resolve gets an explicit `# TODO(JUDG:<rule-id>)` marker rather than a
silently-wrong translation. Reach for Orbiter or Otto only where `scaffold_dags.py` doesn't yet
have an emitter for a job family and writing one isn't worth it for the volume involved — the
question in `assess-migration-complexity-scoring`'s `tooling_hint` field is really asking exactly
this.

## Sources

- [P1] Project-internal — `skills/migrate-jil-to-airflow-translation/scripts/scaffold_dags.py` and `_emitters/` (per-family emitter architecture, verified this session against the 297-job fixture estate)
- [P2] Project-internal — `skills/astro-design-best-practices/reference/migration-execution-and-coexistence/otto-assisted-translation-workflow.md`
- NEEDS_EXEC_CHECK — current Orbiter source-format plugin availability for JIL/AutoSys; current Otto licensing/access model. Not independently verified this session.
