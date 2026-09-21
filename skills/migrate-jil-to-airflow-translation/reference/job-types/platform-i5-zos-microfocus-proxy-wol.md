---
topic: platform-i5-zos-microfocus-proxy-wol
family: migration
skill: migrate-jil-to-airflow-translation
verified_against:
  airflow: "3.3.1"
  astro_runtime: "3.3-2"
  autosys: "12.0"
  autosys_doc_pages: [2551, 2549, 2425, 2848]
last_verified: 2026-09-17
confidence: mixed
signals: [zos, windows]
---

# Platform: I5, ZOS, ZOSM, ZOSDST, MICROFOCUS, PROXY, WOL

| Code | Default target | Disposition |
|---|---|---|
| `I5` (IBM i / i5/OS) [AS p.2551] | `SSHOperator` to the IBM i host, running `QSH`/`CL` commands | JUDG |
| `ZOS` / `ZOSM` / `ZOSDST` [AS p.2549, p.2848] | **Route to `migrate-topology-mainframe-boundary`** — these are native z/OS job types, not translated here | route |
| `MICROFOCUS` [AS p.2551] | `SSHOperator`/`BashOperator` on the Micro Focus COBOL runtime host | JUDG |
| `PROXY` (Remote Execution) [AS p.2551] | `SSHOperator` — remote execution is literally what `PROXY` already is | **MECH** |
| `WOL` (Wake on LAN) [AS p.2425] | **No orchestration equivalent** — document and move on | **NONE** |

## `ZOS`/`ZOSM`/`ZOSDST` always route

These three job types are the **definitive** signal `migrate-topology-mainframe-boundary`'s
`boundary_job_scanner.py` uses (job-type match, before any heuristic pattern matching) — never
translate them in this skill; hand off entirely. See
`autosys-reference/reference/job-types.md`'s platform family table for what each does.

## `PROXY` is the one MECH job in this family

`PROXY` exists specifically to run a command on a remote machine via the agent — that's exactly
what `SSHOperator` does, so this is the rare platform-family job with no real judgment call
beyond confirming the target host's reachability (a `migrate-topology-onprem-distributed`
question, not a translation question).

## `WOL`

No Airflow equivalent exists for waking a physical machine over the network. Document the
operational alternative (does the target environment even have machines that need waking, or is
this obsolete once workloads move to cloud-hosted compute) and move on — this is rarely a
blocker.

## What the scaffolder emits vs. leaves as TODO

Emits `SSHOperator` skeletons for `I5`/`MICROFOCUS`/`PROXY` with the host parameterized; refuses
to scaffold `ZOS`/`ZOSM`/`ZOSDST` (routes instead) and `WOL` (NONE, refused per the hard rule).
