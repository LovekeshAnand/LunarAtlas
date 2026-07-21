"""
LunarAtlas Latency Benchmark Suite (v3)
========================================

Changes from v2:
  - REMOVED Tukey's-IQR-fence "clean mean" trimming from latency reporting.
    Latency distributions are expected to be right-skewed (connection
    setup, GC pauses, cold caches, network jitter) — the right tail IS
    the phenomenon being measured, not noise to discard. Reporting a
    trimmed mean next to P99 from the untrimmed set is internally
    inconsistent (P99 says the tail is real; the trimmed mean says it
    isn't) and invites a reviewer to ask which number you actually
    believe. Standard practice for latency reporting is to quote the
    FULL raw distribution: mean, std, median, P95, P99.
  - The IQR fence is still computed, but only as a diagnostic count of
    how many points fall outside it (e.g. to flag a run contaminated by
    a stalled connection). This count is NEVER used to exclude data or
    compute an alternate mean, and is labeled as such everywhere it's
    printed.
  - Warmup-run discarding (20 runs before measurement starts) is
    UNCHANGED — that excludes cold-start effects before steady-state
    begins, which is a legitimate and different thing from trimming
    steady-state data after the fact.

Changes from v1 (carried over into v2/v3):
  - THREE environments instead of two, matching what the paper text actually
    describes (previously the paper conflated "local server + remote DB"
    and "production server + remote DB" under a single ambiguous "WAN"
    label — this version keeps them separate so the numbers can't be
    mislabeled again):
        1. local_colocated       : local server + local/co-located Postgres
        2. local_remote_db       : local server + remote (Supabase) Postgres
                                    -> isolates the pure DB-WAN cost
        3. production_remote_db  : production server + remote Postgres
                                    -> full real-world production stack
  - Paired downsample=true/false requests now fire in RANDOM order each
    iteration (previously always full-then-downsampled, which could bias
    the "downsampling saves time" number via query-plan/connection warm
    effects on the second request of the pair).
  - DB index-vs-seqscan speedup now takes ONE query and forces the planner
    via SET enable_seqscan/enable_indexscan/enable_bitmapscan, reading the
    authoritative "Execution Time:" line from EXPLAIN ANALYZE, repeated
    N times and averaged (previously required two hand-written queries and
    parsed only the first "actual time=" occurrence from a single run).
  - Report generation now loops generically over however many environments
    are configured, instead of hardcoding two environment keys.
  - Report includes an explicit reviewer-facing warning about not mixing
    numbers between environments/labels.

Usage
-----
Edit the CONFIG block below, then:

    pip install requests psycopg2-binary --break-system-packages
    python latency_benchmark_suite_v3.py

Outputs (written to ./latency_results/):
    - raw_<env>_baseline.csv
    - raw_<env>_sweep.csv
    - raw_<env>_downsample_contribution.csv
    - results.json
    - latency_report.txt
"""

import csv
import json
import math
import os
import platform
import random
import re
import socket
import statistics
import subprocess
import time
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

# =============================================================================
# CONFIG — edit this block for your setup
# =============================================================================

OUT_DIR = Path("latency_results")

# Define every environment you want benchmarked with the SAME methodology.
# Leave an entry out (or comment it) if that environment isn't available —
# the report will clearly state which environments were actually measured,
# and will NOT print a number for any environment that wasn't run.
#
# IMPORTANT: these three are intentionally kept separate. Do NOT relabel
# "local_remote_db" as "WAN" in the paper and then also call
# "production_remote_db" the same thing — that is the exact mislabeling
# that produced the contradictory numbers in the current draft
# (Abstract vs Section 4.5 vs Table 9 currently disagree with each other).
ENVIRONMENTS = {
    "local_colocated": {
        "label": "Local server + local/co-located PostgreSQL (true co-located)",
        "base_url": "http://127.0.0.1:8020/api/v1/spectrum",
        "health_url": "http://127.0.0.1:8020/health",
    },
    "local_remote_db": {
        "label": "Local server + remote Supabase PostgreSQL (isolates DB-WAN cost)",
        # Point this at a local server instance whose DB connection string
        # has been pointed at the remote Supabase database (e.g. a second
        # uvicorn process on a different port, or the same process with a
        # different DATABASE_URL env var at startup).
        "base_url": "http://127.0.0.1:8021/api/v1/spectrum",
        "health_url": "http://127.0.0.1:8021/health",
    },
    "production_remote_db": {
        "label": "Production server + remote Supabase PostgreSQL (full production stack)",
        "base_url": "https://apis.lunaratlas.in/api/v1/spectrum",
        "health_url": "https://apis.lunaratlas.in/api/v1/health",
    },
}

