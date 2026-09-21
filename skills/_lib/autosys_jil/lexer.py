"""JIL tokenizer: raw text -> attribute blocks.

Deterministic; no I/O.

JIL facts encoded here [AS p.2400 "AutoSys Job Information Language"]:
  - A block starts with a subcommand line `insert_job: name` (or update_job, delete_job,
    override_job, insert_machine, insert_resource, insert_xinst, insert_monbro,
    insert_blob/glob, insert_job_type, insert_connectionprofile and their update/delete forms).
  - The header line may carry a second attribute: `insert_job: X   job_type: CMD`.
  - Comments are C-style `/* ... */` (may span lines). `#` is NOT a comment character in JIL.
  - Values may be quoted with double quotes and may contain `:`; unquoted values run to end of line.
  - A trailing backslash continues the value on the next line.
  - `insert_calendar` is accepted for fixtures/hand-written files even though calendars
    are normally managed with `autocal_asc` [AS commands].
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterator

SUBCOMMANDS = {
    "insert_job", "update_job", "delete_job", "override_job",
    "insert_job_type", "update_job_type", "delete_job_type",
    "insert_machine", "update_machine", "delete_machine",
    "insert_resource", "update_resource", "delete_resource",
    "insert_xinst", "update_xinst", "delete_xinst",
    "insert_connectionprofile", "update_connectionprofile", "delete_connectionprofile",
    "insert_monbro", "update_monbro", "delete_monbro",
    "insert_blob", "update_blob", "delete_blob",
    "insert_glob", "update_glob", "delete_glob",
    "insert_calendar",
}

_HEADER_RE = re.compile(r"^\s*([A-Za-z_]+)\s*:\s*(\S+)(.*)$")
_ATTR_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*)$")
_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)


@dataclass(slots=True)
class RawAttr:
    key: str
    raw: str
    line: int


@dataclass(slots=True)
class Block:
    kind: str  # subcommand, or "unknown"
    name: str
    header_line: int
    attrs: list[RawAttr] = field(default_factory=list)
    index: int = 0


def strip_comments(text: str) -> str:
    """Remove /* */ comments while preserving line numbers (replace with same count of newlines)."""
    def repl(m: re.Match) -> str:
        return "\n" * m.group(0).count("\n")
    return _COMMENT_RE.sub(repl, text)


def _unquote(value: str) -> str:
    v = value.strip()
    if len(v) >= 2 and v[0] == '"' and v[-1] == '"':
        return v[1:-1].replace('\\"', '"')
    return v


def _join_continuations(lines: list[str]) -> list[tuple[int, str]]:
    """Merge backslash-continued lines. Returns (original_line_no, text)."""
    out: list[tuple[int, str]] = []
    buf: str | None = None
    buf_line = 0
    for i, line in enumerate(lines, start=1):
        if buf is not None:
            buf += line
        else:
            buf = line
            buf_line = i
        if buf.rstrip().endswith("\\") and not buf.rstrip().endswith("\\\\"):
            buf = buf.rstrip()[:-1]
            continue
        out.append((buf_line, buf))
        buf = None
    if buf is not None:
        out.append((buf_line, buf))
    return out


def tokenize(text: str) -> Iterator[Block]:
    """Yield Blocks in file order. Lines before the first header are ignored."""
    if text.startswith("\ufeff"):
        text = text[1:]
    text = strip_comments(text.replace("\r\n", "\n").replace("\r", "\n"))
    current: Block | None = None
    index = 0
    for lineno, line in _join_continuations(text.split("\n")):
        if not line.strip():
            continue
        m = _HEADER_RE.match(line)
        if m and m.group(1).lower() in SUBCOMMANDS:
            if current is not None:
                yield current
            kind = m.group(1).lower()
            name = _unquote(m.group(2))
            current = Block(kind=kind, name=name, header_line=lineno, index=index)
            index += 1
            rest = m.group(3).strip()
            if rest:
                am = _ATTR_RE.match(rest)
                if am:
                    current.attrs.append(RawAttr(am.group(1).lower(), _unquote(am.group(2)), lineno))
            continue
        # a header-looking line with an unknown subcommand: keep as its own block so nothing is lost
        if m and m.group(1).lower().startswith(("insert_", "update_", "delete_")) and current is None:
            current = Block(kind="unknown", name=_unquote(m.group(2)), header_line=lineno, index=index)
            current.attrs.append(RawAttr("_subcommand", m.group(1).lower(), lineno))
            index += 1
            continue
        if m and m.group(1).lower().startswith(("insert_", "update_", "delete_")) and current is not None \
                and m.group(1).lower() not in SUBCOMMANDS:
            yield current
            current = Block(kind="unknown", name=_unquote(m.group(2)), header_line=lineno, index=index)
            current.attrs.append(RawAttr("_subcommand", m.group(1).lower(), lineno))
            index += 1
            continue
        if current is None:
            continue
        am = _ATTR_RE.match(line)
        if am:
            current.attrs.append(RawAttr(am.group(1).lower(), _unquote(am.group(2)), lineno))
        else:
            # not key: value -- treat as continuation of previous attr's value
            if current.attrs:
                current.attrs[-1].raw += " " + line.strip()
    if current is not None:
        yield current
