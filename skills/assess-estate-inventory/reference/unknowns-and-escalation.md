---
topic: unknowns-and-escalation
family: assessment
skill: assess-estate-inventory
verified_against:
  autosys: "12.0"
last_verified: 2026-09-17
confidence: cited
signals: []
---

# Unknowns and escalation

Every unknown `_lib.autosys_jil.parser` records gets resolved or explicitly escalated — never
silently dropped or silently assumed benign. This file is the decision tree for each unknown
kind, all found in `Instance.unknowns` / `manifest.instances.<id>.unknowns`.

## Unknown job type (`unknowns.job_types`)

1. Check `Instance.objects` for a matching `GenericObject(kind="job_type", name=<the code>)` —
   this means it's a legitimate customer-defined type via `insert_job_type`
   [AS p.2855; `autosys-reference/reference/job-types.md`'s "Custom job types" section]. Not an
   error; record its family/translation approach as a discovery item, not a registry gap.
2. If not a custom type, check whether it's a real AutoSys code just missing from
   `job_types.json` — grep `research/autosys-12.0/*.txt` for the code. If found, this is a
   registry completeness gap: add it to `_lib/autosys_jil/registry/job_type_families.yaml` and
   regenerate (`build_registry.py`), don't work around it in this skill.
3. If genuinely not found anywhere (not a customer type, not in the corpus), check whether it
   might be a 12.1+ addition (`autosys-reference/SKILL.md`'s version caveat) — if so, mark
   `confidence: mixed` wherever it's discussed and proceed with best-effort translation guidance.
4. If none of the above, it's a real typo or data-quality issue in the export — flag it plainly
   in the report; do not guess what job type was intended.

## Unknown attribute (`unknowns.attributes`)

1. Grep `research/autosys-12.0/*.txt` for the attribute name — if it's real and just missing
   from `attributes.json`, this is a registry gap (same fix as above, via
   `attribute_families.yaml`).
2. If genuinely not found, check whether the estate's fixture-derived precedent applies: this
   project's own reference fixtures include a few attributes (`host`, `send_report`,
   `job_on_hold`, `job_on_ice`) that turned out to be non-canonical names used by a synthetic
   test estate, not real AutoSys fields — a customer estate could have the same kind of
   locally-invented or renamed field. Ask the platform team directly rather than guessing intent.
3. Never invent a plausible-sounding meaning for an unrecognized attribute name.

## Condition parse failure (`unknowns.condition_parse_failures`)

1. Read the raw string by hand against `autosys-reference/reference/conditions-grammar.md`. Most
   real-world failures are: mixed-case function names (illegal, [AS p.2437]), an unescaped `:` in
   a job name, or a malformed look-back value.
2. If the grammar in `_lib.autosys_jil.conditions` genuinely doesn't cover a construct the PDF
   documents, that's a real parser gap — file it as a `_lib` fix, not a per-job workaround.
3. A condition that fails to parse is NOT the same as a condition that references an undefined
   job (which parses fine and is handled separately, below) — don't conflate the two failure
   modes in the report.

## Unresolved reference (`unknowns.unresolved_refs`)

Kinds: `box_name`, `condition`, `machine`, `calendar`, `resource`.

1. **Stale export** — the referenced object was deleted after this export was taken but before
   the reference was removed. Check `delete_job`/`delete_machine` records and export dates.
2. **Cross-instance, not actually missing** — a condition referencing `job^INST` where `INST`'s
   own JIL wasn't included in this assessment's scope. Not a defect; note it as an
   assessment-scope boundary, and if `INST` will also migrate, flag for a later joint review.
3. **Genuinely undefined** — per [AS p.2436], AutoSys itself evaluates a condition on an
   undefined job as `false`; the dependent job simply never runs via that path. State this
   plainly — it may be intentional (a safety net) or a real defect the customer doesn't know
   about; either way, don't silently "fix" it in translation without asking.
4. **Deleted-but-referenced calendar/resource/machine** — same "stale export" logic as box names;
   confirm against a fresh export before treating as a real gap.

## When to escalate back to discovery

If resolving an unknown requires an artifact `assess-estate-discovery` didn't collect (a second
JIL export covering another instance, a machine registry CSV, confirmation from the platform
team), escalate explicitly — add it to that skill's checklist rather than guessing and moving on.
`build_estate_manifest.py --strict` exiting nonzero is the mechanical trigger for this: don't
re-run without `--strict` just to make the number go away.
