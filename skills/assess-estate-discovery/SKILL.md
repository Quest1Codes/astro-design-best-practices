---
name: assess-estate-discovery
description: First phase of an AutoSys estate assessment — figure out what artifacts exist, request them with exact commands, validate what comes back, and run the stakeholder questionnaire. Use at the very start of any AutoSys-to-Astronomer engagement, before any manifest exists. Produces a checklist of received/missing/waived artifacts and validated evidence; does not parse JIL itself (that's assess-estate-inventory). Read-only: never touches a live AutoSys or Astro system, only files the customer already exported.
---

# Estate discovery

Figure out what this estate actually is before assessing it. AutoSys has no single "export
everything" command — job definitions, machine registry, calendars, run history, and platform
config all come from different commands and sometimes different teams (DBA for history, platform
team for machine/agent facts, security team for EEM). This skill's job is to make that checklist
explicit, track what's arrived, and sanity-check that what arrived is actually what it claims to
be — before `assess-estate-inventory` tries to parse any of it.

## Requirements

- `_lib.autosys_jil` installed (`pip install -e skills/_lib`).
- A named contact for each of: the AutoSys platform team, a DBA with access to the event server,
  and (if EEM/native-security details matter) the security team. Discovery routinely stalls on
  "who do I even ask" — get names before requesting artifacts.

## Hard rules

- **Read-only, always.** Every script here reads files the customer already produced; nothing
  connects to a live AutoSys or Astro instance. The commands in
  `reference/autorep-and-export-commands.md` are what *the customer* runs, not what this skill
  runs on their behalf.
- **No silent gaps.** Every artifact in `reference/artifact-checklist.md` ends `received`,
  `validated`, or `waived (reason)` before this phase gates to `parsed`-ready. A waived required
  artifact is a stated limitation in the eventual report, not a thing to quietly work around.
- **Validate before trusting.** A file that claims to be `autorep -M ALL -q` output but doesn't
  have the right columns is not that file — `validate_artifacts.py` sniffs shape before anything
  downstream parses it as fact.

## Workflow

### Phase 1: Identify instances

Find out how many AutoSys instances (`$AUTOSERV` values) are in scope — a customer with
production, DR, and multiple business-unit instances needs this decided before requesting
per-instance exports. `autorep -J ALL -q` run against each candidate instance (or asked of the
platform team) confirms which are live and worth including.

### Phase 2: Emit the checklist

```
python3 scripts/discovery_checklist.py --instances ACE,PRD --received ./received/ \
  --out checklist.json --md checklist.md
```

Walks `reference/artifact-checklist.md`'s artifact list per instance, checks `./received/` for
files already sniffed as matching by `validate_artifacts.py`, and prints what's still missing
with the exact command to request it.

### Phase 3: Receive and validate

As artifacts land in the received directory:

```
python3 scripts/validate_artifacts.py --received ./received/ --out evidence.json
```

Sniffs each file's shape (JIL export has `insert_job:` blocks; `autorep -M` output has the right
column headers; `autocal_asc` output has date lines; a CSV has recognizable columns; etc.),
records a SHA-256 + size + detected kind + instance guess for each, and refuses unknown file
kinds unless `--allow-unknown` is passed (a genuinely new artifact type should be looked at, not
silently absorbed). This `evidence.json` becomes `estate_manifest.json`'s `evidence[]` once
`assess-estate-inventory` runs.

### Phase 4: Stakeholder questionnaire

Work through `reference/stakeholder-questions.md` with the customer — SLAs not encoded in JIL,
RTO/RPO, compliance overlays, change-freeze calendars, on-call model, target platform
constraints, commercial timeline. Record answers in an `answers.yaml` matching that file's
schema; `assess-estate-inventory` folds it into `manifest.nfr{}`.

### Phase 5: Gate

`python3 -m autosys_jil.status --manifest checklist.json summary --workflow assessment` should
show `collected` only once every *required* artifact (per `artifact-checklist.md`) is `received`
and `validated`, or explicitly `waived` with a reason recorded. Optional artifacts missing is
fine and expected — call it out in the eventual report, don't block on it.

## Reference routing

| Question | Read |
|---|---|
| What to collect, exact command, why it matters | `reference/artifact-checklist.md` |
| The runnable export recipe (copy-paste per OS, pitfalls) | `reference/autorep-and-export-commands.md` |
| What JIL alone can never tell you | `reference/what-jil-cannot-tell-you.md` |
| Structured NFR/stakeholder questions | `reference/stakeholder-questions.md` |

## Scripts

| Script | Purpose |
|---|---|
| `scripts/discovery_checklist.py` | Per-instance artifact checklist: received/missing/waived, with the exact command to run for anything missing |
| `scripts/validate_artifacts.py` | Sniff each received file's shape, hash it, record it as evidence; refuses unrecognized kinds by default |
