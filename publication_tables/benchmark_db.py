#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path

# Add project root to path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

def main():
    script_path = root_dir / "figures" / "fig6_db_benchmark.py"
    if not script_path.exists():
        print(f"[ERROR] Benchmark script not found at {script_path}")
        return
        
    print("[INFO] Running database query benchmark via figures/fig6_db_benchmark.py...")
    try:
        subprocess.run([sys.executable, str(script_path)], check=True)
    except Exception as e:
        print(f"[ERROR] Failed to run database benchmark: {e}")

if __name__ == "__main__":
    main()
