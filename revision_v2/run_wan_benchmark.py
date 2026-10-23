#!/usr/bin/env python3
"""
WAN benchmark against the public demonstration API (approved by the owner on 2026-10-23).

Target  : https://apis.lunaratlas.in/api/v1/spectrum, Measurement ID FI-20230825-104221-00-3
          (the deployment holds legacy-ingested records; this ID is identical to the revision output).
Matrix  : SESSIONS sessions spaced GAP_S apart x workloads x cache {bypassed, warm} x concurrency {1, 4, 8};
          WARMUP discarded + REQUESTS measured per cell. Keep-alive session per client thread.
Load cap: at most 8 concurrent requests; a session is aborted if a cell has > 10 % errors or p50 > 15 s.
Also    : /api/v1/health latency per session (network + minimal server work), and the server's own
          `server_processing_ms` from each response, which separates server time from network time.
Writes  : revision_v2/outputs/benchmark_wan/{raw_latencies.csv, summary.csv, environment.json}
"""
import json
import os
import platform
import socket
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import requests

BASE = os.environ.get("LUNARATLAS_API", "https://apis.lunaratlas.in")
API, HEALTH = f"{BASE}/api/v1/spectrum", f"{BASE}/api/v1/health"
OUT = Path(__file__).resolve().parent / "outputs" / "benchmark_wan"
MID = "FI-20230825-104221-00-3"
SESSIONS, GAP_S, CONCURRENCY, REQUESTS, WARMUP, TIMEOUT_S = 3, 900, [1, 4, 8], 100, 10, 30
WORKLOADS = {
    "full_raw_2094": dict(lambda_min=0, lambda_max=1000, force_raw="true"),
    "calibrated_lttb_k4": dict(lambda_min=220, lambda_max=800, zoom_level=4),
}
CACHE = {"bypassed": "false", "warm": "true"}


def one(session, url, params):
    t = time.perf_counter()
    try:
        r = session.get(url, params=params, timeout=TIMEOUT_S)
        ms = (time.perf_counter() - t) * 1000
        j = r.json() if r.status_code == 200 else {}
        return ms, r.status_code, len(j.get("data", [])), len(r.content), j.get("server_processing_ms"), j.get("cached"), ""
    except requests.Timeout:
        return (time.perf_counter() - t) * 1000, 0, 0, 0, None, None, "timeout"
    except (requests.RequestException, ValueError) as e:
        return (time.perf_counter() - t) * 1000, 0, 0, 0, None, None, type(e).__name__


def cell(url, params, conc):
    local = threading.local()

    def task(_):
        if not hasattr(local, "s"):
            local.s = requests.Session()
        return one(local.s, url, params)

    with ThreadPoolExecutor(conc) as ex:
        list(ex.map(task, range(WARMUP)))  # for the warm condition this also fills the cache
        t0 = time.perf_counter()
        res = list(ex.map(task, range(REQUESTS)))
        dur = time.perf_counter() - t0
    return res, dur


def summarise(res, dur, **key):
    lat = np.array([r[0] for r in res])
    ok = np.array([r[1] == 200 for r in res])
    srv = np.array([r[4] for r in res if r[1] == 200 and r[4] is not None], float)
    g = lambda a, q: float(np.percentile(a, q)) if len(a) else float("nan")
    return {**key, "requests": len(res), "ok": int(ok.sum()), "errors": int((~ok).sum()),
            "timeouts": sum(r[6] == "timeout" for r in res), "duration_s": dur, "throughput_rps": len(res) / dur,
            "p50_ms": g(lat[ok], 50), "p95_ms": g(lat[ok], 95), "p99_ms": g(lat[ok], 99),
            "max_ms": float(lat[ok].max()) if ok.any() else float("nan"),
            "server_p50_ms": g(srv, 50), "server_p95_ms": g(srv, 95),
            "cached_share": float(np.mean([bool(r[5]) for r in res if r[1] == 200])) if ok.any() else float("nan"),
            "points": res[0][2], "bytes": res[0][3]}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    env = {"target": API, "measurement_id": MID, "client_os": platform.platform(), "client_host": socket.gethostname(),
           "client_python": sys.version.split()[0], "sessions": SESSIONS, "gap_between_sessions_s": GAP_S,
           "concurrency": CONCURRENCY, "requests_per_cell": REQUESTS, "warmup_discarded": WARMUP,
           "timeout_s": TIMEOUT_S, "workloads": WORKLOADS, "cache_conditions": CACHE,
           "abort_rule": "error rate > 10 % or p50 > 15 s in any cell", "sessions_log": []}
    rows, summ = [], []
    for s in range(1, SESSIONS + 1):
        if s > 1:
            time.sleep(GAP_S)
        start = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        h, hd = cell(HEALTH, {}, 1)
        summ.append(summarise(h, hd, session=s, workload="health", cache="n/a", concurrency=1))
        aborted = None
        for w, p in WORKLOADS.items():
            for cname, cval in CACHE.items():
                params = {"measurement_id": MID, "use_cache": cval, **p}
                for c in CONCURRENCY:
                    res, dur = cell(API, params, c)
                    for i, r in enumerate(res):
                        rows.append({"session": s, "workload": w, "cache": cname, "concurrency": c, "i": i,
                                     "latency_ms": r[0], "status": r[1], "points": r[2], "bytes": r[3],
                                     "server_processing_ms": r[4], "cached": r[5], "error": r[6]})
                    summ.append(summarise(res, dur, session=s, workload=w, cache=cname, concurrency=c))
                    print({k: summ[-1][k] for k in ["session", "workload", "cache", "concurrency", "errors",
                                                    "p50_ms", "p95_ms", "throughput_rps", "server_p50_ms"]}, flush=True)
                    if summ[-1]["errors"] > 0.1 * REQUESTS or not summ[-1]["p50_ms"] <= 15000:
                        aborted = f"{w}/{cname}/c{c}"
                        break
                if aborted:
                    break
            if aborted:
                break
        env["sessions_log"].append({"session": s, "started": start, "finished": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                                    "aborted_at": aborted})
        pd.DataFrame(rows).to_csv(OUT / "raw_latencies.csv", index=False)
        pd.DataFrame(summ).to_csv(OUT / "summary.csv", index=False)
        (OUT / "environment.json").write_text(json.dumps(env, indent=2))
        if aborted:
            print("ABORTED", aborted, flush=True)
            break


if __name__ == "__main__":
    main()
