"""
Concurrent API Load Testing and Latency Benchmark Suite
Author: LunarAtlas Research Team

This script performs concurrent multi-connection load testing against the live 
production REST API of LunarAtlas (https://api.lunaratlas.in) to measure response 
latency, database processing overhead, and connection stability under concurrent load.

Endpoints targeted:
  - GET /api/v1/public/spectra/{measurement_id} (retrieving the full 2,094-channel spectrum)

Usage:
  python concurrent_load_benchmark.py
"""

import time
import urllib.request
import json
import threading

URL = "https://api.lunaratlas.in/api/v1/public/spectra/FI-20230825-104221-00-3?api_key=API_KEY"

def fetch_spectrum():
    """
    Sends a single HTTP GET request to retrieve the 2,094-channel spectrum
    and records the total round-trip response time.
    """
    start = time.perf_counter()
    try:
        req = urllib.request.Request(URL, headers={"User-Agent": "LunarAtlas-Load-Benchmark"})
        with urllib.request.urlopen(req, timeout=12) as response:
            body = response.read().decode('utf-8')
            res_json = json.loads(body)
            results_dict = res_json.get("results", {})
            points = results_dict.get("data", [])
            points_count = len(points)
            latency = (time.perf_counter() - start) * 1000.0
            return True, f"points: {points_count}", latency
    except Exception as e:
        latency = (time.perf_counter() - start) * 1000.0
        return False, str(e), latency

def run_concurrent_test(num_threads):
    """
    Spawns `num_threads` simultaneous connections to query the target
    endpoint in parallel and reports latency statistics.
    """
    results = []
    threads = []
    
    def worker():
        success, info, latency = fetch_spectrum()
        results.append((success, info, latency))
        
    for _ in range(num_threads):
        t = threading.Thread(target=worker)
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()
        
    successes = [r for r in results if r[0]]
    failures = [r for r in results if not r[0]]
    
    avg_latency = sum(r[2] for r in successes) / len(successes) if successes else 0.0
    
    print(f"Concurrent Connections: {num_threads}")
    print(f"  Success Rate: {len(successes)} / {num_threads}")
    if successes:
        print(f"  Sample Output: {successes[0][1]}")
        print(f"  Avg Round-Trip Latency: {avg_latency:.2f} ms")
    if failures:
        print(f"  Failures Count: {len(failures)}")
        print(f"  Sample Failure Error: {failures[0][1]}")
    return avg_latency

if __name__ == "__main__":
    print("======================================================================")
    print("              LUNARATLAS CONCURRENT API LOAD BENCHMARK                ")
    print("======================================================================")
    print(f"Target URL: {URL}")
    print("Running multi-connection test sequence...\n")
    
    print("--- Stage 1: Single Connection (Baseline) ---")
    run_concurrent_test(1)
    
    print("\n--- Stage 2: 5 Concurrent Connections ---")
    run_concurrent_test(5)
    
    print("\n--- Stage 3: 10 Concurrent Connections ---")
    run_concurrent_test(10)
    
    print("\n--- Stage 4: 20 Concurrent Connections ---")
    run_concurrent_test(20)
    print("======================================================================")
