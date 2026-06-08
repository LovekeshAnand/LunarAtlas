# LunarAtlas

**A Reproducible LIBS Spectral Data Processing and Visualization Infrastructure for Chandrayaan-3**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![CI](https://github.com/LovekeshAnand/LunarAtlas/actions/workflows/ci.yml/badge.svg)](https://github.com/LovekeshAnand/LunarAtlas/actions)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.[YOUR-ZENODO-ID].svg)](https://doi.org/10.5281/zenodo.[YOUR-ZENODO-ID])
[![Elsevier SoftwareX](https://img.shields.io/badge/Paper-SoftwareX-orange)](docs/paper/paper.md)

---

## What Is LunarAtlas?

LunarAtlas is an open-source, end-to-end software infrastructure for the
ingestion, processing, and interactive visualization of Laser-Induced
Breakdown Spectroscopy (LIBS) Level-1 calibrated data from the ISRO
Chandrayaan-3 lunar mission.

It solves a real problem: the raw Chandrayaan-3 LIBS data is published in
PDS4 format by ISRO, but no open tool existed to process it into
analysis-ready spectral records. LunarAtlas provides that tool.

**Key results:**
- `max(0, I_plasma - I_background)` clamping reduces unphysical negative
  channel fraction from 49.6% to 0%
- NIST Peak-Union Lock raises elemental line retention from 6.25% to 100%
  at 10x data reduction
- Full pipeline from raw PDS4 to PostgreSQL-queryable spectra in one command

---

## Quick Start (3 Commands)

```bash
# 1. Clone and install
git clone https://github.com/LovekeshAnand/LunarAtlas.git
cd LunarAtlas
pip install -r requirements.txt

# 2. Run the full ingestion pipeline
#    (set RAW_DIR to your ISRO PRADAN download path)
python Pipeline/step2_process_l1_data.py "D:\ch3_libs\lib-v2\data\calibrated"

# 3. Start the API server and dashboard
cd core/server && uvicorn app.main:app --reload --port 8000
cd core/client && npm install && npm run dev
```

Or use Docker:
```bash
docker build -t lunaratlas .
docker run -p 8000:8000 lunaratlas
```

---

## Repository Structure

```
LunarAtlas/
│
├── Pipeline/                      # 8-stage ingestion pipeline
│   ├── step1_structure_study.py   # PDS4 directory scanner
│   ├── step2_process_l1_data.py   # Core: BG subtraction + clamping (Core contribution)
│   ├── step3_graph_plotting.py    # NIST overlay plots (300 DPI)
│   ├── step4_nist_verification_logs.py  # Peak detection + NIST cross-ref
│   ├── step5_md5_checksums.py     # Digital signature manifest
│   ├── step6_segregate_data_folders.py  # ISRO hierarchy replication
│   ├── step7_db_ingestion.py      # Batch PostgreSQL ingestion
│   ├── step8_data_verification.py # End-to-end MD5 audit
│   └── study_summary.json         # PDS4 inventory (auto-generated)
│
├── core/
│   ├── server/                    # FastAPI REST API
│   │   └── app/core/downsampling.py  # LTTB + NIST Peak-Union Lock (Novel algorithm)
│   └── client/                    # React/TypeScript dashboard
│       └── src/workers/downsampleWorker.ts  # Web Worker LTTB
│
├── tests/
│   ├── test_lttb_algorithm.py     # LTTB unit tests (pytest)
│   └── test_pipeline_processing.py  # Pipeline math unit tests (pytest)
│
├── docs/paper/
│   ├── paper.md                   # SoftwareX submission manuscript
│   └── paper.bib                  # Bibliography
│
├── experiment/                    # Ablation and validation scripts
│   ├── run_full_ablation.py       # Full validation experiment suite
│   └── LunarAtlas_Ablation_Study_Guide.pdf
│
├── Benchmarks/                    # Performance benchmarking
│   └── run_benchmarks.py
│
├── CITATION.cff                   # Machine-readable citation metadata
├── DATA_AVAILABILITY.md           # Data availability statement
├── CHANGELOG.md                   # Version history
├── CONTRIBUTING.md                # Contributor guide
├── requirements.txt               # Python dependencies
├── environment.yml                # Conda environment
└── Dockerfile                     # Container build
```

---

## Ingestion Pipeline Architecture

```mermaid
flowchart TD
    %% Subgraphs for Ingestion Pipeline Stages
    subgraph StageGroup1["Data Discovery & Metadata Extraction (Stages 1 & 2)"]
        direction TB
        Scanner["Directory Scanner<br>(step1_structure_study.py)"]
        Parser["XML Label Parser<br>(step2_process_l1_data.py)"]
    end

    subgraph StageGroup2["Spectral Processing Core (Stage 2)"]
        direction TB
        Pairing["Shot Pairing Engine<br>(Laser Fire & Force Reset flags)"]
        Subtraction["Background Subtractor<br>(I_plasma - I_background)"]
        Clamping["Physical Clamper<br>(np.maximum(I_diff, 0))"]
    end

    subgraph StageGroup3["Validation & Quality Assurance (Stages 3 - 5)"]
        direction TB
        Plotter["Plotting Engine<br>(step3_graph_plotting.py)"]
        Verifier["NIST Peak Verifier<br>(step4_nist_verification_logs.py)"]
        Signer["MD5 Integrity Signer<br>(step5_md5_checksums.py)"]
    end

    subgraph StageGroup4["Archive & Database Ingestion (Stages 6 - 8)"]
        direction TB
        Segregator["ISRO Folder Segregator<br>(step6_segregate_data_folders.py)"]
        DBLoader["DB Bulk Loader<br>(step7_db_ingestion.py)"]
        Auditor["Post-Ingestion Auditor<br>(step8_data_verification.py)"]
    end

    %% Flow connections with clear data/control signals
    RawData["Raw PDS4 Directory"] -->|"Scan files"| Scanner
    Scanner -->|"study_summary.json"| Parser
    Parser -->|"Raw dataframes"| Pairing
    Pairing -->|"Background / Plasma vectors"| Subtraction
    Subtraction -->|"Raw differential spectrum"| Clamping
    Clamping -->|"Normalized spectra"| Plotter
    Clamping -->|"Clean long-form data"| Verifier
    Clamping -->|"Processed L1 CSVs"| Signer
    Signer -->|"Checksum manifest"| Segregator
    Segregator -->|"Structured directories"| DBLoader
    DBLoader -->|"PostgreSQL records"| Auditor
    Auditor -->|"Audit status (PASS/FAIL)"| SuccessMark[Ingestion Verification Success]

    %% Styling
    style StageGroup1 fill:#0b132b,stroke:#00b4d8,stroke-width:2px,color:#ffffff
    style StageGroup2 fill:#1c0f13,stroke:#e63946,stroke-width:2px,color:#ffffff
    style StageGroup3 fill:#1a1c1a,stroke:#ffb703,stroke-width:2px,color:#ffffff
    style StageGroup4 fill:#130e20,stroke:#8338ec,stroke-width:2px,color:#ffffff

    classDef default fill:#1d2436,stroke:#4a5568,stroke-width:1px,color:#f7fafc;
```

---

## Software Architecture & Control Flow

```mermaid
flowchart TD
    %% Subgraphs for Subsystems
    subgraph SubClient["Presentation Layer (React Frontend Client)"]
        direction TB
        UIControls["Controls Panel (React UI)<br>- Observation Selector<br>- Wavelength Range [λ_min, λ_max]<br>- Proportion Mode (Ratio)<br>- NIST Element Peak Overlay<br>- LTTB Downsampling Toggle"]
        Worker["Downsample Web Worker<br>(downsampleWorker.ts)"]
        Dashboard["Interactive Spectral Graph<br>(MultiSpectralGraph / amCharts)"]
    end

    subgraph SubBackend["Logic Layer (FastAPI Backend Server)"]
        direction TB
        APIHandler["REST API Handler<br>(GET /api/v1/spectral)"]
        SatCheck["Zoom-Saturation Checker<br>(Wavelength width vs pixel density)"]
        LTTBEngine["Adaptive Downsampler<br>(LTTB + NIST Peak-Union Lock)"]
    end

    subgraph SubStorage["Persistence & Cache Layer"]
        direction TB
        RedisCache["Redis Cache Store<br>(Query & payload caching)"]
        PostgresDB["PostgreSQL Database<br>(Spectral, measurement & metadata tables)"]
    end

    %% Flows indicating control parameters, requests, and datasets
    UIControls -->|"Interactive dashboard inputs"| Dashboard
    UIControls -->|"Downsampling settings & ratio"| Worker
    Dashboard -->|"Zoom / Pan viewport bounds"| APIHandler
    APIHandler -->|"Evaluate resolution constraints"| SatCheck
    SatCheck -->|"Viewport limits & zoom level"| LTTBEngine
    LTTBEngine -->|"Downsampled points (N' <= 150)"| Dashboard
    LTTBEngine -->|"Query raw data"| PostgresDB
    APIHandler -->|"Lookup/cache response payloads"| RedisCache
    Worker -->|"Client-side downsampled paths"| Dashboard

    %% Styling
    style SubClient fill:#0a192f,stroke:#0ea5e9,stroke-width:2px,color:#ffffff
    style SubBackend fill:#1b1912,stroke:#ffb703,stroke-width:2px,color:#ffffff
    style SubStorage fill:#14111c,stroke:#8338ec,stroke-width:2px,color:#ffffff

    classDef default fill:#1d2436,stroke:#4a5568,stroke-width:1px,color:#f7fafc;
```

---

## Running the Tests

```bash
# From the repository root — no database needed
pip install pytest
pytest tests/ -v
```

Expected output:
```
tests/test_pipeline_processing.py::TestBackgroundSubtraction::test_positive_channels_preserved PASSED
tests/test_pipeline_processing.py::TestBackgroundSubtraction::test_negative_channels_clamped_to_zero PASSED
tests/test_pipeline_processing.py::TestAblationConfigs::test_p2_no_clamp_has_negatives PASSED
tests/test_lttb_algorithm.py::TestNISTPeakLock::test_all_target_wavelengths_present PASSED
...
```

---

## Running the Benchmarks

```bash
cd Benchmarks
python run_benchmarks.py
```

Benchmarks a 16,384-point mock LIBS spectrum at 4 reduction levels,
reporting latency and peak preservation accuracy.

---

## Data Availability

Raw data: [ISRO PRADAN Portal](https://pradan.issdc.gov.in/) (free registration)
Processed data + code: [Zenodo DOI: 10.5281/zenodo.[YOUR-ZENODO-ID]](https://doi.org/10.5281/zenodo.[YOUR-ZENODO-ID])

See [`DATA_AVAILABILITY.md`](DATA_AVAILABILITY.md) for the full statement.

---

## Citing LunarAtlas

If you use LunarAtlas in your research, please cite:

```bibtex
@software{lunaratlas2025,
  author    = {Anand, Lovekesh},
  title     = {{LunarAtlas: A Reproducible LIBS Spectral Data Processing
               and Visualization Infrastructure for Chandrayaan-3}},
  year      = {2025},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.[YOUR-ZENODO-ID]},
  url       = {https://github.com/LovekeshAnand/LunarAtlas}
}
```

GitHub also shows a "Cite this repository" button (powered by [`CITATION.cff`](CITATION.cff)).

---

## License

This project is licensed under the **MIT License** — see [`LICENSE`](LICENSE) for details.

---

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for how to report bugs, suggest features,
and submit pull requests.
