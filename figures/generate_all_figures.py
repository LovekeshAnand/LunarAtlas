#!/usr/bin/env python3
"""
generate_all_figures.py — Figure Generation Orchestrator
Executes each of the 6 separate figure scripts in sequence.
"""

import sys
import subprocess
from pathlib import Path

def main():
    print("="*65)
    print(" LUNARATLAS PUBLICATION FIGURES GENERATION ORCHESTRATOR")
    print("="*65)
    
    figures_dir = Path(__file__).resolve().parent
    scripts = [
        "fig1_architecture.py",
        "fig2_reshape_schematic.py",
        "fig3_pre_post_overlay.py",
        "fig4_peak_comparison.py",
        "fig5_nist_overlay.py",
        "fig6_adaptive_zoom.py"
    ]
    
    success_count = 0
    for script in scripts:
        script_path = figures_dir / script
        print(f"\n[RUNNING] {script}...")
        try:
            # Run python as subprocess to ensure isolated environments
            result = subprocess.run([sys.executable, str(script_path)], check=True, capture_output=True, text=True)
            print(result.stdout.strip())
            success_count += 1
            print(f"[SUCCESS] Finished {script}")
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Failed running {script} (exit code {e.returncode}):")
            print(e.stderr.strip())
            
    print("\n" + "="*65)
    print(f" ORCHESTRATION COMPLETE: {success_count}/{len(scripts)} scripts completed successfully.")
    print("="*65)
    
    if success_count < len(scripts):
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