MEASUREMENT_ID = "FI-20230825-104221-00-3"  # reference product, Measurement ID 3

N_BASELINE_RUNS = 1000
N_SWEEP_RUNS = 100
N_DOWNSAMPLE_PAIR_RUNS = 200  # paired requests to isolate downsampling cost
WARMUP_RUNS = 20

ZOOM_LEVELS = [
    ("Full (k=0)", None),
    ("k=1 (50%)", 1),
    ("k=2 (25%)", 2),
    ("k=3 (12.5%)", 3),
    ("k=4 (6.25%)", 4),
]

# Optional: set to a real DSN to measure DB_QUERY_SPEEDUP via EXPLAIN ANALYZE.
# Point this at whichever DB you want the index-vs-seqscan test to target —
# typically the LOCAL database, since that's the one you can safely flip
# planner settings on without affecting production traffic.
# Leave DB_DSN as None to have the report explicitly say "NOT MEASURED"
# instead of printing an unexplained number, as the current draft does
# for its ~85x claim.
DB_DSN = "postgresql://postgres:lovekesh@localhost:5432/LunarAtlas"
DB_QUERY = """
SELECT 
    c.wavelength_nm, 
    c.intensity,
    COALESCE(cal.response_count, c.intensity) AS raw_plasma
FROM spectral_data_clean c
LEFT JOIN spectral_data_raw cal 
  ON c.measurement_id = cal.measurement_id 
  AND c.wavelength_nm = cal.wavelength_nm
WHERE 
    c.measurement_id = 'FI-20230825-104221-00-3'
    AND c.wavelength_nm BETWEEN 200.0 AND 800.0
ORDER BY c.wavelength_nm
"""
DB_SPEEDUP_REPEATS = 5  # EXPLAIN ANALYZE runs per plan, averaged


# =============================================================================
# Helpers
# =============================================================================

def now_iso():
    return datetime.now(timezone.utc).isoformat()


def get_git_commit():
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL
        )
        return out.decode().strip()
    except Exception:
        return "unavailable"


def get_env_fingerprint():
    return {
        "timestamp_utc": now_iso(),
        "hostname": socket.gethostname(),
        "os": platform.platform(),
        "python_version": platform.python_version(),
        "git_commit": get_git_commit(),
    }


def percentile(sorted_vals, pct):
    if not sorted_vals:
        return None
    idx = max(0, int(len(sorted_vals) * pct / 100.0) - 1)
    return sorted_vals[min(idx, len(sorted_vals) - 1)]


def summarize(latencies):
    """Summarize a latency distribution.

    v3 NOTE: This function previously computed a Tukey's-IQR-fence
    "clean mean" by discarding points outside [Q1-1.5*IQR, Q3+1.5*IQR]
    and reporting that trimmed mean as if it were a more "correct" number
    than the raw mean. That practice has been removed.

    Latency distributions are expected to be right-skewed (network
    jitter, GC pauses, connection setup, cold caches, etc.) — the right
    tail IS the phenomenon of interest, not noise to be discarded.
    Standard practice for latency reporting (SRE / systems benchmarking)
    is to report the full raw distribution via mean, std, median, and
    tail percentiles (P95/P99), not a trimmed mean. ONLY the statistics
    returned below should be quoted in the paper — there is no separate
    "clean" number.

    We still compute how many points *would* fall outside the Tukey
    fence, purely as a diagnostic (e.g. to flag a run with unusually
    heavy contamination from a stalled connection or a cold cache), but
    this count is NOT used to exclude data or compute an alternate mean.
    """
    if not latencies:
        return None
    s = sorted(latencies)
    mean = statistics.mean(latencies)
    std = statistics.stdev(latencies) if len(latencies) > 1 else 0.0

    # Diagnostic only — see docstring. Not used to exclude data.
    q1 = percentile(s, 25)
    q3 = percentile(s, 75)
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    n_iqr_flagged = sum(1 for x in latencies if x < lower_bound or x > upper_bound)

    return {
        "n": len(latencies),
        "mean_ms": round(mean, 2),
        "std_ms": round(std, 2),
        "median_ms": round(statistics.median(latencies), 2),
        "p95_ms": round(percentile(s, 95), 2),
        "p99_ms": round(percentile(s, 99), 2),
        "min_ms": round(min(latencies), 2),
        "max_ms": round(max(latencies), 2),
        "n_iqr_flagged_diagnostic_only": n_iqr_flagged,
    }


