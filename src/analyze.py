#!/usr/bin/env python3
"""Normalize a demo cloud inventory and estimate costs from a local rate file."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

REQUIRED = {"provider", "name", "type", "region", "vcpus", "memory_gib", "storage_gib", "hours_per_month"}


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read valid JSON from {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return value


def estimate(resource: dict[str, Any], rates: dict[str, Any]) -> float:
    missing = REQUIRED - resource.keys()
    if missing:
        raise ValueError(f"Resource is missing fields: {', '.join(sorted(missing))}")
    provider = str(resource["provider"]).lower()
    if provider not in rates:
        raise ValueError(f"No price catalogue entry for provider '{provider}'")
    units = [resource[key] for key in ("vcpus", "memory_gib", "storage_gib", "hours_per_month")]
    if any(not isinstance(value, (int, float)) or value < 0 for value in units):
        raise ValueError(f"Resource '{resource['name']}' has a negative or non-numeric quantity")
    price = rates[provider]
    return (
        resource["vcpus"] * price["vcpu_hour"] * resource["hours_per_month"]
        + resource["memory_gib"] * price["memory_gib_hour"] * resource["hours_per_month"]
        + resource["storage_gib"] * price["storage_gib_month"]
    )


def build_report(inventory: dict[str, Any], catalogue: dict[str, Any]) -> dict[str, Any]:
    resources = inventory.get("resources")
    rates = catalogue.get("providers")
    if not isinstance(resources, list) or not isinstance(rates, dict):
        raise ValueError("Inventory must contain a resources list and catalogue must contain providers")
    rows = []
    totals: dict[str, float] = defaultdict(float)
    counts: dict[str, int] = defaultdict(int)
    for resource in resources:
        if not isinstance(resource, dict):
            raise ValueError("Every resource entry must be an object")
        provider = str(resource.get("provider", "")).lower()
        cost = estimate(resource, rates)
        totals[provider] += cost
        counts[provider] += 1
        rows.append({
            "provider": provider,
            "name": resource["name"],
            "type": resource["type"],
            "region": resource["region"],
            "estimated_monthly_cost": round(cost, 2),
            "currency": catalogue.get("currency", "USD"),
            "tags": resource.get("tags", {}),
        })
    return {
        "notice": catalogue.get("notice", "Estimates depend on the supplied rates and assumptions."),
        "currency": catalogue.get("currency", "USD"),
        "providers": [
            {"provider": name, "resource_count": counts[name], "estimated_monthly_cost": round(total, 2)}
            for name, total in sorted(totals.items())
        ],
        "resources": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, default=Path("data/inventory.json"))
    parser.add_argument("--prices", type=Path, default=Path("data/demo-prices.json"))
    parser.add_argument("--hours", type=float, default=None, help="Override hours_per_month for every resource")
    args = parser.parse_args()
    try:
        inventory = load_json(args.inventory)
        catalogue = load_json(args.prices)
        if args.hours is not None:
            if args.hours < 0:
                raise ValueError("--hours cannot be negative")
            for resource in inventory.get("resources", []):
                resource["hours_per_month"] = args.hours
        report = build_report(inventory, catalogue)
    except (ValueError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
