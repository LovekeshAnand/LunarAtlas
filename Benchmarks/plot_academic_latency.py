import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde
import os

def main():
    baseline_csv = "academic_baseline_latencies.csv"
    sweep_csv = "academic_sweep_latencies.csv"
    
    if not os.path.exists(baseline_csv) or not os.path.exists(sweep_csv):
        print("[ERROR] CSV data files not found. Please run the benchmark script first!")
        return

    # Load data
    df_base = pd.read_csv(baseline_csv)
    df_sweep = pd.read_csv(sweep_csv)
    
    latencies = df_base['latency_ms'].values
    mean_lat = np.mean(latencies)
    std_lat = np.std(latencies)
    p50 = np.percentile(latencies, 50)
    p95 = np.percentile(latencies, 95)
    p99 = np.percentile(latencies, 99)

    print(f"Loaded {len(latencies)} baseline runs:")
    print(f"  Mean   : {mean_lat:.2f} ms")
    print(f"  Std Dev: {std_lat:.2f} ms")
    print(f"  P50    : {p50:.2f} ms")
    print(f"  P95    : {p95:.2f} ms")
    print(f"  P99    : {p99:.2f} ms")

    # Set up matplotlib style (Sleek Academic Research Theme)
    plt.rcParams['font.family'] = 'DejaVu Sans'
    plt.rcParams['font.size'] = 9
    plt.rcParams['axes.edgecolor'] = '#4a5568'
    plt.rcParams['axes.linewidth'] = 0.8

    # Create figure with 3 subplots side-by-side
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(14, 4.2), dpi=300)
    
    # ----------------------------------------------------
    # Subplot A: Probability Density Function (PDF)
    # ----------------------------------------------------
    # Plot histogram with density scaling
    n, bins, patches = ax1.hist(latencies, bins=50, density=True, alpha=0.3, color='#1f77b4', edgecolor='none')
    
    # Fit KDE
    kde = gaussian_kde(latencies)
    x_grid = np.linspace(min(latencies) - 10, max(latencies) + 10, 500)
    ax1.plot(x_grid, kde(x_grid), color='#1f77b4', lw=1.5, label='KDE Estimate')
    
    ax1.axvline(mean_lat, color='#d62728', linestyle='--', lw=1.2, label=f'Mean ({mean_lat:.1f} ms)')
    ax1.set_title("Probability Density (PDF)", fontsize=10, fontweight='bold', pad=10)
    ax1.set_xlabel("End-to-End Latency (ms)", labelpad=6)
    ax1.set_ylabel("Density", labelpad=6)
    ax1.grid(True, linestyle=':', alpha=0.5, color='#cbd5e1')
    ax1.legend(frameon=True, facecolor='white', edgecolor='#e2e8f0', fontsize=8)
    
    # ----------------------------------------------------
    # Subplot B: Cumulative Distribution Function (CDF)
    # ----------------------------------------------------
    sorted_lat = np.sort(latencies)
    cdf = np.arange(1, len(sorted_lat) + 1) / len(sorted_lat)
    ax2.plot(sorted_lat, cdf, color='#2ca02c', lw=1.8, label='Empirical CDF')
    
    # Highlight percentiles
    percentiles = [(50, p50, '#1f77b4'), (95, p95, '#ff7f0e'), (99, p99, '#d62728')]
    for pct, val, color in percentiles:
        # Horizontal line
        ax2.axhline(pct / 100.0, color='#94a3b8', linestyle=':', lw=0.8)
        # Vertical line
        ax2.axvline(val, color=color, linestyle='--', lw=1.0, 
                   label=f'P{pct} ({val:.1f} ms)')
        
    ax2.set_title("Cumulative Distribution (CDF)", fontsize=10, fontweight='bold', pad=10)
    ax2.set_xlabel("End-to-End Latency (ms)", labelpad=6)
    ax2.set_ylabel("Cumulative Probability", labelpad=6)
    ax2.set_ylim(-0.02, 1.05)
    ax2.grid(True, linestyle=':', alpha=0.5, color='#cbd5e1')
    ax2.legend(frameon=True, facecolor='white', edgecolor='#e2e8f0', fontsize=8, loc='lower right')

    # ----------------------------------------------------
    # Subplot C: Downsampling Scale Sweep (Latency vs k)
    # ----------------------------------------------------
    sweep_groups = df_sweep.groupby('zoom_level')['latency_ms'].agg(['mean', 'std']).reindex([
        "Full (k=0)", "k=1 (50%)", "k=2 (25%)", "k=3 (12.5%)", "k=4 (6.25%)"
    ])
    
    x_labels = ["Full\n(k=0)", "k=1\n(50%)", "k=2\n(25%)", "k=3\n(12.5%)", "k=4\n(6.25%)"]
    x_pos = np.arange(len(x_labels))
    
    means = sweep_groups['mean'].values
    stds = sweep_groups['std'].values
    
    ax3.errorbar(x_pos, means, yerr=stds, fmt='-o', color='#9467bd', ecolor='#c5b0d5', 
                 elinewidth=1.5, capsize=4, capthick=1.5, ms=6, lw=1.5, label='Mean Latency ± SD')
    
    ax3.set_xticks(x_pos)
    ax3.set_xticklabels(x_labels)
    ax3.set_title("Latency vs. Zoom Level (k)", fontsize=10, fontweight='bold', pad=10)
    ax3.set_xlabel("Downsampling Configuration", labelpad=6)
    ax3.set_ylabel("Latency (ms)", labelpad=6)
    ax3.grid(True, linestyle=':', alpha=0.5, color='#cbd5e1')
    ax3.legend(frameon=True, facecolor='white', edgecolor='#e2e8f0', fontsize=8)

    plt.tight_layout()
    
    # Save the output image
    out_dir = "../publication_figures"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "fig6_db_benchmark.png")
    plt.savefig(out_path, dpi=300, facecolor='white')
    plt.close()
    
    print(f"[SUCCESS] Latency distribution plot saved to: {os.path.abspath(out_path)}")

if __name__ == "__main__":
    main()
