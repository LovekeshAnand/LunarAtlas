#!/usr/bin/env python3
"""
Local API benchmark (no production or WAN traffic).

Throwaway PostgreSQL cluster (port 55433) loaded with the worked-example product via the
revised ingestion; FastAPI server from core/server/venv on 127.0.0.1:8031; client threads with
keep-alive sessions. Redis is not running on this host, so every request is a cache miss
(use_cache=false is also sent): these are bypassed-cache numbers only.

Matrix: 3 sessions (fresh server process each) x workloads x concurrency {1, 4, 16, 32};
REQUESTS per cell after WARMUP discarded requests.
Writes revision_v2/outputs/benchmark/{raw_latencies.csv, summary.csv, environment.json, server_s*.log}
"""
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent.parent
V2 = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "Pipeline"))
from optional_db_ingestion import ingest_cleaned_datasets  # noqa: E402

PG_BIN = Path(os.environ.get("PG_BIN", r"C:\Program Files\PostgreSQL\18\bin"))
PGDATA = V2 / "_pgdata_bench"
PORT_DB, PORT_API = 55433, 8031
DB_URL = f"postgresql://postgres@localhost:{PORT_DB}/lunaratlas_bench"
API = f"http://127.0.0.1:{PORT_API}/api/v1/spectrum"
SERVER_PY = ROOT / "core" / "server" / "venv" / "Scripts" / "python.exe"
OUT = V2 / "outputs" / "benchmark"
OBS = "ch3_lib_002_20230825T104221_00_l1"
MID = "FI-20230825-104221-00-3"
SESSIONS, CONCURRENCY, REQUESTS, WARMUP, TIMEOUT_S = 3, [1, 4, 16, 32], 400, 20, 10
WORKLOADS = {
    "full_raw_2094": dict(lambda_min=0, lambda_max=1000, force_raw="true"),
    "calibrated_raw_1684": dict(lambda_min=220, lambda_max=800, force_raw="true"),
    "calibrated_lttb_k4": dict(lambda_min=220, lambda_max=800, zoom_level=4),
}


