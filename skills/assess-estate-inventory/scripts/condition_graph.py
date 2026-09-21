#!/usr/bin/env python3
"""Build the job/box dependency graph and write its metrics to `manifest.graph{}` [spec §6.2].

Deterministic: given the same manifest, output is byte-identical.
Reads/writes local files only; never contacts a live AutoSys or Astro system.

`networkx` is not available in this environment (see `skills/_lib/pyproject.toml`) -- the graph
algorithms below (cycle detection via DFS coloring, strongly-connected components via Tarjan,
longest-chain via DFS memoization, fan-in/out) are implemented directly over a plain adjacency
list rather than depending on it.

Edge types: `condition:<fn>` (a job's `condition:` referencing another job by status function),
`box_membership` (child -> parent box), `hidden:sendevent:<EVENT>` (a `sendevent` call embedded
in a job's command, from `_lib.commands.analyze()` -- plan §11.2's "#1 source of surprise"),
`cross_instance` (a `job^INST` condition reference).

Usage:
    python3 condition_graph.py --manifest estate_manifest.json [--dot graph.dot]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parents[2] / "_lib"
sys.path.insert(0, str(_LIB))

from autosys_jil import commands as commands_mod  # noqa: E402
from autosys_jil import manifest as manifest_mod  # noqa: E402


def _node_id(instance: str, job: str) -> str:
    return f"{instance}:{job}"


def build_edges(estate) -> list[dict]:
    edges: list[dict] = []
    for inst_id, inst in estate.instances.items():
        for job in inst.jobs.values():
            if job.deleted:
                continue
            src = _node_id(inst_id, job.name)

            if job.box_name:
                edges.append({"from": src, "to": _node_id(inst_id, job.box_name), "kind": "box_membership"})

            if job.condition is not None:
                for leaf in job.condition.leaves:
                    ref = getattr(leaf, "ref", None)
                    if ref is None:
                        continue
                    fn = getattr(leaf, "fn", "exitcode")
                    if ref.instance:
                        edges.append({"from": src, "to": _node_id(ref.instance, ref.job),
                                     "kind": "cross_instance"})
                    else:
                        edges.append({"from": src, "to": _node_id(inst_id, ref.job),
                                     "kind": f"condition:{fn}"})

            if job.command:
                analysis = commands_mod.analyze(job.command)
                for edge in analysis.hidden_control_flow:
                    if edge.job:
                        edges.append({"from": src, "to": _node_id(inst_id, edge.job),
                                     "kind": f"hidden:sendevent:{edge.event}"})
    return edges


def _adjacency(edges: list[dict]) -> tuple[dict[str, list[str]], set[str]]:
    adj: dict[str, list[str]] = {}
    nodes: set[str] = set()
    for e in edges:
        adj.setdefault(e["from"], []).append(e["to"])
        nodes.add(e["from"])
        nodes.add(e["to"])
    return adj, nodes


def find_cycles(adj: dict[str, list[str]], nodes: set[str]) -> list[list[str]]:
    """DFS 3-color cycle detection; returns one representative cycle per back-edge found."""
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {n: WHITE for n in nodes}
    stack: list[str] = []
    cycles: list[list[str]] = []

    def dfs(u: str) -> None:
        color[u] = GRAY
        stack.append(u)
        for v in adj.get(u, []):
            if color.get(v, WHITE) == WHITE:
                dfs(v)
            elif color.get(v) == GRAY:
                idx = stack.index(v)
                cycles.append(stack[idx:] + [v])
        stack.pop()
        color[u] = BLACK

    for n in sorted(nodes):
        if color[n] == WHITE:
            dfs(n)
    return cycles


def tarjan_sccs(adj: dict[str, list[str]], nodes: set[str]) -> list[list[str]]:
    """Standard Tarjan SCC algorithm, iterative to avoid recursion-depth issues on large estates."""
    index_counter = [0]
    stack: list[str] = []
    on_stack: set[str] = set()
    indices: dict[str, int] = {}
    lowlink: dict[str, int] = {}
    result: list[list[str]] = []

    for start in sorted(nodes):
        if start in indices:
            continue
        work: list[tuple[str, int]] = [(start, 0)]
        while work:
            v, pi = work[-1]
            if pi == 0:
                indices[v] = lowlink[v] = index_counter[0]
                index_counter[0] += 1
                stack.append(v)
                on_stack.add(v)
            recursed = False
            neighbors = adj.get(v, [])
            i = pi
            while i < len(neighbors):
                w = neighbors[i]
                if w not in indices:
                    work[-1] = (v, i + 1)
                    work.append((w, 0))
                    recursed = True
                    break
                elif w in on_stack:
                    lowlink[v] = min(lowlink[v], indices[w])
                i += 1
            if recursed:
                continue
            work.pop()
            if work:
                parent = work[-1][0]
                lowlink[parent] = min(lowlink[parent], lowlink[v])
            if lowlink[v] == indices[v]:
                scc = []
                while True:
                    w = stack.pop()
                    on_stack.discard(w)
                    scc.append(w)
                    if w == v:
                        break
                result.append(scc)
    return result


def longest_chain(adj: dict[str, list[str]], nodes: set[str]) -> list[str]:
    """Longest simple path by DFS memoization; only valid on the DAG portion (cyclic estates
    still get a best-effort answer -- cycles are already reported separately)."""
    memo: dict[str, list[str]] = {}
    visiting: set[str] = set()

    def dfs(u: str) -> list[str]:
        if u in memo:
            return memo[u]
        if u in visiting:
            return [u]
        visiting.add(u)
        best: list[str] = [u]
        for v in adj.get(u, []):
            candidate = [u] + dfs(v)
            if len(candidate) > len(best):
                best = candidate
        visiting.discard(u)
        memo[u] = best
        return best

    longest: list[str] = []
    for n in sorted(nodes):
        path = dfs(n)
        if len(path) > len(longest):
            longest = path
    return longest


def compute_graph(estate, top_n: int = 10) -> dict:
    edges = build_edges(estate)
    adj, nodes = _adjacency(edges)

    fan_in: dict[str, int] = {n: 0 for n in nodes}
    fan_out: dict[str, int] = {n: 0 for n in nodes}
    for e in edges:
        fan_out[e["from"]] = fan_out.get(e["from"], 0) + 1
        fan_in[e["to"]] = fan_in.get(e["to"], 0) + 1

    cycles = find_cycles(adj, nodes)
    sccs = [s for s in tarjan_sccs(adj, nodes) if len(s) > 1]
    chain = longest_chain(adj, nodes)

    cross_box = [e for e in edges if e["kind"].startswith("condition:")]
    cross_instance = [e for e in edges if e["kind"] == "cross_instance"]
    hidden = [e for e in edges if e["kind"].startswith("hidden:")]

    all_job_names = {_node_id(inst_id, j.name) for inst_id, inst in estate.instances.items()
                     for j in inst.jobs.values()}
    orphan_refs = sorted(n for n in nodes if n not in all_job_names)

    return {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "edges": edges,
        "cycles": cycles,
        "strongly_connected_components": sccs,
        "longest_chain": chain,
        "longest_chain_length": len(chain),
        "fan_in_top": sorted(fan_in.items(), key=lambda kv: -kv[1])[:top_n],
        "fan_out_top": sorted(fan_out.items(), key=lambda kv: -kv[1])[:top_n],
        "cross_box_condition_edge_count": len(cross_box),
        "cross_instance_edge_count": len(cross_instance),
        "hidden_control_flow_edge_count": len(hidden),
        "hidden_control_flow_edges": hidden,
        "orphan_references": orphan_refs,
    }


def render_dot(edges: list[dict]) -> str:
    lines = ["digraph estate {"]
    for e in edges:
        style = ' [style=dashed,color=red]' if e["kind"].startswith("hidden:") else ""
        lines.append(f'  "{e["from"]}" -> "{e["to"]}" [label="{e["kind"]}"]{style};')
    lines.append("}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--dot", type=Path, default=None)
    ap.add_argument("--top-n", type=int, default=10)
    args = ap.parse_args(argv)

    if not args.manifest.exists():
        print(f"error: {args.manifest} not found -- run build_estate_manifest.py first", file=sys.stderr)
        return 1

    # find_cycles()/longest_chain() recurse per graph edge (Tarjan's SCC pass above is
    # iterative specifically to avoid this); a very large or deeply chained estate could
    # exceed the default limit. Real box/condition chains observed so far are shallow
    # (tens, not thousands, of hops) -- this is a pragmatic headroom bump, not a fix for an
    # unbounded estate.
    sys.setrecursionlimit(max(sys.getrecursionlimit(), 10_000))

    estate = manifest_mod.from_json(args.manifest)
    graph = compute_graph(estate, args.top_n)
    estate.graph = graph
    manifest_mod.to_json(estate, args.manifest, tool="condition_graph.py")

    if args.dot:
        args.dot.write_text(render_dot(graph["edges"]))

    print(f"updated {args.manifest}: {graph['node_count']} nodes, {graph['edge_count']} edges, "
          f"{len(graph['cycles'])} cycle(s), {len(graph['strongly_connected_components'])} SCC(s), "
          f"longest chain {graph['longest_chain_length']}, "
          f"{graph['hidden_control_flow_edge_count']} hidden control-flow edge(s)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