def load_baseline_from_csv(csv_path, n_requested):
    latencies = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            if row:
                latencies.append(float(row[1]))
    stats = summarize(latencies)
    stats["n_failures"] = n_requested - len(latencies)
    stats["n_requested"] = n_requested
    return stats


def load_sweep_from_csv(csv_path):
    per_zoom = {}
    by_zoom = {}
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            if row:
                label = row[0]
                lat = float(row[2])
                if label not in by_zoom:
                    by_zoom[label] = []
                by_zoom[label].append(lat)
    for label, lats in by_zoom.items():
        per_zoom[label] = summarize(lats)
    return per_zoom


def paired_t_test(deltas):
    if not deltas:
        return None
    n = len(deltas)
    mean_d = statistics.mean(deltas)
    std_d = statistics.stdev(deltas) if n > 1 else 0.0
    se = std_d / math.sqrt(n) if n > 1 else 0.0
    
    # 95% Confidence Interval critical value for large n is ~1.96
    margin_of_error = 1.95996 * se
    ci_lower = mean_d - margin_of_error
    ci_upper = mean_d + margin_of_error
    
    # Paired t-statistic
    t_stat = mean_d / se if se > 0 else 0.0
    
    # p-value calculation via standard normal approximation
    # normal_cdf(z) = 0.5 * (1.0 + erf(z / sqrt(2)))
    z_val = abs(t_stat)
    p_val = 2.0 * (1.0 - 0.5 * (1.0 + math.erf(z_val / math.sqrt(2.0))))
    
    return {
        "n": n,
        "mean_ms": round(mean_d, 4),
        "std_ms": round(std_d, 4),
        "se_ms": round(se, 4),
        "ci_95": (round(ci_lower, 4), round(ci_upper, 4)),
        "t_stat": round(t_stat, 4),
        "p_value": p_val,
        "statistically_significant": p_val < 0.05
    }


def load_downsample_contribution_from_csv(csv_path):
    by_zoom = {}
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            if row:
                k = row[0]
                delta = float(row[5])
                ds_time = float(row[6])
                if k not in by_zoom:
                    by_zoom[k] = {"deltas": [], "ds_times": []}
                by_zoom[k]["deltas"].append(delta)
                by_zoom[k]["ds_times"].append(ds_time)
                
    results = {}
    for k, data in by_zoom.items():
        results[k] = {
            "end_to_end": paired_t_test(data["deltas"]),
            "server_side": summarize(data["ds_times"])
        }
    return results


def is_server_up(url):
    try:
        r = requests.get(url, timeout=5)
        return r.status_code < 500
    except Exception:
        return False


def fetch_once(session, url, params):
    """Single timed request. Returns (latency_ms, server_ms, server_downsample_ms, server_query_ms)."""
    start = time.perf_counter()
    resp = session.get(url, params=params, timeout=20)
    latency_ms = (time.perf_counter() - start) * 1000.0
    resp.raise_for_status()
    body = resp.json()

    results = body.get("results", body) if isinstance(body, dict) else {}
    data = results.get("data", []) if isinstance(results, dict) else []
    if not data:
        raise ValueError("Empty response data — check API key / measurement_id")

    server_ms = results.get("server_processing_ms")
    server_downsample_ms = results.get("downsample_time_ms")
    server_query_ms = results.get("query_time_ms")

    return latency_ms, server_ms, server_downsample_ms, server_query_ms


# =============================================================================
# Benchmark routines
# =============================================================================

def run_baseline(session, url, n_runs, warmup, out_csv, failures_log=None, delay=0.0):
    params = {
        "measurement_id": MEASUREMENT_ID,
        "use_cache": "false",
        "force_raw": "true"
    }

    for i in range(warmup):
        try:
            fetch_once(session, url, params)
        except Exception as e:
            msg = f"[warmup {i+1}/{warmup}] failed: {e}"
            print("    " + msg)
            if failures_log:
                with open(failures_log, "a", encoding="utf-8") as f:
                    f.write(f"[{now_iso()}] {msg}\n")
        if delay > 0:
            time.sleep(delay)

    latencies, failures = [], 0
    for i in range(n_runs):
        try:
            lat, _, _, _ = fetch_once(session, url, params)
            latencies.append(lat)
        except Exception as e:
            failures += 1
            msg = f"[FAIL run {i+1}] {type(e).__name__}: {e}"
            print("    " + msg)
            if failures_log:
                with open(failures_log, "a", encoding="utf-8") as f:
                    f.write(f"[{now_iso()}] {msg}\n")
        if (i + 1) % 200 == 0 and latencies:
            print(f"    [{i+1}/{n_runs}] running mean: {statistics.mean(latencies):.2f} ms")
        if delay > 0:
            time.sleep(delay)

    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["run_index", "latency_ms"])
        for idx, lat in enumerate(latencies, start=1):
            w.writerow([idx, round(lat, 4)])

    stats = summarize(latencies)
    stats["n_failures"] = failures
    stats["n_requested"] = n_runs
    return stats


