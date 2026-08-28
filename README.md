# ArgosFS Autopilot

**Paper:** *ArgosFS Autopilot: Safe Closed-Loop Autonomous Maintenance for Resilient File Systems*

This repository contains the LaTeX source for the ArgosFS Autopilot preprint. The manuscript studies a safety-first file-system controller that turns imperfect device-health observations into bounded scrub, rebalance, and proactive-drain actions.

The draft is complete at the method/design level. It includes:

- problem formulation and explicit safety envelope;
- persistent evidence, confirmation, hysteresis, and cooldown design;
- safe drain, incremental scrub/rebalance, foreground-pressure feedback, and outcome history;
- implementation details and current prototype limitations;
- a related-work comparison spanning autonomic storage, proactive fault tolerance, scrub scheduling, reliability coordination, and maintenance I/O scheduling;
- a frozen RQ1--RQ4 evaluation protocol with baselines, metrics, trace generation, hardware setup, and statistical rules;
- completed RQ1 policy-replay and file-system validation results, with raw and processed data archived under `data/`;
- explicit placeholders only for the still-pending recovery/performance values and result plots.

Completed safety/controller counts are reported only where retained artifacts exist. Risk-exposure and foreground-performance effect sizes remain unclaimed until their corresponding experiment artifacts are produced.

## Build

```bash
make build
```

The PDF is written to `build/paper.pdf`.

For structural and PDF validation:

```bash
make check
```

For an arXiv-ready source bundle after results are filled:

```bash
make dist
```

## Repository layout

```text
paper.tex                 Root document
metadata.tex              Title and author metadata
sections/                 Manuscript sections
figures/                  Method figure sources
config/                   LaTeX packages and commands
tables/                   Design, configuration, and result tables
data/                     Retained raw data, derived summaries, manifest
references.bib             Bibliography
scripts/                   Build, validation, and data-summary utilities
```

## Status

- Repository visibility: public
- Public PDF preview: enabled through GitHub Pages
- Non-result manuscript content: complete draft
- Quantitative results: RQ1/controller validation populated; RQ2/RQ3 performance values remain explicit placeholders
- Scope: current Autopilot CLI on the ArgosFS host-volume backend; block-backend fault behavior is treated separately as substrate validation

## Related implementation

The implementation evaluated by this manuscript is maintained in `fwerkor/ArgosFS`.

## License

Repository infrastructure is derived from `fwerkor/latex-paper-template`. See `LICENSE` for the current license terms.
