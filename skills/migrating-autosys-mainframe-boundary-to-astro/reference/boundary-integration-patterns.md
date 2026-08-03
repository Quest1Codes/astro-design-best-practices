# Boundary integration patterns

## The three shapes a boundary job usually takes

### 1. Watching for mainframe-produced data

An AutoSys `f` (file watcher) job polls for a file the mainframe has dropped — typically via an MFT/Connect:Direct/NDM delivery to a landing zone the distributed side can see, or occasionally a direct dataset-to-file bridge. The AutoSys job's role is purely "notice it arrived, kick off downstream processing."

**Translation**: `FileSensor` if the landing zone is a filesystem the Airflow environment can reach directly; if the landing zone is itself behind another protocol (SFTP, an object store the MFT tool writes to), use the matching provider sensor. Consider whether this is better redesigned as an event-driven trigger (if the MFT tool can call a webhook or write to a queue on arrival) rather than polling — ask the platform team whether that option already exists before assuming polling is the only choice.

### 2. Delivering data to the mainframe

An AutoSys `FT` job pushes a file to the mainframe side, usually via Connect:Direct/NDM (a widely used MFT product in mainframe-adjacent shops) or SFTP to a gateway that then relays into z/OS.

**Translation**: depends entirely on the confirmed protocol (see `reference/operator-mapping.md`). Connect:Direct specifically has no first-party Airflow provider as of this writing — verify current provider availability before assuming one exists; if none does, the honest translation is a wrapped CLI call to the Connect:Direct command-line client (`direct` CLI or equivalent) via `@task.bash`, not a fabricated "ConnectDirectOperator."

### 3. Triggering mainframe batch (JCL submission)

An AutoSys job (often a plain `c` command job) invokes some mechanism to submit a JCL job to the mainframe's job entry subsystem (JES) — commonly via an FTP-based JCL submission (writing to an internal reader), a vendor bridge tool, or a REST-facing gateway product if the mainframe side exposes one.

**Translation**: the AutoSys-side job becomes a task that performs the same submission call (via the same mechanism — FTP/API/CLI, whatever it confirmed to be) from Airflow. This skill translates the *submission call*, not the JCL itself, which is out of scope and unchanged.

## What stays exactly the same

In all three shapes, the mainframe-side system, its schedule, its JCL, and its own internal dependencies are not part of this migration. The only thing moving is which distributed-side scheduler issues the call/watches the file. State this explicitly to stakeholders — "the mainframe job still runs the same way, at the same time, doing the same thing; only the trigger/watcher on the other side of the wire changed" is the accurate framing.

## When a job doesn't cleanly fit one of these three

Some boundary jobs are hybrids (e.g., a job that both waits for one file and delivers another as part of the same script). Don't force a single pattern — decompose into however many Airflow tasks are actually needed to represent the distinct integration points, and note the decomposition in the manifest as a JUDG-classified translation (per the core skill's `reference/mapping.md` scheme).
