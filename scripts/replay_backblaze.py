#!/usr/bin/env python3
"""Replay Q1 2026 Backblaze SMART snapshots through the ArgosFS risk/controller policy.

The 1.31-GB source archive is intentionally not stored in this repository. Download it
from the URL below, then pass its path with --archive. This scalar implementation uses
only the Python standard library; it favors transparent replay semantics over speed.
"""

import argparse
import csv
import hashlib
import io
import json
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
import zipfile

SOURCE_URL = "https://f001.backblazeb2.com/file/Backblaze-Hard-Drive-Data/data_Q1_2026.zip"
EXPECTED_ARCHIVE_SHA256 = "cad66574292b89bae8ec8370dbb5e90d2e0b45d61341502708df328fdb15ed5c"
ARGOSFS_REVISION = "a52f6d2b5899a806829a5e12cd392d8676ff4034"
METHODS = ("autopilot", "threshold", "no-persistent-memory", "periodic-7")


def rawint(row: dict[str, str], key: str) -> int:
    value = row.get(key, "")
    if not value:
        return 0
    try:
        return max(0, int(float(value)))
    except (ValueError, OverflowError):
        return 0


def observation(row: dict[str, str]) -> tuple[float, bool]:
    realloc = rawint(row, "smart_5_raw")
    pending = rawint(row, "smart_197_raw")
    crc = rawint(row, "smart_199_raw")
    temp = rawint(row, "smart_194_raw")
    if temp < 0 or temp > 100:
        temp = 0
    score = 0.0
    if realloc > 0:
        score += min(realloc / 400.0, 0.25)
    if pending > 0:
        score += min(pending / 100.0, 0.25)
    if crc > 0:
        score += min(crc / 500.0, 0.12)
    if temp > 55:
        score += min((temp - 55.0) / 80.0, 0.10)
    score = min(score, 1.0)
    predicted = score >= 0.65 or pending >= 8
    return score, predicted


class State:
    __slots__ = ("risk_streak", "healthy_streak", "drained")

    def __init__(self) -> None:
        self.risk_streak = 0
        self.healthy_streak = 0
        self.drained: date | None = None


