#!/usr/bin/env python3
"""Render the assessment report from `estate_manifest.json` [spec §6.5].

Deterministic: given the same manifest, `--draft` output is byte-identical.
Reads/writes local files only; never contacts a live AutoSys or Astro system.

Three modes:
  --draft  Renders assessment_report.md.j2 fresh from the manifest. G sections are filled with
           real data; H sections contain a `HUMAN: <prompt>` placeholder for a person to author
           directly in the output file. Always safe to re-run -- but re-running OVERWRITES the
           file, including any human edits already made. Use --draft only to create the first
           draft, or to intentionally discard human edits and start over.
  --lint   Advisory, non-blocking (always exits 0). Runs the estate-specificity and
           knowledge-skill-echo checks (see below) against the CURRENT --out file, even if it's
           still mid-authoring. Use this during Phase 2 to catch generic/rephrased H-section prose
           before it reaches --final.
  --final  Does NOT re-render. Validates the EXISTING --out file and refuses (exit 1) if:
             1. any `HUMAN:` placeholder remains,
             2. any `<!-- G:empty:... -->` marker remains without an adjacent
                `<!-- WAIVED: reason -->` comment,
             3. an H section contains no estate-specific signal at all (no digit and no token
                traceable to this report's own G-section data) -- i.e. it reads as generic
                explanation rather than analysis of this estate, or
             4. an H-section sentence near-verbatim matches (>=0.92 similarity) a sentence from
                this KB's own knowledge skills (astro-design-best-practices, autosys-reference,
                autosys-to-astronomer) -- i.e. it's the skill's reference content copied/rephrased
                rather than a finding.
           Moderate similarity (0.75-0.92) to knowledge-skill text is printed as a non-blocking
           warning for human review, not a hard failure -- correctly citing KB terminology isn't
           itself wrong, only substituting it for analysis is.
           This is the gate that protects human-authored prose from being silently overwritten by
           a second render, AND from being a rephrase of the reference skills instead of estate
           analysis.

Usage:
    python3 render_report.py --manifest estate_manifest.json --out report.md --draft
    python3 render_report.py --out report.md --lint
    python3 render_report.py --out report.md --final
    python3 render_report.py --manifest estate_manifest.json --out report.md --docx report.docx --draft
"""
from __future__ import annotations

import argparse
import difflib
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import jinja2

_LIB = Path(__file__).resolve().parents[2] / "_lib"
sys.path.insert(0, str(_LIB))

from autosys_jil import manifest as manifest_mod  # noqa: E402
from autosys_jil import registry as registry_mod  # noqa: E402

_TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "templates"
_HUMAN_RE = re.compile(r"\bHUMAN:")
_EMPTY_MARKER_RE = re.compile(r"<!-- G:empty:(\w+) -->")
_WAIVED_RE = re.compile(r"<!-- WAIVED: .+? -->")

# --- Estate-specificity / knowledge-echo harness -----------------------------------------------
# See SKILL.md and reference/report-structure.md: H sections are analysis, not documentation --
# every one must be traceable to *this* estate's own G-section data, not a restatement of concepts
# the reader already has from the knowledge skills.

_SKILLS_ROOT = Path(__file__).resolve().parents[2]
_KNOWLEDGE_SKILL_DIRS = ["astro-design-best-practices", "autosys-reference", "autosys-to-astronomer"]

# Numbered sections that carry a HUMAN: placeholder in the template -- these are the only ones the
# specificity/echo checks look at (pure-G sections like 3-6, 9 need no human judgment to check).
_SPECIFICITY_CHECK_SECTIONS = {"1", "2", "7", "8", "10", "11", "12", "13", "14"}

