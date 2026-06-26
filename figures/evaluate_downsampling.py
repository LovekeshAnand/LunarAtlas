#!/usr/bin/env python3
"""
LunarAtlas Downsampling and Peak Preservation Evaluation Script
==============================================================
Reproduces all metrics and LaTeX tables for Section 4.3 of the paper.
"""

import os
import sys
import time
import math
import json
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.signal import find_peaks
from scipy.interpolate import interp1d

# Add core/server to path for app imports
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir / "core" / "server"))

from app.core.downsampling import lttb_downsample

# NIST Reference lines from the pipeline
NIST_DB = [
    {"element": "Mg II", "wavelength": 279.55},
    {"element": "Mg II", "wavelength": 280.27},
    {"element": "Mg I",  "wavelength": 285.21},
    {"element": "Si I",  "wavelength": 288.16},
    {"element": "Al I",  "wavelength": 308.22},
    {"element": "Al I",  "wavelength": 309.27},
    {"element": "Ti II", "wavelength": 334.94},
    {"element": "Fe I",  "wavelength": 373.49},
    {"element": "Fe I",  "wavelength": 385.99},
    {"element": "Si I",  "wavelength": 390.55},
    {"element": "Ca II", "wavelength": 393.37},
    {"element": "Al I",  "wavelength": 394.40},
    {"element": "Al I",  "wavelength": 396.15},
    {"element": "Ca II", "wavelength": 396.85},
    {"element": "Fe I",  "wavelength": 404.58},
    {"element": "Ca I",  "wavelength": 422.67},
    {"element": "Fe I",  "wavelength": 438.36},
    {"element": "Mg I",  "wavelength": 518.36},
    {"element": "Na I",  "wavelength": 588.99},
    {"element": "Na I",  "wavelength": 589.59},
    {"element": "H I",   "wavelength": 656.28},
    {"element": "O I",   "wavelength": 777.19},
    {"element": "Ca II", "wavelength": 849.80},
    {"element": "Ca II", "wavelength": 854.21},
    {"element": "Ca II", "wavelength": 866.21},
]

def uniform_decimation(wavelengths, intensities, threshold):
    """Uniform decimation keeping first and last points."""
    if threshold <= 2:
        return [0, len(wavelengths) - 1] if len(wavelengths) > 1 else [0]
    indices = np.linspace(0, len(wavelengths) - 1, threshold, dtype=int)
    return sorted(list(set(indices)))

def max_binning(wavelengths, intensities, threshold):
    """Max-binning keeping first and last points, taking argmax per bin."""
    if threshold <= 2:
        return [0, len(wavelengths) - 1] if len(wavelengths) > 1 else [0]
    inner_indices = np.arange(1, len(wavelengths) - 1)
    bins = np.array_split(inner_indices, threshold - 2)
    sampled = [0]
    for b in bins:
        if len(b) > 0:
            max_idx = b[np.argmax(intensities[b])]
            sampled.append(int(max_idx))
    sampled.append(len(wavelengths) - 1)
    return sorted(list(set(sampled)))

def compute_retention(peak_indices, downsampled_indices):
    """Compute peak retention rate using the formal ±1 channel neighbor definition."""
    if len(peak_indices) == 0:
        return 100.0
    retained_count = 0
    ds_set = set(downsampled_indices)
    for ip in peak_indices:
        # Check if ip, ip-1, or ip+1 is in downsampled_indices
        if ip in ds_set or (ip - 1) in ds_set or (ip + 1) in ds_set:
            retained_count += 1
    return (retained_count / len(peak_indices)) * 100.0

def compute_rmse(wavelengths, intensities, downsampled_indices):
    """Compute RMSE of reconstructed spectrum via linear interpolation."""
    if len(downsampled_indices) < 2:
        return 0.0
    ds_wl = wavelengths[downsampled_indices]
    ds_int = intensities[downsampled_indices]
    
    f = interp1d(ds_wl, ds_int, kind='linear', fill_value="extrapolate")
    interp_int = f(wavelengths)
    
    rmse = np.sqrt(np.mean((intensities - interp_int) ** 2))
    return rmse