def run_sweep(session, url, n_runs, out_csv, failures_log=None, delay=0.0):
    rows = []
    per_zoom = {}
    for label, zoom in ZOOM_LEVELS:
        params = {
            "measurement_id": MEASUREMENT_ID,
            "use_cache": "false",
        }
        if zoom is None:
            params["force_raw"] = "true"
        else:
            params["force_raw"] = "false"
            params["zoom_level"] = str(zoom)

        latencies = []
        for i in range(n_runs):
            try:
                lat, _, _, _ = fetch_once(session, url, params)
                latencies.append(lat)
                rows.append([label, i + 1, round(lat, 4)])
            except Exception as e:
                msg = f"[FAIL sweep {label} run {i+1}] {type(e).__name__}: {e}"
                print("    " + msg)
                if failures_log:
                    with open(failures_log, "a", encoding="utf-8") as f:
                        f.write(f"[{now_iso()}] {msg}\n")
            if delay > 0:
                time.sleep(delay)

        per_zoom[label] = summarize(latencies)
        mean_str = f"{per_zoom[label]['mean_ms']:.2f}" if per_zoom[label] else "N/A"
        print(f"    {label}: mean {mean_str} ms")

    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["zoom_level", "run_index", "latency_ms"])
        w.writerows(rows)

    return per_zoom


def measure_downsampling_contribution(session, url, n_pairs, out_csv, failures_log=None, delay=0.0):
    zoom_levels = [1, 2, 3, 4]
    results = {}
    rows = []
    
    for k in zoom_levels:
        params_full = {
            "measurement_id": MEASUREMENT_ID,
            "use_cache": "false",
            "force_raw": "true"
        }
        params_down = {
            "measurement_id": MEASUREMENT_ID,
            "use_cache": "false",
            "force_raw": "false",
            "zoom_level": str(k),
        }
        
        deltas = []
        server_ds_times = []
        
        print(f"    Zoom level k={k} ({100 / (2**k)}%): running {n_pairs} paired trials...")
        for i in range(n_pairs):
            full_first = random.random() < 0.5
            try:
                if full_first:
                    lat_full, _, _, _ = fetch_once(session, url, params_full)
                    if delay > 0:
                        time.sleep(delay)
                    lat_down, _, ds_time_ms, _ = fetch_once(session, url, params_down)
                else:
                    lat_down, _, ds_time_ms, _ = fetch_once(session, url, params_down)
                    if delay > 0:
                        time.sleep(delay)
                    lat_full, _, _, _ = fetch_once(session, url, params_full)
                
                delta = lat_full - lat_down
                deltas.append(delta)
                if ds_time_ms is not None:
                    server_ds_times.append(ds_time_ms)
                
                rows.append([
                    k,
                    i + 1,
                    "full_first" if full_first else "downsampled_first",
                    round(lat_full, 4),
                    round(lat_down, 4),
                    round(delta, 4),
                    round(ds_time_ms, 4) if ds_time_ms is not None else 0.0
                ])
            except Exception as e:
                msg = f"[FAIL downsample-pair k={k} run {i+1}] {type(e).__name__}: {e}"
                print("    " + msg)
                if failures_log:
                    with open(failures_log, "a", encoding="utf-8") as f:
                        f.write(f"[{now_iso()}] {msg}\n")
            if delay > 0:
                time.sleep(delay)
        
        results[str(k)] = {
            "end_to_end": paired_t_test(deltas),
            "server_side": summarize(server_ds_times)
        }

    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["zoom_level", "run_index", "fired_order", "latency_full_ms", "latency_downsampled_ms",
                     "delta_ms", "server_downsample_time_ms"])
        w.writerows(rows)
        
    return results


def _extract_execution_time(explain_output):
    """Prefer the authoritative 'Execution Time: X ms' summary line that
    Postgres prints at the end of EXPLAIN ANALYZE output. Fall back to the
    top-level node's actual time only if that line isn't present (e.g. on
    very old Postgres versions)."""
    m = re.search(r"Execution Time:\s*([\d.]+)\s*ms", explain_output)
    if m:
        return float(m.group(1))
    m = re.search(r"actual time=[\d.]+\.\.([\d.]+)", explain_output)
    return float(m.group(1)) if m else None