_SECTION_HEADING_RE = re.compile(r"^## (\d+)\. .+$", re.MULTILINE)
_TABLE_ROW_RE = re.compile(r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|", re.MULTILINE)
_INLINE_TOKEN_RE = re.compile(r"\*\*([^*]+)\*\*|`([^`]+)`")
_WORD_RE = re.compile(r"[A-Za-z0-9_./%-]{3,}")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")
_MD_STRIP_RE = re.compile(r"[`*_#]|\[([^\]]*)\]\([^)]*\)|\[[A-Za-z0-9., ]+\]")

_VOCAB_STOPWORDS = {
    "the", "and", "for", "with", "this", "that", "count", "value", "choice", "metric",
    "recommendation", "component", "units", "pts", "artifact", "first", "none", "total",
    "wave", "basis", "reason", "observed", "floor", "instances", "assessed",
}


def _extract_sections(text: str) -> dict[str, str]:
    """Split the rendered report into {section_number: body_text} by its `## N. Title` headings."""
    matches = list(_SECTION_HEADING_RE.finditer(text))
    sections: dict[str, str] = {}
    for i, m in enumerate(matches):
        num = m.group(1)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections[num] = text[start:end]
    return sections


def _extract_vocabulary(text: str) -> set[str]:
    """Pull estate-specific tokens (table cells, bold/code spans) out of the whole rendered doc.

    Tables and bold/code spans in this template are always G-rendered data (real names, numbers,
    decisions) -- never HUMAN: prose -- so this is a safe source of "things that actually belong
    to this estate" regardless of which section they appeared in.
    """
    vocab: set[str] = set()
    for row in _TABLE_ROW_RE.finditer(text):
        for cell in row.groups():
            vocab.update(_tokenize(cell))
    for span in _INLINE_TOKEN_RE.finditer(text):
        for group in span.groups():
            if group:
                vocab.update(_tokenize(group))
    return vocab


def _tokenize(fragment: str | None) -> set[str]:
    if not fragment:
        return set()
    return {
        tok.lower() for tok in _WORD_RE.findall(fragment)
        if tok.lower() not in _VOCAB_STOPWORDS
    }


def check_estate_specificity(text: str) -> list[str]:
    """Fail any H section that contains no digit and no token traceable to this report's own data."""
    vocab = _extract_vocabulary(text)
    sections = _extract_sections(text)
    problems = []
    for num in sorted(_SPECIFICITY_CHECK_SECTIONS, key=int):
        body = sections.get(num, "")
        if not body.strip():
            continue  # caught separately as an unfilled HUMAN: placeholder
        has_digit = bool(re.search(r"\d", body))
        body_tokens = _tokenize(body)
        has_vocab_hit = bool(body_tokens & vocab)
        if not has_digit and not has_vocab_hit:
            problems.append(
                f"section {num}: no estate-specific number or named finding detected -- reads as "
                f"generic explanation rather than analysis of this estate (see "
                f"reference/report-structure.md)"
            )
    return problems


def _normalize_for_compare(sentence: str) -> str:
    stripped = _MD_STRIP_RE.sub(" ", sentence)
    stripped = re.sub(r"\[[^\]]*\]", " ", stripped)  # citation markers like [B1], [AS p.123]
    return re.sub(r"\s+", " ", stripped).strip().lower()


def _split_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_SPLIT_RE.split(text) if s.strip()]


_knowledge_corpus_cache: list[str] | None = None


def _load_knowledge_corpus() -> list[str]:
    """Normalized, >=8-word sentences from this KB's own knowledge skills (not the assess-* family)."""
    global _knowledge_corpus_cache
    if _knowledge_corpus_cache is not None:
        return _knowledge_corpus_cache
    sentences: list[str] = []
    for skill_dir in _KNOWLEDGE_SKILL_DIRS:
        root = _SKILLS_ROOT / skill_dir
        if not root.exists():
            continue
        paths = [root / "SKILL.md"] + sorted((root / "reference").rglob("*.md")) if (root / "reference").exists() else [root / "SKILL.md"]
        for path in paths:
            if not path.exists():
                continue
            try:
                raw = path.read_text(encoding="utf-8")
            except OSError:
                continue
            for sent in _split_sentences(raw):
                norm = _normalize_for_compare(sent)
                if len(norm.split()) >= 8:
                    sentences.append(norm)
    _knowledge_corpus_cache = sentences
    return sentences


def check_knowledge_echo(text: str) -> tuple[list[str], list[str]]:
    """Hard-fail near-verbatim echoes of knowledge-skill text; warn on moderate similarity."""
    corpus = _load_knowledge_corpus()
    if not corpus:
        return [], ["knowledge-skill corpus not found (run from within the full skills/ checkout) -- echo check skipped"]
    problems: list[str] = []
    warnings: list[str] = []
    sections = _extract_sections(text)
    for num in sorted(_SPECIFICITY_CHECK_SECTIONS, key=int):
        for sent in _split_sentences(sections.get(num, "")):
            norm = _normalize_for_compare(sent)
            if len(norm.split()) < 8:
                continue
            matches = difflib.get_close_matches(norm, corpus, n=1, cutoff=0.75)
            if not matches:
                continue
            ratio = difflib.SequenceMatcher(None, norm, matches[0]).ratio()
            preview = sent[:110] + ("..." if len(sent) > 110 else "")
            if ratio >= 0.92:
                problems.append(f"section {num}: sentence closely matches knowledge-skill text (ratio {ratio:.2f}): {preview!r}")
            else:
                warnings.append(f"section {num}: sentence resembles knowledge-skill text (ratio {ratio:.2f}, review before finalizing): {preview!r}")
    return problems, warnings


