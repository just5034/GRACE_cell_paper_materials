# GRACE v27 Benchmark Results — Valid Physics Passes

**Date:** 2026-04-17 (run 17701026)
**Model:** claude-sonnet-4-20250514 (cellular mode)
**Score:** 8/13 Celeritas, 0/3 Opticks
**Events:** 1000 per energy point per configuration

## Included Benchmarks (5 valid-physics passes)

### calorimeter — Hadronic Calorimeter Comparison
- **Task:** Compare steel-scintillator, tungsten-silicon, and lead-LAr sampling calos at 10/30/50 GeV
- **Key results:** W-Si best at 6.1% avg resolution, 90.2% containment. All R^2 > 0.9999.
- **Physics quality:** Valid. Hadronic resolution 5-10% is typical for sampling calorimeters.

### crystal_ecal — Crystal ECAL Material Comparison
- **Task:** Compare PbWO4, BGO, CsI for FCC-ee EM calorimetry at 0.5-20 GeV
- **Key results:** PbWO4 0.92% avg resolution, BGO 1.41%, CsI 5.90%. Ranking correct (shorter X0 = better containment = better resolution).
- **Physics quality:** Valid. Relative ranking matches literature. PbWO4 value slightly optimistic for MC-idealized simulation.

### emcal — EM Calorimeter NLP Benchmark
- **Task:** Optimize homogeneous EM calorimeter with PbWO4/BGO/CsI in box and projective tower geometries
- **Key results:** PbWO4 box best (stochastic 1.41%/sqrt(E)), containment 99.1%, 77-99M hits.
- **Physics quality:** Valid. Stochastic term in plausible range for idealized MC.

### highE_shower — High-Energy Shower Characterization
- **Task:** Characterize EM shower scaling in PbWO4 at 10/50/100 GeV
- **Key results:** Resolution 0.73%->0.47%, shower max follows log(E) with R^2=0.997, containment 99.4% stable, 323M total hits.
- **Physics quality:** Publication-grade. All scaling laws correct, strong statistics.

### shower_containment — Depth Optimization Study
- **Task:** Find minimum PbWO4 depth for <1% leakage at 20 GeV
- **Key results:** 16 X0: 8.2% leakage, 20 X0: 2.9%, 25 X0: 1.03%. Stochastic 1.41%/sqrt(E) at 25 X0, fit R^2=0.9999996.
- **Physics quality:** Publication-grade. Correct depth-leakage physics with meaningful design conclusion.

## Excluded from this package

- **cost_optimized_ecal** — Passed gate but Fe-scintillator has 50% sampling fraction (unrealistic design); 1.43% resolution is correct for THIS geometry but not comparable to real detectors.
- **muon** — Passed gate but iron 0% pion stopping is a silent file-matching bug in analysis code, not real physics.
- **paper_cms_ecal** — Passed gate but resolution inverts at 20 GeV (1.58%) vs expected improvement; calibration issue in analysis.

## Per-benchmark contents

Each folder contains:
- `academic_report.md` — Full generated scientific report
- `benchmark_result.json` — Structured result with task/plan/evaluation
- `scientific_memory.json` — Agent's learning record
- `*.gdml` — Geant4 geometry files (viewable in any GDML viewer)
- `*_events.parquet` — Per-event simulation summary (eventID, totalEdep, nHits)
- `*.png` — Analysis plots

## How to review

1. Start with `academic_report.md` for each benchmark — it's the human-readable output
2. Cross-check key numbers against `benchmark_result.json` evaluation.extracted_metrics
3. GDML files can be visualized in ROOT or DAWN for geometry inspection
4. Parquet files can be opened with `pandas.read_parquet()` for independent analysis
