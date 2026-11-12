# Revision checks, November 2026 (SoftwareX resubmission, SOFTX-D-26-00895)

Scripts and outputs behind the revised manuscript (`manuscript/main.tex`), points 1–4 of the review.
Bulky temporary data (stage-2 runs, throwaway PostgreSQL cluster, Python venv) live outside the
repository in `D:\lunaratlas_tools\`.

Environment: Python 3.11.9 venv with `core/server/requirements.txt` (pinned); PostgreSQL 18 binaries
for the throwaway cluster; client for the benchmarks = system Python, stdlib only.

| Check (review point) | Command (from repo root) | Output |
|---|---|---|
| Archive count, label MD5/size (1, 2) | `python Benchmarks/revision_2026_11/archive_count.py datasets/uploads` | `outputs/archive_count.txt` |
| Stage 2 twice, byte comparison (2) | `python .../determinism_check.py . datasets/uploads D:\lunaratlas_tools\determinism` | `outputs/determinism_check.txt` |
| Clamped fraction, Table 4 (3) | `python .../clip_stats.py D:\lunaratlas_tools\determinism\run1` | `outputs/clip_stats.txt` |
| Ingest twice into a throwaway DB (2) | `python .../ingest_twice.py . <run1> datasets/uploads postgresql://tester@localhost:55441/lunar_bench` | `outputs/ingest_twice.txt` |
| Tests incl. DB test (2) | `LUNARATLAS_TEST_DB_URL=<throwaway db> pytest tests -q` | `outputs/pytest.txt` |
| Production vs raw, read-only (1, 2) | `python .../verify_prod_vs_raw.py core/server/.env datasets/uploads` | `outputs/verify_prod_vs_raw.txt` |
| WAN benchmark, public deployment (4) | `python -I .../concurrency_bench.py https://apis.lunaratlas.in outputs/wan wan_s1` (then `wan_s2`) | `outputs/wan/` |
| Local loopback benchmark (4) | server: uvicorn, 1 worker, `DB_POOL_SIZE=10`, `DB_MAX_OVERFLOW=20`, Redis off, throwaway DB; client: `concurrency_bench.py http://127.0.0.1:8031 outputs/local local_s1 1,8,16,32,64` (×3) | `outputs/local/` |

Throwaway cluster: `initdb -D D:\lunaratlas_tools\pg -U tester -A trust`, `pg_ctl ... -o "-p 55441"`,
`createdb lunar_bench`, `createdb lunar_test`; deleted after use. The local server is started from a
directory without `.env` so it cannot reach the production database.

Benchmark request (both runs, same as the July 2026 benchmark): `/api/v1/spectrum?measurement_id=FI-20230825-104221-00-3&use_cache=false`
plus `force_raw=true` (1,737 points, default 200–800 nm window) or `zoom_level=4` (130 points).
10 warm-up + 100 measured requests per level, closed loop, 30 s timeout, stop rule >10 % errors.

WAN: 10 Nov 2026, session 1 13:08–13:13 IST, session 2 13:13–13:18 IST, one client (India);
API on Render (GCP us-west1), DB on Supabase (ap-southeast-1). 1 of 1,600 requests timed out
(session 2, k=4, c=16).
| NIST line corroboration, 15 worked-example matches (R6 line ratios) | `python Benchmarks/revision_2026_11/line_corroboration.py datasets/nist_asd_lines datasets/processed/calibrated/20230825/ch3_lib_002_20230825T104221_00_l1/ch3_lib_002_20230825T104221_00_l1_cleaned.csv Benchmarks/table_outputs/table8_nist_verification.csv Benchmarks/table_outputs/revision/line_corroboration` | `Benchmarks/table_outputs/revision/line_corroboration/` |
| Archive-wide checks of co-author claims (tolerance, per-line, per-species Holm, contested, pairs, 132 excluded) | `python -P Benchmarks/revision_2026_11/dua_claims_check.py` | `Benchmarks/table_outputs/revision/dua_claims_check.txt` |
| Re-check: ID 3 tolerance series, O I with 10,000 shifts, analytic per-line null, offset quantisation | `python -P Benchmarks/revision_2026_11/dua_claims_recheck.py` | `Benchmarks/table_outputs/revision/dua_claims_recheck.txt` |
| Wavelength axis vs archive documents (Annexure-I/II, App. Note-2, markers, label audit) | `python -P Benchmarks/revision_2026_11/archive_docs_check.py <ch3_libs/lib-v2> datasets/processed` | `Benchmarks/table_outputs/revision/archive_docs_check.txt` |
| Before/after plots, IDs 1–4 | `python Benchmarks/revision_2026_11/fig_background_subtraction.py datasets/uploads datasets/processed Benchmarks/table_outputs/revision/per_measurement <id>` | `Benchmarks/table_outputs/revision/per_measurement/` |
| Base temperature per product, from the archive's operational table | `python -P Benchmarks/revision_2026_11/base_temperatures.py <ch3_libs/lib-v2> Benchmarks/table_outputs/revision/base_temperatures.csv` | `Benchmarks/table_outputs/revision/base_temperatures.csv` |
| Random-shift and per-species tests after the Annexure-II temperature correction (both axes, both signs) | `python -P Benchmarks/revision_2026_11/temperature_correction_check.py Benchmarks/table_outputs/revision/base_temperatures.csv` | `Benchmarks/table_outputs/revision/temperature_correction_check.txt` |
| Correction sign vs Application Note-2 markers (613 spectra) | `python -P Benchmarks/revision_2026_11/marker_sign_check.py Benchmarks/table_outputs/revision/base_temperatures.csv` | `Benchmarks/table_outputs/revision/marker_sign_check.txt` |
| Line corroboration after temperature and/or instrument-response correction | `python -P Benchmarks/revision_2026_11/corroboration_variants.py <ch3_libs/lib-v2> Benchmarks/table_outputs/revision/line_corroboration_variants` | `Benchmarks/table_outputs/revision/line_corroboration_variants/` |
| Archive-wide downsampling: peak retention and RMSE, 613 spectra, k = 1–5 | `python -P Benchmarks/revision_2026_11/archive_downsampling.py datasets/processed/calibrated Benchmarks/table_outputs/revision/archive_downsampling.csv` | `Benchmarks/table_outputs/revision/archive_downsampling.txt` |
| Re-scoring of the co-author's species tests (pilot, expanded) from her line groups; 89% and 859-pair counts | `python -P Benchmarks/revision_2026_11/verify_dua_species.py <her species_corroboration/outputs>` | `Benchmarks/table_outputs/revision/verify_dua_species.txt` |
| Competitor-aware species test and branching-ratio screen (co-author, ported) | see `Benchmarks/revision_2026_11/species_corroboration/README.md` | `Benchmarks/revision_2026_11/species_corroboration/outputs/` |

NIST ASD line lists for the corroboration check (19 species, 220–800 nm, CSV export): `datasets/nist_asd_lines/`.
| Figure 1: original diagram with three labels corrected (viewer / API / response arrow) | `python -P Benchmarks/revision_2026_11/fig1_original_labels.py` | `publication_figures/fig1_architecture_rev.{pdf,png}` |
