#!/usr/bin/env python3
"""Regenerate processed summaries for the retained Autopilot evaluation data."""

import csv
import hashlib
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"
REVISION = "a52f6d2b5899a806829a5e12cd392d8676ff4034"
PLATFORM = "Linux-7.0.0-28-generic-x86_64-with-glibc2.39"


def load_jsonl(name: str) -> list[dict]:
    return [json.loads(line) for line in (RAW / name).read_text().splitlines() if line.strip()]


def write_matrix_summary(source: str, destination: str) -> None:
    groups: dict[str, list[dict]] = {}
    for row in load_jsonl(source):
        groups.setdefault(row["scenario"], []).append(row)

    with (OUT / destination).open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["scenario", "runs", "passed", "failed", "pass_rate", "median_duration_sec"])
        for scenario in sorted(groups):
            rows = groups[scenario]
            passed = sum(row["status"] == "passed" for row in rows)
            writer.writerow(
                [
                    scenario,
                    len(rows),
                    passed,
                    len(rows) - passed,
                    f"{passed / len(rows):.6f}",
                    f"{statistics.median(row['duration_sec'] for row in rows):.6f}",
                ]
            )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    write_matrix_summary("autopilot-matrix.jsonl", "autopilot-matrix-summary.csv")
    write_matrix_summary("failure-matrix.jsonl", "failure-matrix-summary.csv")

    replay = json.loads((RAW / "policy-replay.json").read_text())
    with (OUT / "policy-replay-summary.csv").open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["method", "cohort", "traces", "failures", "drains", "false_drains", "protected", "ppr", "udr"])
        for method in sorted(replay["methods"]):
            for cohort in sorted(replay["methods"][method]):
                row = replay["methods"][method][cohort]
                writer.writerow(
                    [
                        method,
                        cohort,
                        row["traces"],
                        row["failures"],
                        row["drains"],
                        row["false_drains"],
                        row["protected"],
                        row["ppr"],
                        row["udr"],
                    ]
                )

    policies = ["reactive", "periodic-2", "periodic-4", "threshold", "autopilot", "oracle"]
    failure_cohorts = ["critical-failure", "intermittent-failure", "sustained-failure"]
    with (OUT / "rq1-policy-summary.csv").open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            [
                "policy",
                "single_noise_false_drains",
                "double_noise_false_drains",
                "protected_failure_traces",
                "failure_traces",
                "protection_rate",
            ]
        )
        for policy in policies:
            rows = replay["methods"][policy]
            protected = sum(rows[cohort]["protected"] for cohort in failure_cohorts)
            failures = sum(rows[cohort]["failures"] for cohort in failure_cohorts)
            writer.writerow(
                [
                    policy,
                    rows["single-noise"]["false_drains"],
                    rows["double-noise"]["false_drains"],
                    protected,
                    failures,
                    f"{protected / failures:.6f}",
                ]
            )

    checksums = {
        str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(RAW.iterdir())
    }
    manifest = {
        "argosfs_revision": REVISION,
        "platform": PLATFORM,
        "completed_datasets": {
            "autopilot-matrix": {"runs": 18, "scenarios": 6},
            "failure-matrix": {"runs": 30, "scenarios": 6},
            "policy-replay": {
                "traces": replay["traces"],
                "per_cohort": replay["per_cohort"],
                "seed": replay["seed"],
                "cooldown_checks": replay["cooldown_checks"],
            },
        },
        "sha256": checksums,
        "notes": [
            "Backblaze Q1 2026 replay is not included because the attempted remote-stream replay terminated before completing all 90 days; no partial result is used in the manuscript."
        ],
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
