#!/usr/bin/env python3
"""
fig3_pre_post_overlay.py — Figure 3 Generator
"""

import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt

def main():
    print("[Fig 3] Generating pre- vs. post-subtraction spectrum overlay...")
    
    # Paths
    raw_data = r"d:\LunarAtlas\datasets\uploads\20230825\ch3_lib_002_20230825T104221_00_l1\ch3_lib_002_20230825T104221_00_l1.csv"
    cleaned_data = r"d:\LunarAtlas\datasets\processed\calibrated\20230825\ch3_lib_002_20230825T104221_00_l1\ch3_lib_002_20230825T104221_00_l1_cleaned.csv"
    output_dir = Path("publication_figures")
    
    r_path = Path(sys.argv[1] if len(sys.argv) > 1 else raw_data)
    d_path = Path(sys.argv[2] if len(sys.argv) > 2 else cleaned_data)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not r_path.exists():
        raise FileNotFoundError(f"Raw data file not found: {r_path}")
    if not d_path.exists():
        raise FileNotFoundError(f"Cleaned data file not found: {d_path}")
        
    df = pd.read_csv(d_path)
    raw_df = pd.read_csv(r_path)
    
    # We need raw wide-form row 3 (iloc[2] of plasma) and cleaned row 3
    # Extract wavelengths and values
    wl_cols = [c for c in raw_df.columns if c.replace('.', '', 1).isdigit()]
    raw_wl = np.array([float(c) for c in wl_cols])
    
    fire_col = 'Laser Fire status' if 'Laser Fire status' in raw_df.columns else 'Laser Fire Status'
    reset_col = 'Force Reset status' if 'Force Reset status' in raw_df.columns else 'Force Reset Status'
    plasma_df = raw_df[(raw_df[fire_col] == 1) & (raw_df[reset_col] == 0)].copy()
    
    # Row 3 values
    raw_val = plasma_df.iloc[2][wl_cols].values.astype(float)
    
    # Cleaned values for ID 3
    c_sub = df[df['Measurement_ID'] == 3].sort_values('Wavelength_nm')
    cleaned_wl = c_sub['Wavelength_nm'].values
    cleaned_val = c_sub['Cleaned_Intensity'].values
    
    # Filters for 560 - 580 nm validation window
    raw_mask = (raw_wl >= 560.0) & (raw_wl <= 580.0)
    cleaned_mask = (cleaned_wl >= 560.0) & (cleaned_wl <= 580.0)
    
    w_raw = raw_wl[raw_mask]
    v_raw = raw_val[raw_mask]
    
    w_clean = cleaned_wl[cleaned_mask]
    v_clean = cleaned_val[cleaned_mask]
    
    mean_raw = np.mean(v_raw)
    mean_clean = np.mean(v_clean)
    
    # Set up matplotlib configuration
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['Arial', 'Liberation Sans', 'DejaVu Sans'],
        'svg.fonttype': 'none'
    })
    
    fig, ax = plt.subplots(figsize=(10, 4.0), dpi=300)
    
    # Plot spectrum overlay lines
    ax.plot(w_raw, v_raw, color='#94a3b8', linestyle='-', lw=1.2, alpha=0.9, label='Raw L1 Intensity (a.u.)')
    ax.plot(w_clean, v_clean, color='#0284c7', linestyle='-', lw=1.2, alpha=0.9, label='Cleaned L1-Processed Intensity (a.u.)')
    
    # Draw mean level lines
    ax.axhline(mean_raw, color='#b91c1c', linestyle='--', lw=1.0, alpha=0.8)
    ax.axhline(mean_clean, color='#0369a1', linestyle='--', lw=1.0, alpha=0.8)
    
    # Text annotations for means
    ax.text(561.0, mean_raw + 25, f"Mean Raw: {mean_raw:.1f} a.u.", fontsize=8.5, color='#b91c1c', fontweight='semibold')
    ax.text(561.0, mean_clean + 25, f"Mean Cleaned: {mean_clean:.1f} a.u.", fontsize=8.5, color='#0369a1', fontweight='semibold')
    
    # Double-headed arrow indicating baseline suppression
    arrow_x = 578.0
    ax.annotate(
        '', xy=(arrow_x, mean_clean), xytext=(arrow_x, mean_raw),
        arrowprops=dict(arrowstyle="<->", color='#475569', lw=1.2, shrinkA=0, shrinkB=0)
    )
    
    # Ratio label
    ratio = mean_raw / mean_clean if mean_clean > 0 else 0
    ax.text(
        arrow_x - 0.3, (mean_raw + mean_clean)/2, f"Baseline Suppression\nRatio: {ratio:.2f}×",
        fontsize=8.5, fontweight='bold', color='#475569', ha='right', va='center'
    )
    
    ax.set_xlim(560.0, 580.0)
    # Increased top y-limit boundary from 1.15 to 1.35 to allocate vertical headroom for the legend box
    ax.set_ylim(bottom=0, top=max(v_raw) * 1.35)
    ax.grid(True, color='#f1f5f9', linestyle='-', linewidth=0.5)
    ax.set_facecolor('#fafafb')
    
    # Set y-axis and x-axis ticks inward
    ax.tick_params(direction='in', top=True, right=True)
    
    # Axis borders
    for spine in ['top', 'bottom', 'left', 'right']:
        ax.spines[spine].set_color('#cbd5e1')
        ax.spines[spine].set_linewidth(0.8)
        
    ax.set_xlabel("Wavelength (nm)", fontsize=10, fontweight='semibold', color='#0f172a')
    ax.set_ylabel("Intensity (a.u.)", fontsize=10, fontweight='semibold', color='#0f172a')
    
    ax.legend(loc='upper right', facecolor='white', edgecolor='#e2e8f0', framealpha=0.95)
    
    png_path = output_dir / "fig3_pre_post_overlay.png"
    pdf_path = output_dir / "fig3_pre_post_overlay.pdf"
    
    fig.savefig(png_path, dpi=300, bbox_inches='tight')
    fig.savefig(pdf_path, bbox_inches='tight')
    print(f"  * Saved Figure 3 to: {png_path} and {pdf_path}")
    plt.close()

if __name__ == "__main__":
    main()
