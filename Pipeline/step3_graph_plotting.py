#!/usr/bin/env python3
"""
LunarAtlas Ingestion Pipeline - Stage 3: Graph Plotting with NIST References
=============================================================================
Reads processed CSV files and renders publication-quality high-DPI plots
comparing the cleaned LIBS measurements with reference atomic emission lines.
"""

import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

DEFAULT_PROCESSED_DIR = r"c:\Users\ZBook\Desktop\LunarAtlas\datasets\processed"

# Premium color palette for measurements
COLOURS = ['#0f172a', '#ea580c', '#16a34a', '#7c3aed', '#db2777', '#2563eb', '#0891b2', '#ca8a04']

# Expanded NIST reference lines for moon mineral exploration
NIST_LINES = {
    'Mg II (279.55 nm)': (279.55, 'Mg II'),
    'Mg II (280.27 nm)': (280.27, 'Mg II'),
    'Mg I (285.21 nm)':  (285.21, 'Mg I'),
    'Si I (288.16 nm)':  (288.16, 'Si I'),
    'Al I (308.22 nm)':  (308.22, 'Al I'),
    'Al I (309.27 nm)':  (309.27, 'Al I'),
    'Ti II (334.94 nm)': (334.94, 'Ti II'),
    'Fe I (373.49 nm)':  (373.49, 'Fe I'),
    'Fe I (385.99 nm)':  (385.99, 'Fe I'),
    'Si I (390.55 nm)':  (390.55, 'Si I'),
    'Ca II (393.37 nm)': (393.37, 'Ca II'),
    'Al I (394.40 nm)':  (394.40, 'Al I'),
    'Al I (396.15 nm)':  (396.15, 'Al I'),
    'Ca II (396.85 nm)': (396.85, 'Ca II'),
    'Fe I (404.58 nm)':  (404.58, 'Fe I'),
    'Ca I (422.67 nm)':  (422.67, 'Ca I'),
    'Fe I (438.36 nm)':  (438.36, 'Fe I'),
    'Mg I (518.36 nm)':  (518.36, 'Mg I'),
    'Na I (588.99 nm)':  (588.99, 'Na I'),
    'Na I (589.59 nm)':  (589.59, 'Na I'),
    'H I (656.28 nm)':   (656.28, 'H-alpha'),
    'O I (777.19 nm)':   (777.19, 'O I'),
    'Ca II (849.80 nm)': (849.80, 'Ca II'),
    'Ca II (854.21 nm)': (854.21, 'Ca II'),
    'Ca II (866.21 nm)': (866.21, 'Ca II'),
}

def generate_improved_plots(processed_dir):
    print("====================================================")
    print(" STAGE 3: HIGH-FIDELITY GRAPH PLOTTER")
    print("====================================================")
    
    base_dir = Path(processed_dir)
    if not base_dir.exists():
        print(f"[ERROR] Processed data directory not found: {base_dir}")
        return
        
    cleaned_files = list(base_dir.glob("calibrated/*/*/*_cleaned.csv"))
    print(f"[INFO] Found {len(cleaned_files)} cleaned CSV files to plot.")
    
    for csv_path in cleaned_files:
        stem_name = csv_path.name.replace("_cleaned.csv", "")
        plots_folder = csv_path.parent / "plots"
        plot_out = plots_folder / f"{stem_name}_nist_comparison.png"
        
        if plot_out.exists():
            print(f"  [SKIP] Plot already exists for: {csv_path.name}")
            continue
            
        print(f"\nPlotting spectra for file: {csv_path.name}")
        df = pd.read_csv(csv_path)
        
        mids = sorted(df['Measurement_ID'].unique())
        wl_min = df['Wavelength_nm'].min()
        wl_max = df['Wavelength_nm'].max()
        
        # 1. Overlay Plot Setup
        fig, ax = plt.subplots(figsize=(16, 7), dpi=200)
        
        # Cleaned Canvas aesthetics
        ax.set_facecolor('#f8fafc')
        ax.grid(True, color='#e2e8f0', linestyle='-', linewidth=0.5)
        
        # Plot each measurement sequence
        for idx, mid in enumerate(mids):
            sub = df[df['Measurement_ID'] == mid].sort_values('Wavelength_nm')
            colour = COLOURS[idx % len(COLOURS)]
            ax.plot(sub['Wavelength_nm'], sub['Cleaned_Intensity'],
                    color=colour, linewidth=1.0, alpha=0.9,
                    label=f"Measurement #{mid} ({sub.iloc[0]['Laser_Energy_V']}V)")
            
        # Draw NIST Atomic reference lines
        ymax = df['Cleaned_Intensity'].max()
        for name, (wl, element) in NIST_LINES.items():
            if wl_min <= wl <= wl_max:
                # Vertical dashed line
                ax.axvline(wl, color='#94a3b8', linewidth=0.7, linestyle='--', alpha=0.7)
                # Text label
                ax.text(wl + 1.2, ymax * 0.90, element,
                        fontsize=7, color='#64748b', rotation=90, va='top', fontweight='semibold')
                
        # Design labels and legend
        ax.set_xlabel('Wavelength (nm)', fontsize=11, fontweight='bold', color='#1e293b', labelpad=8)
        ax.set_ylabel('Cleaned Intensity (counts)', fontsize=11, fontweight='bold', color='#1e293b', labelpad=8)
        
        stem_name = csv_path.name.replace("_cleaned.csv", "")
        ax.set_title(f'Chandrayaan-3 LIBS Cleaned Spectrum vs NIST References\nSession: {stem_name}',
                     fontsize=13, fontweight='bold', color='#0f172a', pad=15)
                     
        ax.legend(fontsize=9, loc='upper right', facecolor='white', edgecolor='#e2e8f0', framealpha=0.95)
        ax.set_xlim(wl_min, wl_max)
        ax.set_ylim(bottom=0, top=ymax * 1.05)
        
        # Clean tick colors
        ax.tick_params(axis='both', colors='#475569', labelsize=9)
        for spine in ax.spines.values():
            spine.set_edgecolor('#cbd5e1')
            
        fig.tight_layout()
        
        # Save PNG plot inside authentic subfolder
        plots_folder = csv_path.parent / "plots"
        plots_folder.mkdir(exist_ok=True)
        
        plot_out = plots_folder / f"{stem_name}_nist_comparison.png"
        fig.savefig(plot_out, dpi=200, bbox_inches='tight')
        plt.close(fig)
        
        print(f"  [SUCCESS] Plot saved to: {plot_out.relative_to(base_dir)}")
        
    print("\n[SUCCESS] Stage 3: All spectral graphs successfully updated.")
    print("====================================================\n")

if __name__ == "__main__":
    import sys
    processed = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PROCESSED_DIR
    generate_improved_plots(processed)
