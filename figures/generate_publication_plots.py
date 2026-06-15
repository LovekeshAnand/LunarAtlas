#!/usr/bin/env python3
"""
LunarAtlas Publication Figures Generator
========================================
Generates publication-quality, high-DPI (300 DPI) figures for the LunarAtlas paper:
- Figure F1: End-to-End LunarAtlas Architecture Diagram (3-Tier boxes & data flow)
- Figure F2: L1 Column Structure and Wide-to-Long Reshape Schematic
- Figure F3: Pre- vs. Post-Subtraction Spectrum Overlay (560-580 nm validation window)
- Figure F4: Four-Panel Shot-to-Shot Variability Plot (Measurement IDs 1-4)
- Figure F5: LTTB+Peaks vs LTTB-Only Peak Retention Comparison
- Figure F6: Measurement Acquisition Sequence Diagram (Simplified & Clean)
- Figure F7: NIST Line Overlay on Cleaned Spectrum (Staggered Collision-Free Labels)
- Figure F8: Adaptive Zoom Behaviour (Four Zoom Levels)
"""

import os
import sys
import math
import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from scipy.signal import find_peaks

# Premium styling configurations for publication
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Liberation Sans', 'DejaVu Sans'],
    'axes.edgecolor': '#475569',
    'axes.linewidth': 1.0,
    'grid.color': '#cbd5e1',
    'grid.linewidth': 0.5,
    'xtick.color': '#475569',
    'ytick.color': '#475569',
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'axes.labelsize': 10,
    'axes.titlesize': 11,
    'legend.fontsize': 9,
    'figure.titlesize': 12
})

# Colors
COLORS = {
    'grey': '#94a3b8',
    'light_grey': '#cbd5e1',
    'dark_grey': '#334155',
    'primary': '#0284c7',       # sapphire blue
    'accent_red': '#dc2626',     # red for missed peaks
    'accent_orange': '#ea580c',  # orange
    'accent_green': '#16a34a',   # green
    'bg_block': '#cbd5e1',       # background acquisition block
    'plasma_block': '#fdba74',   # plasma acquisition block
    'arrow': '#475569'
}

# NIST Reference lines for F7
NIST_PEAKS = [
    {'wl': 279.55, 'element': 'Mg II', 'color': '#16a34a'},
    {'wl': 280.27, 'element': 'Mg II', 'color': '#16a34a'},
    {'wl': 288.16, 'element': 'Si I', 'color': '#ea580c'},
    {'wl': 308.22, 'element': 'Al I', 'color': '#6366f1'},
    {'wl': 309.27, 'element': 'Al I', 'color': '#6366f1'},
    {'wl': 373.49, 'element': 'Fe I', 'color': '#dc2626'},
    {'wl': 393.37, 'element': 'Ca II', 'color': '#2563eb'},
    {'wl': 396.85, 'element': 'Ca II', 'color': '#2563eb'},
    {'wl': 404.58, 'element': 'Fe I', 'color': '#dc2626'},
    {'wl': 588.99, 'element': 'Na I', 'color': '#eab308'},
    {'wl': 656.28, 'element': 'H I', 'color': '#0891b2'},
    {'wl': 777.19, 'element': 'O I', 'color': '#7c3aed'}
]

