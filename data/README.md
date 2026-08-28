# ArgosFS Autopilot evaluation data

This directory archives the completed non-performance experiments currently used by the manuscript. Results are tied to ArgosFS revision `a52f6d2b5899a806829a5e12cd392d8676ff4034` (`a52f6d2`).

## Raw data

- `raw/autopilot-matrix.jsonl`: 18 file-system-level Autopilot runs, covering six scenarios with three repetitions each.
- `raw/failure-matrix.jsonl`: 30 failure/recovery runs, covering six scenarios with five repetitions each.
- `raw/policy-replay.json`: 100,000 seeded synthetic policy traces (20,000 per cohort), plus 10,000 cooldown checks. The `autopilot` rows call the production Rust risk-memory and drain-decision functions; baseline and ablation rows are harness policies.

## Processed data

Regenerate all derived files with `python3 scripts/summarize_data.py`.

- `processed/autopilot-matrix-summary.csv`: pass counts and median duration by Autopilot scenario.
- `processed/failure-matrix-summary.csv`: pass counts and median duration by failure scenario.
- `processed/policy-replay-summary.csv`: direct counts for every policy and trace cohort.
- `processed/rq1-policy-summary.csv`: compact RQ1 comparison used in the paper.
- `processed/manifest.json`: revision, experiment sizes, raw-file SHA-256 checksums, and scope notes.

The manuscript reports counts directly from these files. In particular, a single transient risk observation causes no drain in the full controller but causes 20,000/20,000 false drains when confirmation is removed. Two consecutive false-positive observations are sufficient to satisfy the current two-observation confirmation rule, so the full controller drains in 20,000/20,000 `double-noise` traces; this limitation is reported rather than hidden. Persistent risk memory is also necessary for the current intermittent-failure trace: removing it reduces pre-failure protection from 20,000/20,000 to 0/20,000.

The attempted Q1 2026 Backblaze replay is intentionally excluded from this data release because its remote ZIP stream terminated after day 62 of 90. No statistic from that incomplete run is used in the manuscript. Performance/RQ3 data are also not included yet because those experiments are still pending.
