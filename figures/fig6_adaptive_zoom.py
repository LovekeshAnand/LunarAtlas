#!/usr/bin/env python3
"""
fig6_adaptive_zoom.py — Figure 6 Generator
Generates a 2x2 multi-panel plot showing LTTB + Peaks downsampling at four zoom levels
(k = 1, 2, 3, and 4) applied to the cleaned Chandrayaan-3 spectrum.
Ensures x-axis tick labels are visible on all subplots and eliminates overlapping.
"""

import os
import sys
import math
import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

def lttb_peaks_downsample(wl, val, threshold, raw_peaks_idx):
    n_raw = len(wl)
    if threshold >= n_raw:
        return np.arange(n_raw)
        
    every = (n_raw - 2) / (threshold - 2)
    lttb_indices = [0]
    a = 0
    for i in range(threshold - 2):
        avg_start = math.floor((i + 1) * every) + 1
        avg_end = min(math.floor((i + 2) * every) + 1, n_raw)
        avg_x = np.mean(wl[avg_start:avg_end])
        avg_y = np.mean(val[avg_start:avg_end])
        
        r_start = math.floor(i * every) + 1
        r_end = math.floor((i + 1) * every) + 1
        bx = wl[r_start:r_end]
        by = val[r_start:r_end]
        
        areas = np.abs(
            wl[a] * (by - avg_y) +
            bx * (avg_y - val[a]) +
            avg_x * (val[a] - by)
        )
        max_idx = r_start + np.argmax(areas)
        lttb_indices.append(int(max_idx))
        a = max_idx
    lttb_indices.append(n_raw - 1)
    
    # Peak-Union step: combine LTTB indices with raw peaks indices
    combined = set(lttb_indices) | set(raw_peaks_idx)
    return sorted(list(combined))

def main():
    print("[Fig 6] Generating LTTB+Peaks multi-zoom panel plot...")
    
    # Paths
    cleaned_data = r"d:\LunarAtlas\datasets\processed\calibrated\20230825\ch3_lib_002_20230825T104221_00_l1\ch3_lib_002_20230825T104221_00_l1_cleaned.csv"
    output_dir = Path("publication_figures")
    
    d_path = Path(sys.argv[1] if len(sys.argv) > 1 else cleaned_data)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not d_path.exists():
        raise FileNotFoundError(f"Cleaned data file not found: {d_path}")
        
    df = pd.read_csv(d_path)
    
    sub = df[df['Measurement_ID'] == 3].sort_values('Wavelength_nm')
    wl = sub['Wavelength_nm'].values
    val = sub['Cleaned_Intensity'].values
    ymax = max(val)
    
    # Detect peaks for reference
    cont_mask = (wl >= 560.0) & (wl <= 580.0)
    noise_floor = np.std(val[cont_mask])
    prominence = 3 * noise_floor
    raw_peaks_idx, _ = find_peaks(val, prominence=prominence, distance=5)
    
    # Set up matplotlib configuration
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['Arial', 'Liberation Sans', 'DejaVu Sans'],
        'svg.fonttype': 'none',
        'xtick.direction': 'in',
        'ytick.direction': 'in',
        'xtick.top': True,
        'ytick.right': True,
        'xtick.minor.visible': True,
        'ytick.minor.visible': True
    })
    
    # Set sharex=False to ensure x-axis labels are visible on all 4 subplots
    fig, axs = plt.subplots(2, 2, figsize=(12, 7.2), dpi=300, sharex=False, sharey=True)
    axs = axs.ravel()
    
    zoom_levels = [1, 2, 3, 4]
    letters = ['(a)', '(b)', '(c)', '(d)']
    
    for idx, k in enumerate(zoom_levels):
        ax = axs[idx]
        
        target_size = int(math.ceil(2094 * (2 ** -k)))
        down_idx = lttb_peaks_downsample(wl, val, target_size, raw_peaks_idx)
        n_down = len(down_idx)
        pct = (n_down / len(wl)) * 100
        
        ax.plot(wl, val, color='#cbd5e1', lw=0.5, alpha=0.7, label='Full Resolution')
        ax.plot(wl[down_idx], val[down_idx], color='#1d4ed8', lw=0.6, alpha=0.9,
                marker='o', markersize=1.5, markeredgecolor='#1d4ed8', label='Downsampled')
        
        ax.scatter(wl[raw_peaks_idx], val[raw_peaks_idx], color='#dc2626', marker='x', 
                   s=12, zorder=5, label='Preserved Peaks')
        
        # Clean text placement at the top-left (no bounding box overlap, smaller text)
        ax.text(
            0.03, 0.95, f"{letters[idx]} Zoom level $k={k}$\n$N={n_down}$ points ({pct:.1f}%)", 
            transform=ax.transAxes, ha='left', va='top', fontsize=8, fontweight='bold',
            color='#1e293b'
        )
        
        ax.set_xlim(240.0, 800.0)
        # Increased y-axis limit headroom from 1.1 to 1.35 to prevent overlap with the legend/labels
        ax.set_ylim(-25, ymax * 1.35)
        ax.grid(True, color='#f1f5f9', linestyle='-', linewidth=0.5)
        
        ax.tick_params(which='major', length=5, width=0.7, color='#94a3b8')
        ax.tick_params(which='minor', length=2.5, width=0.5, color='#cbd5e1')
        
        # Ensure tick labels are visible on all subplots
        ax.tick_params(labelbottom=True)
        
        for spine in ['top', 'bottom', 'left', 'right']:
            ax.spines[spine].set_color('#cbd5e1')
            ax.spines[spine].set_linewidth(0.8)
            
    # Set axis labels for all subplots (since they all show ticks)
    for ax in axs:
        ax.set_xlabel("Wavelength (nm)", fontsize=9, fontweight='semibold', color='#0f172a')
    
    axs[0].set_ylabel("Cleaned Intensity (a.u.)", fontsize=9, fontweight='semibold', color='#0f172a')
    axs[2].set_ylabel("Cleaned Intensity (a.u.)", fontsize=9, fontweight='semibold', color='#0f172a')
    
    # Place a clean, non-overlapping legend at the top right of panel 1
    axs[1].legend(loc='upper right', facecolor='white', edgecolor='#e2e8f0', framealpha=0.9, fontsize=8)
    
    png_path = output_dir / "fig6_adaptive_zoom.png"
    pdf_path = output_dir / "fig6_adaptive_zoom.pdf"
    
    plt.tight_layout()
    fig.savefig(png_path, dpi=300, bbox_inches='tight')
    fig.savefig(pdf_path, bbox_inches='tight')
    print(f"  * Saved Figure 6 to: {png_path} and {pdf_path}")
    plt.close()

if __name__ == "__main__":
    main()
