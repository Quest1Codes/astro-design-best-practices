---
topic: orbiter-vs-otto-vs-hand-translation
family: knowledge
skill: astro-design-best-practices
verified_against:
  airflow: "3.3.1"
  astro_runtime: "3.3-2"
last_verified: 2026-10-22
confidence: mixed
signals:
  - factory_candidate
---

# Orbiter vs. Otto vs. Hand Translation

> **Corrected 2026-10-22.** An earlier version said neither Orbiter nor Otto had AutoSys/JIL
> support. That was wrong. Checked against live sources:
> - **Orbiter**: Astronomer's open-source rule-based converter has a public AutoSys ruleset
>   (`orbiter_translations/autosys/jil_demo.py`), but it is explicitly a **demo**. It translates only
>   `CMD` jobs (to `BashOperator`), with no BOX, conditions, calendars or dependencies, and it directs
>   users to Astronomer for "access to our full translation" [B1]. The community-translations repo
>   was archived (read-only) on 2026-03-16 [B1].
> - **Otto**: Astronomer markets Otto's migration feature for AutoSys explicitly ("it takes your
>   Control-M XML or AutoSys JIL and produces Python that runs in Airflow") [B2]. Otto is a Labs /
>   early-access feature, reached via `astro otto` or the Astro IDE [B3].
>
> The scope of Astronomer's full (non-demo) Orbiter AutoSys ruleset, and Otto's actual JIL coverage
> and stop conditions, are not publicly documented: **NEEDS_EXEC_CHECK** with Astronomer before
> relying on either for a real engagement.

## The three options for a given unit

| Option | Mechanism | JIL-native? |
|---|---|---|
| **This project's `scaffold_dags.py`** | Rule-based, per-job-family emitters (`_emitters/<family>.py`) reading the parsed `estate_manifest.json` directly | Yes — built for this estate's JIL shape specifically |
| **Orbiter** | Rule-based, general-purpose workflow-to-DAG converter with per-source translation rulesets | Partly. The public AutoSys ruleset is a `CMD`-only demo [B1]; a full ruleset is available from Astronomer on request, with scope not publicly documented (NEEDS_EXEC_CHECK) |
| **Otto** | AI-assisted translation, drafts DAG code from source input + conventions | Yes, marketed for AutoSys JIL input [B2], but Labs/early access [B3], with no documented stop-condition guarantees as strict as this project's own REDESIGN/NONE refusal (see `otto-assisted-translation-workflow.md`) |
| **Hand translation** | A human writes the DAG directly | Always available; the only option for REDESIGN units by definition |

## Decision table

| Signal | Recommendation |
|---|---|
| Unit is `MECH`, high `factory_candidate` volume (many structurally-similar boxes) | `scaffold_dags.py` — already JIL-native, deterministic, and this project's own emitters are the closest fit to the estate's actual JIL shapes; no translation-tool licensing/access question to resolve |
| Unit is `JUDG` with a resolved `manifest.decisions[]` entry, moderate volume, low condition-graph complexity | Either `scaffold_dags.py` (if the family already has an emitter) or Otto as a drafting aid, always followed by the same `dag_quality_gate.py`/human-review pass either way |
| Unit is `JUDG`, condition-graph complexity is high (deep boxes, `or_conditions`, cross-instance edges) | Hand translation — this is exactly the case where an automated translator's draft needs the most rework, and the time saved by automation is smallest relative to review cost |
| Unit is `REDESIGN` or `NONE` | Hand translation only — see `otto-assisted-translation-workflow.md`'s "Where it stops" section; no automated tool should be pointed at these |
| Engagement is an Astronomer partner/customer engagement where Astronomer's full Orbiter AutoSys ruleset or Otto migration access is available | Evaluate it on a pilot slice of `MECH` units against `scaffold_dags.py` output before choosing. Both go through the same `dag_quality_gate.py` and human review. {syn: B1,B2,B3} |
| Orbiter (full ruleset) or Otto access is not already provisioned for this engagement | Default to `scaffold_dags.py` plus hand translation for the remainder — don't add a new tool-procurement dependency to a migration's critical path unless the estate's scale genuinely justifies it (see `factory_candidate` volume threshold in `assess-migration-complexity-scoring`) |

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
- [B1] Astronomer — `orbiter-community-translations`, `orbiter_translations/autosys/jil_demo.py` (docstring: "Demonstration of translating AutoSys JIL files into Airflow DAGs ... Contact Astronomer ... for access to our full translation"; `CMD` → `BashOperator` only; repo archived 2026-03-16): https://github.com/astronomer/orbiter-community-translations/tree/main/orbiter_translations/autosys (tier 2, source code; accessed 2026-10-22)
- [B2] Astronomer Blog — "Introducing AI-assisted migrations with Otto" ("Otto supports migrations from tools like Control-M, AutoSys, Automic ..."; "takes your Control-M XML or AutoSys JIL and produces Python"): https://www.astronomer.io/blog/introducing-ai-assisted-migrations-with-otto-your-airflow-expert-for-the-translation-work-that-stalls-every-project/ (tier 3, vendor blog, not product docs; accessed 2026-10-22)
- [B3] Astronomer Docs — Otto overview (Labs feature; `astro otto`, Astro IDE, Astro for VS Code): https://www.astronomer.io/docs/astro/otto/otto-overview (tier 1; accessed 2026-10-22)
- NEEDS_EXEC_CHECK — scope of Astronomer's full (non-demo) Orbiter AutoSys ruleset; Otto's actual JIL job-type coverage, licensing/access model, and stop conditions. Not publicly documented as of 2026-10-22.