def measure_db_speedup(dsn, query, n_repeats):
    """Measures index-vs-seqscan speedup for a SINGLE query by forcing the
    planner's choice via SET enable_seqscan/enable_indexscan/enable_bitmapscan,
    rather than requiring two hand-written query variants (which risks the
    two queries silently diverging and no longer measuring the same thing).
    Repeats each plan N times and averages, since a single EXPLAIN ANALYZE
    run is noisy (cache state, background I/O, etc.)."""
    if not dsn or not query:
        return {"measured": False, "note": "NOT MEASURED — DB_DSN/DB_QUERY not configured"}
    try:
        import psycopg2
    except ImportError:
        return {"measured": False, "note": "NOT MEASURED — psycopg2 not installed"}

    try:
        conn = psycopg2.connect(dsn)
        conn.autocommit = True
        cur = conn.cursor()

        indexed_times, seqscan_times = [], []
        for _ in range(n_repeats):
            cur.execute("SET enable_seqscan = off;")
            cur.execute("SET enable_indexscan = on;")
            cur.execute("SET enable_bitmapscan = on;")
            cur.execute(f"EXPLAIN ANALYZE {query}")
            plan = "\n".join(r[0] for r in cur.fetchall())
            t = _extract_execution_time(plan)
            if t is not None:
                indexed_times.append(t)

            cur.execute("SET enable_seqscan = on;")
            cur.execute("SET enable_indexscan = off;")
            cur.execute("SET enable_bitmapscan = off;")
            cur.execute(f"EXPLAIN ANALYZE {query}")
            plan = "\n".join(r[0] for r in cur.fetchall())
            t = _extract_execution_time(plan)
            if t is not None:
                seqscan_times.append(t)

        cur.execute("RESET enable_seqscan;")
        cur.execute("RESET enable_indexscan;")
        cur.execute("RESET enable_bitmapscan;")
        cur.close()
        conn.close()

        if indexed_times and seqscan_times:
            idx_mean = statistics.mean(indexed_times)
            seq_mean = statistics.mean(seqscan_times)
            return {
                "measured": True,
                "n_repeats": n_repeats,
                "indexed_ms_mean": round(idx_mean, 3),
                "seqscan_ms_mean": round(seq_mean, 3),
                "indexed_runs_ms": [round(x, 3) for x in indexed_times],
                "seqscan_runs_ms": [round(x, 3) for x in seqscan_times],
                "speedup_x": round(seq_mean / idx_mean, 1) if idx_mean > 0 else None,
            }
        return {"measured": False, "note": "NOT MEASURED — could not parse EXPLAIN ANALYZE Execution Time"}
    except Exception as e:
        return {"measured": False, "note": f"NOT MEASURED — DB error: {e}"}


# =============================================================================
# Report generation
# =============================================================================

