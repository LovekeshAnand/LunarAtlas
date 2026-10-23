# Revision v2 report

Scope: verify the reported results, fix genuine code/manuscript inconsistencies, regenerate tables
and figures from one input version. Manuscript: `revision_v2/paper/paper.tex` → `paper.pdf`, with
`paper.bib` and `response_to_reviewers_v2.md` (moved here from the git-ignored `docs/paper/v2/`; the
previous `docs/paper/paper.tex` / `main.tex` are unchanged).

Status words: **Confirmed** = reproduced from data/code in this revision; **Fixed** = code or text
changed and re-checked; **Unresolved** = known, not fixed.

## 1. Change log (concern → finding → fix → evidence → manuscript location)

| # | Concern | Finding | Fix | Evidence | Manuscript |
|---|---|---|---|---|---|
| 1 | 779/647 vs 745/613 | **Confirmed.** Old output (`processed_backup_20261020`) stored 613 paired + 132 unpaired plasma *unsubtracted* + 34 background frames from 33 background-only products = 779. 647 was never a valid count (779 − 132). Archive has 745 plasma, 613 paired. | Stage 2 already excluded unpaired shots (uncommitted change before this revision); verified, regression-tested | `outputs/archive_audit/summary.json`, `products.csv` | §4.1 "Earlier counts", Table 3 |
| 2 | Source integrity | 1,491/1,582 MD5 matched label as printed; the 91 others are label checksums printed without leading zeros — **all 1,582 match** after padding. Sizes 1,582/1,582, record counts 301/301. Previous "checksum passes 301" compared processed files with their own DB copy (consistency, not source integrity). | Audit script compares with label values | `input_manifest.csv` | §2.2 step 1, Table 3 |
| 3 | Unmatched background | Old pipeline served raw plasma as "cleaned"; current excludes. Quality info (`Background_Subtracted`, clip fraction) was **not** ingested. | Ingestion stores `background_subtracted`, `background_row`, `clip_fraction` | `outputs/ingestion/summary.json` (613/613 populated) | §2.2, §4.1 |
| 4 | Ingestion drops tables | **Confirmed bug**: `ensure_schema_tables_exist` dropped all tables incl. `app_users`, `api_keys` on every run. | Removed DROP; `CREATE … IF NOT EXISTS`; `ALTER … ADD COLUMN IF NOT EXISTS`; NIST seed guarded | second ingestion added 0 rows | §4.1 |
| 5 | Raw/clean ID linkage | **Confirmed bug**: raw plasma rule `L=1 or LaserEnergy>0` counted 35 background rows (Laser Energy 1–4) as plasma → `measurement_raw` IDs shifted, `/spectrum` `raw_plasma` could join the wrong shot. | Same `(F=0,L=1)` rule as stage 2 | SQL recomputation max\|Δ\| = 0.0 over 1,283,622 points; `tests/test_ingestion_db.py` | §2.2 step 3 |
| 6 | Hard-coded raw path | Ingestion read raw files only from `D:\ch3_libs\…` (no longer exists) → raw tables silently empty. | `raw_dir` argument, default `datasets/uploads` | 230/230 raw MD5 stored | — |
| 7 | Determinism | **Confirmed**: two runs byte-identical for 230 cleaned CSV, 230 params, 230 XML; metadata JSON differs only by timestamp; cleaned values identical to `datasets/processed`. | — | `outputs/determinism/summary.json` | §4.1 |
| 8 | Idempotent ingestion | **Confirmed** (after fix 4): 2nd run 0 new rows, 0 duplicate (measurement, λ). | — | `outputs/ingestion/summary.json` | §4.1 |
| 9 | Clip fraction definition | Old: share of zeros after clamping (counts P=B channels). | Pre-clamp negative residuals / 2,094 channels; 256/613 flagged (was 258) | `B_clip_threshold_sensitivity.csv`, test | §2.2 step 6, §4.2, Fig. 3 |
| 10 | 50 % threshold | No evidence it is optimal. 25/50/75 %: 372/256/157 flagged. ρ(clip, mean cleaned) = −0.93 (same residual — expected), ρ(clip, #peaks) = −0.28. | Described as a convention; flagged spectra stored; ID 2 excluded only from worked-example evaluation | `B_clip_vs_quality_measures.csv` | §4.2, Fig. 3 |
| 11 | "Supports minority usable" | Citation used as confirmation of the 42 % figure without evidence | Removed | — | §4.2 |
| 12 | 200 ms pairing | Timestamps 1 s resolution: gaps 0 s (206), 1 s (264), 2–13 s (143); 416 pairs adjacent rows | Text describes stability assumption and measured gaps | `B_pair_gap_distribution.csv` | §2.2 step 5, §4.1 |
| 13 | Archive wavelength axis | **New finding**: single-shot files carry identical counts on a second axis offset −4.96…−11.14 nm from the parent-table axis | Disclosed; parent axis used; sensitivity run | `subfiles.csv`, `D_wavelength_axis_sensitivity.csv` | §4.1, §4.4 |
| 14 | Noise √2 argument | Unequal variances → independence predicts 1.37, not 1.41; covariance (r = 0.085) reproduces 1.31 by identity; window std includes spectral structure | Causal claim (correlated CCD readout, "independent support") removed; statistics descriptive | `A_worked_example_window_560_580.csv` | §4.2, Table 4 |
| 15 | Table 2 "0.5 % negative, 560–580 nm" | 0.5 % is full range; window has 0 % | Corrected | `A_worked_example_ids.csv` | §4.2 |
| 16 | "2–5× background ratios typical" | Unsupported comparison | Removed | — | §4.2 |
| 17 | LTTB+Peaks rule | Production adds nearest channel of *caller targets*; no peak detection. Paper table passed the detected peaks as targets → 100 % retention by construction; 147–167 points vs 130 for others. Fig. 2 used a separate LTTB copy with ceil(1684·2⁻ᵏ). Formula in text said ceil; code floors. | Algorithm/bound rewritten; equal-budget and matched-size comparisons added; Fig. 2 regenerated from the production function | `C_downsampling.csv` | §2.2.1, §4.3, Table 6, Fig. 4 |
| 18 | Penalty "4.9–13.0 %" | At equal 130-pt budget: +9.0–22.0 a.u. (11.7–31.0 %) | Updated | `C_downsampling.csv` | Abstract, §4.3 |
| 19 | Web viewer | Client downsamples in a browser Web Worker (paper said client does no reduction). The 47.5–61.9 % figure is the **server** function with the **24-line analysis list** on 220–800 nm at T = 130, not the viewer. The viewer as configured: TypeScript `lttb`, all 2,094 channels (164.35–878.26 nm), ratio 0.1 → T = 209, targets = 32-line `ELEMENT_PEAKS` (`spectralUtils.ts`) → 237–239 points, 55.9–71.4 % of peaks (LTTB alone 50.8–69.0 %). TypeScript and Python return identical channels in 24/24 configurations. | Text and Table 6 split into server/viewer blocks; viewer run with its own code | `browser_downsampling.py`, `browser_lttb.mjs`, `C_browser_viewer.csv` | §2.1, §2.2.1, §4.3, Table 6 |
| 20 | NIST counts | **Reproduced**: 42/59/73 peaks, 2/8/5 coincidences. Code uses `<` 0.5 nm (paper said ≤). | Text says `<`; per-peak table with signed offsets, prominence, references within 0.5 and 1.1 nm | `D_per_line_candidates.csv` | §2.2.2, §4.4, Table 7 |
| 21 | Random-shift test | Audited: common shift, \|s\|~U(2,20), random sign, peaks counted once; boundary irrelevant here (no line leaves 220–800 nm). Draw counts differ by test (see table below); archive draws apply one shift to all spectra and sum counts. **Archive 0.096 (not significant)**. "Makes the test conservative" was asserted without support. | Draw counts and seeds moved into `settings.json`; `D_null_summary.csv` written by `analysis.py` (all earlier outputs reproduced byte-identically); "conservative" sentence removed | `D_null_summary.csv`, Fig. 6 | §4.4, Table 7, Abstract |
| 22 | Selective near-matches | "H I 0.81 nm near-match" singled out; Al I 309.27, Si I 390.55, Al I 396.15 equally close; "five sub-threshold lines" not reproducible from any defined rule | All near-misses listed; unreproducible claim dropped | — | §4.4 |
| 23 | Blend labels | Labels now list every reference within 1.1 nm with "?"; text says label ≠ all present | — | Fig. 5 | §4.4 |
| 24 | Resolution | 0.34 nm is label spacing; < 1.1 nm FWHM treated as upper bound | Text | — | §1 |
| 25 | Auth claim | `/api/v1/spectrum` and `/api/v1/cache/clear` are unauthenticated in code; only `/public/*` use key + rate limit | Text corrected (code not changed — see U4) | `core/server/app/api/v1/endpoints.py` | §2.1 |
| 26 | Testing claim | `test_pipeline_processing.py` tests helpers defined in the test file, not the pipeline; MD5/reshape/flag parsing not covered | Text describes the actual coverage; new tests exercise the real processor and ingestion | `outputs/tests/pytest_all.log` | §2.3 |
| 27 | "L1-derived" | Outputs described as L1-derived, not Level-2 | Text | — | Abstract, §2.2, Conclusions |
| 28 | API benchmarks | See §3 | Local bypassed-cache concurrency sweep added | `outputs/benchmark/` | §4.5, Table 8 |
| 29 | Quality fields "served" | No endpoint returns `clip_fraction`/`background_row`/`background_subtracted` (checked every SELECT and response schema) | Text: stored in DB and `_params.csv`, not yet returned by the API | `core/server/app/api/v1/*.py`, `app/schemas/spectral.py` | §4.2, Limitations, U5 |
| 30 | 24- vs viewer list | Table row called "web-viewer configuration" was the server function + 24-line analysis list | Relabelled; viewer evaluated with its own TypeScript, 32-line list, 2,094 ch, T = 209 | `C_browser_viewer.csv` | §2.2.1, §4.3, Table 6 |
| 31 | Null-model draw counts | 10,000 / 1,000 / 300 draws in different tests; archive design not stated; "conservative" unsupported | One table (N, observed, mean, k, p) used in paper, report, response; archive = common shift, summed counts; sentence removed | `D_null_summary.csv`, `settings.json` | §4.4, Table 7 |
| 32 | Equal-budget variant | Construction not documented | Defined as an evaluation-only variant (budget reduction, duplicates, mandatory ends, 129–130, \|P\| ≥ T case) | `analysis.py` `section_c` | §2.2.1, Table 6 |
| 33 | API example | Listing lacked timeout/error handling; runnability unverified | Verified on the public endpoint (legacy DB): ID exists, keys present, values equal revision on 2,094 channels; timeout + `raise_for_status()`; file `api_example.py` | `outputs/api_example/` | §3, Listing 1 |
| 34 | Product categories | "background-only / no paired plasma" overlapped by wording | Verified disjoint (230+33+38 = 301); third label "plasma, none with a preceding background" + footnote (34 without background, 4 with background only after the last plasma) | `products.csv`, `rows.csv` | Table 3 |
| 35 | Live DB migration | Re-ingestion alone would not remove stale records and the old code dropped app tables | Reversible build–copy–rename migration rehearsed end to end incl. rollback (§6) | `outputs/migration_rehearsal/summary.json` | §4.1 |
| 36 | Viewer "L2" label | Denoise option labelled "None (L2 Clean)" | "None (L1-processed)" | `DenoiseToggle.tsx` | — |
| 37 | Packaging | Manuscript, bib, figures outside Git | Sources in `revision_v2/paper/`, figures referenced from their generated location; clean-checkout test (§8) | `outputs/clean_checkout/` | — |

### Random-shift null model — authoritative values (`outputs/analysis/D_null_summary.csv`)

| Evaluation | Draws N | Observed | Null mean | Exceedances k | p = (1+k)/(1+N) |
|---|---|---|---|---|---|
| ID 1 | 10,000 | 2 | 1.28 | 3,419 | 0.34 |
| ID 3 | 10,000 | 8 | 2.41 | 0 | 0.0001 |
| ID 4 | 10,000 | 5 | 2.31 | 617 | 0.062 |
| Archive, parent axis, 613 paired | 1,000 | 1,572 | 1,437.1 | 95 | 0.096 |
| Archive, parent axis, clip ≤ 0.5 (357) | 1,000 | 959 | 863.9 | 79 | 0.080 |
| Archive, parent axis, 613 (axis comparison) | 300 | 1,572 | 1,440.0 | 30 | 0.10 |
| Archive, single-shot axis, 613 | 300 | 1,386 | 1,451.8 | 215 | 0.72 |

Worked examples: seed 20261021. Archive: seed 20261022; per draw one common shift for every spectrum,
statistic = sum of per-spectrum matched-peak counts. Axis comparison: first 300 archive draws, same
detected channels labelled with either axis.

## 2. Test and run logs

- `outputs/tests/pytest_all.log` — 33 passed, 1 skipped (DB test needs a disposable DB).
- `outputs/ingestion/pytest_db_rerun.log` — DB test passed against a throwaway cluster
  (first attempt failed because of a wrong expected value in the new test — 1/3 vs 0 — fixed).
- `outputs/determinism/run1.log`, `run2.log`; `outputs/ingestion/ingest_run1.log`, `ingest_run2.log`.
- The new ingestion regression test was not run against the *old* ingestion code (that code also
  drops tables and needs the missing `D:\ch3_libs` path, so it would fail for other reasons too).

## 3. API benchmark

- **Inspected first:** `concurrent_load_benchmark.py` targets the production URL, so it was **not
  run**. `final_benchmarks.py` was not re-run either: it uses the production and remote databases.
- **New script:** `run_local_benchmark.py`.
  - Setup: loopback only, a throwaway PostgreSQL 18 cluster holding the worked-example product,
    and 1 uvicorn worker (venv Python 3.11.9).
  - Cache: Redis absent, so this is the bypassed-cache condition only.
  - Matrix: 3 sessions (fresh server each) × 3 workloads × concurrency 1/4/16/32 × 400 measured
    requests (20 warm-up discarded).
  - Results: **14,400 requests, 0 errors, 0 timeouts.** Throughput plateaus at about 42–58 req/s
    for full spectra and 96–136 req/s for k = 4.
  - Files: `outputs/benchmark/summary.csv`, `raw_latencies.csv`, `environment.json`,
    `server_s*.log`.
- **Found during the benchmark:** on a freshly loaded database without planner statistics, the
  `/spectrum` clean↔raw join runs as a nested loop, taking 422 ms instead of 1.3 ms. Ingestion now
  runs `ANALYZE` at the end (`Pipeline/optional_db_ingestion.py`). The first benchmark attempt,
  run before this fix, was discarded.
- **Earlier July 2026 campaign:**
  - Medians and means reproduce exactly from `latency_results/*.csv`.
  - P95/P99 differ by ≤ 0.2 ms (percentile interpolation method); the recomputed values are now
    in the paper.
  - The "DB index 133× speedup" claim was not re-verified and has been removed from the
    manuscript.

## 4. Unresolved issues

- **U1 Live database/deployment** still holds the old 779-measurement ingestion (incl. unsubtracted
  plasma and background frames served as "clean"); confirmed 2026-10-23 by one read of `/api/v1/context`
  (301 observations, record_count sum 779). A reversible migration is prepared and rehearsed (§6) —
  **applying it needs your approval**; not done.
- **U2 Raw records** are ingested only for products with cleaned output: 156 acquisitions in 71
  products are not in `measurement_raw`. Ingesting them needs observation rows for products without
  cleaned output (ingester restructuring).
- **U3 Archive wavelength axis**: parent vs single-shot axes differ by 5–11 nm; which is correct
  cannot be decided from the archive. Ask ISSDC/PRADAN.
- **U4 Unauthenticated `/api/v1/cache/clear`** and `/api/v1/spectrum`; hard-coded `rate_limit_remaining`
  values (999, 998, …) in public responses. **New:** `clear_pattern` scans `lunaratlas:{pattern}*` but
  keys are written as `lunaratlas_v2:<md5>`, so the endpoint deletes nothing. Not fixed: making it work
  without adding authentication would give anyone a working cache flush; fix both together (your decision).
- **U5 Quality fields not in any API response.** Verified in the code: the response schemas/SELECTs of
  `/api/v1/measurements`, `/api/v1/public/measurements`, `/api/v1/spectrum`, `/api/v1/public/spectra[/{id}]`
  and `/api/v1/export/*` contain none of `clip_fraction`, `background_row`, `background_subtracted`.
  They exist only in `measurement_clean` and the `_params.csv` files. Manuscript §4.2 now says so
  (it previously said "served with their clip fraction"). Exposing them must wait for the migration.
- **U6 Three reference lists.** (a) analysis: 24 lines in 220–800 nm from `step4_nist_verification_logs.py`;
  (b) DB `nist_lines` seed: 33 lines, used by the viewer only for overlays and the validation panel,
  round-number `relative_intensity` of unknown provenance (must not be used for line ratios);
  (c) viewer downsampling targets: 32 lines, `ELEMENT_PEAKS` in `core/client/src/utils/spectralUtils.ts`.
  (Correction: the previous report implied the 33-line seed was the viewer's downsampling list.)
- **U7 NaN-intensity policy**: plasma NaNs are set to 0 before subtraction. No NaN occurs in this
  archive (0 rows), so no result depends on it; a stricter policy is advisable for other archives.
- **U8 CI**: coverage step ends with `|| true`; the DB test is not in CI.
- **U9 Retrieval date** of the raw copy was not recorded (file mtimes are from the copy, labels say
  2024-05-16). The original mount `D:\ch3_libs` has been deleted.
- **U10 Code version**: no new tag/Zenodo release; manuscript C1 says "pending". Commit hash to be
  cited after you tag.
- **U11 AI declaration** now states that Claude drafted revised text and the response letter, reviewed
  code, and wrote/ran the revision scripts and code changes. Please confirm it matches your use of both
  tools and that the "reviewed and edited" attestation is accurate.
- **U12 Length**: the revised paper compiles to 11 pages (previously 7). The current SoftwareX guide for
  authors was not checked — decide what moves to supplementary files.
- **U13 Manuscript in Git**: `.gitignore` keeps `docs/` local. The manuscript sources now live in the
  tracked `revision_v2/paper/` on this local branch (not pushed). If the paper should not be public in
  the repository, leave it out of the push and put it only in the release archive. `docs/api/README.md`
  (data-semantics note) is still git-ignored.
- **U14 Observation count after migration**: the corrected ingestion creates observation rows only for
  the 230 products with paired plasma, so `/api/v1/context` will list 230 instead of 301 observations
  (part of U2).

## 5. Blocked tasks

- Production/WAN latency re-measurement and multi-session WAN tests — need approval (public service).
- Warm-cache benchmarks — Redis not installed and Docker daemon not running on this host.
- Earlier WAN/co-located latency numbers (July 2026) are reported unchanged; they were not re-run.

## 6. Production migration — rehearsed, not applied

Tool: `migrate_db.py` (phases `snapshot`, `backup`, `build`, `cutover`, `rollback`, `verify`). Nothing is
changed in place: corrected data go into `<db>_v2`, the legacy DB is kept as `<db>_legacy`, and both the
swap and the rollback are two `ALTER DATABASE … RENAME` statements. Every table not written by ingestion
(users, API keys, usage log, `alembic_version`, anything else) is copied from the live DB at cutover and
verified by content digest before any rename.

Rehearsal (`rehearse_migration.py`, `outputs/migration_rehearsal/summary.json`), throwaway PostgreSQL 18.1:

| Check | Result |
|---|---|
| Legacy state (git d1f4e42 ingestion on `processed_backup_20261020`) + synthetic users/keys/usage rows | 779 clean, 301 observations (as production reports) |
| Backup: `pg_dump -Fc` restored into a scratch DB; counts and app digests equal | yes (33.6 MB dump) |
| After cutover: clean / points / raw rows | 613 / 1,283,622 / 1,125 |
| Stale clean records (in DB, not in processed files) | 0 |
| Not background-subtracted / quality fields NULL | 0 / 0 |
| Clean ID without raw plasma row / without raw paired-background row | 0 / 0 |
| `max(0, raw P − raw B)` recomputed in SQL vs stored (1,283,622 points) | max abs diff 0.0 |
| Files vs DB (per-measurement point counts and sums) | identical |
| App tables after cutover (digests); next user id | identical; 3 (sequence carried over) |
| Legacy DB after cutover | unchanged |
| Rollback restores the pre-migration snapshot | exactly |
| Second cutover after rollback | all checks pass |
| Timings | legacy build 204 s, backup + restore check 18 s, candidate build 208 s, cutover 1.3 s, rollback 0.1 s |

Repeated ingestion adding zero rows is **not** the evidence for stale-record removal; that is
`only_in_db_stale = 0` on the migrated database.

Proposed production run (each step needs your go-ahead):
1. Announce a window; stop the API (user/key/usage writes must stop before cutover).
2. `snapshot`, `backup` (keep the dump off-host), `build`, `verify` on `<db>_v2`.
3. `cutover`; flush Redis with `redis-cli --scan --pattern 'lunaratlas_v2:*' | xargs -r redis-cli del`
   (`/api/v1/cache/clear` cannot do it, U4); start the API; `verify`; check `/api/v1/context` (230
   observations, U14) and Listing 1.
4. If anything fails: stop the API, `rollback`, flush Redis again, start the API.
5. Drop `<db>_legacy` only after an agreed observation period.

Not rehearsed: the Redis flush (no Redis locally), an API restart against the renamed DB, and whether the
hosting provider allows `CREATE DATABASE` / `ALTER DATABASE … RENAME` (if not, a schema swap would be
needed — not implemented).

## 7. API example (Listing 1)

`api_example.py` is Listing 1, now with `timeout=30` and `raise_for_status()`. It was run once against the
public endpoint on 2026-10-23 (`outputs/api_example/api_example_public.log`): exit 0; keys `data`,
`wavelength_nm` and `intensity` present. `FI-20230825-104221-00-3` follows the `{file_info_id}-{n}`
scheme (`file_info_id = FI-{date}-{time}-{sub}`). Unsmoothed, the live response equals the revision output
on all 2,094 channels (cleaned and `raw_plasma`), because ID 3 is paired in both versions. Five read-only
GETs to the public service in total (example, two identity checks, `/health`, `/context`); no load test.