def compute_fidelity(wavelengths, intensities, peak_indices, downsampled_indices):
    """Compute peak height and position errors for retained peaks."""
    pos_errors = []
    height_errors = []
    pct_errors = []
    
    ds_set = set(downsampled_indices)
    for ip in peak_indices:
        # Check if peak is retained (±1 channel)
        if ip in ds_set or (ip - 1) in ds_set or (ip + 1) in ds_set:
            # Nearest index in downsampled_indices
            j_nearest = min(downsampled_indices, key=lambda idx: abs(idx - ip))
            
            wl_diff = abs(wavelengths[ip] - wavelengths[j_nearest])
            h_diff = abs(intensities[ip] - intensities[j_nearest])
            pct_diff = (h_diff / intensities[ip] * 100.0) if intensities[ip] > 0 else 0.0
            
            pos_errors.append(wl_diff)
            height_errors.append(h_diff)
            pct_errors.append(pct_diff)
            
    if not pos_errors:
        return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        
    return (
        np.mean(pos_errors), np.std(pos_errors),
        np.mean(height_errors), np.std(height_errors),
        np.mean(pct_errors), np.std(pct_errors)
    )

def main():
    print("==============================================================")
    # Load cleaned data
    cleaned_path = root_dir / "datasets" / "processed" / "calibrated" / "20230825" / "ch3_lib_002_20230825T104221_00_l1" / "ch3_lib_002_20230825T104221_00_l1_cleaned.csv"
    if not cleaned_path.exists():
        # Fallback to search if path is different
        print("[INFO] Cleaned path not found. Searching...")
        candidates = list((root_dir / "datasets").glob("**/calibrated/*/*/*_cleaned.csv"))
        if not candidates:
            print("[ERROR] No cleaned files found.")
            sys.exit(1)
        cleaned_path = candidates[0]
        
    print(f"Loading cleaned dataset: {cleaned_path.name}")
    df = pd.read_csv(cleaned_path)
    
    # Evaluate prominence per measurement ID
    mids = sorted(df['Measurement_ID'].unique())
    measurements = {}
    
    print("\n--- Phase 1: Peak Detection & Prominence Computation ---")
    for mid in mids:
        sub = df[df['Measurement_ID'] == mid].sort_values('Wavelength_nm')
        wls = sub['Wavelength_nm'].values
        ints = sub['Cleaned_Intensity'].values
        
        # Continuum region (560-580 nm)
        cont_mask = (wls >= 560.0) & (wls <= 580.0)
        if np.sum(cont_mask) > 0:
            noise_floor = np.std(ints[cont_mask])
        else:
            # Fallback if window is missing
            noise_floor = 15.0
            
        prominence = 3 * noise_floor
        
        # Peak detection: prominence = 3σ, minimum distance = 5 channels
        peaks, _ = find_peaks(ints, prominence=prominence, distance=5)
        
        # NIST matching
        nist_matched_peaks = []
        for pk_idx in peaks:
            pk_wl = wls[pk_idx]
            is_nist = any(abs(pk_wl - entry["wavelength"]) < 0.5 for entry in NIST_DB)
            if is_nist:
                nist_matched_peaks.append(pk_idx)
                
        measurements[mid] = {
            "wls": wls,
            "ints": ints,
            "noise_floor": noise_floor,
            "prominence": prominence,
            "peaks": peaks,
            "nist_peaks": np.array(nist_matched_peaks)
        }
        
        print(f"Measurement ID {mid}:")
        print(f"  - Noise Floor (560-580 nm): {noise_floor:.2f} counts")
        print(f"  - 3-sigma Prominence Threshold: {prominence:.2f} counts")
        print(f"  - Detected Peaks: {len(peaks)} local maxima")
        print(f"  - NIST-Matched Peaks: {len(nist_matched_peaks)} / {len(peaks)}")
        
    # Main evaluations on Valid Plasmas (IDs 3 and 4)
    print("\n--- Phase 2: Algorithm Comparison at 10% Density (Measurement ID 3) ---")
    # 10% density of 2094 is 209 points
    mid_eval = 3
    data_eval = measurements[mid_eval]
    wls = data_eval["wls"]
    ints = data_eval["ints"]
    peaks = data_eval["peaks"]
    nist_peaks = data_eval["nist_peaks"]
    
    n_points = len(wls)
    threshold = 209 # 10%
    proportion = 0.10
    
    data_2d = np.column_stack([wls, ints])
    target_wls = [float(x) for x in wls[peaks]]
    
    # 1. Uniform
    uniform_idx = uniform_decimation(wls, ints, threshold)
    # 2. Max-binning
    maxbin_idx = max_binning(wls, ints, threshold)
    # 3. LTTB
    lttb_res = lttb_downsample(data_2d, zoom_level=0, lambda_min=wls.min(), lambda_max=wls.max(), target_wavelengths=None, proportion=proportion)
    lttb_idx = [np.searchsorted(wls, p["wavelength_nm"]) for p in lttb_res["data"]]
    # Ensure they map to valid indices
    lttb_idx = [min(idx, n_points - 1) for idx in lttb_idx]
    
    # 4. LTTB+Peaks
    lttb_peaks_res = lttb_downsample(data_2d, zoom_level=0, lambda_min=wls.min(), lambda_max=wls.max(), target_wavelengths=target_wls, proportion=proportion)
    lttb_peaks_idx = [np.searchsorted(wls, p["wavelength_nm"]) for p in lttb_peaks_res["data"]]
    lttb_peaks_idx = [min(idx, n_points - 1) for idx in lttb_peaks_idx]
    
    # Compute metrics for ID 3
    algorithms = {
        "Uniform decimation": uniform_idx,
        "Max-binning": maxbin_idx,
        "Standard LTTB": lttb_idx,
        "LTTB + Peaks": lttb_peaks_idx
    }
    
    comparison_results = {}
    for name, idxs in algorithms.items():
        ret = compute_retention(peaks, idxs)
        rmse = compute_rmse(wls, ints, idxs)
        comparison_results[name] = {"retention": ret, "rmse": rmse, "size": len(idxs)}
        print(f"{name:20s}: Size = {len(idxs)}, Peak Retention = {ret:.2f}%, RMSE = {rmse:.4f}")
        
    # Latency benchmarks
    print("\n--- Latency Benchmarks (1000 Repetitions on Measurement ID 3) ---")
    latency_results = {}
    for name, idxs in algorithms.items():
        times = []
        for _ in range(1000):
            t0 = time.perf_counter()
            if name == "Uniform decimation":
                _ = uniform_decimation(wls, ints, threshold)
            elif name == "Max-binning":
                _ = max_binning(wls, ints, threshold)
            elif name == "Standard LTTB":
                _ = lttb_downsample(data_2d, zoom_level=0, lambda_min=wls.min(), lambda_max=wls.max(), target_wavelengths=None, proportion=proportion)
            elif name == "LTTB + Peaks":
                _ = lttb_downsample(data_2d, zoom_level=0, lambda_min=wls.min(), lambda_max=wls.max(), target_wavelengths=target_wls, proportion=proportion)
            t1 = time.perf_counter()
            times.append((t1 - t0) * 1000.0) # ms
            
        mean_l = np.mean(times)
        std_l = np.std(times)
        latency_results[name] = (mean_l, std_l)
        print(f"{name:20s}: Latency = {mean_l:.3f} ± {std_l:.3f} ms")
        
    # Dual Retention Metrics (Table A)
    print("\n--- Dual Retention Metrics (Measurement ID 3) ---")
    dual_metrics = {}
    for name in ["Standard LTTB", "LTTB + Peaks"]:
        idxs = algorithms[name]
        loc_max_ret = compute_retention(peaks, idxs)
        nist_ret = compute_retention(nist_peaks, idxs)
        dual_metrics[name] = {
            "local_maxima": loc_max_ret,
            "nist_matched": nist_ret
        }
        print(f"{name:15s}: Local Maxima Retention = {loc_max_ret:.2f}%, NIST-matched Peak Retention = {nist_ret:.2f}%")
        
    # Density sweep
    print("\n--- Phase 3: Density Sweep (Peak Retention %) ---")
    densities = [0.05, 0.10, 0.15, 0.20, 0.50]
    sweep_results = {name: [] for name in algorithms.keys()}
    
    for d in densities:
        t_size = int(n_points * d)
        target_wls_sweep = [float(x) for x in wls[peaks]]
        
        # Uniform
        u_idx = uniform_decimation(wls, ints, t_size)
        sweep_results["Uniform decimation"].append(compute_retention(peaks, u_idx))
        
        # Max-binning
        mb_idx = max_binning(wls, ints, t_size)
        sweep_results["Max-binning"].append(compute_retention(peaks, mb_idx))
        
        # LTTB
        l_res = lttb_downsample(data_2d, zoom_level=0, lambda_min=wls.min(), lambda_max=wls.max(), target_wavelengths=None, proportion=d)
        l_idx = [min(np.searchsorted(wls, p["wavelength_nm"]), n_points - 1) for p in l_res["data"]]
        sweep_results["Standard LTTB"].append(compute_retention(peaks, l_idx))
        
        # LTTB+Peaks
        lp_res = lttb_downsample(data_2d, zoom_level=0, lambda_min=wls.min(), lambda_max=wls.max(), target_wavelengths=target_wls_sweep, proportion=d)
        lp_idx = [min(np.searchsorted(wls, p["wavelength_nm"]), n_points - 1) for p in lp_res["data"]]
        sweep_results["LTTB + Peaks"].append(compute_retention(peaks, lp_idx))
        
    for name, rets in sweep_results.items():
        sweep_str = ", ".join(f"{d*100:.0f}%: {r:.1f}%" for d, r in zip(densities, rets))
        print(f"{name:20s}: {sweep_str}")
        
    # Peak Fidelity (Table C) for valid plasmas (ID 3 and 4)
    print("\n--- Phase 4: Peak Fidelity Metrics (retained by LTTB+Peaks @ 10% density) ---")
    fidelity_results = {}
    for mid in [3, 4]:
        d_val = measurements[mid]
        wls_m = d_val["wls"]
        ints_m = d_val["ints"]
        peaks_m = d_val["peaks"]
        target_wls_m = [float(x) for x in wls_m[peaks_m]]
        
        d_2d_m = np.column_stack([wls_m, ints_m])
        lp_res = lttb_downsample(d_2d_m, zoom_level=0, lambda_min=wls_m.min(), lambda_max=wls_m.max(), target_wavelengths=target_wls_m, proportion=0.10)
        lp_idx = [min(np.searchsorted(wls_m, p["wavelength_nm"]), len(wls_m) - 1) for p in lp_res["data"]]
        
        mean_pos_err, std_pos_err, mean_h_err, std_h_err, mean_pct_err, std_pct_err = compute_fidelity(
            wls_m, ints_m, peaks_m, lp_idx
        )
        
        fidelity_results[mid] = {
            "pos_mean": mean_pos_err, "pos_std": std_pos_err,
            "height_mean": mean_h_err, "height_std": std_h_err,
            "pct_mean": mean_pct_err, "pct_std": std_pct_err
        }
        print(f"Measurement ID {mid}:")
        print(f"  - Peak position error: {mean_pos_err:.4f} ± {std_pos_err:.4f} nm")
        print(f"  - Peak height error: {mean_h_err:.2f} ± {std_h_err:.2f} counts")
        print(f"  - Peak height error (%): {mean_pct_err:.2f}% ± {std_pct_err:.2f}%")
        
    # Compute mean across IDs 3 & 4
    mean_pos_all = (fidelity_results[3]["pos_mean"] + fidelity_results[4]["pos_mean"]) / 2
    mean_pos_std_all = np.sqrt(fidelity_results[3]["pos_std"]**2 + fidelity_results[4]["pos_std"]**2) / np.sqrt(2)
    mean_h_all = (fidelity_results[3]["height_mean"] + fidelity_results[4]["height_mean"]) / 2
    mean_h_std_all = np.sqrt(fidelity_results[3]["height_std"]**2 + fidelity_results[4]["height_std"]**2) / np.sqrt(2)
    mean_pct_all = (fidelity_results[3]["pct_mean"] + fidelity_results[4]["pct_mean"]) / 2
    mean_pct_std_all = np.sqrt(fidelity_results[3]["pct_std"]**2 + fidelity_results[4]["pct_std"]**2) / np.sqrt(2)
    
    fidelity_results["mean"] = {
        "pos_mean": mean_pos_all, "pos_std": mean_pos_std_all,
        "height_mean": mean_h_all, "height_std": mean_h_std_all,
        "pct_mean": mean_pct_all, "pct_std": mean_pct_std_all
    }
    
    # Save JSON of all evaluation results
    all_results = {
        "measurements": {
            int(mid): {
                "noise_floor": float(measurements[mid]["noise_floor"]),
                "prominence": float(measurements[mid]["prominence"]),
                "n_peaks": int(len(measurements[mid]["peaks"])),
                "n_nist_peaks": int(len(measurements[mid]["nist_peaks"]))
            } for mid in mids
        },
        "comparison_id3": {
            name: {
                "retention": float(res["retention"]),
                "rmse": float(res["rmse"]),
                "size": int(res["size"]),
                "latency_mean": float(latency_results[name][0]),
                "latency_std": float(latency_results[name][1])
            } for name, res in comparison_results.items()
        },
        "dual_metrics_id3": {
            name: {
                "local_maxima": float(dual_metrics[name]["local_maxima"]),
                "nist_matched": float(dual_metrics[name]["nist_matched"])
            } for name in ["Standard LTTB", "LTTB + Peaks"]
        },
        "density_sweep_id3": {
            name: [float(r) for r in sweep_results[name]] for name in algorithms.keys()
        },
        "fidelity": {
            str(k): {vk: float(vv) for vk, vv in v.items()} for k, v in fidelity_results.items()
        }
    }
    
    output_json = root_dir / "figures" / "downsampling_eval_results.json"
    with open(output_json, 'w') as f:
        json.dump(all_results, f, indent=4)
    print(f"\n[SUCCESS] Saved all results to {output_json.name}")
    
    # Print LaTeX snippets ready for copy-pasting
    print("\n" + "="*40 + " LaTeX Snippets " + "="*40)
    
    # Snippet 1: Downsampling Algorithm Comparison Table (Table 5)
    print("\n--- Table 5 LaTeX Snippet ---")
    print(r"\begin{table}[h]")
    print(r"\centering")
    print(r"\caption{Downsampling algorithm comparison at 10\% density (209 points from 2,094) for Measurement ID 3. Retention: fraction of detected peaks preserved. RMSE: computed against the full 2,094-point spectrum. Latency: mean $\pm$ std over 1,000 repetitions on Intel Core i7-12700.}")
    print(r"\label{table:downsampling}")
    print(r"\begin{tabular}{lccc}")
    print(r"\hline")
    print(r"Algorithm & Retention (\%) & RMSE (counts) & Latency (ms) \\")
    print(r"\hline")
    for name in ["Uniform decimation", "Max-binning", "Standard LTTB", "LTTB + Peaks"]:
        res = comparison_results[name]
        lat = latency_results[name]
        bold_prefix = r"\textbf{" if name == "LTTB + Peaks" else ""
        bold_suffix = r"}" if name == "LTTB + Peaks" else ""
        print(f"{bold_prefix}{name}{bold_suffix} & {bold_prefix}{res['retention']:.1f}\\%{bold_suffix} & {bold_prefix}{res['rmse']:.2f}{bold_suffix} & {bold_prefix}{lat[0]:.2f} $\\pm$ {lat[1]:.2f}{bold_suffix} \\\\")
    print(r"\hline")
    print(r"\end{tabular}")
    print(r"\end{table}")
    
    # Snippet 2: Dual Retention Metrics Table
    print("\n--- Dual Retention Table LaTeX Snippet ---")
    print(r"\begin{table}[h]")
    print(r"\centering")
    print(r"\caption{Engineering vs. scientific peak retention validation at 10\% density for Measurement ID 3.}")
    print(r"\label{table:dual_retention}")
    print(r"\begin{tabular}{lcc}")
    print(r"\hline")
    print(r"Metric & Standard LTTB & LTTB+Peaks \\")
    print(r"\hline")
    print(f"Local maxima retention & {dual_metrics['Standard LTTB']['local_maxima']:.1f}\\% & \\textbf{{{dual_metrics['LTTB + Peaks']['local_maxima']:.1f}\\%}} \\\\")
    print(f"NIST-matched peak retention & {dual_metrics['Standard LTTB']['nist_matched']:.1f}\\% & \\textbf{{{dual_metrics['LTTB + Peaks']['nist_matched']:.1f}\\%}} \\\\")
    print(r"\hline")
    print(r"\end{tabular}")
    print(r"\end{table}")
    
    # Snippet 3: Density Sweep Table (Table 6)
    print("\n--- Density Sweep Table LaTeX Snippet ---")
    print(r"\begin{table}[h]")
    print(r"\centering")
    print(r"\caption{Peak retention (\%) as a function of downsampling density (Measurement ID 3).}")
    print(r"\label{table:density_sweep}")
    print(r"\begin{tabular}{lccccc}")
    print(r"\hline")
    print(r"Algorithm & 5\% (104 pts) & 10\% (209 pts) & 15\% (314 pts) & 20\% (418 pts) & 50\% (1047 pts) \\")
    print(r"\hline")
    for name in ["Uniform decimation", "Max-binning", "Standard LTTB", "LTTB + Peaks"]:
        rets = sweep_results[name]
        bold_prefix = r"\textbf{" if name == "LTTB + Peaks" else ""
        bold_suffix = r"}" if name == "LTTB + Peaks" else ""
        print(f"{bold_prefix}{name}{bold_suffix} & " + " & ".join(f"{bold_prefix}{r:.1f}\\%{bold_suffix}" for r in rets) + r" \\")
    print(r"\hline")
    print(r"\end{tabular}")
    print(r"\end{table}")
    
    # Snippet 4: Peak Fidelity Table (Table 7)
    print("\n--- Peak Fidelity Table LaTeX Snippet ---")
    print(r"\begin{table}[h]")
    print(r"\centering")
    print(r"\caption{Peak height and position errors for retained peaks using LTTB+Peaks at 10\% density.}")
    print(r"\label{table:fidelity}")
    print(r"\begin{tabular}{lccc}")
    print(r"\hline")
    print(r"Metric & Measurement ID 3 & Measurement ID 4 & Combined Mean \\")
    print(r"\hline")
    
    fid3 = fidelity_results[3]
    fid4 = fidelity_results[4]
    fid_mean = fidelity_results["mean"]
    
    print(f"Peak position error (nm) & {fid3['pos_mean']:.3f} $\\pm$ {fid3['pos_std']:.3f} & {fid4['pos_mean']:.3f} $\\pm$ {fid4['pos_std']:.3f} & {fid_mean['pos_mean']:.3f} $\\pm$ {fid_mean['pos_std']:.3f} \\\\")
    print(f"Peak height error (counts) & {fid3['height_mean']:.2f} $\\pm$ {fid3['height_std']:.2f} & {fid4['height_mean']:.2f} $\\pm$ {fid4['height_std']:.2f} & {fid_mean['height_mean']:.2f} $\\pm$ {fid_mean['height_std']:.2f} \\\\")
    print(f"Peak height error (\\%) & {fid3['pct_mean']:.2f}\\% $\\pm$ {fid3['pct_std']:.2f}\\% & {fid4['pct_mean']:.2f}\\% $\\pm$ {fid4['pct_std']:.2f}\\% & {fid_mean['pct_mean']:.2f}\\% $\\pm$ {fid_mean['pct_std']:.2f}\\% \\\\")
    
    print(r"\hline")
    print(r"\end{tabular}")
    print(r"\end{table}")
    
    print("="*96 + "\n")

if __name__ == "__main__":
    main()
