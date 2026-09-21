---
topic: what-jil-cannot-tell-you
family: assessment
skill: assess-estate-discovery
verified_against:
  autosys: "12.0"
last_verified: 2026-09-17
confidence: mixed
signals: [windows, zos, credential_hits]
---

# What JIL cannot tell you

A JIL export (and even the fuller `estate_manifest.json` built from it) is a definition of intent
— job names, commands, conditions, machine *names*. It says nothing about what those machines
actually provide, who really operates the estate day to day, or what happens outside AutoSys
entirely. This file is the checklist of things to go ask for, not derive.

## Machine and environment facts

| Fact needed | Typical source |
|---|---|
| OS and version | Platform team / CMDB — a `machine:` value is just a name |
| Agent version and installed plugins | Platform team, or `agentparm.txt` (see `reference/artifact-checklist.md`) |
| Locally installed software/drivers a command depends on | Read the actual script, not just its name — the JIL only shows the invocation |
| Mapped drives / local file paths | grep the command and any config it reads; becomes a network mount or a redesign target |
| Service account and its auth model (domain-joined? Kerberos? local?) | Platform team — determines Hosted-vs-Hybrid feasibility for that machine group |
| Network reachability from each machine (what it can reach today) | Network team / firewall documentation — the baseline the target environment must reproduce or intentionally change |

## Mainframe boundary specifics (when `migrate-topology-mainframe-boundary` is in scope)

- What's actually on the other side of a flagged boundary job (system name, owner) — a dataset
  name or MFT keyword match is a hint, not a confirmed system.
- The real integration mechanism and protocol (not just a guessed keyword from
  `boundary_job_scanner.py`).
- Whether the mainframe side has any timing dependency on the AutoSys-side job (does it wait for
  a specific file pattern or delivery window).
- Network/security context for the boundary itself — DMZ, dedicated MFT gateway, RACF-governed
  access — since these determine what (if anything) changes about how the boundary is crossed
  once the distributed side moves to Astro.

## Operational and human facts

- **Who actually operates this estate day to day** — the on-call model, who has WCC/Web UI
  access and to what, who gets paged, who approves changes. None of this is in JIL.
- **WCC/Web UI dashboard layouts, saved views, Quick Edit groups** — not exportable via CLI at
  all (see `autosys-reference/reference/wcc-and-web-ui.md`); ask who uses what and why.
- **Inbound callers** — anything calling into AEWS, or issuing `sendevent` from outside this
  estate's own jobs, needs to be found (access logs, or asking) and repointed at cutover; a JIL
  export only shows outbound `sendevent` calls embedded in commands, never inbound ones.
- **Undocumented/tribal runtime cloning logic** — a global-variable-driven pattern where one
  template job is cloned repeatedly via `sendevent` at runtime is real but often invisible in a
  static JIL export; ask directly if `command_analysis.py`'s `global_var_refs` findings look like
  this pattern.
- **Business SLAs not encoded as `must_complete_times`** — a job might have a real business
  deadline the JIL never states; `reference/stakeholder-questions.md` is where this gets asked.

## Security posture

- Native security mode vs. external (CA EEM) — see `autosys-reference/reference/security-eem-and-native.md`.
  This determines whether `owner`/`permission` attributes are the real access-control mechanism
  or just a fallback under an EEM policy layer.
- Credential storage: OS-level service-account passwords, a vault/CyberArk integration, or
  hardcoded in scripts (`_lib.commands.analyze()`'s `credential_hits` flags the last case, never
  the value itself).

## Compliance and commercial context

Covered structurally in `reference/stakeholder-questions.md` (residency, vertical overlays,
license end dates, engagement timeline) — listed here as a reminder that none of it comes from a
technical artifact at all.
