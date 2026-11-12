"""Closed-loop concurrency benchmark for /api/v1/spectrum (stdlib only).

Per workload and concurrency c: 10 warm-up requests (discarded), then N measured requests issued by
c parallel workers, each sending its next request as soon as the previous one returns. Cache is
bypassed (use_cache=false), as in the original July 2026 single-session benchmark (same request).
Stop rule: a level with >10% errors ends the session (no higher concurrency is tried).

usage: concurrency_bench.py <base_url> <out_dir> <label> [levels=1,8,16,32] [n=100]
"""
import sys, csv, json, time, statistics, platform, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

base, out, label = sys.argv[1].rstrip("/"), Path(sys.argv[2]), sys.argv[3]
levels = [int(x) for x in (sys.argv[4] if len(sys.argv) > 4 else "1,8,16,32").split(",")]
N = int(sys.argv[5]) if len(sys.argv) > 5 else 100
WARMUP, TIMEOUT = 10, 30
MID = "FI-20230825-104221-00-3"
WORKLOADS = {
    # default 200-800 nm window -> 1,737 points (same request as the July benchmark)
    "full_raw": {"measurement_id": MID, "use_cache": "false", "force_raw": "true"},
    "lttb_k4":  {"measurement_id": MID, "use_cache": "false", "zoom_level": "4"},
}
out.mkdir(parents=True, exist_ok=True)


def one(url):
    t0 = time.perf_counter()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "LunarAtlas-benchmark"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            body = json.loads(r.read())
            status = r.status
        ms = (time.perf_counter() - t0) * 1000
        res = body.get("results", body)
        ok = status == 200 and bool(res.get("data"))
        return ms, ok, res.get("server_processing_ms"), len(res.get("data", []))
    except Exception as e:
        return (time.perf_counter() - t0) * 1000, False, None, repr(e)[:80]


def pct(x, p):
    return statistics.quantiles(x, n=100, method="inclusive")[p - 1] if len(x) > 1 else x[0]


rows, summary = [], []
started = datetime.now(timezone.utc).isoformat()
stop = False
for wname, params in WORKLOADS.items():
    url = f"{base}/api/v1/spectrum?{urllib.parse.urlencode(params)}"
    for c in levels:
        if stop:
            break
        with ThreadPoolExecutor(max_workers=c) as ex:
            list(ex.map(one, [url] * WARMUP))
            t0 = time.perf_counter()
            res = list(ex.map(one, [url] * N))
            wall = time.perf_counter() - t0
        lat = [r[0] for r in res if r[1]]
        err = sum(1 for r in res if not r[1])
        srv = [r[2] for r in res if r[1] and r[2] is not None]
        for i, r in enumerate(res):
            rows.append([label, wname, c, i + 1, round(r[0], 3), r[1], r[2], r[3]])
        s = dict(session=label, workload=wname, concurrency=c, n=N, errors=err,
                 p50=round(statistics.median(lat), 1) if lat else None,
                 p95=round(pct(lat, 95), 1) if lat else None,
                 p99=round(pct(lat, 99), 1) if lat else None,
                 mean=round(statistics.mean(lat), 1) if lat else None,
                 server_ms_p50=round(statistics.median(srv), 1) if srv else None,
                 req_per_s=round(len(lat) / wall, 2), points=res[0][3] if res[0][1] else None)
        summary.append(s)
        print(json.dumps(s), flush=True)
        if err > 0.1 * N:
            print(f"STOP: {err}/{N} errors at c={c}", flush=True)
            stop = True

with open(out / f"raw_{label}.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["session", "workload", "concurrency", "i", "latency_ms", "ok", "server_ms", "points_or_error"])
    w.writerows(rows)
with open(out / f"summary_{label}.json", "w") as f:
    json.dump(dict(base=base, label=label, started_utc=started, finished_utc=datetime.now(timezone.utc).isoformat(),
                   client=platform.platform(), python=platform.python_version(), levels=levels, n=N,
                   warmup=WARMUP, timeout_s=TIMEOUT, summary=summary), f, indent=1)
