# Revision v2 — audit, regenerated results, reproduction

Branch `revision/audit-v2`. Nothing here touches the live database, the deployment, or
`datasets/processed` (the earlier output and `datasets/processed_backup_20261020` are kept as they were).

## Inputs (not in Git)

| Path | Content | Needed by |
|---|---|---|
| `datasets/uploads` | local copy of PRADAN `lib-v2` calibrated (301 products, labels created 2024-05-16); per-file checksums in `outputs/archive_audit/input_manifest.csv` | all steps |
| `datasets/processed` | stage-2 output before this revision (compared, not modified) | step 1 |
| `datasets/processed_backup_20261020` | legacy output (779 records) | step 1, step 9 |

## Environment

Python 3.11+ with `requirements` of `core/server` plus pandas, scipy, matplotlib, psycopg2, requests;
Node.js ≥ 22.6 (step 5, runs the client's TypeScript directly); PostgreSQL 18 binaries on `PG_BIN`
(steps 3, 6, 9); LaTeX with `elsarticle` and latexmk (step 10). Versions used: `outputs/benchmark/environment.json`,
`outputs/clean_checkout/environment.txt`.

## Reproduce (from the repository root)

| Step | Command | Output |
|---|---|---|
| 1 Archive audit | `python revision_v2/audit_archive.py` | `outputs/archive_audit/` |
| 2 Process twice, compare | `python revision_v2/run_determinism.py` | `processed_run1/`, `processed_run2/`, `outputs/determinism/` |
| 3 Isolated ingestion (throwaway cluster, port 55432) | `python revision_v2/run_isolated_ingestion.py` | `outputs/ingestion/` |
| 4 Analysis (all manuscript tables) | `python revision_v2/analysis.py` | `outputs/analysis/` (settings in `settings.json`; null-model summary `D_null_summary.csv`) |
| 5 Web-viewer downsampling (client TypeScript under Node) | `cd revision_v2 && python browser_downsampling.py` | `outputs/analysis/C_browser_viewer*.{csv,json}` |
| 6 Local API benchmark (loopback, throwaway cluster, port 55433/8031) | `python revision_v2/run_local_benchmark.py` | `outputs/benchmark/` |
| 7 Figures | `python revision_v2/figures.py` | `figures/` |
| 8 Tests | `pytest tests -v` (+ `LUNARATLAS_TEST_DB_URL=<disposable db>` for the DB test) | `outputs/tests/` |
| 9 Migration rehearsal (throwaway cluster, port 55435) | `cd revision_v2 && python rehearse_migration.py` | `outputs/migration_rehearsal/` |
| 10 Paper + supplement | `cd revision_v2/paper && latexmk -pdf paper.tex supplementary.tex` | `paper/paper.pdf`, `paper/supplementary.pdf` |
| — API example (Listing 1, one request to the public demo) | `python revision_v2/api_example.py` | `outputs/api_example/` |

Steps 3–5 and 7 read `processed_run1/` from step 2.

## Production migration (not performed)

`migrate_db.py` is the tool rehearsed in step 9 (`snapshot → backup → build → cutover`, `rollback`,
`verify`). Running it against the production server requires the owner's approval; see
`REVISION_REPORT.md` §6.

See `REVISION_REPORT.md` for the change log, unresolved issues and blocked tasks.
