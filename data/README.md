# ArgosFS Autopilot evaluation data

This directory archives the completed non-performance experiments currently used by the manuscript. Results are tied to ArgosFS revision `a52f6d2b5899a806829a5e12cd392d8676ff4034` (`a52f6d2`).

## Raw data

- `raw/autopilot-matrix.jsonl`: 18 file-system-level Autopilot runs, covering six scenarios with three repetitions each.
- `raw/failure-matrix.jsonl`: 30 failure/recovery runs, covering six scenarios with five repetitions each.
- `raw/policy-replay.json`: 100,000 seeded synthetic policy traces (20,000 per cohort), plus 10,000 cooldown checks. The `autopilot` rows call the production Rust risk-memory and drain-decision functions; baseline and ablation rows are harness policies.
- `raw/backblaze-q1-2026.json`: complete 90-day Q1 2026 Backblaze SMART replay over 30,597,484 drive-day rows, 351,095 unique drives, and 1,030 labeled failures.

## Processed data

Regenerate all derived files with `python3 scripts/summarize_data.py`.

- `processed/autopilot-matrix-summary.csv`: pass counts and median duration by Autopilot scenario.
- `processed/failure-matrix-summary.csv`: pass counts and median duration by failure scenario.
- `processed/policy-replay-summary.csv`: direct counts for every policy and trace cohort.
- `processed/rq1-policy-summary.csv`: compact synthetic RQ1 comparison used in the paper.
- `processed/backblaze-q1-2026-summary.csv`: 7-day and 30-day public-trace protection/non-failure-drain metrics.
- `processed/manifest.json`: revision, experiment sizes, raw-file SHA-256 checksums, and scope notes.

The manuscript reports counts directly from these files. In particular, a single transient risk observation causes no drain in the full controller but causes 20,000/20,000 false drains when confirmation is removed. Two consecutive false-positive observations are sufficient to satisfy the current two-observation confirmation rule, so the full controller drains in 20,000/20,000 `double-noise` traces; this limitation is reported rather than hidden. Persistent risk memory is also necessary for the current intermittent-failure trace: removing it reduces pre-failure protection from 20,000/20,000 to 0/20,000.

The Backblaze replay is now complete. The source archive is 1.31 GB and is not checked into this repository; its SHA-256 is `cad66574292b89bae8ec8370dbb5e90d2e0b45d61341502708df328fdb15ed5c`. Reproduce the raw result with `python3 scripts/replay_backblaze.py --archive /path/to/data_Q1_2026.zip`, then regenerate processed summaries with `python3 scripts/summarize_data.py`. The reported run used a vectorized equivalent for speed and was cross-checked against the scalar replay for the first seven days: predicted-row counts and every per-drive drain date matched for all replayed policies. The earlier incomplete remote-stream attempt is not retained or used.

The public trace is intentionally not tuned to the built-in ArgosFS risk score. At a 30-day horizon, threshold control protects 221/1,030 labeled failures (21.5%) and Autopilot protects 208/1,030 (20.2%). Among drain decisions with sufficient follow-up, 96.2% and 96.4%, respectively, have no labeled failure within 30 days. This negative result is kept because it shows that confirmation cannot compensate for a weakly calibrated predictor. Performance/RQ3 data are still pending.
