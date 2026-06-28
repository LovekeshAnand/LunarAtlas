#!/usr/bin/env python3
"""
fig5_nist_overlay.py — Figure 5 Generator
Generates a highly refined, publication-quality NIST reference line overlay plot.
Uses classic physics-journal style: inward ticks on all sides, minor ticks, and
formal bracket annotations for spectroscopic doublets (Mg II, Al I, Ca II).
Restored to the full wavelength range (240.0 - 800.0 nm) and all 9 reference lines.
"""

import os
import sys
import math
import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt

def draw_doublet_annotation(ax, wl1, wl2, label, color, y_base, ymax):
    # Bracket horizontal base line
    ax.plot([wl1, wl2], [y_base, y_base], color=color, linewidth=1.0, zorder=5)
    # Downward tick markers at the two components
    tick_h = ymax * 0.02
    ax.plot([wl1, wl1], [y_base - tick_h, y_base], color=color, linewidth=1.0, zorder=5)
    ax.plot([wl2, wl2], [y_base - tick_h, y_base], color=color, linewidth=1.0, zorder=5)
    # Thin guide lines from zero up to the ticks
    ax.plot([wl1, wl1], [0, y_base - tick_h], color=color, linewidth=0.7, linestyle='--', alpha=0.85)
    ax.plot([wl2, wl2], [0, y_base - tick_h], color=color, linewidth=0.7, linestyle='--', alpha=0.85)
    # Vertical text label centered above the bracket
    ax.text(
        (wl1 + wl2)/2, y_base + ymax * 0.03, label, 
        rotation=90, va='bottom', ha='center', fontsize=8.5, fontweight='semibold',
        color=color, zorder=10
    )

def draw_single_annotation(ax, wl, label, color, y_base, ymax):
    # Downward tick marker
    tick_h = ymax * 0.02
    ax.plot([wl, wl], [y_base - tick_h, y_base], color=color, linewidth=1.0, zorder=5)
    # Thin guide line from zero to tick
    ax.plot([wl, wl], [0, y_base - tick_h], color=color, linewidth=0.7, linestyle='--', alpha=0.85)
    # Vertical text label above the tick
    ax.text(
        wl, y_base + ymax * 0.03, label, 
        rotation=90, va='bottom', ha='center', fontsize=8.5, fontweight='semibold',
        color=color, zorder=10
    )

def main():
    print("[Fig 5] Generating NIST line overlay with collision-free labels...")
    
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
    
    # Set up matplotlib configuration for high-end academic layout
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
    
    fig, ax = plt.subplots(figsize=(11.5, 6.2), dpi=300)
    
    # Plot spectral intensity curve in academic royal blue (#1d4ed8, alpha=1.0)
    ax.plot(wl, val, color='#1d4ed8', lw=0.6, alpha=1.0, label='Cleaned LIBS Spectrum (ID 3)')
    
    # Base height for annotations (perfectly scaled to ymax)
    y_base = ymax * 1.05
    
    # Draw all 9 original annotations
    draw_doublet_annotation(ax, 279.55, 280.27, "Mg II (280 nm)", "#16a34a", y_base, ymax)
    draw_single_annotation(ax, 288.16, "Si I (288 nm)", "#ea580c", y_base, ymax)
    draw_doublet_annotation(ax, 308.22, 309.27, "Al I (309 nm)", "#4f46e5", y_base, ymax)
    draw_single_annotation(ax, 373.49, "Fe I (373 nm)", "#dc2626", y_base, ymax)
    draw_doublet_annotation(ax, 393.37, 396.85, "Ca II (395 nm)", "#2563eb", y_base, ymax)
    draw_single_annotation(ax, 404.58, "Fe I (405 nm)", "#dc2626", y_base, ymax)
    draw_single_annotation(ax, 588.99, "Na I (589 nm)", "#d97706", y_base, ymax)
    draw_single_annotation(ax, 656.28, "H I (656 nm)", "#0891b2", y_base, ymax)
    draw_single_annotation(ax, 777.19, "O I (777 nm)", "#7c3aed", y_base, ymax)
    
    # Dummy plot item for the legend to represent reference lines
    ax.plot([], [], color='#475569', linestyle='--', label='NIST Reference Wavelengths')
            
    # Viewport limits restored to full range
    ax.set_xlim(240.0, 800.0)
    # Reduced top y-limit boundary from ymax * 1.70 to ymax * 1.48 so the legend is closer to the graph
    ax.set_ylim(bottom=-20, top=ymax * 1.48)
    
    # Custom major ticks up to ymax
    tick_max = int(math.ceil(ymax / 100.0)) * 100
    ticks = list(range(0, tick_max + 1, 100))
    ax.set_yticks(ticks)
    
    # Ticks length and styling
    ax.tick_params(which='major', length=6, width=0.8, color='#94a3b8')
    ax.tick_params(which='minor', length=3, width=0.6, color='#cbd5e1')
    
    # Darker grid lines for clear background representation
    ax.grid(True, color='#cbd5e1', linestyle='-', linewidth=0.5, alpha=0.5)
    ax.set_facecolor('white')
    
    ax.set_xlabel("Wavelength (nm)", fontsize=10, fontweight='semibold', color='#0f172a')
    ax.set_ylabel("Cleaned Intensity (a.u.)", fontsize=10, fontweight='semibold', color='#0f172a')
    
    # Elegant, simple frame
    for spine in ['top', 'bottom', 'left', 'right']:
        ax.spines[spine].set_color('#94a3b8')
        ax.spines[spine].set_linewidth(0.8)
        
    # Compact, professional legend in upper-right corner (closer to the graph curves)
    ax.legend(loc='upper right', facecolor='white', edgecolor='#e2e8f0', framealpha=0.95, fontsize=9.5)
    
    png_path = output_dir / "fig5_nist_overlay.png"
    pdf_path = output_dir / "fig5_nist_overlay.pdf"
    
    plt.tight_layout()
    fig.savefig(png_path, dpi=300, bbox_inches='tight')
    fig.savefig(pdf_path, bbox_inches='tight')
    print(f"  * Saved Figure 5 to: {png_path} and {pdf_path}")
    plt.close()

if __name__ == "__main__":
    main()