def _table_global(data, key_label: str, value_label: str) -> str:
    """Jinja global: render a dict or list-of-pairs as a Markdown table."""
    if isinstance(data, dict):
        items = list(data.items())
    else:
        items = list(data)
    if not items:
        return f"_(no data -- {key_label.lower()} table is empty)_"
    lines = [f"| {key_label} | {value_label} |", "|---|---|"]
    for k, v in sorted(items, key=lambda kv: (-(kv[1] if isinstance(kv[1], (int, float)) else 0), str(kv[0]))):
        lines.append(f"| {k} | {v} |")
    return "\n".join(lines)


def build_context(estate) -> dict:
    stats = estate.stats if isinstance(estate.stats, dict) else {}
    graph = estate.graph if isinstance(estate.graph, dict) else {}
    schedules = estate.schedules if isinstance(estate.schedules, dict) else {}
    commands = estate.command_summary if isinstance(estate.command_summary, dict) else {}
    history = estate.history if isinstance(estate.history, dict) else {}
    scores = estate.scores if isinstance(estate.scores, dict) else {}
    architecture = estate.architecture if isinstance(estate.architecture, dict) else {}
    waves = estate.waves if isinstance(estate.waves, list) else []

    job_count = sum(len(i.jobs) for i in estate.instances.values())
    box_count = sum(len(i.boxes) for i in estate.instances.values())
    machine_count = sum(len(i.machines) for i in estate.instances.values())

    unknown_jt: set[str] = set()
    unknown_attrs: set[str] = set()
    cond_failures = 0
    unresolved = 0
    for inst in estate.instances.values():
        unknown_jt.update(inst.unknowns.job_types)
        unknown_attrs.update(inst.unknowns.attributes)
        cond_failures += len(inst.unknowns.condition_parse_failures)
        unresolved += len(inst.unknowns.unresolved_refs)

    scheduled = list(schedules.values())
    cron_count = sum(1 for s in scheduled if s.get("cron_expressible"))
    dst_count = sum(1 for s in scheduled if s.get("dst_gap_instants") or s.get("dst_overlap_instants"))

    sizing = architecture.get("sizing", {})
    sizing_summary = {}
    for name, v in sizing.items():
        if isinstance(v, dict) and "value" in v:
            sizing_summary[name] = f"{v['value']} ({v.get('basis', '?')})"

    decisions = architecture.get("decisions", {})
    arch_decisions = {k: v.get("choice") for k, v in decisions.items()}

    wave_summary = {}
    for w in waves:
        label = f"Wave {w.get('wave')}" + (" (pilot)" if w.get("is_pilot") else "")
        wave_summary[label] = f"{len(w.get('units', []))} units, {w.get('total_points')} pts"

    cost = architecture.get("cost_estimate", {})
    cost_range = cost.get("monthly_estimate_range", [None, None])

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "registry_version": registry_mod.registry_version(),
        "schema_version": manifest_mod.SCHEMA_VERSION,
        "instances": sorted(estate.instances),
        "evidence_count": len(estate.evidence),
        "evidence_kinds": sorted({e.kind for e in estate.evidence}),
        "job_count": job_count, "box_count": box_count, "machine_count": machine_count,
        "job_type_histogram": stats.get("job_type_histogram", {}),
        "owner_histogram": stats.get("owner_histogram", {}),
        "attribute_family_histogram": stats.get("attribute_family_histogram", {}),
        "history_available": bool(history.get("job_stats")),
        "history_run_count": history.get("run_count", 0),
        "dead_job_count": len(history.get("dead_job_candidates", [])),
        "dead_job_trusted": scores.get("estate", {}).get("dead_job_detection_trusted", True),
        "history_coverage_pct": f"{scores.get('estate', {}).get('history_coverage_ratio', 0):.0%}",
        "manual_intervention_total": history.get("manual_intervention", {}).get("total", 0),
        "sla_breach_count": len(history.get("sla_breaches", [])),
        "unknown_job_types": sorted(unknown_jt), "unknown_attributes": sorted(unknown_attrs),
        "condition_parse_failure_count": cond_failures, "unresolved_ref_count": unresolved,
        "graph_node_count": graph.get("node_count", 0), "graph_edge_count": graph.get("edge_count", 0),
        "graph_cycle_count": len(graph.get("cycles", [])),
        "graph_longest_chain": graph.get("longest_chain_length", 0),
        "graph_cross_box_count": graph.get("cross_box_condition_edge_count", 0),
        "graph_cross_instance_count": graph.get("cross_instance_edge_count", 0),
        "graph_hidden_count": graph.get("hidden_control_flow_edge_count", 0),
        "interpreter_histogram": commands.get("interpreters", {}),
        "os_hint_histogram": commands.get("os_hints", {}),
        "credential_hit_total": commands.get("credential_hit_total", 0),
        "template_cluster_count": len(commands.get("template_clusters", [])),
        "scheduled_job_count": len(scheduled),
        "cron_expressible_count": cron_count,
        "cron_expressible_pct": f"{(cron_count / len(scheduled)):.0%}" if scheduled else "n/a",
        "dst_sensitive_count": dst_count,
        "by_disposition": scores.get("estate", {}).get("by_disposition", {}),
        "effort_points": scores.get("estate", {}).get("effort_points", 0),
        "effort_days_range": scores.get("estate", {}).get("effort_days_range", [0, 0]),
        "tooling_hint": scores.get("estate", {}).get("tooling_hint", "unknown"),
        "architecture_decisions": arch_decisions,
        "sizing_summary": sizing_summary,
        "cost_estimate_range": cost_range,
        "cost_currency": cost.get("currency", "USD"),
        "cost_basis_note": cost.get("basis", "not yet estimated"),
        "wave_summary": wave_summary,
        "risk_flags": scores.get("estate", {}).get("by_flag", {}),
        "evidence_table": {e.path: e.sha256[:12] for e in estate.evidence},
    }


