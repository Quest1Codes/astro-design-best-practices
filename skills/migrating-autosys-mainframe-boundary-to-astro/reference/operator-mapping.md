# Operator mapping

Pick the operator from the **confirmed** protocol (Phase 2 of `SKILL.md`), never from a guessed one. This table names what's commonly applicable; verify current provider package names/versions against the target Airflow/Astro Runtime version before use, per the "do not invent APIs" discipline carried over from the core skill.

| Confirmed mechanism | Likely Airflow target | Notes |
|---|---|---|
| SFTP to/from a landing zone or gateway | `SFTPOperator` / `SFTPSensor` (`apache-airflow-providers-sftp`) | Straightforward if the gateway genuinely speaks SFTP end to end |
| Plain FTP | `FTPHook`-based operator or a custom `@task` wrapping `ftplib` if no maintained high-level operator covers the exact need | Plain FTP is increasingly rare in security-conscious mainframe shops; confirm it's really FTP and not FTPS/SFTP mislabeled colloquially |
| Connect:Direct / NDM | No confirmed first-party Airflow provider as of this writing — verify current state before assuming otherwise. If none exists: a `@task.bash` (or `@task` calling a Python wrapper) invoking the Connect:Direct CLI client already installed wherever the task executes | Do not fabricate a "ConnectDirectOperator" import; say plainly in the report that this is a CLI-wrapped task, not a native provider integration |
| A vendor MFT gateway with its own REST API | A generic `SimpleHttpOperator`/`HttpOperator`-based call, or a Python `@task` using `requests` against the documented API | Confirm the actual API contract with the platform team or the gateway's own docs — don't assume a REST shape |
| Filesystem landing zone (mainframe already delivered via some MFT tool to a mounted/shared filesystem) | `FileSensor` (`apache-airflow-providers-standard` or wherever it currently lives) | The simplest case; confirm the mount is actually visible from wherever the task executes (ties into the on-prem-distributed skill's networking concerns if execution moves off-network) |
| Object storage landing zone (MFT tool writes to S3/Azure Blob/GCS as its terminal step) | The matching cloud provider's sensor (`S3KeySensor`, etc.) | Increasingly common as shops modernize MFT tooling; often the easiest boundary case to migrate cleanly |
| JCL submission via FTP-to-internal-reader | A `@task` wrapping the same FTP call the AutoSys job made (submitting to the same JES internal reader target) | The submission mechanism, not the JCL content, is what's being translated |
| JCL submission via a vendor bridge/API tool | Whatever operator matches that tool's actual interface (CLI wrap or HTTP call, per its docs) | Confirm the tool's current interface directly; these vary by vendor and version |

## When no clean operator exists

The honest answer is a `@task.bash`/`@task` wrapping the exact same CLI/script the AutoSys job already ran — this is not a downgrade or a failure of the migration; it's often exactly right, since the underlying integration tool (Connect:Direct client, a vendor bridge) doesn't change just because the scheduler calling it did. Don't invent a provider operator to make the translation look more "native" than it is.
