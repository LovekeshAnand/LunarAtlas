#!/usr/bin/env python3
"""
fig4_peak_comparison.py — Figure 4 Generator
Calculates LTTB downsampling on full 2,094-point spectrum and displays a zoomed-in range (250.0 - 450.0 nm)
to clearly illustrate peak preservation details.
"""

import os
import sys
import math
import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

def main():
    print("[Fig 4] Generating peak comparison plot...")
    
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
    
    # Compute noise floor from a continuum region (560-580 nm)
    cont_mask = (wl >= 560.0) & (wl <= 580.0)
    noise_floor = np.std(val[cont_mask])
    prominence = 3 * noise_floor
    
    raw_peaks_idx, _ = find_peaks(val, prominence=prominence, distance=5)
    n_raw_peaks = len(raw_peaks_idx)
    
    threshold = 200
    n_raw = len(wl)
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
    lttb_indices = sorted(list(set(lttb_indices)))
    
    preserved_peaks = []
    missed_peaks = []
    for idx in raw_peaks_idx:
        retained = False
        for s_idx in lttb_indices:
            if abs(s_idx - idx) <= 1:
                retained = True
                break
        if retained:
            preserved_peaks.append(idx)
        else:
            missed_peaks.append(idx)
            
    n_preserved = len(preserved_peaks)
    n_missed = len(missed_peaks)
    
    # Set up matplotlib configuration
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['Arial', 'Liberation Sans', 'DejaVu Sans'],
        'svg.fonttype': 'none',
        'xtick.direction': 'in',
        'ytick.direction': 'in',
        'xtick.top': True,
        'ytick.right': True
    })
    
    fig, ax = plt.subplots(figsize=(10, 4.8), dpi=300)
    
    # Darker grey raw spectrum background line for contrast
    ax.plot(wl, val, color='#64748b', lw=0.6, alpha=0.85, label='Raw Spectrum')
    
    wl_d = wl[lttb_indices]
    val_d = val[lttb_indices]
    ax.plot(wl_d, val_d, color='#0284c7', lw=0.8, alpha=0.9, label=f'LTTB Downsampled ({threshold} pts)')
    
    # Plot markers
    if preserved_peaks:
        ax.scatter(wl[preserved_peaks], val[preserved_peaks], 
                   color='#16a34a', marker='o', s=12, zorder=5, alpha=0.95,
                   label=f'Preserved Peaks ({n_preserved}/{n_raw_peaks})')
                   
    if missed_peaks:
        ax.scatter(wl[missed_peaks], val[missed_peaks], 
                   color='#dc2626', marker='x', s=18, zorder=5, alpha=0.95,
                   label=f'Missed Peaks ({n_missed}/{n_raw_peaks})')
                   
    # Focused range of wavelengths (250.0 to 450.0 nm) as requested
    ax.set_xlim(250.0, 450.0)
    
    # Calculate y-headroom specifically for the zoomed range (leaving space for the legend)
    zoomed_val = val[(wl >= 250.0) & (wl <= 450.0)]
    zoom_ymax = max(zoomed_val)
    ax.set_ylim(bottom=-20, top=zoom_ymax * 1.30)
    
    ax.set_xlabel("Wavelength (nm)", fontsize=10, fontweight='semibold', color='#0f172a')
    ax.set_ylabel("Intensity (a.u.)", fontsize=10, fontweight='semibold', color='#0f172a')
    ax.grid(True, color='#f1f5f9', linestyle='-', linewidth=0.5)
    ax.set_facecolor('#fafafb')
    
    for spine in ['top', 'bottom', 'left', 'right']:
        ax.spines[spine].set_color('#cbd5e1')
        ax.spines[spine].set_linewidth(0.8)
        
    ax.legend(loc='upper right', facecolor='white', edgecolor='#e2e8f0', framealpha=0.95, fontsize=9.5)
    
    png_path = output_dir / "fig4_peak_comparison.png"
    pdf_path = output_dir / "fig4_peak_comparison.pdf"
    
    fig.savefig(png_path, dpi=300, bbox_inches='tight')
    fig.savefig(pdf_path, bbox_inches='tight')
    print(f"  * Saved Figure 4 to: {png_path} and {pdf_path}")
    plt.close()

if __name__ == "__main__":
    main()
