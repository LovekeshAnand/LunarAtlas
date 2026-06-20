---
title: 'LunarAtlas: From PDS4 Archives to Analysis-Ready Spectra - A Reproducible Infrastructure for Chandrayaan-3 LIBS Level-1 Data'

tags:
  - planetary science
  - LIBS spectroscopy
  - Chandrayaan-3
  - lunar science
  - data pipeline
  - PDS4
  - Python
  - NIST atomic database
  - LTTB downsampling

authors:
  - name: "Lovekesh Anand"
    orcid: "0009-0009-4947-4040"
    affiliation: 1
  - name: "Dua Saeed"
    affiliation: 1

affiliations:
  - name: "Mahavir Swami Institute of Technology, India"
    index: 1

date: 2026-06-20
bibliography: paper.bib
---

# Summary

LunarAtlas is an open-source, end-to-end software infrastructure for
processing and interactive visualization of Laser-Induced Breakdown
Spectroscopy (LIBS) Level-1 calibrated data from ISRO's
Chandrayaan-3 lunar mission. The system addresses a critical barrier
in planetary data science: the raw Chandrayaan-3 LIBS dataset is
published by ISRO in the Planetary Data System 4 (PDS4) format as
wide-format CSV tables pairing plasma emission shots with dark-field
background acquisitions. Transforming these into analysis-ready spectral
records requires resolving the pairing of acquisition types via status
flags, performing background subtraction with physical clamping, and
maintaining a provenance chain traceable back to the original ISRO
observation codes. No existing open tool addresses this pipeline.

LunarAtlas provides an 8-stage reproducible ingestion pipeline
(`Pipeline/step1_*.py` through `step8_*.py`) that produces clean,
long-form spectral CSV records with MD5-verified integrity, a FastAPI
REST API serving the data with multi-zoom Largest Triangle Three Buckets
(LTTB) downsampling augmented by a NIST atomic line Peak-Union Lock, and
a React/TypeScript browser dashboard for interactive exploration.

# Statement of Need

The Chandrayaan-3 LIBS instrument acquired elemental abundance spectra of
the lunar south-pole regolith at 2,094 wavelength channels spanning
220–800 nm. These data are publicly available from the ISRO Planetary
Data Archive (PRADAN) but are published in PDS4 wide-format tables where
plasma shots and dark-field backgrounds are interleaved in a single CSV
identified only by two binary status flag columns (`Force Reset Status`,
`Laser Fire Status`). No documented, open-source tool exists to:

1. Correctly identify and pair plasma-background shot pairs from the flag
   columns.
2. Perform physically-valid background subtraction with non-negativity
   enforcement (`max(0, I_plasma − I_background)`).
3. Cross-reference detected emission peaks against the NIST Atomic Spectra
   Database and produce per-observation element verification logs.
4. Serve the processed data at interactive framerates without sacrificing
   elemental emission line fidelity.

Without such a tool, researchers working on Chandrayaan-3 LIBS data must
independently re-implement the same preprocessing logic, creating a
reproducibility gap in the literature. LunarAtlas closes this gap by
providing a single, well-documented, version-controlled pipeline with
MD5 checksums linking every output file to its exact processing provenance.

# Architecture and Implementation

The LunarAtlas system consists of three integrated layers (Figure 1):

## Layer 1 — Ingestion Pipeline (Steps 1–8)

**Step 1** (`step1_structure_study.py`) scans the ISRO PDS4 directory
hierarchy and constructs a `study_summary.json` inventory of all observation
folders using a strict ISRO naming regex.

**Step 2** (`step2_process_l1_data.py`) is the core processing stage. For
each observation, it:

- Parses the PDS4 XML label to extract instrument metadata
- Identifies plasma shots (`Laser Fire Status = 1, Force Reset Status = 0`)
  and background shots (`Force Reset Status = 1, Laser Fire Status = 0`)
- Pairs each plasma shot with its temporally nearest background shot
- Computes the cleaned intensity: `I_clean(λ) = max(0, I_plasma(λ) − I_bg(λ))`
- Outputs long-form CSV records indexed by `Measurement_ID` and `Wavelength_nm`

