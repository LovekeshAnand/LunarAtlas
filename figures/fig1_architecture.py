#!/usr/bin/env python3
"""
fig1_architecture.py — System Architecture Figure Generator

Generates Figure 1 (End-to-End System Architecture) for the paper,
redesigned to look extremely professional, with optimized vertical spacing
to prevent text overlaps and cut-offs.
"""

import os
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def main():
    print("[Fig 1] Generating redesigned system architecture diagram...")
    
    output_dir = Path("publication_figures")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Set up matplotlib configuration
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['Arial', 'Liberation Sans', 'DejaVu Sans'],
        'svg.fonttype': 'none'
    })
    
    # Adjusted figsize and ylim to prevent condensing and cut-offs
    fig, ax = plt.subplots(figsize=(11.5, 5.8), dpi=300)
    ax.set_xlim(0, 11.5)
    ax.set_ylim(0.2, 7.4)
    
    # Layer Backgrounds (Rounded rectangular boxes representing the layers)
    # Presentation Layer (Row 1)
    ax.add_patch(patches.FancyBboxPatch(
        (0.4, 5.6), 10.7, 1.6,
        boxstyle="round,pad=0.08",
        facecolor='#eff6ff', edgecolor='#2563eb', linewidth=1.2, alpha=0.9
    ))
    
    # Logic Layer (Row 2)
    ax.add_patch(patches.FancyBboxPatch(
        (0.4, 2.5), 10.7, 2.4,
        boxstyle="round,pad=0.08",
        facecolor='#faf5ff', edgecolor='#7c3aed', linewidth=1.2, alpha=0.9
    ))
    
    # Database & Pipeline Layer (Row 3 - Shifted bottom to 0.3 to increase vertical gap for labels)
    ax.add_patch(patches.FancyBboxPatch(
        (0.4, 0.3), 10.7, 1.5,
        boxstyle="round,pad=0.08",
        facecolor='#f0fdf4', edgecolor='#16a34a', linewidth=1.2, alpha=0.9
    ))
    
    # --- Layer Sidetitles (Shifted to x=1.4 to prevent left margin clipping) ---
    ax.text(1.4, 6.4, "1. PRESENTATION\nLAYER\n(Client Side)", fontsize=9, fontweight='black', color='#1e3a8a', ha='center', va='center')
    ax.text(1.4, 3.7, "2. LOGIC LAYER\n(Server Side)", fontsize=9, fontweight='black', color='#581c87', ha='center', va='center')
    ax.text(1.4, 1.1, "3. DATABASE &\nPIPELINE LAYER", fontsize=9, fontweight='black', color='#14532d', ha='center', va='center')
    
    # ==========================================
    # 1. PRESENTATION LAYER COMPONENTS
    # ==========================================
    # Web Application (React 18) Box
    ax.add_patch(patches.FancyBboxPatch((2.5, 5.8), 3.0, 1.0, boxstyle="round,pad=0.04", facecolor='white', edgecolor='#64748b', linewidth=1.2))
    ax.text(4.0, 6.3, "Web Application\n(React 18 UI)", fontsize=9, fontweight='bold', color='#475569', ha='center', va='center')
    
    # Interactive Spectral Viewer (SVG) Box
    ax.add_patch(patches.FancyBboxPatch((6.5, 5.8), 3.0, 1.0, boxstyle="round,pad=0.04", facecolor='white', edgecolor='#64748b', linewidth=1.2))
    ax.text(8.0, 6.3, "Spectral Viewer\n(SVG Graphics Canvas)", fontsize=9, fontweight='bold', color='#475569', ha='center', va='center')
    
    # ==========================================
    # 2. LOGIC LAYER COMPONENTS
    # ==========================================
    # API Service Box
    ax.add_patch(patches.FancyBboxPatch((2.5, 2.8), 6.2, 1.7, boxstyle="round,pad=0.04", facecolor='white', edgecolor='#7c3aed', linewidth=1.2))
    
    # Title centered at the top of the box
    ax.text(5.6, 4.15, "API Service (FastAPI)", fontsize=9, fontweight='bold', color='#581c87', ha='center', va='center')
    # Bullet points left-aligned inside the box for clean layout
    api_bullets = (
        "• Route Handler & Redis Cache Check\n"
        "• ALS Baseline & Savitzky-Golay Denoising\n"
        "• LTTB + Peaks Downsampling Engine"
    )
    ax.text(2.8, 3.35, api_bullets, fontsize=8.5, fontweight='bold', color='#581c87', ha='left', va='center', linespacing=1.6)
    
    # Cache Decision Diamond (Cache found?)
    diamond_pts = [[10.1, 4.0], [10.9, 3.4], [10.1, 2.8], [9.3, 3.4]]
    ax.add_patch(patches.Polygon(diamond_pts, facecolor='#fed7aa', edgecolor='#ea580c', linewidth=1.2, zorder=5))
    ax.text(10.1, 3.4, "Cache\nfound?", fontsize=8, fontweight='bold', color='#7c2d12', ha='center', va='center', zorder=6)
    
    # ==========================================
    # 3. DATABASE & PIPELINE LAYER COMPONENTS (Shifted y down by 0.2 units to increase text spaces)
    # ==========================================
    # PostgreSQL Database Storage Box
    ax.add_patch(patches.FancyBboxPatch((2.5, 0.4), 3.4, 1.2, boxstyle="round,pad=0.04", facecolor='white', edgecolor='#16a34a', linewidth=1.2))
    ax.text(4.2, 1.3, "PostgreSQL Database", fontsize=9, fontweight='bold', color='#14532d', ha='center', va='center')
    db_bullets = "• Raw Count Readings\n• Cleaned Spectra Data\n• NIST Reference Lines"
    ax.text(2.8, 0.8, db_bullets, fontsize=8.5, fontweight='bold', color='#14532d', ha='left', va='center', linespacing=1.4)
    
    # Ingestion Pipeline Box
    ax.add_patch(patches.FancyBboxPatch((6.5, 0.4), 2.2, 1.2, boxstyle="round,pad=0.04", facecolor='white', edgecolor='#2563eb', linewidth=1.2))
    ax.text(7.6, 1.3, "Ingestion Pipeline", fontsize=9, fontweight='bold', color='#1e3a8a', ha='center', va='center')
    pipe_bullets = "• XML Metadata Ingestion\n• Wide-to-Long Reshape\n• Background Subtraction"
    ax.text(6.6, 0.8, pipe_bullets, fontsize=8.5, fontweight='bold', color='#1e3a8a', ha='left', va='center', linespacing=1.4)
    
    # Raw PDS4 L1 Archive Box
    ax.add_patch(patches.FancyBboxPatch((9.6, 0.4), 1.2, 1.2, boxstyle="round,pad=0.04", facecolor='white', edgecolor='#64748b', linewidth=1.2))
    ax.text(10.2, 1.0, "Raw PDS4 L1\nArchive\n(XML/CSV)", fontsize=9, fontweight='bold', color='#475569', ha='center', va='center')
    
    # ==========================================
    # FLOW ARROWS AND CONNECTIONS
    # ==========================================
    # Arrow properties
    arrow_grey = dict(facecolor='#64748b', edgecolor='#64748b', width=1.0, headwidth=4, headlength=5, shrink=0.02)
    arrow_blue = dict(facecolor='#2563eb', edgecolor='#2563eb', width=1.0, headwidth=4, headlength=5, shrink=0.02)
    
    # --- Presentation -> Logic ---
    # Web App -> API Service (x=4.0, from y=5.78 to y=4.52)
    ax.annotate("", xy=(4.0, 4.52), xytext=(4.0, 5.78), arrowprops=arrow_grey)
    ax.text(3.9, 5.25, "HTTP Request", fontsize=8, fontweight='bold', color='#475569', ha='right', va='center')
    
    # --- Cache Checking flows ---
    # API Service -> Cache Decision (x=8.72 to x=9.28)
    ax.annotate("", xy=(9.28, 3.4), xytext=(8.72, 3.4), arrowprops=arrow_grey)
    
    # Cache Decision -> Interactive Viewer [Yes Path - Cache Hit]
    ax.plot([10.1, 10.1, 9.5], [4.02, 6.3, 6.3], color='#16a34a', lw=1.2)
    ax.annotate("", xy=(9.5, 6.3), xytext=(9.6, 6.3), arrowprops=dict(arrowstyle="->", color='#16a34a', lw=1.2))
    ax.text(10.2, 5.25, "Yes\n(Cache Hit)", fontsize=8, fontweight='bold', color='#15803d', ha='left', va='center')
    
    # Cache Decision -> PostgreSQL Database [No Path - Cache Miss]
    ax.plot([10.1, 10.1, 5.0, 5.0], [2.78, 2.25, 2.25, 1.62], color='#dc2626', lw=1.2, ls='--')
    ax.annotate("", xy=(5.0, 1.62), xytext=(5.0, 1.67), arrowprops=dict(arrowstyle="->", color='#dc2626', lw=1.2))
    ax.text(10.2, 2.25, "No\n(Cache Miss)", fontsize=8, fontweight='bold', color='#b91c1c', ha='left', va='center')
    
    # --- PostgreSQL -> API Service --- (x=4.0, from y=1.62 to y=2.78)
    ax.annotate("", xy=(4.0, 2.78), xytext=(4.0, 1.62), arrowprops=arrow_grey)
    # Placed text y to 2.18 (gap is 1.6 to 2.5), giving massive space from top (2.5) and bottom (1.6)
    ax.text(3.9, 2.18, "Responds with\nclean data", fontsize=7.5, color='#475569', ha='right', va='center')
    
    # --- API Service -> Interactive Viewer --- (x=8.0, from y=4.52 to y=5.78)
    ax.annotate("", xy=(8.0, 5.78), xytext=(8.0, 4.52), arrowprops=arrow_blue)
    ax.text(8.1, 5.25, "Responds with denoised,\ndownsampled data", fontsize=7.5, color='#1e3a8a', ha='left', va='center')
    
    # --- Ingestion Pipeline Flow ---
    # Raw PDS4 Archive Input -> Ingestion Pipeline (Wavelength / metadata read)
    ax.annotate("", xy=(8.7, 1.0), xytext=(9.6, 1.0), arrowprops=arrow_blue)
    ax.text(9.15, 1.15, "Reads", fontsize=8, fontweight='bold', color='#2563eb', ha='center', va='bottom')
    
    # Ingestion Pipeline -> Database Storage
    ax.annotate("", xy=(5.9, 1.0), xytext=(6.5, 1.0), arrowprops=arrow_grey)
    ax.text(6.2, 1.15, "Saves", fontsize=8, fontweight='bold', color='#475569', ha='center', va='bottom')
    
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)
    
    png_path = output_dir / "fig1_architecture.png"
    pdf_path = output_dir / "fig1_architecture.pdf"
    
    fig.savefig(png_path, dpi=300, bbox_inches='tight')
    fig.savefig(pdf_path, bbox_inches='tight')
    print(f"  * Saved Figure 1 to: {png_path} and {pdf_path}")
    plt.close()

if __name__ == "__main__":
    main()
