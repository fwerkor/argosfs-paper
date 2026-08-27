# ArgosFS Autopilot

**Paper:** *ArgosFS Autopilot: Safe Closed-Loop Autonomous Maintenance for Resilient File Systems*

This repository contains the LaTeX source for the ArgosFS Autopilot preprint. The paper studies how a resilient file system can turn imperfect device-health observations into autonomous maintenance actions without violating redundancy constraints or overwhelming foreground I/O.

The manuscript is organized around:

- persistent risk memory and confirmation/cooldown gates for noisy health signals;
- redundancy-aware and conflict-aware safety checks before mutating maintenance;
- unified observe, scrub, rebalance, and proactive-drain decisions;
- foreground-latency and background-I/O feedback for bounded maintenance;
- evaluation against reactive, periodic, fixed-threshold, and oracle policies;
- trace replay, device-mapper fault injection, mounted workloads, QEMU, and component ablations.

The current version is an initial research scaffold. It describes the implemented mechanism and the evaluation protocol, but does not yet claim final quantitative experimental results.

## Build

```bash
make build
```

The PDF is written to `build/paper.pdf`.

For structural and PDF validation:

```bash
make check
```

For an arXiv-ready source bundle:

```bash
make dist
```

## Repository layout

```text
paper.tex                 Root document
metadata.tex              Title and author metadata
sections/                 Manuscript sections
figures/                  Figure sources
config/                   LaTeX packages and commands
tables/                   Evaluation tables
references.bib             Bibliography
scripts/                   Build and validation utilities
```

## Status

- Repository visibility: public
- Public PDF preview: enabled through GitHub Pages
- Scope of v1: safe closed-loop maintenance in ArgosFS
- Final quantitative evaluation: pending publication experiments

## Related implementation

The implementation evaluated by this manuscript is maintained in `fwerkor/ArgosFS`.

## License

Repository infrastructure is derived from `fwerkor/latex-paper-template`. See `LICENSE` for the current license terms.