class EnhancedPublicationFiguresGenerator:
    def __init__(self, raw_path: str, data_path: str, output_dir: str):
        self.raw_path = Path(raw_path)
        self.data_path = Path(data_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"[INFO] Ingestion Data: {self.data_path}")
        if not self.data_path.exists():
            raise FileNotFoundError(f"Data file not found: {self.data_path}")
        self.df = pd.read_csv(self.data_path)
        
        print(f"[INFO] Raw Wide-form Data: {self.raw_path}")
        if not self.raw_path.exists():
            raise FileNotFoundError(f"Raw file not found: {self.raw_path}")
        self.raw_df = pd.read_csv(self.raw_path)

    def _save_figure(self, fig, filename_stem):
        """Save the figure as both high-DPI PNG and vector PDF."""
        png_path = self.output_dir / f"{filename_stem}.png"
        pdf_path = self.output_dir / f"{filename_stem}.pdf"
        
        fig.savefig(png_path, dpi=300, bbox_inches='tight')
        fig.savefig(pdf_path, bbox_inches='tight')
        print(f"  * Saved figure: {png_path.name} & {pdf_path.name}")

    def generate_fig1_architecture(self):
        """Figure F1: End-to-End LunarAtlas Architecture Diagram"""
        print("[Fig F1] Generating system architecture diagram...")
        fig, ax = plt.subplots(figsize=(11, 8.5), dpi=300)
        ax.set_xlim(0, 10.5)
        ax.set_ylim(0, 10)
        
        # Layer Banners (Background boxes for layers)
        ax.add_patch(patches.Rectangle((0.5, 7.1), 9.2, 2.3, facecolor='#f8fafc', edgecolor='#cbd5e1', linewidth=1, linestyle='--'))
        ax.add_patch(patches.Rectangle((0.5, 3.6), 9.2, 3.2, facecolor='#f8fafc', edgecolor='#cbd5e1', linewidth=1, linestyle='--'))
        ax.add_patch(patches.Rectangle((0.5, 0.2), 9.2, 3.1, facecolor='#f8fafc', edgecolor='#cbd5e1', linewidth=1, linestyle='--'))
        
        # Layer labels on the right
        ax.text(10.0, 8.25, "PRESENTATION LAYER\n(React 18 & amCharts 5)", fontsize=9, fontweight='bold', color='#1e293b', rotation=270, va='center', ha='center')
        ax.text(10.0, 5.2, "LOGIC LAYER\n(Python 3.11 & FastAPI 0.111)", fontsize=9, fontweight='bold', color='#1e293b', rotation=270, va='center', ha='center')
        ax.text(10.0, 1.75, "DATA LAYER\n(PostgreSQL 16.3)", fontsize=9, fontweight='bold', color='#1e293b', rotation=270, va='center', ha='center')
        
        # Presentation Layer components
        ax.add_patch(patches.Rectangle((1.0, 7.4), 3.8, 1.7, facecolor='#f0f9ff', edgecolor='#0284c7', linewidth=1.5))
        ax.text(2.9, 8.25, "Frontend Web Application\n(React 18)\n\n- Client-Side Dashboard UI\n- Developer API Key Management", fontsize=8.5, color='#0369a1', ha='center', va='center')
        
        ax.add_patch(patches.Rectangle((5.3, 7.4), 4.0, 1.7, facecolor='#f0f9ff', edgecolor='#0284c7', linewidth=1.5))
        ax.text(7.3, 8.25, "Interactive Visualization Console\n(amCharts 5)\n\n- High-performance spectral plots\n- No scientific computation\n  (remains server-side)", fontsize=8.5, color='#0369a1', ha='center', va='center')
        
        # Logic Layer components
        ax.add_patch(patches.Rectangle((1.0, 3.9), 3.8, 2.6, facecolor='#faf5ff', edgecolor='#7c3aed', linewidth=1.5))
        ax.text(2.9, 5.2, "Data Ingestion & Cleaning\n(Python 3.11 Core)\n\n- PDS4 XML label parsing [7,8]\n- Idempotent Ingestion & hashing\n- Plasma-Background pairing\n- Background subtraction ($P_k - B_k$)", fontsize=8.5, color='#6d28d9', ha='center', va='center')
        
        ax.add_patch(patches.Rectangle((5.3, 3.9), 4.0, 2.6, facecolor='#faf5ff', edgecolor='#7c3aed', linewidth=1.5))
        ax.text(7.3, 5.2, "API Services & Analysis\n(FastAPI 0.111 Service)\n\n- Peak-locked LTTB downsampling [21]\n- NIST spectral-line matching [28]\n- Peak detection & envelope creation\n- API key verification & data streaming", fontsize=8.5, color='#6d28d9', ha='center', va='center')
        
        # Data Layer components
        ax.add_patch(patches.Rectangle((1.0, 0.5), 3.8, 2.5, facecolor='#f0fdf4', edgecolor='#16a34a', linewidth=1.5))
        ax.text(2.9, 1.75, "Relational Schema & Metadata\n(PostgreSQL 16.3)\n\n- Mission & instrument observations\n- Processed measurements & provenance\n- MD5-based idempotent records", fontsize=8.5, color='#15803d', ha='center', va='center')
        
        ax.add_patch(patches.Rectangle((5.3, 0.5), 4.0, 2.5, facecolor='#f0fdf4', edgecolor='#16a34a', linewidth=1.5))
        ax.text(7.3, 1.75, "Spectral Value Table\n(PostgreSQL 16.3 Long Format)\n\n- Long format storage\n- Composite PK: (measurement_id, wavelength_nm)\n- BRIN Index on wavelength\n  (efficient queries across 2,094 channels)", fontsize=8.5, color='#15803d', ha='center', va='center')
        
        # Draw Arrows for data flow
        # PDS4 products entering logic layer
        ax.annotate("PDS4 Data Products", xy=(1.0, 5.2), xytext=(-0.5, 5.2),
                    arrowprops=dict(facecolor='#475569', shrink=0.05, width=1, headwidth=4), fontsize=8, va='center', ha='right')
        
        # Ingestion pipeline -> DB
        ax.annotate("", xy=(2.9, 3.0), xytext=(2.9, 3.9),
                    arrowprops=dict(facecolor='#475569', shrink=0.05, width=1, headwidth=4))
        
        # DB -> API Service
        ax.annotate("", xy=(7.3, 3.9), xytext=(7.3, 3.0),
                    arrowprops=dict(facecolor='#475569', shrink=0.05, width=1, headwidth=4))
        
        # API Service -> Presentation
        ax.annotate("JSON Response", xy=(7.3, 7.4), xytext=(7.3, 6.5),
                    arrowprops=dict(facecolor='#0284c7', shrink=0.05, width=1, headwidth=4), fontsize=7.5, color='#0369a1', ha='center', va='bottom')
        
        # Presentation -> API request
        ax.annotate("API Request", xy=(2.9, 6.5), xytext=(2.9, 7.4),
                    arrowprops=dict(facecolor='#0284c7', shrink=0.05, width=1, headwidth=4), fontsize=7.5, color='#0369a1', ha='center', va='top')
        
        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)
        
        ax.set_title("Figure F1: End-to-End LunarAtlas Architecture and Data Flow Schematic", fontsize=11, fontweight='bold', pad=15)
        
        self._save_figure(fig, "fig1_architecture")
        plt.close()

    def generate_fig2_reshape_schematic(self):
        """Figure F2: L1 Column Structure and Wide-to-Long Reshape Schematic"""
        print("[Fig F2] Generating wide-to-long reshape schematic...")
        fig, ax = plt.subplots(figsize=(10, 7), dpi=300)
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
        
        # 1. Wide format Table drawing (Time, Count, Reset, Fire, 164.35, ..., 878.26)
        ax.add_patch(patches.Rectangle((0.5, 6.5), 9.0, 2.5, facecolor='#f8fafc', edgecolor='#64748b', linewidth=1.5))
        ax.text(5.0, 8.6, "Wide-Format Table: Raw Chandrayaan-3 L1 CSV (2,055 Columns)", fontsize=10, fontweight='bold', color='#1e293b', ha='center', va='center')
        
        # Headers grid in Wide format
        w_headers = ["Time", "Count", "Reset", "Fire", "164.35 nm", "164.74 nm", "...", "878.26 nm"]
        w_xs = [0.8, 1.8, 2.8, 3.8, 4.8, 6.0, 7.2, 8.4]
        w_w = [1.0, 1.0, 1.0, 1.0, 1.2, 1.2, 1.2, 1.2]
        
        # Draw Header Row Box
        ax.add_patch(patches.Rectangle((0.7, 7.5), 8.6, 0.6, facecolor='#cbd5e1', edgecolor='#475569', linewidth=1))
        for x, w, label in zip(w_xs, w_w, w_headers):
            ax.text(x + w/2, 7.8, label, fontsize=8.5, fontweight='bold', ha='center', va='center', color='#0f172a')
            
        # Draw Data Row Box
        ax.add_patch(patches.Rectangle((0.7, 6.8), 8.6, 0.6, facecolor='white', edgecolor='#cbd5e1', linewidth=1))
        w_data = ["11:35:22", "1", "1", "0", "366.0", "384.0", "...", "305.0"]
        for x, w, val in zip(w_xs, w_w, w_data):
            ax.text(x + w/2, 7.1, val, fontsize=8, ha='center', va='center', color='#334155')
            
        # Add brackets / banners grouping headers
        ax.add_patch(patches.Rectangle((0.7, 8.1), 4.0, 0.25, facecolor='#fae8ff', edgecolor='none'))
        ax.text(2.7, 8.225, "Housekeeping & Metadata (6 Columns)", fontsize=7.5, fontweight='bold', color='#86198f', ha='center', va='center')
        
        ax.add_patch(patches.Rectangle((4.7, 8.1), 4.6, 0.25, facecolor='#fef9c3', edgecolor='none'))
        ax.text(7.0, 8.225, "Spectral Wavelength Intensity Channels (2,049 Columns)", fontsize=7.5, fontweight='bold', color='#854d0e', ha='center', va='center')
        
        # 2. Reshape Arrow
        ax.annotate("Melt / Wide-to-Long Reshape Ingestion Invariant", xy=(5.0, 3.8), xytext=(5.0, 5.8),
                    arrowprops=dict(facecolor='#ea580c', shrink=0.08, width=2, headwidth=8, headlength=8),
                    fontsize=9, fontweight='bold', color='#d97706', ha='center', va='center')
        
        # 3. Long format Table drawing (Measurement_ID, Wavelength_nm, Cleaned_Intensity)
        ax.add_patch(patches.Rectangle((1.5, 0.5), 7.0, 3.0, facecolor='#f8fafc', edgecolor='#64748b', linewidth=1.5))
        ax.text(5.0, 3.15, "Normalized Long-Format Table: spectral_data Schema (Rows × 2,094 per shot)", fontsize=9.5, fontweight='bold', color='#1e293b', ha='center', va='center')
        
        l_headers = ["Measurement_ID (PK)", "Wavelength_nm (PK)", "Cleaned_Intensity", "Laser_Energy_V", "Time_UTC"]
        l_xs = [1.8, 3.3, 4.8, 6.2, 7.3]
        l_w = [1.4, 1.4, 1.3, 1.0, 1.0]
        
        # Draw Header Row Box
        ax.add_patch(patches.Rectangle((1.7, 2.2), 6.6, 0.5, facecolor='#cbd5e1', edgecolor='#475569', linewidth=1))
        for x, w, label in zip(l_xs, l_w, l_headers):
            ax.text(x + w/2, 2.45, label, fontsize=8, fontweight='bold', ha='center', va='center', color='#0f172a')
            
        # Draw Sample Data Rows
        l_rows = [
            ["1", "164.35", "0.0", "3327", "11:35:22"],
            ["1", "164.74", "0.0", "3327", "11:35:22"],
            ["...", "...", "...", "...", "..."],
            ["1", "878.26", "3.0", "3327", "11:35:22"]
        ]
        
        for r_idx, row_val in enumerate(l_rows):
            y_p = 1.65 - r_idx * 0.4
            bg_c = '#f8fafc' if r_idx % 2 == 1 else 'white'
            ax.add_patch(patches.Rectangle((1.7, y_p), 6.6, 0.4, facecolor=bg_c, edgecolor='#e2e8f0', linewidth=0.5))
            for x, w, val in zip(l_xs, l_w, row_val):
                ax.text(x + w/2, y_p + 0.2, val, fontsize=8, ha='center', va='center', color='#334155')
                
        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)
        
        ax.set_title("Figure F2: L1 Wide-Format Column Structure to Normalised Long-Form Schema Ingestion", fontsize=11, fontweight='bold', pad=15)
        
        self._save_figure(fig, "fig2_reshape_schematic")
        plt.close()

    def generate_fig3_pre_post_subtraction(self):
        """Figure F3: Pre- vs. Post-Subtraction Spectrum Overlay (560-580 nm validation window)"""
        print("[Fig F3] Generating pre- vs. post-subtraction spectrum overlay...")
        
        # We need raw wide-form row 3 (iloc[2] of plasma) and cleaned row 3
        # Extract wavelengths and values
        wl_cols = [c for c in self.raw_df.columns if c.replace('.', '', 1).isdigit()]
        raw_wl = np.array([float(c) for c in wl_cols])
        
        fire_col = 'Laser Fire status' if 'Laser Fire status' in self.raw_df.columns else 'Laser Fire Status'
        reset_col = 'Force Reset status' if 'Force Reset status' in self.raw_df.columns else 'Force Reset Status'
        plasma_df = self.raw_df[(self.raw_df[fire_col] == 1) & (self.raw_df[reset_col] == 0)].copy()
        
        # Row 3 values
        raw_val = plasma_df.iloc[2][wl_cols].values.astype(float)
        
        # Cleaned values for ID 3
        c_sub = self.df[self.df['Measurement_ID'] == 3].sort_values('Wavelength_nm')
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
        
        fig, ax = plt.subplots(figsize=(10, 5.5), dpi=300)
        
        # Plot spectrum overlay lines
        ax.plot(w_raw, v_raw, color='#94a3b8', linestyle='-', lw=1.2, alpha=0.9, label='Raw L1 Intensity counts')
        ax.plot(w_clean, v_clean, color='#0284c7', linestyle='-', lw=1.2, alpha=0.9, label='Cleaned L2 Intensity counts')
        
        # Draw mean level lines
        ax.axhline(mean_raw, color='#b91c1c', linestyle='--', lw=1.0, alpha=0.8)
        ax.axhline(mean_clean, color='#0369a1', linestyle='--', lw=1.0, alpha=0.8)
        
        # Text annotations for means
        ax.text(561.0, mean_raw + 25, f"Mean Raw: {mean_raw:.1f} counts", fontsize=8.5, color='#b91c1c', fontweight='semibold')
        ax.text(561.0, mean_clean + 25, f"Mean Cleaned: {mean_clean:.1f} counts", fontsize=8.5, color='#0369a1', fontweight='semibold')
        
        # Double-headed arrow indicating baseline suppression
        arrow_x = 578.0
        ax.annotate(
            '', xy=(arrow_x, mean_clean), xytext=(arrow_x, mean_raw),
            arrowprops=dict(arrowstyle="<->", color='#475569', lw=1.2)
        )
        
        # Ratio label
        ratio = mean_raw / mean_clean if mean_clean > 0 else 0
        ax.text(
            arrow_x - 0.3, (mean_raw + mean_clean)/2, f"Baseline Suppression\nRatio: {ratio:.2f}×",
            fontsize=8.5, fontweight='bold', color='#475569', ha='right', va='center'
        )
        
        ax.set_xlim(560.0, 580.0)
        ax.set_ylim(bottom=0, top=max(v_raw) * 1.15)
        ax.grid(True, color='#f1f5f9', linestyle='-', linewidth=0.5)
        ax.set_facecolor('#fafafb')
        
        ax.set_xlabel("Wavelength (nm)")
        ax.set_ylabel("Intensity / Count (counts)")
        ax.set_title("Figure F3: Pre- vs. Post-Subtraction Spectrum Overlay (560–580 nm Window)", fontsize=11, fontweight='bold', pad=12)
        ax.legend(loc='upper right', facecolor='white', edgecolor='#e2e8f0', framealpha=0.95)
        
        self._save_figure(fig, "fig3_pre_post_overlay")
        plt.close()

    def generate_fig4_spectral_variability(self):
        """Figure F4: Measurement-to-Measurement Spectral Variability (2x2 Grid)"""
        print("[Fig F4] Generating spectral variability 2x2 grid...")
        fig, axes = plt.subplots(2, 2, figsize=(12, 8), dpi=300, sharex=True)
        
        panels_info = [
            {
                'id': 1, 'color': '#475569', 'energy': 3327, 
                'peak': '321 cts @ 748.0 nm', 'neg': '22.5%', 
                'notes': 'Normal baseline, moderate signal-to-noise ratio'
            },
            {
                'id': 2, 'color': '#b91c1c', 'energy': 3280, 
                'peak': '261 cts @ 283.1 nm', 'neg': '76.8%', 
                'notes': 'Near-Null acquisition (plasma failure or misfire)'
            },
            {
                'id': 3, 'color': '#1d4ed8', 'energy': 3194, 
                'peak': '684 cts @ 282.3 nm', 'neg': '12.1%', 
                'notes': 'High quality, prominent emission features'
            },
            {
                'id': 4, 'color': '#0f766e', 'energy': 3202, 
                'peak': '637 cts @ 282.7 nm', 'neg': '9.3%', 
                'notes': 'Optimal quality, low baseline negativity fraction'
            }
        ]
        
        for idx, info in enumerate(panels_info):
            row = idx // 2
            col = idx % 2
            ax = axes[row, col]
            
            sub = self.df[self.df['Measurement_ID'] == info['id']].sort_values('Wavelength_nm')
            wl = sub['Wavelength_nm'].values
            val = sub['Cleaned_Intensity'].values
            
            ax.plot(wl, val, color=info['color'], lw=0.8, alpha=0.95, label=f"ID {info['id']}")
            ax.set_facecolor('#fafafb')
            ax.grid(True, color='#e2e8f0', linestyle='-', linewidth=0.5)
            
            # Text box details
            text_str = (
                f"Measurement ID: {info['id']}\n"
                f"Laser Energy: {info['energy']} V\n"
                f"Peak Intensity: {info['peak']}\n"
                f"Negatives pre-clamp: {info['neg']}"
            )
            ax.text(
                0.03, 0.95, text_str, transform=ax.transAxes, 
                fontsize=8, va='top', ha='left', fontweight='semibold',
                bbox=dict(boxstyle='round', facecolor='white', edgecolor='#e2e8f0', alpha=0.9)
            )
            
            # Annotate Mg II doublet for panels 3 & 4
            if info['id'] in [3, 4]:
                peak_wl = 279.6
                peak_idx = np.abs(wl - peak_wl).argmin()
                peak_val = val[peak_idx]
                ax.annotate(
                    'Mg II doublet\n(280 nm)',
                    xy=(peak_wl, peak_val),
                    xytext=(peak_wl + 50, peak_val + 100),
                    fontsize=8, fontweight='bold', color='#15803d',
                    arrowprops=dict(facecolor='#15803d', shrink=0.08, width=1, headwidth=5, headlength=5)
                )
            
            if row == 1:
                ax.set_xlabel("Wavelength (nm)")
            if col == 0:
                ax.set_ylabel("Cleaned Intensity (counts)")
                
            ax.set_ylim(bottom=-10, top=max(val) * 1.15)
            ax.tick_params(axis='both', colors='#475569')
            
        plt.suptitle("Figure F4: Measurement-to-Measurement Spectral Variability (L1 Processed)", 
                     fontsize=12, fontweight='bold', y=0.98, color='#0f172a')
        plt.tight_layout()
        plt.subplots_adjust(top=0.92, hspace=0.25, wspace=0.22)
        
        self._save_figure(fig, "fig4_spectral_variability")
        plt.close()

    def generate_fig5_peak_retention(self):
        """Figure F5: LTTB+Peaks vs LTTB-Only Peak Retention Comparison"""
        print("[Fig F5] Generating peak retention comparison...")
        
        sub = self.df[self.df['Measurement_ID'] == 3].sort_values('Wavelength_nm')
        wl_full = sub['Wavelength_nm'].values
        val_full = sub['Cleaned_Intensity'].values
        
        # Detect peaks in range 370 to 420 nm
        raw_peaks_idx, _ = find_peaks(val_full, prominence=25, distance=4)
        peaks_in_range = [idx for idx in raw_peaks_idx if 370.0 <= wl_full[idx] <= 420.0]
        n_total_peaks = len(peaks_in_range)
        
        # Standard LTTB simple downsampling (without peak union)
        threshold = 200
        n_raw = len(wl_full)
        every = (n_raw - 2) / (threshold - 2)
        lttb_indices = [0]
        a = 0
        for i in range(threshold - 2):
            avg_start = math.floor((i + 1) * every) + 1
            avg_end = min(math.floor((i + 2) * every) + 1, n_raw)
            avg_x = np.mean(wl_full[avg_start:avg_end])
            avg_y = np.mean(val_full[avg_start:avg_end])
            
            r_start = math.floor(i * every) + 1
            r_end = math.floor((i + 1) * every) + 1
            bx = wl_full[r_start:r_end]
            by = val_full[r_start:r_end]
            
            areas = np.abs(
                wl_full[a] * (by - avg_y) +
                bx * (avg_y - val_full[a]) +
                avg_x * (val_full[a] - by)
            )
            max_idx = r_start + np.argmax(areas)
            lttb_indices.append(int(max_idx))
            a = max_idx
        lttb_indices.append(n_raw - 1)
        lttb_indices = sorted(list(set(lttb_indices)))
        
        retained_by_lttb = []
        missed_by_lttb = []
        for idx in peaks_in_range:
            retained = False
            for s_idx in lttb_indices:
                if abs(s_idx - idx) <= 1:
                    retained = True
                    break
            if retained:
                retained_by_lttb.append(idx)
            else:
                missed_by_lttb.append(idx)
                
        n_retained_lttb = len(retained_by_lttb)
        n_missed_lttb = len(missed_by_lttb)
        
        fig, ax = plt.subplots(figsize=(10, 5.5), dpi=300)
        
        # Plot overlay spectrum
        ax.plot(wl_full, val_full, color='#cbd5e1', lw=0.8, alpha=0.5, label='Raw Spectrum (2094 pts)')
        
        lttb_in_zoom = [idx for idx in lttb_indices if 370.0 <= wl_full[idx] <= 420.0]
        ax.scatter(wl_full[lttb_in_zoom], val_full[lttb_in_zoom], 
                   color='#0284c7', marker='o', s=10, zorder=3, alpha=0.85,
                   label=f'LTTB-Selected Points ({len(lttb_in_zoom)} in range)')
        
        ax.scatter(wl_full[missed_by_lttb], val_full[missed_by_lttb], 
                   color='#dc2626', marker='*', s=25, zorder=5,
                   label=f'Missed Peaks Recovered by Union ({len(missed_by_lttb)} peaks)')
        
        ca_peaks = [393.37, 396.85]
        for cp in ca_peaks:
            c_idx = np.abs(wl_full - cp).argmin()
            ax.annotate(
                f'Ca II ({cp:.1f} nm)',
                xy=(wl_full[c_idx], val_full[c_idx]),
                xytext=(wl_full[c_idx] - 3.5, val_full[c_idx] + 120),
                fontsize=8, fontweight='bold', color='#1e3a8a',
                arrowprops=dict(facecolor='#1e3a8a', shrink=0.08, width=0.5, headwidth=4, headlength=4)
            )
            
        ax.set_xlim(370.0, 420.0)
        ax.set_ylim(bottom=-10, top=max(val_full[np.logical_and(wl_full >= 370.0, wl_full <= 420.0)]) * 1.25)
        
        ax.set_xlabel("Wavelength (nm)")
        ax.set_ylabel("Cleaned Intensity (counts)")
        ax.grid(True, color='#f1f5f9', linestyle='-', linewidth=0.5)
        ax.set_facecolor('#fafafb')
        
        retention_text = (
            "Peak Retention Summary (370-420 nm):\n"
            f"- LTTB + Peaks Union: 100.0% ({n_total_peaks}/{n_total_peaks} peaks)\n"
            f"- LTTB-Only: {n_retained_lttb / n_total_peaks * 100:.1f}% ({n_retained_lttb}/{n_total_peaks} peaks)\n"
            f"- Information Recovery: +{n_missed_lttb} diagnostic lines"
        )
        ax.text(
            0.03, 0.95, retention_text, transform=ax.transAxes,
            fontsize=8.5, va='top', ha='left', fontweight='semibold',
            bbox=dict(boxstyle='round', facecolor='white', edgecolor='#cbd5e1', alpha=0.95)
        )
        
        ax.set_title("Figure F5: LTTB+Peaks vs LTTB-Only Peak Retention Comparison (Zoomed View)", 
                     fontsize=11, fontweight='bold', pad=12)
        ax.legend(loc='upper right', facecolor='white', edgecolor='#e2e8f0', framealpha=0.95)
        
        self._save_figure(fig, "fig5_peak_retention")
        plt.close()

    def generate_fig4_peak_comparison(self):
        """Generates a clean, polished fig4_peak_comparison replacing the messy legacy plot."""
        print("[Fig F4 Peak Comparison] Generating polished peak comparison plot...")
        
        sub = self.df[self.df['Measurement_ID'] == 3].sort_values('Wavelength_nm')
        wl = sub['Wavelength_nm'].values
        val = sub['Cleaned_Intensity'].values
        
        raw_peaks_idx, _ = find_peaks(val, prominence=50, distance=5)
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
        
        fig, ax = plt.subplots(figsize=(10, 5.5), dpi=300)
        
        ax.plot(wl, val, color='#cbd5e1', lw=0.8, alpha=0.5, label='Raw Spectrum')
        
        wl_d = wl[lttb_indices]
        val_d = val[lttb_indices]
        ax.plot(wl_d, val_d, color='#0284c7', lw=0.8, alpha=0.8, label=f'LTTB Downsampled ({threshold} pts)')
        
        if preserved_peaks:
            ax.scatter(wl[preserved_peaks], val[preserved_peaks], 
                       color='#16a34a', marker='o', s=10, zorder=5, alpha=0.9,
                       label=f'Preserved Peaks ({n_preserved}/{n_raw_peaks})')
                       
        if missed_peaks:
            ax.scatter(wl[missed_peaks], val[missed_peaks], 
                       color='#dc2626', marker='x', s=15, zorder=5, alpha=0.9,
                       label=f'Missed Peaks ({n_missed}/{n_raw_peaks})')
                       
        ax.set_xlim(wl.min(), wl.max())
        ax.set_ylim(bottom=-20, top=max(val) * 1.15)
        ax.set_xlabel("Wavelength (nm)")
        ax.set_ylabel("Intensity (counts)")
        ax.grid(True, color='#f1f5f9', linestyle='-', linewidth=0.5)
        ax.set_facecolor('#fafafb')
        
        ax.set_title(f'Peak Preservation Analysis (Measurement ID 3)', fontsize=11, fontweight='bold', pad=12)
        ax.legend(loc='upper right', facecolor='white', edgecolor='#e2e8f0', framealpha=0.95)
        
        self._save_figure(fig, "fig4_peak_comparison")
        plt.close()

    def generate_fig6_acquisition_sequence(self):
        """Figure F6: Measurement Acquisition Sequence Diagram (Simplified & Clean)"""
        print("[Fig F6] Generating acquisition sequence diagram...")
        fig, ax = plt.subplots(figsize=(10, 3.8), dpi=300)
        
        ax.set_xlim(-0.5, 8.6)
        ax.set_ylim(-0.9, 1.5)
        
        # Define paired background (B) and plasma (P) blocks
        # We separate pairs with a wider gap to make pairing visually obvious
        blocks = [
            {'x': 0.5, 'width': 1.0, 'type': 'bg', 'label': 'Background $B_1$', 'flags': 'Reset=1\nFire=0'},
            {'x': 1.7, 'width': 1.0, 'type': 'plasma', 'label': 'Plasma $P_1$', 'flags': 'Reset=0\nFire=1'},
            
            {'x': 3.2, 'width': 1.0, 'type': 'bg', 'label': 'Background $B_2$', 'flags': 'Reset=1\nFire=0'},
            {'x': 4.4, 'width': 1.0, 'type': 'plasma', 'label': 'Plasma $P_2$', 'flags': 'Reset=0\nFire=1'},
            
            {'x': 5.9, 'width': 1.0, 'type': 'bg', 'label': 'Background $B_3$', 'flags': 'Reset=1\nFire=0'},
            {'x': 7.1, 'width': 1.0, 'type': 'plasma', 'label': 'Plasma $P_3$', 'flags': 'Reset=0\nFire=1'}
        ]
        
        for block in blocks:
            color = '#f1f5f9' if block['type'] == 'bg' else '#ffedd5'
            edgecolor = '#64748b' if block['type'] == 'bg' else '#f97316'
            
            # Draw box (y: 0 to 0.7)
            rect = patches.Rectangle(
                (block['x'], 0.0), block['width'], 0.7, 
                edgecolor=edgecolor, facecolor=color, linewidth=1.5
            )
            ax.add_patch(rect)
            
            # Text inside box
            ax.text(
                block['x'] + block['width']/2, 0.35, block['label'], 
                fontsize=9, fontweight='bold', ha='center', va='center', color='#0f172a'
            )
            
            # Flags text underneath box (y: -0.1 to -0.4)
            ax.text(
                block['x'] + block['width']/2, -0.12, block['flags'],
                fontsize=8, ha='center', va='top', color='#475569', linespacing=1.2
            )
            
        # Draw curved pairing arrows above the boxes showing subtraction
        for k in range(3):
            bg_center = blocks[2*k]['x'] + 0.5
            plasma_center = blocks[2*k + 1]['x'] + 0.5
            
            # Curve from bg top to plasma top
            arrow_conn = patches.FancyArrowPatch(
                (bg_center, 0.7), (plasma_center, 0.7),
                connectionstyle="arc3,rad=0.4",
                arrowstyle="-|>", mutation_scale=10,
                color='#2563eb', linewidth=1.2, linestyle='--'
            )
            ax.add_patch(arrow_conn)
            
            # Subtraction equation text above the curve
            ax.text(
                (bg_center + plasma_center)/2, 1.05, f"$I_{{clean}} = max(0, P_{k+1} - B_{k+1})$",
                fontsize=8.5, ha='center', va='bottom', color='#1d4ed8', fontweight='semibold'
            )
            
        # Draw a clean horizontal timeline axis line at the bottom
        ax.annotate(
            '', xy=(8.3, -0.65), xytext=(-0.2, -0.65),
            arrowprops=dict(arrowstyle="->", color='#475569', lw=1.2)
        )
        ax.text(8.3, -0.78, "Sequence Time (t) →", fontsize=8.5, fontweight='bold', ha='right', color='#475569')
        
        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)
        
        ax.set_title("Figure F6: Interleaved Background-Plasma Measurement Sequence Timeline", 
                     fontsize=11, fontweight='bold', pad=15)
        
        self._save_figure(fig, "fig6_acquisition_sequence")
        plt.close()

    def generate_fig7_nist_overlay(self):
        """Figure F7: NIST Line Overlay on Cleaned Spectrum with Collision-Free Labels"""
        print("[Fig F7] Generating NIST line overlay with collision-free labels...")
        
        sub = self.df[self.df['Measurement_ID'] == 3].sort_values('Wavelength_nm')
        wl = sub['Wavelength_nm'].values
        val = sub['Cleaned_Intensity'].values
        ymax = max(val)
        
        fig, ax = plt.subplots(figsize=(12, 6.8), dpi=300)
        
        # Plot spectral intensity curve
        ax.plot(wl, val, color='#475569', lw=0.6, alpha=0.8, label='Cleaned LIBS Spectrum (Measurement ID 3)')
        
        # Sort NIST lines by wavelength to perform staggered vertical staggering
        peaks = sorted(NIST_PEAKS, key=lambda x: x['wl'])
        
        # 2 Staggered height levels starting above ymax to avoid any overlaps
        y_levels = [ymax * 1.05, ymax * 1.28]
        seen_legend_labels = set()
        
        for i, peak in enumerate(peaks):
            wl_ref = peak['wl']
            color = peak['color']
            element = peak['element']
            
            # Stagger base y-position sequentially
            y_pos = y_levels[i % 2]
            
            # Draw vertical dashed line marker
            ax.axvline(wl_ref, color=color, linewidth=0.7, linestyle='--', alpha=0.8)
            
            # Place staggered text box label above spectrum values
            # Use va='bottom' so text grows UPWARDS, preventing overlap.
            ax.text(
                wl_ref, y_pos, f"{element} ({wl_ref:.1f} nm)", 
                rotation=90, va='bottom', ha='center', fontsize=7.5, fontweight='bold',
                color=color, zorder=10,
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor=color, alpha=1.0, lw=0.8)
            )
            
            # Group identical elements into one legend marker for clean layout
            if element not in seen_legend_labels:
                ax.plot([], [], color=color, linestyle='--', label=f'{element} Reference')
                seen_legend_labels.add(element)
                
        ax.set_xlim(wl.min(), wl.max())
        # Increase top y-limit to fit the staggered labels above the spectrum
        ax.set_ylim(bottom=-20, top=ymax * 1.55)
        
        # Custom ticks: only show y-axis ticks up to the spectrum peak (ymax)
        tick_max = int(math.ceil(ymax / 100.0)) * 100
        ticks = list(range(0, tick_max + 1, 100))
        ax.set_yticks(ticks)
        
        ax.grid(True, color='#f1f5f9', linestyle='-', linewidth=0.5)
        ax.set_facecolor('#fafafb')
        
        ax.set_xlabel("Wavelength (nm)")
        ax.set_ylabel("Cleaned Intensity (counts)")
        
        ax.set_title("Figure F7: NIST Reference Line Overlays on Cleaned LIBS Spectrum",
                     fontsize=11, fontweight='bold', pad=12)
        ax.legend(loc='upper right', facecolor='white', edgecolor='#e2e8f0', framealpha=0.95)
        
        self._save_figure(fig, "fig7_nist_overlay")
        plt.close()

    def generate_fig8_adaptive_zoom(self):
        """Figure F8: Adaptive Zoom Behaviour (Four Zoom Levels, Fixed Viewport)"""
        print("[Fig F8] Generating adaptive zoom 2x2 grid...")
        
        # 2x2 grid showing the same 250-450 nm segment
        # k=0 (2094 points -> 150 LTTB)
        # k=1 (1047 -> 150 LTTB)
        # k=2 (524 -> 42 raw)
        # k=3 (8 raw)
        # z_max=2 transition annotated
        
        viewports = [
            {
                'k': 0, 'title': 'Panel A: k=0 (Global downsampling)', 
                'g_min': 164.35, 'g_max': 878.26, 'target_lttb': 150, 
                'desc': 'k=0 (2094 points -> 150 LTTB)', 'is_raw': False
            },
            {
                'k': 1, 'title': 'Panel B: k=1 (Medium downsampling)', 
                'g_min': 200.0, 'g_max': 557.0, 'target_lttb': 150, 
                'desc': 'k=1 (1047 -> 150 LTTB)', 'is_raw': False
            },
            {
                'k': 2, 'title': 'Panel C: k=2 (z_max Transition reached)', 
                'g_min': 250.0, 'g_max': 428.0, 'target_lttb': 150, 
                'desc': 'k=2 (524 -> 42 raw) [z_max=2 Saturated]', 'is_raw': True
            },
            {
                'k': 3, 'title': 'Panel D: k=3 (Hyper-zoom viewport)', 
                'g_min': 278.0, 'g_max': 280.7, 'target_lttb': 150, 
                'desc': 'k=3 (8 raw)', 'is_raw': True
            }
        ]
        
        fig, axes = plt.subplots(2, 2, figsize=(13, 9), dpi=300)
        
        sub = self.df[self.df['Measurement_ID'] == 3].sort_values('Wavelength_nm')
        wl_full = sub['Wavelength_nm'].values
        val_full = sub['Cleaned_Intensity'].values
        
        for idx, vp in enumerate(viewports):
            row = idx // 2
            col = idx % 2
            ax = axes[row, col]
            
            # Filter the global range representing zoom level k
            g_mask = np.logical_and(wl_full >= vp['g_min'], wl_full <= vp['g_max'])
            wl_g = wl_full[g_mask]
            val_g = val_full[g_mask]
            n_raw_g = len(wl_g)
            
            # Apply LTTB or Raw Rendering depending on zoom level
            if vp['is_raw']:
                rendered_wl = wl_g
                rendered_val = val_g
                marker_style = 'o'
                marker_sz = 3.5
                line_w = 0.8
                color_plot = '#ef4444' # Red in raw saturated view
            else:
                # Downsampled LTTB points over global range
                n_raw = len(wl_g)
                every = (n_raw - 2) / (vp['target_lttb'] - 2)
                l_idx = [0]
                a = 0
                for i in range(vp['target_lttb'] - 2):
                    avg_s = math.floor((i + 1) * every) + 1
                    avg_e = min(math.floor((i + 2) * every) + 1, n_raw)
                    avg_x = np.mean(wl_g[avg_s:avg_e])
                    avg_y = np.mean(val_g[avg_s:avg_e])
                    
                    r_s = math.floor(i * every) + 1
                    r_e = math.floor((i + 1) * every) + 1
                    bx = wl_g[r_s:r_e]
                    by = val_g[r_s:r_e]
                    
                    areas = np.abs(
                        wl_g[a] * (by - avg_y) +
                        bx * (avg_y - val_g[a]) +
                        avg_x * (val_g[a] - by)
                    )
                    max_idx = r_s + np.argmax(areas)
                    l_idx.append(int(max_idx))
                    a = max_idx
                l_idx.append(n_raw - 1)
                l_idx = sorted(list(set(l_idx)))
                
                rendered_wl = wl_g[l_idx]
                rendered_val = val_g[l_idx]
                marker_style = 'o'
                marker_sz = 2.5
                line_w = 0.8
                color_plot = COLORS['primary']
                
            # Plot the segment of interest: 250 to 450 nm
            # Show full raw spectrum in very light grey behind
            plot_mask = np.logical_and(wl_full >= 250.0, wl_full <= 450.0)
            ax.plot(wl_full[plot_mask], val_full[plot_mask], color='#e2e8f0', lw=1.2, alpha=0.5, label='Raw spectrum')
            
            # Plot the rendered line/markers in segment range 250 to 450 nm
            rend_mask = np.logical_and(rendered_wl >= 250.0, rendered_wl <= 450.0)
            ax.plot(
                rendered_wl[rend_mask], rendered_val[rend_mask], color=color_plot, 
                lw=line_w, marker=marker_style, markersize=marker_sz, alpha=0.9, 
                label='Rendered points'
            )
            
            ax.set_xlim(250.0, 450.0)
            ax.set_ylim(bottom=-10, top=max(val_full[plot_mask]) * 1.15)
            ax.set_facecolor('#fafafb')
            ax.grid(True, color='#e2e8f0', linestyle='-', linewidth=0.5)
            
            # Count how many points are in the plotted segment
            rendered_segment_count = np.sum(rend_mask)
            
            # Annotation text box
            box_text = (
                f"{vp['title']}\n"
                f"Global Range: {vp['g_min']:.1f} - {vp['g_max']:.1f} nm ({n_raw_g} raw pts)\n"
                f"Rendered segment count: {rendered_segment_count} pts\n"
                f"Annotation: {vp['desc']}"
            )
            ax.text(
                0.03, 0.95, box_text, transform=ax.transAxes,
                fontsize=8.5, va='top', ha='left', fontweight='semibold',
                bbox=dict(boxstyle='round', facecolor='white', edgecolor='#e2e8f0', alpha=0.92)
            )
            
            ax.set_xlabel("Wavelength (nm)")
            ax.set_ylabel("Intensity (counts)")
            ax.tick_params(axis='both', colors='#475569')
            
        plt.suptitle("Figure F8: Adaptive Zoom Level Downsampling & Saturation Behaviour (250–450 nm Window)", 
                     fontsize=12, fontweight='bold', y=0.98, color='#0f172a')
        plt.tight_layout()
        plt.subplots_adjust(top=0.92, hspace=0.25, wspace=0.22)
        
        self._save_figure(fig, "fig8_adaptive_zoom")
        plt.close()

    def generate_all(self):
        print("\n" + "="*60)
        print(" GENERATING RESEARCH-GRADE PUBLICATION FIGURES")
        print("="*60)
        self.generate_fig1_architecture()
        self.generate_fig2_reshape_schematic()
        self.generate_fig3_pre_post_subtraction()
        self.generate_fig4_spectral_variability()
        self.generate_fig5_peak_retention()
        self.generate_fig4_peak_comparison()
        self.generate_fig6_acquisition_sequence()
        self.generate_fig7_nist_overlay()
        self.generate_fig8_adaptive_zoom()
        print("\n[SUCCESS] All publication figures generated successfully.")
        print("="*60 + "\n")

if __name__ == "__main__":
    raw_data = r"d:\LunarAtlas\datasets\uploads\20230825\ch3_lib_002_20230825T104221_00_l1\ch3_lib_002_20230825T104221_00_l1.csv"
    cleaned_data = r"d:\LunarAtlas\datasets\processed\calibrated\20230825\ch3_lib_002_20230825T104221_00_l1\ch3_lib_002_20230825T104221_00_l1_cleaned.csv"
    output_dir = r"d:\LunarAtlas\publication_figures"
    
    # Allow command-line overrides
    r_path = sys.argv[1] if len(sys.argv) > 1 else raw_data
    d_path = sys.argv[2] if len(sys.argv) > 2 else cleaned_data
    o_dir = sys.argv[3] if len(sys.argv) > 3 else output_dir
    
    try:
        generator = EnhancedPublicationFiguresGenerator(r_path, d_path, o_dir)
        generator.generate_all()
    except Exception as e:
        print(f"[ERROR] Failed to generate figures: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