def generate_report(all_results, out_path):
    lines = []
    lines.append("=" * 78)
    lines.append("LUNARATLAS LATENCY BENCHMARK — AUTO-GENERATED REPORT")
    lines.append("=" * 78)
    lines.append(f"Generated: {all_results['fingerprint']['timestamp_utc']}")
    lines.append(f"Host: {all_results['fingerprint']['hostname']}")
    lines.append(f"OS: {all_results['fingerprint']['os']}")
    lines.append(f"Python: {all_results['fingerprint']['python_version']}")
    lines.append(f"Git commit: {all_results['fingerprint']['git_commit']}")
    lines.append("")
    lines.append(
        "REVIEWER-SAFETY NOTE: this run may measure up to three DISTINCT "
        "environments (local+local DB, local+remote DB, production+remote DB). "
        "Keep their labels distinct everywhere in the paper (Abstract, Section "
        "4.5, Table 9). Do not reuse the word 'WAN' or 'co-located' for two "
        "different configurations, and do not copy a number from one "
        "environment's paragraph into another environment's table row."
    )
    lines.append(
        "STATISTICS NOTE (v3): no trimmed/'clean' mean is computed anywhere in "
        "this report. All latency figures below are the RAW distribution "
        "(mean, std, median, P95, P99). Quote these directly — do not derive "
        "or report any outlier-excluded alternative."
    )
    lines.append("")

    envs_measured = [k for k, v in all_results["environments"].items() if v.get("baseline")]
    envs_all = list(all_results["environments"].keys())
    lines.append(f"Environments configured: {envs_all}")
    lines.append(f"Environments actually measured this run: {envs_measured}")
    lines.append("")

    for env_key, env_data in all_results["environments"].items():
        b = env_data.get("baseline")
        sw = env_data.get("sweep")
        lines.append("-" * 78)
        lines.append(f"[{env_key}] {env_data['label']}")
        lines.append("-" * 78)
        if b:
            lines.append(
                f"  Baseline latency (raw, full distribution): {b['mean_ms']} +/- {b['std_ms']} ms "
                f"(median {b['median_ms']}, P95 {b['p95_ms']}, P99 {b['p99_ms']}) "
                f"over {b['n']}/{b['n_requested']} successful runs "
                f"({b['n_failures']} failures)."
            )
            if b.get("n_iqr_flagged_diagnostic_only", 0) > 0:
                lines.append(
                    f"  [diagnostic only, NOT excluded from the numbers above] "
                    f"{b['n_iqr_flagged_diagnostic_only']}/{b['n']} runs fall outside "
                    f"the Tukey IQR fence — expected for right-skewed latency data."
                )
        else:
            lines.append("  Baseline: NOT MEASURED (server unreachable this run).")

        if sw:
            lines.append("")
            lines.append("  Downsampling Scale Sweep (raw distribution):")
            for label, stats in sw.items():
                if stats:
                    flagged = stats.get("n_iqr_flagged_diagnostic_only", 0)
                    flag_str = f" [{flagged} pts IQR-flagged, diagnostic only]" if flagged else ""
                    lines.append(
                        f"    - {label}: {stats['mean_ms']} +/- {stats['std_ms']} ms "
                        f"(median {stats['median_ms']} ms, P95 {stats['p95_ms']} ms, "
                        f"P99 {stats['p99_ms']} ms){flag_str}"
                    )
        lines.append("")

    ds = all_results.get("downsampling_contribution")
    lines.append("-" * 78)
    lines.append(f"Downsampling contribution (measured against '{all_results.get('downsampling_contribution_env', 'N/A')}')")
    lines.append("-" * 78)
    if ds:
        for k_str, val in sorted(ds.items(), key=lambda x: int(x[0])):
            lines.append(f"  Zoom Level k={k_str} ({100 / (2**int(k_str))}%):")
            ete = val.get("end_to_end")
            if ete:
                sig_str = "STATISTICALLY SIGNIFICANT" if ete["statistically_significant"] else "NOT SIGNIFICANT"
                lines.append(
                    f"    - End-to-End Paired Delta: {ete['mean_ms']} +/- {ete['std_ms']} ms "
                    f"over {ete['n']} paired requests. "
                    f"95% CI: [{ete['ci_95'][0]}, {ete['ci_95'][1]}] ms | p-value: {ete['p_value']:.4e} ({sig_str})"
                )
            sv = val.get("server_side")
            if sv and sv.get("mean_ms") is not None:
                lines.append(
                    f"    - Server-Side Downsample Compute Time (raw): {sv['mean_ms']} +/- {sv['std_ms']} ms "
                    f"(median {sv['median_ms']} ms, P95 {sv['p95_ms']} ms, max {sv['max_ms']} ms) "
                    f"over {sv['n']} requests."
                )
    else:
        lines.append("  NOT MEASURED — no environment was reachable this run.")
    lines.append("")

    db = all_results.get("db_speedup", {})
    lines.append("-" * 78)
    lines.append("DB Query Speedup (index vs. seq. scan, single query, planner-forced)")
    lines.append("-" * 78)
    if db.get("measured"):
        lines.append(
            f"  Indexed (mean of {db['n_repeats']} runs): {db['indexed_ms_mean']} ms | "
            f"Seq scan (mean of {db['n_repeats']} runs): {db['seqscan_ms_mean']} ms "
            f"| Speedup: {db['speedup_x']}x"
        )
    else:
        lines.append(f"  {db.get('note', 'NOT MEASURED')}")
        lines.append("  Do NOT print a speedup number in the paper unless this is measured.")
    lines.append("")

    # ---- Paper-ready sentences (generic over however many environments ran) ----
    lines.append("=" * 78)
    lines.append("PAPER-READY TEXT (copy only what was actually measured)")
    lines.append("=" * 78)

    for env_key, env_data in all_results["environments"].items():
        b = env_data.get("baseline")
        lines.append(f"\n[{env_key} — {env_data['label']}]")
        if b:
            lines.append(
                f"  Under single-connection, no-load conditions ({env_data['label']}), "
                f"mean end-to-end API latency was {b['mean_ms']} \u00b1 {b['std_ms']} ms "
                f"(median {b['median_ms']} ms; P95 {b['p95_ms']} ms; P99 {b['p99_ms']} ms; n={b['n']})."
            )
            lines.append(
                "  ^ This is the raw, full distribution. Do not also quote a "
                "trimmed/'clean' mean — none is computed in v3."
            )
        else:
            lines.append(
                "  NOT run this session — DO NOT quote a latency number for this "
                "environment/label combination until this exists."
            )

    lines.append("\n[Table 9 — LaTeX rows, only include rows that were measured]")
    lines.append(r"\begin{tabular}{@{}p{6.0cm}c@{}}")
    lines.append(r"\toprule")
    lines.append(r"\textbf{Metric} & \textbf{Value} \\")
    lines.append(r"\midrule")
    for env_key, env_data in all_results["environments"].items():
        b = env_data.get("baseline")
        if b:
            lines.append(
                rf"Mean API Latency ({env_data['label']}) & {b['mean_ms']} $\pm$ {b['std_ms']}~ms \\"
            )
    if ds:
        for k_str, val in sorted(ds.items(), key=lambda x: int(x[0])):
            ete = val.get("end_to_end")
            if ete and ete.get("mean_ms") is not None:
                lines.append(
                    rf"Downsampling Contribution (paired, k={k_str}) & {ete['mean_ms']} $\pm$ {ete['std_ms']}~ms \\"
                )
    if db.get("measured"):
        lines.append(
            rf"DB Query Speedup (index vs.\ seq.\ scan) & $\approx {db['speedup_x']}\times$ \\"
        )
    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")

    lines.append("")
    lines.append("=" * 78)
    lines.append(
        "REVIEWER CHECKLIST: every number quoted above traces to a CSV in this "
        "folder and the fingerprint block at the top of this report. If a number "
        "appears in the paper that is NOT in this report, remove it or re-run "
        "the benchmark that produces it. Cross-check that Abstract, Section 4.5, "
        "and Table 9 all use the SAME number for the SAME environment label. "
        "No trimmed/'clean' mean should appear anywhere in the paper — quote "
        "the raw mean/std/median/P95/P99 only."
    )
    lines.append("=" * 78)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print("\n".join(lines))


