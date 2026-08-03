# Dynamic Task Mapping Design

The internal reference file `global-variables-and-templating.md` already classifies this translation as **REDESIGN**, not a mechanical mapping: an AutoSys "template" job cloned N times at runtime (via `sendevent`/scripted `jil` generation) has no line-by-line Airflow equivalent — the cloning logic has to be reconstructed as a mapping input [P1]. This file is that reconstruction's design guidance.

## Core mechanics

- Dynamic task mapping creates tasks at runtime based on the output of a previous task — the scheduler generates the actual task instances, replacing what would otherwise be a manual `for` loop written at parse time [F1].
- `partial()` carries the arguments that must stay static across every mapped instance (`task_id`, `queue`, `pool`, and most other `BaseOperator` arguments) [F2].
- `expand()` takes only keyword arguments, and is what actually varies per generated task instance [F2].
- To map over another task's output, reference it explicitly (`SomeOperator.partial(...).expand(input=upstream_task.output)`) rather than mapping over the operator itself [F2].

## {syn: P1,F1,F2} Design guidance

The AutoSys-side cloning trigger — whatever currently decides "how many instances, with what per-instance parameters" — becomes the mapping input, not a Python loop in the DAG file. Concretely:

1. Identify what actually drove the clone count in AutoSys: a fixed list in a config file, a database query, a preceding job's output, or an operator manually running `jil` inserts. This determines whether the mapping input is a static list (`.expand(x=[1,2,3])`), a Variable/config read, or genuinely another task's output (`.expand(input=upstream.output)`) [F2].
2. Everything that was identical across every cloned job instance (the job's command template, its machine/queue assignment, its `owner`) goes into `partial()`; everything that varied per clone (a filename, a region code, a per-instance parameter) goes into `expand()` [F2].
3. If the clone count itself needs to vary per DAG run (not just the per-instance parameters), the upstream task producing the mapping input must run and complete before the mapped task set is generated — this is a real DAG-structure implication (an extra upstream task), not just a syntax choice.

## What NOT to do

Do not attempt to preserve the *mechanics* of AutoSys's cloning (e.g., literally generating and inserting N separate JIL-equivalent job definitions via a factory at parse time) when dynamic task mapping is available — that reintroduces exactly the top-level-code-at-parse-time problem covered in `dag-parsing-performance-budget.md`. Dynamic task mapping generates task instances at *run* time, which is the correct place for a count that can vary run-to-run; a DAG-factory should only be regenerating the *static* structure (which jobs/boxes exist), not simulating per-run clone counts.

## Sources

- [F1] Apache Airflow docs — Dynamic Task Mapping (overview, replaces manual for-loop): https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/dynamic-task-mapping.html (tier 2)
- [F2] Apache Airflow docs — Dynamic Task Mapping (`partial()`/`expand()` mechanics): same as F1 (tier 2)
- [P1] Project-internal — `skills/migrating-autosys-to-astronomer/reference/global-variables-and-templating.md` (runtime job templating → REDESIGN classification)
