# Changelog

All notable changes to LunarAtlas are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] — 2025-08-23

### Initial Public Release

This is the first public, citable release of LunarAtlas, archived at
[Zenodo DOI: 10.5281/zenodo.20771541].

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
- `step7_db_ingestion.py` — Batch PostgreSQL ingestion using `execute_batch`
  with `page_size=5000` for high-throughput spectral data loading
- `step8_data_verification.py` — End-to-end audit: MD5 recalculation against
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
