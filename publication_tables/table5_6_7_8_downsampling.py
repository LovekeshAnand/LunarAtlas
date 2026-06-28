#!/usr/bin/env python3
import os
import sys
import json
from pathlib import Path

# Add project root to path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

def main():
    print("====================================================")
    print(" REPRODUCING TABLES 5, 6, 7, 8: DOWNSAMPLING RESULTS")
    print("====================================================")
    
    json_path = root_dir / "figures" / "downsampling_eval_results.json"
    
    if not json_path.exists():
        print("[INFO] Evaluating downsampling from scratch...")
        # Execute the figures evaluate script to generate it
        try:
            import subprocess
            subprocess.run([sys.executable, str(root_dir / "figures" / "evaluate_downsampling.py")], check=True)
        except Exception as e:
            print(f"[ERROR] Failed to run evaluate_downsampling.py: {e}")
            return
            
    with open(json_path, 'r') as f:
        res = json.load(f)
        
    # Table 5: Algorithm Comparison
    print("\n--- Table 5 LaTeX Snippet ---")
    for name in ["Uniform decimation", "Max-binning", "Standard LTTB", "LTTB + Peaks"]:
        r_val = res["comparison_id3"][name]
        bold_prefix = r"\textbf{" if name == "LTTB + Peaks" else ""
        bold_suffix = r"}" if name == "LTTB + Peaks" else ""
        print(f"{bold_prefix}{name}{bold_suffix} & {bold_prefix}{r_val['retention']:.1f}\\%{bold_suffix} & {bold_prefix}{r_val['rmse']:.2f}{bold_suffix} & {bold_prefix}{r_val['latency_mean']:.2f} $\\pm$ {r_val['latency_std']:.2f}{bold_suffix} \\\\")
        
    # Table 6: Dual Retention
    print("\n--- Table 6 LaTeX Snippet ---")
    dm = res["dual_metrics_id3"]
    print(f"Local maxima retention & {dm['Standard LTTB']['local_maxima']:.1f}\\% & \\textbf{{{dm['LTTB + Peaks']['local_maxima']:.1f}\\%}} \\\\")
    print(f"NIST-matched peak retention & {dm['Standard LTTB']['nist_matched']:.1f}\\% & \\textbf{{{dm['LTTB + Peaks']['nist_matched']:.1f}\\%}} \\\\")
    
    # Table 7: Density Sweep
    print("\n--- Table 7 LaTeX Snippet ---")
    ds = res["density_sweep_id3"]
    for name in ["Uniform decimation", "Max-binning", "Standard LTTB", "LTTB + Peaks"]:
        rets = ds[name]
        bold_prefix = r"\textbf{" if name == "LTTB + Peaks" else ""
        bold_suffix = r"}" if name == "LTTB + Peaks" else ""
        print(f"{bold_prefix}{name}{bold_suffix} & " + " & ".join(f"{bold_prefix}{r:.1f}\\%{bold_suffix}" for r in rets) + r" \\")
        
    # Table 8: Peak Fidelity
    print("\n--- Table 8 LaTeX Snippet ---")
    f_3 = res["fidelity"]["3"]
    f_4 = res["fidelity"]["4"]
    f_mean = res["fidelity"]["mean"]
    print(f"Peak position error (nm) & {f_3['pos_mean']:.3f} $\\pm$ {f_3['pos_std']:.3f} & {f_4['pos_mean']:.3f} $\\pm$ {f_4['pos_std']:.3f} & {f_mean['pos_mean']:.3f} $\\pm$ {f_mean['pos_std']:.3f} \\\\")
    print(f"Peak height error (counts) & {f_3['height_mean']:.2f} $\\pm$ {f_3['height_std']:.2f} & {f_4['height_mean']:.2f} $\\pm$ {f_4['height_std']:.2f} & {f_mean['height_mean']:.2f} $\\pm$ {f_mean['height_std']:.2f} \\\\")
    print(f"Peak height error (\\%) & {f_3['pct_mean']:.2f}\\% $\\pm$ {f_3['pct_std']:.2f}\\% & {f_4['pct_mean']:.2f}\\% $\\pm$ {f_4['pct_std']:.2f}\\% & {f_mean['pct_mean']:.2f}\\% $\\pm$ {f_mean['pct_std']:.2f}\\% \\\\")
    print("---------------------------\n")

if __name__ == "__main__":
    main()