**Steps 3–4** render publication-quality spectral plots (300 DPI) and
cross-reference detected peaks against a curated NIST emission line database
(25 reference lines for Mg, Si, Al, Ca, Ti, Fe, Na, H, O) with a 0.5 nm
match tolerance.

**Steps 5–6** generate MD5 checksums for all output files and replicate the
ISRO folder hierarchy in the processed output directory.

**Steps 7–8** ingest the processed records into a PostgreSQL database using
`execute_batch` for throughput, then perform an end-to-end MD5 audit
verifying that every local file matches its database-stored checksum.

## Layer 2 — REST API (FastAPI/Python)

The FastAPI server exposes processed data at sub-500 ms latency. The
`/spectrum` endpoint accepts a `measurement_id`, wavelength range, and
`zoom_level` and returns downsampled spectral data. The downsampling
algorithm is an index-space LTTB formulation:

```
N(k) = min(2094, 2094 × 2^(−k))
```

This is augmented by a NIST Peak-Union Lock:

```
P_final = LTTB(data) ∪ Peaks_NIST(data)
```

Where `Peaks_NIST(data)` is the set of indices nearest to each of the 25
NIST reference wavelengths. This union guarantees 100% retention of target
elemental emission peaks at all zoom levels, regardless of whether the
LTTB triangle-area maximization would have selected them.

Redis caching with a configurable TTL reduces repeated query latency from
~180 ms to ~2 ms.

## Layer 3 — Visualization Dashboard (React/TypeScript)

A browser-based React single-page application renders spectral data from
the API with a Web Worker (`downsampleWorker.ts`) performing additional
client-side LTTB downsampling off the main thread. A `variancePeak`
integrity check detects if downsampling has clipped the highest-intensity
peak in the spectrum, enabling real-time peak retention validation.

# Validation

## Pipeline Correctness

Table 1 shows baseline noise (standard deviation in the spectral dead zone,
700–800 nm) and physical validity (fraction of channels with non-negative
intensity) for five pipeline configurations.

*Table 1: L1 pipeline ablation — averaged over all mission observation pairs.*

| Configuration | Noise (cts) | Validity | Negatives |
|---|---|---|---|
| P-3: Raw L1 (no subtraction) | 67.14 | 100% | 0.0% |
| P-4: Average BG subtraction | 37.97 | 100% | 0.0% |
| P-5: Median BG subtraction | 39.21 | 100% | 0.0% |
| P-2: Paired subtraction, no clamping | 69.02 | 50.4% | **49.6%** |
| **P-1: Full pipeline (LunarAtlas)** | **40.46** | **100%** | **0.0%** |

Without physical clamping (P-2), 49.6% of all spectral channels register
unphysical negative intensities, making the data incompatible with
downstream chemometric analysis. LunarAtlas applies `max(0, I_diff)` to
enforce physical non-negativity while retaining the temporal pairing
benefit of average-BG subtraction.

## Downsampling Fidelity

Table 2 shows peak retention and reconstruction RMSE for four downsampling
strategies at 10% density (209 output points from 2,094 input channels).

*Table 2: Downsampling algorithm comparison at 10% density.*

| Algorithm | Target Peak Retention | RMSE (cts) | Latency (ms) |
|---|---|---|---|
| Uniform decimation | 0.0% | 55.74 | 0.03 |
| Max-binning | 8.33% | 88.99 | 0.54 |
| Standard LTTB (no lock) | 6.25% | 56.68 | 5.36 |
| **LTTB + NIST Peak Lock (LunarAtlas)** | **100.0%** | **56.04** | **0.04** |

The NIST Peak-Union Lock raises target peak retention from a probabilistic
6.25% to a deterministic 100%, at lower latency than standard LTTB alone,
because the O(K) union operation replaces the O(N log B) LTTB inner loop
for the target wavelengths.

# Acknowledgements

The authors acknowledge ISRO for making the Chandrayaan-3 LIBS Level-1
calibrated data publicly available through the PRADAN data portal. NIST
atomic emission line reference data was obtained from the NIST Atomic
Spectra Database (https://physics.nist.gov/asd).

# References

<!-- References are managed in paper.bib — see the bibliography file -->
