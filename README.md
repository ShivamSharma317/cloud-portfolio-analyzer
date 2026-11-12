# Cloud Portfolio Analyzer

A small Python CLI that normalizes cloud resource inventories into one schema and estimates monthly infrastructure cost from an editable sample price catalogue. It compares AWS, Azure and GCP demo inventories and emits a JSON report.

## What it demonstrates

- A provider-neutral inventory model for compute, memory and storage.
- Cost estimation using explicit per-unit prices and configurable runtime hours.
- Input validation and a machine-readable output suitable for a later API or dashboard.
- A deliberately offline demo flow: the sample inventories and rates are illustrative; this project does not connect to cloud accounts or use credentials.

## Run

Requires Python 3.10 or newer. From this directory:

```bash
python src/analyze.py --inventory data/inventory.json --prices data/demo-prices.json --hours 730
```

The command prints a provider summary and per-resource estimates as JSON. Replace the inventory and price catalogue with reviewed data before using the estimates for a real decision.

## Cost model

Each resource is estimated as `vCPU × vCPU-hour rate × hours` + `GiB memory × GiB-hour rate × hours` + `GiB storage × GiB-month rate`. The catalogue marks its values as illustrative; actual prices depend on provider, region, discount, usage and service configuration.
