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
# 1. Clone and install dependencies
git clone https://github.com/LovekeshAnand/LunarAtlas.git
cd LunarAtlas
pip install -r requirements.txt

# 2. Run the full ingestion pipeline (using Bash or PowerShell)
cd Pipeline
./run_pipeline.sh      # On Linux/macOS/Git Bash
# OR
.\run_pipeline.ps1     # On Windows PowerShell

# 3. Start the API server and dashboard
# (In separate terminals from the repository root)
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
│   ├── run_pipeline.sh            # Ingestion orchestrator (Bash)
│   ├── run_pipeline.ps1           # Ingestion orchestrator (PowerShell)
│   ├── step1_structure_study.py   # PDS4 directory scanner
│   ├── step2_process_l1_data.py   # Core: BG subtraction + clamping
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

## Ingestion Pipeline

The end-to-end PDS4 LIBS data ingestion pipeline processes raw ISRO files and loads them into PostgreSQL. You can run the entire 8-stage pipeline using either a Bash script or a PowerShell script located in the `Pipeline` directory:

- **Using Bash (Linux/macOS/Git Bash)**:
  ```bash
  cd Pipeline
  chmod +x run_pipeline.sh
  ./run_pipeline.sh
  ```
- **Using PowerShell (Windows)**:
  ```powershell
  cd Pipeline
  .\run_pipeline.ps1
  ```

The scripts will guide you through running all 8 processing stages:
1. **Directory Structure Scanner** (`step1_structure_study.py`)
2. **L1 Ingestion & Processing Core** (`step2_process_l1_data.py`)
3. **Publication-Quality Graph Generation** (`step3_graph_plotting.py`)
4. **NIST peak detection & Verification logs** (`step4_nist_verification_logs.py`)
5. **MD5 digital checksum signatures** (`step5_md5_checksums.py`)
6. **Replicated Folder Segregation** (`step6_segregate_data_folders.py`)
7. **PostgreSQL Database Ingestion** (`step7_db_ingestion.py`)
8. **End-to-End Validation & Audit** (`step8_data_verification.py`)

---

## Ingestion Pipeline Architecture

```mermaid
flowchart LR
    Raw[Raw PDS4 Directory] --> Study[1. Directory Scan & XML Parsing]
    Study --> Process[2. Background Subtraction & Clamping]
    Process --> QA[3. NIST Peak Validation & Checksums]
    QA --> Archive[4. Folder Segregation & DB Ingestion]
    Archive --> DB[(PostgreSQL Database)]

    style Raw fill:#f9fafb,stroke:#d1d5db,stroke-width:1px,color:#374151
    style Study fill:#e0f2fe,stroke:#38bdf8,stroke-width:1px,color:#0369a1
    style Process fill:#e0f2fe,stroke:#38bdf8,stroke-width:1px,color:#0369a1
    style QA fill:#fef3c7,stroke:#f59e0b,stroke-width:1px,color:#78350f
    style Archive fill:#dcfce7,stroke:#22c55e,stroke-width:1px,color:#14532d
    style DB fill:#f3e8ff,stroke:#a855f7,stroke-width:1px,color:#581c87
```

---

## Backend Software & Serving Architecture

This diagram shows how the backend serves processed spectral data efficiently using downsampling, caching, and peak preservation.

```mermaid
flowchart TD
    Client[Web UI / Client] -->|1. Request Range & Downsampling Ratio| Server[FastAPI Server]
    Server -->|2. Check Cache| Cache{Redis Cache}
    
    Cache -->|Cache Hit| Return[3a. Return Downsampled Data]
    Cache -->|Cache Miss| DB[(PostgreSQL Database)]
    
    DB -->|3b. Retrieve Raw High-Res Spectrum| Engine[Downsampling Engine]
    Engine -->|4. Apply LTTB + Peak Preservation| Server
    Server -->|5. Store Result| Cache
    Server -->|6. Return Optimized Spectrum| Client

    style Client fill:#f9fafb,stroke:#d1d5db,stroke-width:1px,color:#374151
    style Server fill:#e0f2fe,stroke:#38bdf8,stroke-width:1px,color:#0369a1
    style Cache fill:#fef3c7,stroke:#f59e0b,stroke-width:1px,color:#78350f
    style DB fill:#f3e8ff,stroke:#a855f7,stroke-width:1px,color:#581c87
    style Engine fill:#dcfce7,stroke:#22c55e,stroke-width:1px,color:#14532d
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
