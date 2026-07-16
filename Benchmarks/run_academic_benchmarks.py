import csv
import json
import statistics
import time
import requests
from pathlib import Path

BASE_URL = "http://127.0.0.1:8020/api/v1/public/spectra/FI-20230825-104221-00-3"
API_KEY = "DEMO_KEY"

def fetch_once(session: requests.Session, params: dict) -> float:
    start = time.perf_counter()
    resp = session.get(BASE_URL, params=params, timeout=20)
    latency_ms = (time.perf_counter() - start) * 1000.0
    resp.raise_for_status()
    # Check response structure to verify it's valid data
    body = resp.json()
    results = body.get("results", body)
    data = results.get("data", []) if isinstance(results, dict) else []
    if not data:
        raise ValueError("Empty response data")
    return latency_ms

def run_baseline(session: requests.Session, n_runs: int, warmup: int, out_csv: Path):
    print("="*60)
    print(f"RUNNING BASELINE LATENCY DISTRIBUTION (N={n_runs})")
    print("="*60)
    
    # Warmup
    print(f"Warming up ({warmup} runs)...")
    params = {"api_key": API_KEY, "use_cache": "false"}
    for i in range(warmup):
        try:
            fetch_once(session, params)
        except Exception as e:
            print(f"  Warmup {i+1} failed: {e}")
            
    print("Starting measured baseline runs...")
    latencies = []
    for i in range(n_runs):
        try:
            lat = fetch_once(session, params)
            latencies.append(lat)
        except Exception as e:
            print(f"  [FAIL] Run {i+1}: {e}")
            
        if (i + 1) % 100 == 0:
            print(f"  [{i+1}/{n_runs}] Mean: {statistics.mean(latencies):.2f} ms")
            
    # Save CSV
    with open(out_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["run_index", "latency_ms"])
        for idx, lat in enumerate(latencies, start=1):
            writer.writerow([idx, round(lat, 4)])
            
    print(f"[SUCCESS] Saved baseline data to {out_csv}")
    print(f"  Mean   : {statistics.mean(latencies):.2f} ms")
    print(f"  P50    : {statistics.median(latencies):.2f} ms")
    sorted_lats = sorted(latencies)
    print(f"  P95    : {sorted_lats[int(len(sorted_lats)*0.95)-1]:.2f} ms")
    print(f"  P99    : {sorted_lats[int(len(sorted_lats)*0.99)-1]:.2f} ms")

def run_sweep(session: requests.Session, n_runs: int, out_csv: Path):
    print("\n" + "="*60)
    print("RUNNING DOWNSAMPLING SCALE SWEEP")
    print("="*60)
    
    # Sweep configurations: (zoom_level, params)
    sweeps = [
        ("Full (k=0)", {"api_key": API_KEY, "use_cache": "false", "downsample": "false"}),
        ("k=1 (50%)", {"api_key": API_KEY, "use_cache": "false", "downsample": "true", "zoom_level": "1"}),
        ("k=2 (25%)", {"api_key": API_KEY, "use_cache": "false", "downsample": "true", "zoom_level": "2"}),
        ("k=3 (12.5%)", {"api_key": API_KEY, "use_cache": "false", "downsample": "true", "zoom_level": "3"}),
        ("k=4 (6.25%)", {"api_key": API_KEY, "use_cache": "false", "downsample": "true", "zoom_level": "4"}),
    ]
    
    with open(out_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["zoom_level", "run_index", "latency_ms"])
        
        for name, params in sweeps:
            print(f"Running sweep for {name}...")
            latencies = []
            for i in range(n_runs):
                try:
                    lat = fetch_once(session, params)
                    latencies.append(lat)
                    writer.writerow([name, i + 1, round(lat, 4)])
                except Exception as e:
                    print(f"  [FAIL] Sweep {name} Run {i+1}: {e}")
            print(f"  {name} Mean: {statistics.mean(latencies):.2f} ms")
            
    print(f"[SUCCESS] Saved sweep data to {out_csv}")

def main():
    session = requests.Session()
    
    # Check if local server is up
    try:
        session.get("http://127.0.0.1:8020/health", timeout=5)
    except Exception:
        print("[ERROR] Local server on port 8020 is not running. Please start the server first!")
        return
        
    run_baseline(session, n_runs=1000, warmup=20, out_csv=Path("academic_baseline_latencies.csv"))
    run_sweep(session, n_runs=100, out_csv=Path("academic_sweep_latencies.csv"))

if __name__ == "__main__":
    main()
