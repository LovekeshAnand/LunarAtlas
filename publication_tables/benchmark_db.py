#!/usr/bin/env python3
"""
LunarAtlas — Database Query Benchmark Runner
=============================================
Runs the API latency and database query benchmarks and prints a summary.

The full benchmark suite is in Benchmarks/:
  - run_latency_benchmarks.py  : co-located latency sweep
  - final_benchmarks.py        : comprehensive benchmark including WAN configs
  - concurrent_load_benchmark.py : concurrent-connection load test

Usage
-----
  python publication_tables/benchmark_db.py

Requirements
------------
  The FastAPI server must be running locally (uvicorn app.main:app --port 8000).
  See README.md for setup instructions.
"""

import sys
import subprocess
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))


def main():
    # Prefer run_latency_benchmarks.py for a quick co-located benchmark
    for script_name in ("run_latency_benchmarks.py", "run_benchmarks.py"):
        script_path = root_dir / "Benchmarks" / script_name
        if script_path.exists():
            print(f"[INFO] Running benchmark: {script_path.relative_to(root_dir)}")
            try:
                subprocess.run([sys.executable, str(script_path)], check=True)
            except subprocess.CalledProcessError as e:
                print(f"[ERROR] Benchmark exited with code {e.returncode}")
            except Exception as e:
                print(f"[ERROR] Failed to run benchmark: {e}")
            return

    print("[ERROR] No benchmark script found in Benchmarks/.")
    print("  Expected one of: run_latency_benchmarks.py, run_benchmarks.py")
    print("  Ensure the FastAPI server is running before launching benchmarks.")


if __name__ == "__main__":
    main()