def update_autopilot(state: State, predicted: bool, day: date, score: float, persistent: bool) -> None:
    if state.drained is not None:
        return
    if predicted:
        state.risk_streak += 1
        state.healthy_streak = 0
    else:
        state.healthy_streak += 1
        if state.healthy_streak >= 2 if persistent else True:
            state.risk_streak = 0
    if predicted and (score >= 0.85 or state.risk_streak >= 2):
        state.drained = day


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def evaluate(states: dict[str, defaultdict[str, State]], failure_dates: dict[str, date], end: date) -> dict:
    results = {}
    for method in METHODS:
        drains = {serial: state.drained for serial, state in states[method].items() if state.drained is not None}
        row = {"drains": len(drains)}
        for horizon in (7, 30):
            window = timedelta(days=horizon)
            protected = sum(
                1
                for serial, failday in failure_dates.items()
                if (drain := drains.get(serial)) is not None
                and timedelta(days=1) <= failday - drain <= window
            )
            evaluable = true = false = censored = 0
            for serial, drain in drains.items():
                failday = failure_dates.get(serial)
                if failday is not None and timedelta(days=1) <= failday - drain <= window:
                    evaluable += 1
                    true += 1
                elif drain + window <= end:
                    evaluable += 1
                    false += 1
                else:
                    censored += 1
            row[f"h{horizon}"] = {
                "failures": len(failure_dates),
                "protected_failures": protected,
                "ppr": protected / len(failure_dates) if failure_dates else 0.0,
                "evaluable_drains": evaluable,
                "true_drains": true,
                "false_drains": false,
                "censored_drains": censored,
                "udr": false / evaluable if evaluable else 0.0,
            }
        results[method] = row
    results["reactive"] = {
        "drains": len(failure_dates),
        "h7": {"failures": len(failure_dates), "protected_failures": 0, "ppr": 0.0},
        "h30": {"failures": len(failure_dates), "protected_failures": 0, "ppr": 0.0},
    }
    results["oracle"] = {
        "drains": len(failure_dates),
        "h7": {"failures": len(failure_dates), "protected_failures": len(failure_dates), "ppr": 1.0, "evaluable_drains": len(failure_dates), "true_drains": len(failure_dates), "false_drains": 0, "censored_drains": 0, "udr": 0.0},
        "h30": {"failures": len(failure_dates), "protected_failures": len(failure_dates), "ppr": 1.0, "evaluable_drains": len(failure_dates), "true_drains": len(failure_dates), "false_drains": 0, "censored_drains": 0, "udr": 0.0},
    }
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("data/raw/backblaze-q1-2026.json"))
    parser.add_argument("--skip-checksum", action="store_true")
    args = parser.parse_args()

    if not args.skip_checksum:
        actual = sha256(args.archive)
        if actual != EXPECTED_ARCHIVE_SHA256:
            raise SystemExit(f"archive checksum mismatch: {actual}")

    states = {method: defaultdict(State) for method in METHODS}
    failure_dates: dict[str, date] = {}
    first_seen: dict[str, date] = {}
    last_seen: dict[str, date] = {}
    models: set[str] = set()
    rows = predicted_rows = 0

    with zipfile.ZipFile(args.archive) as archive:
        names = sorted((name for name in archive.namelist() if name.endswith(".csv")), key=lambda n: n.rsplit("/", 1)[-1])
        if len(names) != 90:
            raise SystemExit(f"expected 90 daily CSV files, found {len(names)}")
        for index, name in enumerate(names, 1):
            day = date.fromisoformat(Path(name).stem)
            with archive.open(name) as binary:
                reader = csv.DictReader(io.TextIOWrapper(binary, encoding="utf-8", newline=""))
                for row in reader:
                    rows += 1
                    serial = row.get("serial_number", "")
                    if not serial:
                        continue
                    model = row.get("model", "")
                    if model:
                        models.add(model)
                    first_seen.setdefault(serial, day)
                    last_seen[serial] = day
                    if row.get("failure") == "1":
                        failure_dates.setdefault(serial, day)
                    score, predicted = observation(row)
                    predicted_rows += int(predicted)
                    update_autopilot(states["autopilot"][serial], predicted, day, score, True)
                    update_autopilot(states["no-persistent-memory"][serial], predicted, day, score, False)
                    threshold = states["threshold"][serial]
                    if threshold.drained is None and predicted:
                        threshold.drained = day
                    periodic = states["periodic-7"][serial]
                    if periodic.drained is None and day.toordinal() % 7 == 0 and predicted:
                        periodic.drained = day
            print(f"day={index}/90 date={day} rows={rows} failures={len(failure_dates)}", flush=True)

    end = max(last_seen.values())
    result = {
        "experiment": "backblaze-smart-trace-replay",
        "source": SOURCE_URL,
        "source_archive_sha256": EXPECTED_ARCHIVE_SHA256,
        "argosfs_revision": ARGOSFS_REVISION,
        "period": {"start": min(first_seen.values()).isoformat(), "end": end.isoformat(), "days": len(names)},
        "rows": rows,
        "unique_drives": len(first_seen),
        "models": len(models),
        "failures": len(failure_dates),
        "predicted_rows": predicted_rows,
        "mapping": {
            "smart_5_raw": "reallocated_sectors",
            "smart_197_raw": "pending_sectors",
            "smart_199_raw": "crc_errors",
            "smart_194_raw": "temperature_c when 0..100",
            "unavailable_argosfs_signals": ["io_errors", "latency_ms", "wear_percent", "near_capacity", "disk_status"],
            "same_day_failure_warning_counts_as_proactive": False,
        },
        "results": evaluate(states, failure_dates, end),
        "limitations": [
            "Controller replay uses only SMART fields that map directly to current ArgosFS health counters; unavailable signals are absent.",
            "False-drain metrics use fixed 7-day and 30-day horizons and censor drains without sufficient follow-up.",
            "Daily snapshots do not establish within-day SMART/failure ordering; same-day warnings are conservatively excluded from proactive protection.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
