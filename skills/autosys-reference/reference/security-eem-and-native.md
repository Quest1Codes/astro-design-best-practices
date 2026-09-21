---
topic: security-eem-and-native
family: knowledge
skill: autosys-reference
verified_against:
  autosys: "12.0"
  autosys_doc_pages: [668, 669, 670, 682, 706, 755, 756, 757, 782, 783, 2637, 2638]
last_verified: 2026-09-17
confidence: cited
signals: [credential_hits, fedramp, hipaa, sox]
---

# Security: native vs. external (CA EEM)

## Two modes [AS p.668-669]

| Mode | Scope | Notes |
|---|---|---|
| **Native security** | Job-specific permissions (`permission`/`owner` attributes) + superuser delegation | System-level (UID/GID on UNIX, user-type on Windows). Limited, coarse; the PDF explicitly recommends against it as the sole mechanism. |
| **External security (CA EEM)** | Role-based access, granular, across jobs/calendars/cycles/global variables/machines/resources | **Default mode after install** [AS p.669]. The PDF's own recommendation: "we strongly recommend that you implement CA EEM security on both AutoSys Workload Automation and Web UI" [AS p.669]. |

**System-level security is always in effect regardless of mode** [AS p.668]: password-protected
login, job-owner login credentials required to execute (the agent logs in *as the owner* to run
a job), and login-credential-derived permission grants.

**Important interaction** [AS p.669]: CA EEM policies defined on Web UI do **not** check
security for objects defined via the `jil` command — if native security is in use, `owner`/
`permission` attributes on the job definition are the only enforcement for anything created
outside Web UI. A discovery/assessment pass should note which mode is active
(`autosys_secure` command output, or ask the platform team) before assuming Web UI RBAC policy
is the complete access-control picture.

## `permission` attribute [AS p.2637-2638]

```
permission: value [,value...]
```

| Value | Platform | Grants |
|---|---|---|
| `gx` | UNIX only | Group execute |
| `ge` | UNIX only | Group edit |
| `we` | | World edit |
| `wx` | | World execute |
| `mx` | | Any authorized user may **execute** regardless of machine (otherwise must be logged onto the `owner` field's host/domain) |
| `me` | | Any authorized user may **edit** regardless of machine |

Default: machine permissions off (i.e., without `mx`/`me`, a user must be logged onto the exact
host/domain named in `owner`). The job owner always has full edit+execute rights.
`_lib.autosys_jil.models.Job.permission` carries the raw list;
`assess-astro-target-architecture/scripts/rbac_map.py` (EEM policy → Astro role proposal) treats
`permission`-only jobs (no EEM policy covering them) as a gap to flag explicitly, not silently
default to "no restriction."

## FIPS mode [AS p.755-757]

`EnableFIPSMode` config parameter (see `_lib/autosys_jil/registry/config_params.yaml`) restricts
AutoSys to FIPS 140-2 compliant algorithms; DES encryption and unencrypted communication are
blocked when enabled. Relevant almost exclusively to U.S. government/regulated estates — a
positive finding here should route to
`astro-design-best-practices/reference/regulatory-and-compliance/vertical-overlay-government-fedramp-data-residency.md`.

## `safex` — the EEM policy export format [AS p.782-783]

The migration path from a legacy security tool to CA EEM (and the export format
`migrate-astro-platform-buildout/scripts/rbac_map.py` consumes) is:

1. `as_safetool` installs/registers the current resource classes and default policies for the
   instance in the target CA EEM back-end.
2. `safex` imports (or, for discovery purposes, exports) the generated policy XML.

`safex` is only available on the machine hosting the CA EEM back-end server, and it writes all
output to `stderr` — the PDF explicitly recommends capturing and saving that output to a file
[AS p.783]. This is the artifact `assess-estate-discovery/reference/artifact-checklist.md` asks
for under "EEM `safex` export"; `rbac_map.py` parses it into `(identity, resource class, action)`
triples and proposes an Astro Organization/Workspace/Deployment role and Team mapping, flagging
any EEM construct (typically fine-grained per-job ACL bits) that has no Astro equivalent.

## Credential handling in job definitions

AutoSys native security does not encrypt secrets embedded in a job's `command:`, `profile:`, or
similar fields — a connection string, `-p password` flag, or `%%SECRET%%` global var reference is
exactly as exposed as any other string in the JIL export. `_lib.autosys_jil.commands.analyze()`
and `_lib.autosys_jil.manifest.redact()` both treat this as a first-class finding
(`credential_hits[]`), redacted by default before anything is written to disk (plan §11.6) — a
migration report's "compliance finding" section should cite the redaction pattern name, never the
underlying value, and route the *scope* of the finding (how many jobs, which families) to
`migrate-astro-platform-buildout/reference/secrets-and-identity.md`.
