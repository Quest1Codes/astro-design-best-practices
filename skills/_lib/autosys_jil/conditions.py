"""AutoSys `condition:` string parser -> AST.

Deterministic; no I/O.

Grammar [AS p.2435 "condition Attribute -- Define Starting Conditions for a Job"]:

    expr        := term (("AND" | "OR") term)*
    term        := "(" expr ")" | status_fn | exitcode_fn | value_fn
    status_fn   := STATUS "(" jobref ["," lookback] ")"
    STATUS      := success|s | failure|f | done|d | notrunning|n | terminated|t
    exitcode_fn := "exitcode" "(" jobref ["," lookback] ")" op INT
    value_fn    := "VALUE" "(" GLOBAL ")" op literal
    jobref      := JOBNAME ["^" INSTANCE]          (cross-instance / external dependency)
    lookback    := HH "." MM | INT                 (hours.minutes; 0 = current run only)
    op          := "=" | "!=" | "<" | ">" | "<=" | ">="

Documented rules encoded:
  - Function names may be all upper or all lower case, not mixed.
  - AND/OR are case-insensitive; `&` and `|` are accepted as synonyms.
  - A job name containing ':' is escaped with a backslash.
  - A condition on an undefined job evaluates false (parser cannot know; parser records refs).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterator, Union

STATUS_FUNCS = {
    "s": "success", "success": "success",
    "f": "failure", "failure": "failure",
    "d": "done", "done": "done",
    "n": "notrunning", "notrunning": "notrunning",
    "t": "terminated", "terminated": "terminated",
}
OPS = {"=", "!=", "<", ">", "<=", ">="}


class ConditionParseError(ValueError):
    def __init__(self, text: str, pos: int, message: str):
        super().__init__(f"{message} at position {pos} in {text!r}")
        self.text = text
        self.pos = pos
        self.message = message


@dataclass(frozen=True, slots=True)
class JobRef:
    job: str
    instance: str | None = None

    def __str__(self) -> str:
        return f"{self.job}^{self.instance}" if self.instance else self.job


@dataclass(frozen=True, slots=True)
class Status:
    fn: str  # canonical long form
    ref: JobRef
    lookback: str | None = None  # "HH.MM" or "N"

    def to_string(self) -> str:
        lb = f",{self.lookback}" if self.lookback is not None else ""
        return f"{self.fn}({self.ref}{lb})"


@dataclass(frozen=True, slots=True)
class ExitCode:
    ref: JobRef
    op: str
    value: int
    lookback: str | None = None

    def to_string(self) -> str:
        lb = f",{self.lookback}" if self.lookback is not None else ""
        return f"exitcode({self.ref}{lb}){self.op}{self.value}"


@dataclass(frozen=True, slots=True)
class Value:
    global_name: str
    op: str
    literal: str

    def to_string(self) -> str:
        return f"VALUE({self.global_name}){self.op}{self.literal}"


@dataclass(frozen=True, slots=True)
class And:
    children: tuple["Node", ...]

    def to_string(self) -> str:
        return "(" + " AND ".join(c.to_string() for c in self.children) + ")"


@dataclass(frozen=True, slots=True)
class Or:
    children: tuple["Node", ...]

    def to_string(self) -> str:
        return "(" + " OR ".join(c.to_string() for c in self.children) + ")"


Node = Union[Status, ExitCode, Value, And, Or]


@dataclass(slots=True)
class ConditionAST:
    root: Node
    raw: str

    # ---- derived properties -------------------------------------------------
    def iter_nodes(self) -> Iterator[Node]:
        stack: list[Node] = [self.root]
        while stack:
            n = stack.pop()
            yield n
            if isinstance(n, (And, Or)):
                stack.extend(n.children)

    @property
    def leaves(self) -> list[Node]:
        return [n for n in self.iter_nodes() if not isinstance(n, (And, Or))]

    @property
    def functions_used(self) -> list[str]:
        out = set()
        for n in self.leaves:
            if isinstance(n, Status):
                out.add(n.fn)
            elif isinstance(n, ExitCode):
                out.add("exitcode")
            elif isinstance(n, Value):
                out.add("value")
        return sorted(out)

    @property
    def referenced_jobs(self) -> list[str]:
        return sorted({str(n.ref) for n in self.leaves if isinstance(n, (Status, ExitCode))})

    @property
    def referenced_job_names(self) -> list[str]:
        return sorted({n.ref.job for n in self.leaves if isinstance(n, (Status, ExitCode))})

    @property
    def cross_instance_refs(self) -> list[str]:
        return sorted({str(n.ref) for n in self.leaves
                       if isinstance(n, (Status, ExitCode)) and n.ref.instance})

    @property
    def lookbacks(self) -> list[str]:
        return sorted({n.lookback for n in self.leaves
                       if isinstance(n, (Status, ExitCode)) and n.lookback is not None})

    @property
    def global_refs(self) -> list[str]:
        return sorted({n.global_name for n in self.leaves if isinstance(n, Value)})

    @property
    def has_or(self) -> bool:
        return any(isinstance(n, Or) for n in self.iter_nodes())

    @property
    def has_and(self) -> bool:
        return any(isinstance(n, And) for n in self.iter_nodes())

    @property
    def clause_count(self) -> int:
        return len(self.leaves)

    @property
    def depth(self) -> int:
        def d(n: Node) -> int:
            if isinstance(n, (And, Or)):
                return 1 + max(d(c) for c in n.children)
            return 0
        return d(self.root)

    @property
    def shape(self) -> str:
        if self.clause_count <= 1:
            return "single"
        if self.has_or and self.has_and:
            return "nested"
        if self.has_or:
            return "or_present"
        return "and_only"

    def to_string(self) -> str:
        s = self.root.to_string()
        if s.startswith("(") and s.endswith(")") and isinstance(self.root, (And, Or)):
            return s[1:-1]
        return s

    def summary(self) -> dict:
        return {
            "canonical": self.to_string(),
            "shape": self.shape,
            "depth": self.depth,
            "clause_count": self.clause_count,
            "functions_used": self.functions_used,
            "referenced_jobs": self.referenced_jobs,
            "cross_instance_refs": self.cross_instance_refs,
            "lookbacks": self.lookbacks,
            "global_refs": self.global_refs,
        }


# ------------------------------------------------------------------------------ tokenizer

_TOKEN_RE = re.compile(
    r"""
    (?P<ws>\s+)
  | (?P<lparen>\()
  | (?P<rparen>\))
  | (?P<comma>,)
  | (?P<op><=|>=|!=|=|<|>)
  | (?P<andop>\bAND\b|\band\b|&)
  | (?P<orop>\bOR\b|\bor\b|\|)
  | (?P<ident>(?:[^\s(),=<>!&|^\\]|\\.)+)
  | (?P<caret>\^)
    """,
    re.VERBOSE,
)


@dataclass(slots=True)
class _Tok:
    kind: str
    text: str
    pos: int


def _tokenize(text: str) -> list[_Tok]:
    toks: list[_Tok] = []
    pos = 0
    while pos < len(text):
        m = _TOKEN_RE.match(text, pos)
        if not m:
            raise ConditionParseError(text, pos, f"unexpected character {text[pos]!r}")
        kind = m.lastgroup
        if kind != "ws":
            toks.append(_Tok(kind, m.group(0), pos))
        pos = m.end()
    return toks


# ------------------------------------------------------------------------------ parser

class _Parser:
    def __init__(self, text: str):
        self.text = text
        self.toks = _tokenize(text)
        self.i = 0

    def peek(self) -> _Tok | None:
        return self.toks[self.i] if self.i < len(self.toks) else None

    def take(self, kind: str | None = None) -> _Tok:
        t = self.peek()
        if t is None:
            raise ConditionParseError(self.text, len(self.text), f"unexpected end, expected {kind}")
        if kind and t.kind != kind:
            raise ConditionParseError(self.text, t.pos, f"expected {kind}, got {t.text!r}")
        self.i += 1
        return t

    def parse(self) -> Node:
        node = self.expr()
        if self.peek() is not None:
            t = self.peek()
            raise ConditionParseError(self.text, t.pos, f"trailing input {t.text!r}")
        return node

    def expr(self) -> Node:
        # OR has lower precedence than AND (AutoSys evaluates left-to-right without
        # documented precedence; parentheses are the documented way to group [AS p.2435].
        # We use conventional AND-over-OR precedence and record depth for the reviewer.)
        left = self.and_expr()
        items = [left]
        while (t := self.peek()) is not None and t.kind == "orop":
            self.take()
            items.append(self.and_expr())
        return Or(tuple(items)) if len(items) > 1 else left

    def and_expr(self) -> Node:
        left = self.term()
        items = [left]
        while (t := self.peek()) is not None and t.kind == "andop":
            self.take()
            items.append(self.term())
        return And(tuple(items)) if len(items) > 1 else left

    def term(self) -> Node:
        t = self.peek()
        if t is None:
            raise ConditionParseError(self.text, len(self.text), "unexpected end of condition")
        if t.kind == "lparen":
            self.take()
            node = self.expr()
            self.take("rparen")
            return node
        if t.kind != "ident":
            raise ConditionParseError(self.text, t.pos, f"expected function name, got {t.text!r}")
        fn_tok = self.take()
        fn = fn_tok.text
        if fn != fn.lower() and fn != fn.upper():
            raise ConditionParseError(self.text, fn_tok.pos, f"mixed-case function name {fn!r}")
        fnl = fn.lower()
        self.take("lparen")
        if fnl == "value":
            name = self.take("ident").text
            self.take("rparen")
            op = self.take("op").text
            lit = self.take("ident").text
            return Value(name, op, lit)
        ref, lookback = self.jobref_with_lookback()
        self.take("rparen")
        if fnl == "exitcode":
            op = self.take("op").text
            val_tok = self.take("ident")
            if not re.fullmatch(r"-?\d+", val_tok.text):
                raise ConditionParseError(self.text, val_tok.pos, "exitcode value must be an integer")
            return ExitCode(ref, op, int(val_tok.text), lookback)
        if fnl not in STATUS_FUNCS:
            raise ConditionParseError(self.text, fn_tok.pos, f"unknown condition function {fn!r}")
        return Status(STATUS_FUNCS[fnl], ref, lookback)

    def jobref_with_lookback(self) -> tuple[JobRef, str | None]:
        name_tok = self.take("ident")
        job = name_tok.text.replace("\\:", ":")
        instance = None
        if (t := self.peek()) is not None and t.kind == "caret":
            self.take()
            instance = self.take("ident").text
        lookback = None
        if (t := self.peek()) is not None and t.kind == "comma":
            self.take()
            lb = self.take("ident").text
            if not re.fullmatch(r"\d{1,2}\.\d{2}|\d+", lb):
                raise ConditionParseError(self.text, t.pos, f"bad look-back {lb!r} (expected HH.MM or N)")
            lookback = lb
        return JobRef(job, instance), lookback


def parse(text: str) -> ConditionAST:
    """Parse a condition string. Raises ConditionParseError."""
    stripped = text.strip()
    if not stripped:
        raise ConditionParseError(text, 0, "empty condition")
    return ConditionAST(_Parser(stripped).parse(), text)


def try_parse(text: str) -> tuple[ConditionAST | None, str | None]:
    try:
        return parse(text), None
    except ConditionParseError as exc:
        return None, exc.message + f" (pos {exc.pos})"
