#!/usr/bin/env python3
"""
fig2_reshape_schematic.py — Wide-to-Long Schema Reshape Figure Generator
Corrected columns: 2,094 intensity columns, 2,100 total columns.
Corrected alignment and spacing to prevent overflows and cut-offs.
"""

import os
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def main():
    print("[Fig 2] Generating wide-to-long reshape schematic...")
    
    output_dir = Path("publication_figures")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Set up matplotlib configuration
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['Arial', 'Liberation Sans', 'DejaVu Sans'],
        'svg.fonttype': 'none'
    })
    
    # Reduced vertical height from 4.2 to 3.4
    fig, ax = plt.subplots(figsize=(10, 3.4), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(1.3, 9.1)
    
    # -----------------------------------------------------------------
    # 1. WIDE FORMAT TABLE (Row 1, Top)
    # -----------------------------------------------------------------
    # Outer container box (starts at 0.9, ends at 9.1)
    ax.add_patch(patches.Rectangle((0.9, 6.5), 8.2, 2.5, facecolor='#f8fafc', edgecolor='#64748b', linewidth=1.5))
    ax.text(5.0, 8.6, "Wide-Format Table: Raw Chandrayaan-3 L1 CSV (2,100 Columns)", fontsize=10, fontweight='bold', color='#1e293b', ha='center', va='center')
    
    # Header definitions: total width = 7.8 (starts at 1.1, ends at 8.9)
    w_headers = ["Time", "Count", "Reset", "Fire", "164.35 nm", "164.74 nm", "...", "878.26 nm"]
    w_xs = [1.1, 2.1, 2.9, 3.7, 4.5, 5.7, 6.9, 7.7]
    w_w = [1.0, 0.8, 0.8, 0.8, 1.2, 1.2, 0.8, 1.2]
    
    # Header Row Box
    ax.add_patch(patches.Rectangle((1.1, 7.5), 7.8, 0.6, facecolor='#cbd5e1', edgecolor='#475569', linewidth=1))
    for x, w, label in zip(w_xs, w_w, w_headers):
        ax.text(x + w/2, 7.8, label, fontsize=8.5, fontweight='bold', ha='center', va='center', color='#0f172a')
        
    # Data Row Box
    ax.add_patch(patches.Rectangle((1.1, 6.8), 7.8, 0.6, facecolor='white', edgecolor='#cbd5e1', linewidth=1))
    w_data = ["11:35:22", "1", "1", "0", "366.0", "384.0", "...", "305.0"]
    for x, w, val in zip(w_xs, w_w, w_data):
        ax.text(x + w/2, 7.1, val, fontsize=8, ha='center', va='center', color='#334155')
        
    # Banners grouping headers (Removed "Housekeeping &" word)
    ax.add_patch(patches.Rectangle((1.1, 8.1), 3.4, 0.25, facecolor='#fae8ff', edgecolor='none'))
    ax.text(2.8, 8.225, "Metadata (6 Columns)", fontsize=7.5, fontweight='bold', color='#86198f', ha='center', va='center')
    
    ax.add_patch(patches.Rectangle((4.5, 8.1), 4.4, 0.25, facecolor='#fef9c3', edgecolor='none'))
    ax.text(6.7, 8.225, "Spectral Wavelength Channels (2,094 Columns)", fontsize=7.5, fontweight='bold', color='#854d0e', ha='center', va='center')
    
    # -----------------------------------------------------------------
    # 2. RESHAPE ARROW (Reduced vertical span from 5.8-3.45 to 5.8-4.2)
    # -----------------------------------------------------------------
    ax.annotate("Melt / Wide-to-Long Reshape Ingestion Invariant", xy=(5.0, 4.2), xytext=(5.0, 5.8),
                arrowprops=dict(facecolor='#ea580c', shrink=0.08, width=2, headwidth=8, headlength=8),
                fontsize=9, fontweight='bold', color='#d97706', ha='center', va='center')
    
    # -----------------------------------------------------------------
    # 3. LONG FORMAT TABLE (Row 3, Bottom - Shifted UP vertically)
    # -----------------------------------------------------------------
    # Outer container box starts at y_min=1.4 instead of 0.4
    ax.add_patch(patches.Rectangle((1.9, 1.4), 6.2, 2.5, facecolor='#f8fafc', edgecolor='#64748b', linewidth=1.5))
    ax.text(5.0, 3.65, "Normalized Long-Format Table: spectral_data Schema (2,094 Rows/Shot)", fontsize=9.5, fontweight='bold', color='#1e293b', ha='center', va='center')
    
    # Header definitions: total width = 5.8 (starts at 2.1, ends at 7.9)
    l_headers = ["Measurement_ID", "Wavelength_nm", "Intensity", "Laser_Energy", "Time_UTC"]
    l_xs = [2.1, 3.5, 4.8, 5.9, 6.9]
    l_w = [1.4, 1.3, 1.1, 1.0, 1.0]
    
    # Header Row Box at y=2.8
    ax.add_patch(patches.Rectangle((2.1, 2.8), 5.8, 0.4, facecolor='#cbd5e1', edgecolor='#475569', linewidth=1))
    for x, w, label in zip(l_xs, l_w, l_headers):
        ax.text(x + w/2, 3.0, label, fontsize=8, fontweight='bold', ha='center', va='center', color='#0f172a')
        
    # Sample Data Rows (Shifted vertically to match new baseline)
    l_rows = [
        ["1", "164.35", "0.0", "3327", "11:35:22"],
        ["1", "164.74", "0.0", "3327", "11:35:22"],
        ["...", "...", "...", "...", "..."],
        ["1", "878.26", "3.0", "3327", "11:35:22"]
    ]
    
    for r_idx, row_val in enumerate(l_rows):
        y_p = 2.4 - r_idx * 0.3
        bg_c = '#f8fafc' if r_idx % 2 == 1 else 'white'
        ax.add_patch(patches.Rectangle((2.1, y_p), 5.8, 0.3, facecolor=bg_c, edgecolor='#e2e8f0', linewidth=0.5))
        for x, w, val in zip(l_xs, l_w, row_val):
            ax.text(x + w/2, y_p + 0.15, val, fontsize=8, ha='center', va='center', color='#334155')
            
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)
    
    png_path = output_dir / "fig2_reshape_schematic.png"
    pdf_path = output_dir / "fig2_reshape_schematic.pdf"
    
    fig.savefig(png_path, dpi=300, bbox_inches='tight')
    fig.savefig(pdf_path, bbox_inches='tight')
    print(f"  * Saved Figure 2 to: {png_path} and {pdf_path}")
    plt.close()

if __name__ == "__main__":
    main()
