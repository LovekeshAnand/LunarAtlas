# Revision v2 — audit, regenerated results, reproduction

Branch `revision/audit-v2`. Nothing here touches the live database, the deployment, or
`datasets/processed` (the earlier output and `datasets/processed_backup_20261020` are kept as they were).

## Reproduce (from the repository root, Python 3.11+, PostgreSQL bin on `PG_BIN` for the DB steps)

| Step | Command | Output |
|---|---|---|
| 1 Archive audit | `python revision_v2/audit_archive.py` | `outputs/archive_audit/` |
| 2 Process twice, compare | `python revision_v2/run_determinism.py` | `processed_run1/`, `processed_run2/`, `outputs/determinism/` |
| 3 Isolated ingestion (throwaway cluster, port 55432) | `python revision_v2/run_isolated_ingestion.py` | `outputs/ingestion/` |
| 4 Analysis (all manuscript tables) | `python revision_v2/analysis.py` | `outputs/analysis/` (settings in `settings.json`) |
| 5 Figures | `python revision_v2/figures.py` | `figures/` |
| 6 Local API benchmark (loopback, throwaway cluster, port 55433/8031) | `python revision_v2/run_local_benchmark.py` | `outputs/benchmark/` |
| 7 Tests | `pytest tests -v` (+ `LUNARATLAS_TEST_DB_URL=<disposable db>` for the DB test) | `outputs/tests/` |
| 8 Paper | `cd docs/paper/v2 && latexmk -pdf paper.tex` | `docs/paper/v2/paper.pdf` |

Input version: `datasets/uploads` (local copy of PRADAN `lib-v2` calibrated, labels created
2024-05-16; per-file checksums in `outputs/archive_audit/input_manifest.csv`).

See `REVISION_REPORT.md` for the change log, unresolved issues and blocked tasks.
