#!/usr/bin/env python3
"""Astro consumption estimate from `manifest.architecture.sizing` [spec §6.4, plan §11.9].

Deterministic: given the same manifest and pricing dimensions file, output is byte-identical.
Reads/writes local files only; never contacts a live AutoSys, Astro, or pricing API.

Output is EXPLICITLY LABELED AN ESTIMATE requiring Astronomer's own quote -- never a firm price.
Never produces a license-cost COMPARISON unless `nfr.autosys_license_cost` is supplied by the
customer (plan §11.9); this script refuses to fabricate an AutoSys-side cost number.

Pricing dimensions (`pricing_dimensions.yaml`) are placeholder figures pending a real, dated
source -- see that file's header. Treat this script's output as a rough order-of-magnitude
range for planning conversations, not a number to put in a contract.

Usage:
    python3 estimate_cost.py --manifest estate_manifest.json [--pricing pricing_dimensions.yaml]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

_LIB = Path(__file__).resolve().parents[2] / "_lib"
sys.path.insert(0, str(_LIB))

from autosys_jil import manifest as manifest_mod  # noqa: E402


def estimate(estate, pricing: dict) -> dict:
    sizing = estate.architecture.get("sizing", {}) if isinstance(estate.architecture, dict) else {}
    worker_fleet = sizing.get("worker_fleet", {}).get("value") or {"min": 1, "max": 1}
    scheduler_tier = sizing.get("scheduler_size", {}).get("value", "small")

    worker_hours_per_month = ((worker_fleet.get("min", 1) + worker_fleet.get("max", 1)) / 2) * 24 * 30
    au_rate = pricing.get("au_hourly_rate", {}).get(scheduler_tier, pricing.get("au_hourly_rate", {}).get("small", 0))
    worker_au_rate = pricing.get("worker_au_hourly_rate", 0)

    low = worker_hours_per_month * worker_au_rate * 0.7 + au_rate * 24 * 30 * 0.7
    high = worker_hours_per_month * worker_au_rate * 1.3 + au_rate * 24 * 30 * 1.3

    result = {
        "monthly_estimate_range": [round(low, 2), round(high, 2)],
        "currency": pricing.get("currency", "USD"),
        "basis": "ESTIMATE ONLY -- requires Astronomer's own quote; pricing_dimensions.yaml is "
                "a placeholder pending a real, dated source",
        "inputs": {"worker_hours_per_month": worker_hours_per_month, "scheduler_tier": scheduler_tier},
        "source_date": pricing.get("source_date"),
        "license_comparison": None,
    }

    license_cost = estate.nfr.get("autosys_license_cost") if isinstance(estate.nfr, dict) else None
    if license_cost:
        result["license_comparison"] = {
            "autosys_license_cost": license_cost,
            "note": "Customer-supplied AutoSys license cost. Comparison is a rough order-of-"
                    "magnitude only -- the two costs are not apples-to-apples (support/ops "
                    "labor differs materially between the two models).",
        }

    return result


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--pricing", type=Path, default=Path(__file__).parent / "pricing_dimensions.yaml")
    args = ap.parse_args(argv)

    if not args.manifest.exists():
        print(f"error: {args.manifest} not found -- run build_estate_manifest.py first", file=sys.stderr)
        return 1
    if not args.pricing.exists():
        print(f"error: {args.pricing} not found", file=sys.stderr)
        return 1

    estate = manifest_mod.from_json(args.manifest)
    pricing = yaml.safe_load(args.pricing.read_text())
    result = estimate(estate, pricing)

    arch = estate.architecture if isinstance(estate.architecture, dict) else {}
    arch["cost_estimate"] = result
    estate.architecture = arch
    manifest_mod.to_json(estate, args.manifest, tool="estimate_cost.py")

    print(f"updated {args.manifest}: monthly estimate {result['monthly_estimate_range']} "
          f"{result['currency']} (ESTIMATE ONLY, pricing dimensions are placeholders)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
