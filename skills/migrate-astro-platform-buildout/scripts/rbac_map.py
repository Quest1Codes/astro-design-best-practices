#!/usr/bin/env python3
"""Parse a CA EEM `safex` policy export XML into (identity, resource class, action) triples and
propose an Astro Organization/Workspace/Deployment role and Team mapping [spec §7.5].

Deterministic: given the same XML file, output is byte-identical.
Reads a customer-collected XML export only; never contacts a live CA EEM or Astro system.

PRACTITIONER JUDGMENT on the exact XML schema this parser targets: the ingested 12.0 PDF corpus
documents the safex EXPORT PROCEDURE [AS p.783-797] but does not include a literal schema/DTD
for the resulting XML (see autosys-reference/reference/security-eem-and-native.md). This parser
is schema-flexible on purpose -- it looks for common identity/resource/action element and
attribute names across a few plausible shapes, rather than assuming one exact schema, and
reports any element it could not classify so nothing is silently skipped. Verify its output
against a real customer export early in an engagement, before trusting the proposal wholesale.

Usage:
    python3 rbac_map.py --safex-export eem_policies.xml --out rbac_proposal.json [--md rbac_proposal.md]
"""
from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Candidate element/attribute names for each field, tried in order -- schema-flexible per the
# module docstring's PRACTITIONER JUDGMENT note.
_IDENTITY_KEYS = ("identity", "principal", "user", "userid", "grantee")
_RESOURCE_KEYS = ("resourceclass", "resource_class", "resource", "resourcename")
_ACTION_KEYS = ("action", "permission", "accesstype", "actions")


def _first_attr(elem: ET.Element, keys: tuple[str, ...]) -> str | None:
    for k in keys:
        for attr_name, attr_val in elem.attrib.items():
            if attr_name.lower() == k:
                return attr_val
        child = elem.find(k) or elem.find(k.capitalize())
        if child is not None and child.text:
            return child.text.strip()
    return None


def parse_safex_xml(path: Path) -> tuple[list[dict], list[str]]:
    tree = ET.parse(path)
    root = tree.getroot()
    triples: list[dict] = []
    unclassified: list[str] = []

    # A "policy"-shaped element is any element with at least 2 of the 3 fields resolvable.
    for elem in root.iter():
        identity = _first_attr(elem, _IDENTITY_KEYS)
        resource = _first_attr(elem, _RESOURCE_KEYS)
        action = _first_attr(elem, _ACTION_KEYS)
        found = sum(1 for x in (identity, resource, action) if x)
        if found >= 2:
            triples.append({"identity": identity, "resource_class": resource, "action": action,
                            "element": elem.tag})
        elif elem.attrib and found == 0 and list(elem) == []:
            # a leaf element with attributes we couldn't classify at all
            unclassified.append(f"<{elem.tag} {dict(elem.attrib)}>")

    return triples, unclassified


def propose_roles(triples: list[dict]) -> dict:
    by_identity: dict[str, list[dict]] = {}
    for t in triples:
        if t["identity"]:
            by_identity.setdefault(t["identity"], []).append(t)

    proposals = []
    # group identities with an identical (resource_class, action) SET into one Team.
    signature_groups: dict[tuple, list[str]] = {}
    for identity, policies in by_identity.items():
        sig = tuple(sorted({(p["resource_class"], p["action"]) for p in policies}))
        signature_groups.setdefault(sig, []).append(identity)

    per_job_acl_flags = []
    for identity, policies in by_identity.items():
        resource_classes = {p["resource_class"] for p in policies if p["resource_class"]}
        # A policy scoped to a single named job (not a class of jobs) has no Astro equivalent --
        # Astro RBAC is Workspace/Deployment-grained, not per-job.
        for p in policies:
            if p["resource_class"] and any(ch.isdigit() for ch in (p["resource_class"] or "")) is False \
                    and p["resource_class"] not in ("ALL", "*", None) and len(resource_classes) > 3:
                per_job_acl_flags.append({"identity": identity, "resource": p["resource_class"],
                                          "note": "possible per-job ACL -- no Astro RBAC equivalent, "
                                                  "review manually"})

    for sig, identities in signature_groups.items():
        scope = "organization" if any("admin" in (a or "").lower() for _, a in sig) else \
            ("workspace" if len(sig) > 3 else "deployment")
        proposals.append({
            "identities": sorted(identities),
            "team_candidate": len(identities) > 1,
            "proposed_scope": scope,
            "policy_signature": [{"resource_class": r, "action": a} for r, a in sig],
        })

    return {
        "role_proposals": proposals,
        "unmapped_per_job_acls": per_job_acl_flags,
        "total_identities": len(by_identity),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--safex-export", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--md", type=Path, default=None)
    args = ap.parse_args(argv)

    if not args.safex_export.exists():
        print(f"error: {args.safex_export} not found", file=sys.stderr)
        return 1

    try:
        triples, unclassified = parse_safex_xml(args.safex_export)
    except ET.ParseError as e:
        print(f"error: {args.safex_export} is not valid XML: {e}", file=sys.stderr)
        return 1

    proposal = propose_roles(triples)
    proposal["raw_triples_found"] = len(triples)
    proposal["unclassified_elements"] = unclassified[:50]

    args.out.write_text(json.dumps(proposal, sort_keys=True, indent=2) + "\n")
    if args.md:
        lines = ["# RBAC proposal", "",
                f"{proposal['total_identities']} identities, {len(proposal['role_proposals'])} "
                f"role/Team group(s) proposed, {len(proposal['unmapped_per_job_acls'])} "
                f"possible per-job ACL(s) with no Astro equivalent.", "",
                "| Identities | Scope | Team candidate |", "|---|---|---|"]
        for p in proposal["role_proposals"]:
            lines.append(f"| {', '.join(p['identities'])} | {p['proposed_scope']} | "
                         f"{p['team_candidate']} |")
        args.md.write_text("\n".join(lines) + "\n")

    print(f"wrote {args.out}: {proposal['total_identities']} identities, "
          f"{len(proposal['role_proposals'])} role group(s), "
          f"{len(proposal['unmapped_per_job_acls'])} unmapped per-job ACL(s), "
          f"{len(unclassified)} unclassified element(s)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