# =============================================================================
# Main
# =============================================================================

def main():
    OUT_DIR.mkdir(exist_ok=True)

    all_results = {
        "fingerprint": get_env_fingerprint(),
        "environments": {},
    }

    for env_key, env_cfg in ENVIRONMENTS.items():
        print("\n" + "=" * 60)
        print(f"ENVIRONMENT: {env_key} — {env_cfg['label']}")
        print("=" * 60)

        # Check existing files first
        baseline_csv = OUT_DIR / f"raw_{env_key}_baseline.csv"
        sweep_csv = OUT_DIR / f"raw_{env_key}_sweep.csv"

        baseline_stats = None
        sweep_stats = None

        has_baseline = baseline_csv.exists() and baseline_csv.stat().st_size > 0
        has_sweep = sweep_csv.exists() and sweep_csv.stat().st_size > 0

        if has_baseline:
            print(f"  [LOAD] Existing baseline stats from {baseline_csv.name}...")
            try:
                baseline_stats = load_baseline_from_csv(baseline_csv, N_BASELINE_RUNS)
            except Exception as load_err:
                print(f"  [WARNING] Failed to load baseline CSV: {load_err}. Will re-run if server is up.")
                has_baseline = False

        if has_sweep:
            print(f"  [LOAD] Existing sweep stats from {sweep_csv.name}...")
            try:
                sweep_stats = load_sweep_from_csv(sweep_csv)
            except Exception as load_err:
                print(f"  [WARNING] Failed to load sweep CSV: {load_err}. Will re-run if server is up.")
                has_sweep = False

        # If we have both, we can skip health check and execution entirely
        if has_baseline and has_sweep:
            print(f"  [SKIP] Both baseline and sweep CSVs exist and loaded successfully.")
            all_results["environments"][env_key] = {
                "label": env_cfg["label"],
                "baseline": baseline_stats,
                "sweep": sweep_stats,
            }
            continue

        # Check if server is up before running missing benchmarks
        if not is_server_up(env_cfg["health_url"]):
            print(f"  [WARNING] Server not reachable at {env_cfg['health_url']}")
            if has_baseline:
                print(f"  [KEEP] Keeping loaded baseline stats, skipping sweep (server unreachable).")
                all_results["environments"][env_key] = {
                    "label": env_cfg["label"],
                    "baseline": baseline_stats,
                    "sweep": None,
                    "note": "sweep skipped (server unreachable)",
                }
            else:
                all_results["environments"][env_key] = {
                    "label": env_cfg["label"],
                    "baseline": None,
                    "note": "server unreachable at benchmark time",
                }
            continue

        session = requests.Session()
        url = env_cfg["base_url"]
        failures_log = OUT_DIR / f"failures_{env_key}.log"
        if failures_log.exists():
            failures_log.unlink()

        is_prod = (env_key == "production_remote_db")
        delay_val = 0.2 if is_prod else 0.0

        if has_baseline:
            print(f"  Using pre-loaded baseline stats.")
        else:
            print(f"  Running baseline ({N_BASELINE_RUNS} runs, {WARMUP_RUNS} warmup)...")
            baseline_stats = run_baseline(
                session, url, N_BASELINE_RUNS, WARMUP_RUNS,
                baseline_csv, failures_log=failures_log, delay=delay_val
            )

        if is_prod and not has_sweep:
            print("  Applying 5-second cooldown breather for production server...")
            time.sleep(5.0)

        if has_sweep:
            print(f"  Using pre-loaded sweep stats.")
        else:
            sweep_runs_val = 50 if is_prod else N_SWEEP_RUNS
            print(f"  Running downsampling scale sweep ({sweep_runs_val} runs/level)...")
            sweep_stats = run_sweep(
                session, url, sweep_runs_val, sweep_csv, failures_log=failures_log, delay=delay_val
            )

        all_results["environments"][env_key] = {
            "label": env_cfg["label"],
            "baseline": baseline_stats,
            "sweep": sweep_stats,
        }

    # Measure downsampling contribution against whichever environment is up
    # (prefer local_colocated, since it isolates compute cost from WAN jitter best).
    ds_env_key = None
    for candidate in ("local_colocated", "local_remote_db", "production_remote_db"):
        if all_results["environments"].get(candidate, {}).get("baseline"):
            ds_env_key = candidate
            break

    if ds_env_key:
        ds_csv = OUT_DIR / f"raw_{ds_env_key}_downsample_contribution.csv"
        ds_pairs_val = 500 if ds_env_key == "local_colocated" else 100
        
        if ds_csv.exists() and ds_csv.stat().st_size > 0:
            print(f"Loading downsampling contribution stats from {ds_csv.name}...")
            try:
                all_results["downsampling_contribution"] = load_downsample_contribution_from_csv(ds_csv)
                all_results["downsampling_contribution_env"] = ds_env_key
            except Exception as load_err:
                print(f"  [WARNING] Failed to load downsampling CSV: {load_err}. Re-running downsampling benchmark...")
                url = ENVIRONMENTS[ds_env_key]["base_url"]
                session = requests.Session()
                all_results["downsampling_contribution"] = measure_downsampling_contribution(
                    session, url, ds_pairs_val, ds_csv,
                    failures_log=OUT_DIR / f"failures_{ds_env_key}.log",
                    delay=0.2 if ds_env_key == "production_remote_db" else 0.0
                )
                all_results["downsampling_contribution_env"] = ds_env_key
        else:
            print(f"\nMeasuring downsampling contribution against '{ds_env_key}' ({ds_pairs_val} paired runs per zoom level)...")
            url = ENVIRONMENTS[ds_env_key]["base_url"]
            session = requests.Session()
            all_results["downsampling_contribution"] = measure_downsampling_contribution(
                session, url, ds_pairs_val, ds_csv,
                failures_log=OUT_DIR / f"failures_{ds_env_key}.log",
                delay=0.2 if ds_env_key == "production_remote_db" else 0.0
            )
            all_results["downsampling_contribution_env"] = ds_env_key
    else:
        all_results["downsampling_contribution"] = {
            "measured": False,
            "note": "No environment reachable — not measured.",
        }
        all_results["downsampling_contribution_env"] = "N/A"

    print("\nMeasuring DB query speedup (index vs. seq scan)...")
    all_results["db_speedup"] = measure_db_speedup(DB_DSN, DB_QUERY, DB_SPEEDUP_REPEATS)

    with open(OUT_DIR / "results.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)

    generate_report(all_results, OUT_DIR / "latency_report.txt")

    print(f"\n[DONE] All outputs written to {OUT_DIR.resolve()}/")


if __name__ == "__main__":
    main()