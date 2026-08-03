---
name: migrating-autosys-mainframe-boundary-to-astro
description: Guide for migrating the mainframe-boundary jobs in an AutoSys estate to Airflow on Astro. Use when the estate has file-watcher or file-transfer jobs that watch for or deliver z/OS-produced data (MFT/Connect:Direct/NDM drops), or jobs that submit JCL / trigger mainframe batch via an agent. This is NOT a mainframe workload migration -- AutoSys never ran natively on z/OS (that's a separate Broadcom product line, CA Workload Automation for z/OS / CA-7); this skill covers the orchestration boundary only, with the mainframe staying exactly where it is. Requires manifest.json from migrating-autosys-to-astronomer; load that skill first, this one second. Load reference/boundary-integration-patterns.md before proposing any change to a boundary job.
hooks:
  PostToolUse:
    - matcher: "Edit"
      hooks:
        - type: command
          command: "echo 'Boundary job edited: confirm this does not touch mainframe-side JCL/scheduling -- scope is the orchestration boundary only. Re-run python3 scripts/status.py summary against boundary_manifest.json'"
---

# Mainframe-boundary AutoSys jobs → Astro

Migrate the jobs in an AutoSys estate that sit at the boundary with a mainframe (z/OS) system — jobs that watch for mainframe-produced files, jobs that deliver files to the mainframe (MFT/Connect:Direct/NDM), or jobs that trigger mainframe batch processing (JCL submission via an agent). **The mainframe itself does not move.** AutoSys is a distributed scheduler; it never ran on z/OS. What's migrating is the orchestration sitting on the distributed side of that boundary — the same jobs the core skill would translate anyway, but flagged here because they carry integration-specific risk (security boundary, MFT protocol specifics, coexistence requirements) that the core skill's generic job-type mapping doesn't cover.

This skill assumes `migrating-autosys-to-astronomer` has already produced `manifest.json`. This skill's job is to identify boundary jobs within it, apply the integration-specific translation patterns, and manage the security/coexistence concerns particular to touching mainframe-adjacent systems.

## Requirements

- `manifest.json` from `migrating-autosys-to-astronomer`.
- Confirmation from the platform/mainframe team of which systems on the other side of each boundary job actually are (dataset naming conventions in use, the MFT/Connect:Direct topology, who owns the z/OS side) — do not infer mainframe details from JIL alone; JIL only shows what the AutoSys-side job does.
- Network/security context for the boundary itself: is there a DMZ, a dedicated MFT gateway, RACF-governed access — these determine what changes (if anything) about how the boundary is crossed once the distributed side moves to Astro.

## Hard rules

1. **Never conflate "migrate the boundary job" with "migrate mainframe workload."** If a request or plan starts describing moving JCL, z/OS batch windows, or mainframe compute itself, stop and flag that this skill's scope does not cover that — it is a different (and likely different-vendor) migration entirely.
2. **Detection is heuristic; confirm before acting.** `scripts/boundary_job_scanner.py` flags jobs by keyword/pattern matching (dataset-naming conventions, known MFT tool references, hostnames) — every flagged job needs human/platform-team confirmation before being treated as a true boundary job, and the scanner's silence on a job is not proof it isn't one (obscure or renamed patterns won't match).
3. **No silent omissions.** Every flagged boundary job ends `complete` or `deferred (reason)` in the boundary manifest, same discipline as the core skill.
4. **Coexistence is the default plan, not an exception.** The mainframe side is out of scope for change; assume it keeps running exactly as before unless explicitly told otherwise, and design the Astro-side replacement to interoperate with it unchanged for at least one full validation cycle.
5. **Security boundary changes get explicit sign-off.** Any change to how the distributed side authenticates or connects across the boundary (new source IPs from Astro Hosted/Hybrid, a new service account, a new network path through a DMZ/gateway) needs the mainframe/security team's explicit approval before cutover — this is not a call this skill or its user makes unilaterally.

## Workflow

### Phase 1: Detect boundary jobs

```
python3 scripts/boundary_job_scanner.py --manifest manifest.json --out boundary_manifest.json
```

Scans every job in `manifest.json` for boundary signals: z/OS-style dataset naming conventions (`HLQ.SUBHLQ.NAME`-shaped tokens) in `command`/`watch_file`/`raw_extra` values, known MFT/Connect:Direct keyword references, FT job type generally, and machine/hostname tokens suggesting a gateway (`mft`, `gateway`, `zos`, `ndm`). Every hit is a `flagged`, not a confirmed boundary job — Phase 2 confirms.

### Phase 2: Confirm with the platform/mainframe team

For each flagged job, get from the platform team: what's actually on the other side (system name, owner), the real integration mechanism (protocol, not just a guessed keyword), and whether the mainframe side has any awareness of or dependency on the *timing* of the AutoSys-side job (does the mainframe job wait for a specific file pattern, does it care about exact delivery windows). Record confirmed/not-a-boundary-job/needs-more-info per job.

### Phase 3: Plan the translation

Per `reference/boundary-integration-patterns.md` and `reference/operator-mapping.md`: pick the Airflow provider operator matching the confirmed protocol (SFTP/FTP, or whatever bridges to Connect:Direct/NDM if no native Airflow operator exists — a wrapped CLI call via `@task.bash` may be the honest answer where no provider operator exists, not a fabricated one). Plan the security/coexistence approach per `reference/coexistence-and-security.md`.

### Phase 4: Trial

Migrate 1-2 representative boundary jobs end to end, run them side by side with the AutoSys original for a full cycle (or more, if the integration is timing-sensitive), and get explicit mainframe/security team sign-off on the trial's network/auth path before scaling.

### Phase 5: Migrate and validate

Per `reference/validation.md`, track each boundary job through to `complete` in `boundary_manifest.json`, using `scripts/status.py`.

### Phase 6: Final report

`scripts/status.py summary` must pass. The report: every flagged job's confirmed disposition (true boundary job / false positive / deferred pending platform-team input), the integration pattern and operator used per job, the security sign-off obtained, and explicit confirmation that the mainframe side required zero changes (or, if it did, exactly what and why — a rare case that should be called out prominently, not buried).

## Reference routing

| Question | Read |
|---|---|
| What kinds of boundary integration exist, how do they typically work | `reference/boundary-integration-patterns.md` |
| Which Airflow operator/provider fits which protocol | `reference/operator-mapping.md` |
| Security boundary, RACF/DMZ, keeping the mainframe side stable during migration | `reference/coexistence-and-security.md` |
| Validating a boundary job's translation | `reference/validation.md` |
| Failure classes seen before | `reference/troubleshooting.md` |

## Scripts

| Script | Purpose |
|---|---|
| `scripts/boundary_job_scanner.py` | Flag likely mainframe-boundary jobs in `manifest.json` by pattern (heuristic, needs confirmation) |
| `scripts/status.py` | Per-job state machine + completeness gate over `boundary_manifest.json` |