def render_draft(estate, out: Path) -> str:
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(str(_TEMPLATE_DIR)), trim_blocks=True)
    env.globals["table"] = _table_global
    template = env.get_template("assessment_report.md.j2")
    context = build_context(estate)
    return template.render(**context)


def validate_final(text: str) -> tuple[list[str], list[str]]:
    """Returns (blocking_problems, non_blocking_warnings)."""
    problems = []
    for m in _HUMAN_RE.finditer(text):
        line_no = text.count("\n", 0, m.start()) + 1
        problems.append(f"line {line_no}: unfilled HUMAN: placeholder")
    for m in _EMPTY_MARKER_RE.finditer(text):
        # a G:empty marker is OK only if a WAIVED comment appears within the same paragraph
        window = text[m.end():m.end() + 300]
        if not _WAIVED_RE.search(window):
            problems.append(f"empty G section {m.group(1)!r} has no <!-- WAIVED: reason --> comment")
    # The specificity/echo checks are only meaningful once every HUMAN:/empty-G problem above is
    # clear -- otherwise an unfilled placeholder's own prompt text gets flagged redundantly.
    warnings: list[str] = []
    if not problems:
        problems.extend(check_estate_specificity(text))
        echo_problems, echo_warnings = check_knowledge_echo(text)
        problems.extend(echo_problems)
        warnings.extend(echo_warnings)
    return problems, warnings


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", type=Path, default=None, help="required for --draft")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--docx", type=Path, default=None)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--draft", action="store_true")
    mode.add_argument("--lint", action="store_true",
                       help="advisory checks against the current --out file; always exits 0")
    mode.add_argument("--final", action="store_true")
    args = ap.parse_args(argv)

    if args.draft:
        if not args.manifest or not args.manifest.exists():
            print("error: --draft requires --manifest pointing at a valid estate_manifest.json", file=sys.stderr)
            return 1
        estate = manifest_mod.from_json(args.manifest)
        text = render_draft(estate, args.out)
        args.out.write_text(text)
        print(f"wrote draft {args.out} -- fill every HUMAN: placeholder before --final", file=sys.stderr)
    elif args.lint:
        if not args.out.exists():
            print(f"error: {args.out} not found -- run --draft first", file=sys.stderr)
            return 1
        text = args.out.read_text()
        specificity = check_estate_specificity(text)
        echo_problems, echo_warnings = check_knowledge_echo(text)
        findings = specificity + echo_problems + echo_warnings
        if findings:
            print(f"--lint: {len(findings)} finding(s) in {args.out} (advisory, not blocking):", file=sys.stderr)
            for f in findings[:50]:
                print(f"  {f}", file=sys.stderr)
        else:
            print(f"--lint: no findings in {args.out}", file=sys.stderr)
        return 0
    else:
        if not args.out.exists():
            print(f"error: {args.out} not found -- run --draft first", file=sys.stderr)
            return 1
        text = args.out.read_text()
        problems, warnings = validate_final(text)
        if problems:
            print(f"NOT FINAL -- {len(problems)} problem(s) in {args.out}:", file=sys.stderr)
            for p in problems[:30]:
                print(f"  {p}", file=sys.stderr)
            return 1
        if warnings:
            print(f"{args.out} is final-ready, but {len(warnings)} warning(s) worth a human look:", file=sys.stderr)
            for w in warnings[:30]:
                print(f"  {w}", file=sys.stderr)
        print(f"{args.out} is final-ready: no unfilled HUMAN: placeholders, no un-waived empty "
              f"sections, no missing-estate-signal or near-verbatim-echo H sections", file=sys.stderr)

    if args.docx:
        if shutil.which("pandoc"):
            subprocess.run(["pandoc", str(args.out), "-o", str(args.docx)], check=True)
            print(f"wrote {args.docx} via pandoc", file=sys.stderr)
        else:
            print("warning: pandoc not found -- Markdown only, no DOCX produced "
                  "(documented dependency, see SKILL.md)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
