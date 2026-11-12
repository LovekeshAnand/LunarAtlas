# Changelog

All notable changes to LunarAtlas are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.1.0] — 2026-10-28 — revision for the SoftwareX resubmission

### Fixed
- Stage 2: plasma acquisitions without a preceding background are excluded from cleaned output
  (previously stored unsubtracted); clip fraction now counts channels negative *before* clamping
  (`Clip_Fraction`, previously the share of zeros after clamping); paired background row recorded.
- Stage 7 ingestion: no longer drops every table (including `app_users`, `api_keys`) on each run;
  schema creation is idempotent; raw plasma classified with the same `(F=0, L=1)` rule as stage 2
  (the old `L=1 or Laser Energy>0` rule mislabelled 35 background rows and shifted raw IDs);
  raw directory configurable (default `datasets/uploads`); `background_subtracted`,
  `background_row`, `clip_fraction` stored in `measurement_clean`; NIST seed not duplicated.
- `/api/v1/cache/clear` now clears the keys the server writes (`lunaratlas_v2:*`; it previously matched
  `lunaratlas:*` and deleted nothing) and requires the `X-Admin-Token` header to equal the new
  `CACHE_CLEAR_TOKEN` setting (endpoint disabled when unset).

### Added
- `revision_v2/`: archive audit (label checksums, counts), determinism run, isolated ingestion
  check, analysis, figures, local benchmark; `tests/test_ingestion_db.py`; step-2 regression tests.
- `revision_v2/`: web-viewer downsampling evaluation with the client's own TypeScript; null-model
  summary table; reversible database migration tool (`migrate_db.py`) and its rehearsal; clean-checkout
  reproduction test; WAN benchmark of the public deployment.
- `/api/v1/measurements` returns `background_subtracted`, `background_row` and `clip_fraction`.
- `revision_v2/migrate_schema_swap.py`: migration for hosted databases that cannot be renamed
  (schema swap in one transaction, grants/RLS carried over); used for the production migration
  (`revision_v2/outputs/migration_production/`).

### Changed
- Web viewer: denoise option "None (L2 Clean)" relabelled "None (L1-processed)".

### Deployment
- Public database migrated to the corrected records on 2026-10-28 (613 cleaned acquisitions,
  230 products), verified before and after the swap; application data unchanged.

---

## [1.0.0] — 2025-08-23

### Initial Public Release

This is the first public, citable release of LunarAtlas, archived at
[Zenodo version DOI: 10.5281/zenodo.20771542; concept DOI for all versions: 10.5281/zenodo.20771541].

#### Pipeline (Steps 1–8)

**Added**
- `step1_structure_study.py` — PDS4 directory scanner with strict ISRO naming
  regex (`ch3_lib_\d{3}_\d{8}T\d{6}_\d{2}_l1`), generates `study_summary.json`
- `step2_process_l1_data.py` — Core L1 processor: XML metadata extraction,
  temporal background-plasma pairing via `Force Reset Status` / `Laser Fire Status`
  flags, background subtraction, physical clamping `max(0, I_diff)`, and
  long-form CSV output
- `step3_graph_plotting.py` — Publication-quality (200 DPI) NIST overlay plots
  for all cleaned observations
- `step4_nist_verification_logs.py` — Peak detection with 150-count threshold;
  NIST ASD cross-reference with 0.5 nm offset tolerance; per-observation
  verification log CSVs
- `step5_md5_checksums.py` — MD5 digital signature manifest for all
  processed files
- `step6_segregate_data_folders.py` — Replication of ISRO PDS4 folder hierarchy
  in the processed output directory
- `optional_db_ingestion.py` — Batch PostgreSQL ingestion using `execute_batch`
  with `page_size=5000` for high-throughput spectral data loading
- `optional_data_verification.py` — End-to-end audit: MD5 recalculation against
  database-stored checksums
- `run_pipeline.ps1` / `run_pipeline.sh` — One-command pipeline orchestrators

#### API Server

**Added**
- FastAPI REST server with endpoints:
  - `GET /api/v1/health` — liveness check for database and Redis
  - `GET /api/v1/context` — lists all available observations
  - `GET /api/v1/measurements` — lists measurements per observation
  - `GET /api/v1/spectrum` — spectral data with LTTB downsampling
  - `GET /api/v1/nist/lines` — NIST reference line lookup
  - `POST /api/v1/cache/clear` — Redis cache management
- Vectorized LTTB downsampling (`downsampling.py`) with:
  - Index-space bucket formulation: `N(k) = min(2094, 2094 × 2^(-k))`
  - NIST Peak-Union Lock: `P_final = LTTB(data) ∪ Peaks_NIST(data)`
  - 100% target element peak retention guarantee
- Redis caching layer with configurable TTL

#### Visualization Client

**Added**
- React + TypeScript SPA with Recharts spectral viewer
- Web Worker (`downsampleWorker.ts`) for off-main-thread LTTB processing
- Zoom-responsive rendering with discrete zoom levels (k = 0–5)
- `variancePeak` integrity check (detects if downsampling clips the
  highest-intensity peak)
- NIST reference line overlay with element labels

#### Infrastructure

**Added**
- `Dockerfile` — multi-stage container build for server
- `CITATION.cff` — machine-readable citation metadata (CFF v1.2.0)
- `DATA_AVAILABILITY.md` — Elsevier-compliant data availability statement
- `CONTRIBUTING.md` — community contribution guide
- `pytest` test suite for core LTTB and bucket-size functions

---

## [Unreleased]

Changes in progress that have not yet been tagged as a release.

### Planned
- SHA-256 upgrade for MD5 manifest (FIPS compliance)
- Automated CI via GitHub Actions
- Mendeley Data archive for processed spectral CSV dataset
- Interactive Jupyter notebook tutorial for new users

---

*For the full commit history, see the
[GitHub commit log](https://github.com/[YOUR-GITHUB-USERNAME]/LunarAtlas/commits/main).*
