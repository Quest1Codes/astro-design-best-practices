#!/usr/bin/env python3
"""Run astro dev parse + ruff + the DAG-integrity pytest suite against the target project
[spec §7.1, plan §11.8].

Deterministic given a fixed project state; the checks themselves (parse/lint/pytest) are
standard tooling, not reimplemented here. Runs local subprocesses against the target project
only -- never a live AutoSys or Astro deployment.

The DAG-integrity tests (no import errors; owner/tags/doc_md present; no top-level
Variable.get/DB calls; catchup explicit; retries set; every task traceable via
traceability.json) live in `_lib/fixtures/astro_project/tests/dags/test_dag_integrity.py` and
are copied into the target project's `tests/dags/` on first run if not already present, so a
customer's own Astro project gains this gate without hand-authoring it.

Usage:
    python3 dag_quality_gate.py --project-dir . --traceability traceability.json [--skip-parse] [--skip-ruff]
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

_PYTEST_CMD = [sys.executable, "-m", "pytest"]

_FIXTURE_TESTS = Path(__file__).resolve().parents[2] / "_lib" / "fixtures" / "astro_project" / "tests" / "dags" / "test_dag_integrity.py"


def run(cmd: list[str], cwd: Path) -> tuple[int, str]:
    if not shutil.which(cmd[0]):
        return 127, f"{cmd[0]} not found on PATH"
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return proc.returncode, (proc.stdout + proc.stderr)


def ensure_integrity_tests(project_dir: Path, traceability: Path) -> None:
    target = project_dir / "tests" / "dags" / "test_dag_integrity.py"
    if not target.exists() and _FIXTURE_TESTS.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(_FIXTURE_TESTS.read_text().replace(
            "TRACEABILITY_PATH_PLACEHOLDER", str(traceability.resolve())))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project-dir", type=Path, default=Path("."))
    ap.add_argument("--traceability", type=Path, default=Path("traceability.json"))
    ap.add_argument("--skip-parse", action="store_true")
    ap.add_argument("--skip-ruff", action="store_true")
    ap.add_argument("--skip-pytest", action="store_true")
    args = ap.parse_args(argv)

    overall_ok = True
    results = []

    if not args.skip_parse:
        rc, out = run(["astro", "dev", "parse"], args.project_dir)
        results.append(("astro dev parse", rc, out))
        overall_ok &= rc == 0

    if not args.skip_ruff:
        rc, out = run(["ruff", "check", "."], args.project_dir)
        results.append(("ruff check", rc, out))
        overall_ok &= rc == 0

    if not args.skip_pytest:
        ensure_integrity_tests(args.project_dir, args.traceability)
        rc, out = run(_PYTEST_CMD + ["tests/dags", "-q"], args.project_dir)
        results.append(("pytest tests/dags", rc, out))
        overall_ok &= rc == 0

    for name, rc, out in results:
        status = "PASS" if rc == 0 else ("SKIPPED (tool not found)" if rc == 127 else "FAIL")
        print(f"[{status}] {name}", file=sys.stderr)
        if rc not in (0,):
            print(out[-2000:], file=sys.stderr)

    if not overall_ok:
        print("dag_quality_gate: NOT CLEAN -- fix the failures above before Phase 3 trial", file=sys.stderr)
        return 1
    print("dag_quality_gate: all checks passed", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