def pg_start(*a):
    """pg_ctl start: the postmaster inherits stdout, so never capture it (the pipe would never close)."""
    subprocess.run([str(PG_BIN / "pg_ctl"), *a], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def pg(*a, **kw):
    return subprocess.run([str(PG_BIN / a[0]), *a[1:]], check=True, capture_output=True, text=True, **kw)


def load_db():
    """Ingest only the worked-example product (copied into a private processed tree)."""
    src = V2 / "processed_run1" / "calibrated" / "20230825" / OBS
    dst = PGDATA.parent / "_bench_processed" / "calibrated" / "20230825" / OBS
    shutil.rmtree(dst.parents[2], ignore_errors=True)
    shutil.copytree(src, dst)
    ingest_cleaned_datasets(str(dst.parents[2]), db_url=DB_URL, raw_dir=str(ROOT / "datasets" / "uploads"))
    return dst.parents[2]


def start_server(log):
    env = {**os.environ, "DATABASE_URL": DB_URL, "REDIS_URL": "redis://127.0.0.1:6399/0", "DEBUG": "false"}
    p = subprocess.Popen([str(SERVER_PY), "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1",
                          "--port", str(PORT_API), "--workers", "1"], cwd=ROOT / "core" / "server",
                         env=env, stdout=log, stderr=log)
    for _ in range(120):
        try:
            if requests.get(f"http://127.0.0.1:{PORT_API}/api/v1/health", timeout=1).ok:
                return p
        except requests.RequestException:
            time.sleep(0.5)
    p.kill()
    raise RuntimeError("server did not start")


def one(session, params):
    t = time.perf_counter()
    try:
        r = session.get(API, params=params, timeout=TIMEOUT_S)
        ok = r.status_code == 200
        n = len(r.json().get("data", [])) if ok else 0
        return (time.perf_counter() - t) * 1000, r.status_code, n, len(r.content), ""
    except requests.Timeout:
        return (time.perf_counter() - t) * 1000, 0, 0, 0, "timeout"
    except requests.RequestException as e:
        return (time.perf_counter() - t) * 1000, 0, 0, 0, type(e).__name__


def cell(params, conc):
    local = threading.local()

    def task(_):
        if not hasattr(local, "s"):
            local.s = requests.Session()
        return one(local.s, params)

    with ThreadPoolExecutor(conc) as ex:
        list(ex.map(task, range(WARMUP)))
        t0 = time.perf_counter()
        res = list(ex.map(task, range(REQUESTS)))
        dur = time.perf_counter() - t0
    return res, dur


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    shutil.rmtree(PGDATA, ignore_errors=True)
    pg("initdb", "-D", str(PGDATA), "-U", "postgres", "-A", "trust", "-E", "UTF8")
    pg_start("-D", str(PGDATA), "-o", f"-p {PORT_DB} -c listen_addresses=localhost", "-l",
       str(OUT / "postgres.log"), "-w", "start")
    rows, summ, tmp = [], [], None
    try:
        tmp = load_db()
        env = {"os": platform.platform(), "cpu": platform.processor(), "logical_cpus": os.cpu_count(),
               "host": socket.gethostname(), "client_python": sys.version.split()[0],
               "server_python": subprocess.run([str(SERVER_PY), "--version"], capture_output=True, text=True).stdout.strip(),
               "postgres": pg("postgres", "--version").stdout.strip(), "redis": "not running (all requests are cache misses)",
               "uvicorn_workers": 1, "db_pool_max": 20, "measurement_id": MID,
               "sessions": SESSIONS, "concurrency": CONCURRENCY, "requests_per_cell": REQUESTS,
               "warmup_discarded": WARMUP, "timeout_s": TIMEOUT_S, "workloads": WORKLOADS,
               "started": time.strftime("%Y-%m-%dT%H:%M:%S")}
        for s in range(1, SESSIONS + 1):
            with open(OUT / f"server_s{s}.log", "w") as log:
                srv = start_server(log)
                try:
                    for w, p in WORKLOADS.items():
                        params = {"measurement_id": MID, "use_cache": "false", **p}
                        for c in CONCURRENCY:
                            res, dur = cell(params, c)
                            lat = np.array([r[0] for r in res])
                            ok = np.array([r[1] == 200 for r in res])
                            for i, r in enumerate(res):
                                rows.append({"session": s, "workload": w, "concurrency": c, "i": i, "latency_ms": r[0],
                                             "status": r[1], "points": r[2], "bytes": r[3], "error": r[4]})
                            summ.append({"session": s, "workload": w, "concurrency": c, "requests": len(res),
                                         "ok": int(ok.sum()), "errors": int((~ok).sum()),
                                         "timeouts": sum(r[4] == "timeout" for r in res),
                                         "duration_s": dur, "throughput_rps": len(res) / dur,
                                         "mean_ms": lat[ok].mean(), "std_ms": lat[ok].std(),
                                         "p50_ms": np.percentile(lat[ok], 50), "p95_ms": np.percentile(lat[ok], 95),
                                         "p99_ms": np.percentile(lat[ok], 99), "max_ms": lat[ok].max(),
                                         "points": res[0][2], "bytes": res[0][3]})
                            print(summ[-1], flush=True)
                finally:
                    srv.terminate()
                    srv.wait(15)
        env["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        (OUT / "environment.json").write_text(json.dumps(env, indent=2))
        pd.DataFrame(rows).to_csv(OUT / "raw_latencies.csv", index=False)
        pd.DataFrame(summ).to_csv(OUT / "summary.csv", index=False)
    finally:
        pg("pg_ctl", "-D", str(PGDATA), "-m", "fast", "-w", "stop")
        shutil.rmtree(PGDATA, ignore_errors=True)
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
