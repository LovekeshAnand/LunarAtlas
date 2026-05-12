"""
Enhanced Publication-Quality LTTB Visualization Suite
Clean, Minimalist, Publisher-Ready
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.gridspec import GridSpec
import seaborn as sns
from pathlib import Path
from scipy.signal import find_peaks
import warnings
warnings.filterwarnings('ignore')

# Professional minimalist colors
COLORS = {
    'primary': '#0055A4',      # Deep Blue
    'secondary': '#E35205',    # Vibrant Orange
    'accent1': '#00A3A6',      # Teal
    'accent3': '#FFB81C',      # Yellow
    'grey': '#A7A8AA',         # Neutral Grey
    'dark': '#111111',         # Black
    'highlight': '#C8102E'     # Red Highlight
}

class EnhancedLTTBVisualizer:
    def __init__(self, data_path: str, output_dir: str = 'publication_figures'):
        print(f"Loading data from: {data_path}")
        self.data = pd.read_csv(data_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self._setup_publication_style()
        
    def _setup_publication_style(self):
        """Clean, minimal, Elsevier/Nature standard style"""
        plt.style.use('seaborn-v0_8-whitegrid')
        plt.rcParams.update({
            'figure.dpi': 300,
            'savefig.dpi': 600,
            'savefig.bbox': 'tight',
            'font.family': 'serif',
            'font.serif': ['Times New Roman', 'DejaVu Serif'],
            'font.size': 10,
            'axes.labelsize': 11,
            'axes.titlesize': 12,
            'axes.titleweight': 'bold',
            'xtick.labelsize': 10,
            'ytick.labelsize': 10,
            'legend.fontsize': 9,
            'grid.alpha': 0.3,
            'xtick.direction': 'in',
            'ytick.direction': 'in',
        })
    
    def lttb_downsample_with_tracking(self, wavelengths, intensities, threshold):
        """LTTB Algorithm core tracking"""
        n = len(wavelengths)
        if threshold >= n or threshold < 3:
            return wavelengths, intensities, list(range(n)), []
        
        sampled_indices = [0]
        triangle_info = []
        every = (n - 2) / (threshold - 2)
        a = 0
        
        for i in range(threshold - 2):
            avg_range_start = int((i + 1) * every) + 1
            avg_range_end = min(int((i + 2) * every) + 1, n)
            
            avg_x = np.mean(wavelengths[avg_range_start:avg_range_end])
            avg_y = np.mean(intensities[avg_range_start:avg_range_end])
            
            range_offs = int(i * every) + 1
            range_to = int((i + 1) * every) + 1
            
            point_a_x = wavelengths[a]
            point_a_y = intensities[a]
            
            areas = np.abs(
                point_a_x * (intensities[range_offs:range_to] - avg_y) +
                wavelengths[range_offs:range_to] * (avg_y - point_a_y) +
                avg_x * (point_a_y - intensities[range_offs:range_to])
            )
            
            max_area_idx = np.argmax(areas)
            selected_idx = range_offs + max_area_idx
            
            triangle_info.append({
                'bucket_range': (range_offs, range_to),
                'point_a': (point_a_x, point_a_y),
                'point_b': (wavelengths[selected_idx], intensities[selected_idx]),
                'point_avg': (avg_x, avg_y)
            })
            
            sampled_indices.append(selected_idx)
            a = selected_idx
        
        sampled_indices.append(n - 1)
        return wavelengths[sampled_indices], intensities[sampled_indices], sampled_indices, triangle_info

    def fig1_lttb_mechanism_clear(self):
        """
        Figure 1: Mechanism
        Uses a smooth, synthetic curve to clearly illustrate the algorithm geometry,
        avoiding raw data spikes that hide the logic.
        """
        print("[Fig 1] Generating Clean Mechanism Illustration...")
        
        # Synthetic data: Smooth hump with clear edges
        x = np.linspace(0, 100, 40)
        y = np.sin(x * 0.05) * 50 + np.exp(-0.5 * ((x - 50) / 10)**2) * 150
        
        wl_down, int_down, indices, triangle_info = self.lttb_downsample_with_tracking(x, y, 12)
        
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.plot(x, y, 'o-', color=COLORS['grey'], lw=1.5, alpha=0.5, label='High-Resolution Signal')
        
        if triangle_info:
            tri = triangle_info[len(triangle_info)//2] # Select middle triangle
            bucket_start, bucket_end = tri['bucket_range']
            
            # Highlight Bucket
            ax.axvspan(x[bucket_start], x[bucket_end-1], alpha=0.15, color=COLORS['accent1'], label='Candidate Bucket')
            
            pt_a, pt_b, pt_avg = tri['point_a'], tri['point_b'], tri['point_avg']
            
            # Draw Triangle
            triangle = Polygon([pt_a, pt_b, pt_avg], fill=True, alpha=0.2, facecolor=COLORS['secondary'], edgecolor=COLORS['secondary'], ls='--', lw=2)
            ax.add_patch(triangle)
            
            # Connect the main lines
            ax.plot([pt_a[0], pt_avg[0]], [pt_a[1], pt_avg[1]], color=COLORS['secondary'], lw=1.5, ls='--')
            ax.plot([pt_a[0], pt_b[0]], [pt_a[1], pt_b[1]], color=COLORS['secondary'], lw=1.5, ls='--')
            ax.plot([pt_b[0], pt_avg[0]], [pt_b[1], pt_avg[1]], color=COLORS['secondary'], lw=1.5, ls='--')
            
            # Plot Key Points
            ax.scatter(*pt_a, color=COLORS['primary'], s=120, zorder=5, label='Previous Selected Point')
            ax.scatter(*pt_b, color=COLORS['highlight'], s=150, marker='*', zorder=5, label='Max Area Selection')
            ax.scatter(*pt_avg, color=COLORS['dark'], s=100, marker='X', zorder=5, label='Next Bucket Centroid')
            
        ax.set_xlabel('Index')
        ax.set_ylabel('Intensity')
        ax.set_title('LTTB Triangle Area Maximization (Algorithmic Illustration)')
        ax.legend(loc='upper right', frameon=True)
        
        plt.tight_layout()
        output_path = self.output_dir / 'fig1_lttb_mechanism'
        plt.savefig(f'{output_path}.pdf')
        plt.savefig(f'{output_path}.png', dpi=600)
        plt.close()

    def fig2_perfect_comparison(self, measurement_id=3):
        """
        Figure 2: Perfect Comparison
        Clean 2-panel showing exact before/after alignment.
        """
        print("[Fig 2] Creating Perfect Comparison...")
        df = self.data[self.data['Measurement_ID'] == measurement_id].copy().sort_values('Wavelength_nm')
        wl = df['Wavelength_nm'].values
        val = df['Cleaned_Intensity'].values
        
        wl_d, val_d, _, _ = self.lttb_downsample_with_tracking(wl, val, threshold=500)
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), height_ratios=[1, 1.2])
        
        # Panel A: Full Spectrum
        ax1.plot(wl, val, color=COLORS['grey'], lw=1.5, alpha=0.5, label=f'Original ({len(wl)} pts)')
        ax1.plot(wl_d, val_d, color=COLORS['primary'], lw=1.0, alpha=0.9, label=f'LTTB ({len(wl_d)} pts)')
        ax1.set_title('(a) Full Spectrum Global Comparison')
        ax1.set_ylabel('Intensity')
        ax1.legend()
        
        # Panel B: Zoomed Detail Comparison
        zoom_mask_orig = (wl >= 385) & (wl <= 405) # Complex peaks area
        zoom_mask_down = (wl_d >= 385) & (wl_d <= 405)
        
        ax2.plot(wl[zoom_mask_orig], val[zoom_mask_orig], '-o', color=COLORS['grey'], lw=2, markersize=4, alpha=0.5, label='Original Data')
        ax2.plot(wl_d[zoom_mask_down], val_d[zoom_mask_down], '-s', color=COLORS['highlight'], lw=1.5, markersize=5, alpha=0.9, label='LTTB Preserved Path')
        ax2.set_title('(b) Detailed Zoom: Structural Preservation')
        ax2.set_xlabel('Wavelength (nm)')
        ax2.set_ylabel('Intensity')
        ax2.legend()
        
        plt.tight_layout()
        output_path = self.output_dir / 'fig2_perfect_comparison'
        plt.savefig(f'{output_path}.pdf')
        plt.savefig(f'{output_path}.png', dpi=600)
        plt.close()

    def fig3_adaptive_zoom(self, measurement_id=3):
        """Figure 3: Clean Adaptive Zoom"""
        print("[Fig 3] Creating Clean Adaptive Zoom...")
        df = self.data[self.data['Measurement_ID'] == measurement_id].copy().sort_values('Wavelength_nm')
        wl = df['Wavelength_nm'].values
        val = df['Cleaned_Intensity'].values
        
        configs = [
            {'win': (200, 850), 'label': '(a) Global View'},
            {'win': (250, 450), 'label': '(b) Regional Zoom'},
            {'win': (390, 405), 'label': '(c) Feature Zoom'}
        ]
        
        fig, axes = plt.subplots(1, 3, figsize=(15, 4))
        
        for ax, config in zip(axes, configs):
            w0, w1 = config['win']
            mask = (wl >= w0) & (wl <= w1)
            wl_w, val_w = wl[mask], val[mask]
            wl_p, val_p, _, _ = self.lttb_downsample_with_tracking(wl_w, val_w, 200)
            
            ax.plot(wl_w, val_w, color=COLORS['grey'], lw=1, alpha=0.4)
            ax.plot(wl_p, val_p, '-o', color=COLORS['primary'], markersize=2, lw=1.2)
            ax.set_title(config['label'])
            ax.set_xlabel('Wavelength (nm)')
            if ax == axes[0]: ax.set_ylabel('Intensity')
            
        plt.tight_layout()
        output_path = self.output_dir / 'fig3_adaptive_zoom'
        plt.savefig(f'{output_path}.pdf')
        plt.savefig(f'{output_path}.png', dpi=600)
        plt.close()

    def fig4_peak_preservation(self, measurement_id=3):
        """Figure 4: Clean Pareto Front"""
        print("[Fig 4] Enhancing Quantitative Pareto Front...")
        df = self.data[self.data['Measurement_ID'] == measurement_id].copy().sort_values('Wavelength_nm')
        wl, val = df['Wavelength_nm'].values, df['Cleaned_Intensity'].values
        
        peaks, _ = find_peaks(val, prominence=50, distance=5)
        thresholds = [50, 100, 200, 400, 800, len(wl)]
        res = []
        
        for t in thresholds:
            _, _, idxs, _ = self.lttb_downsample_with_tracking(wl, val, t)
            pres = 100 * np.isin(peaks, idxs).sum() / len(peaks)
            red = len(wl) / len(idxs) if len(idxs) > 0 else 1
            res.append((red, pres, t))
            
        df_res = pd.DataFrame(res, columns=['reduction', 'preservation', 'threshold'])
        
        fig, ax = plt.subplots(figsize=(7, 5))
        ax.plot(df_res['reduction'], df_res['preservation'], 'o-', color=COLORS['accent1'], lw=2)
        
        # Annotate points clearly
        for r, p, t in zip(df_res['reduction'], df_res['preservation'], df_res['threshold']):
            ax.annotate(f'N={t}', (r, p), textcoords="offset points", xytext=(0,10), ha='center', fontsize=9)
            
        ax.set_xlabel('Data Reduction Factor')
        ax.set_ylabel('Peak Preservation (%)')
        ax.set_title('Trade-off: Compression vs Fidelity')
        
        plt.tight_layout()
        output_path = self.output_dir / 'fig4_peak_preservation'
        plt.savefig(f'{output_path}.pdf')
        plt.savefig(f'{output_path}.png', dpi=600)
        plt.close()
        
    def fig5_heatmap(self):
        """Figure 5: Clean Spectral Heatmap"""
        print("[Fig 5] Creating clean heatmap...")
        pivot = self.data.pivot_table(index='Measurement_ID', columns='Wavelength_nm', values='Cleaned_Intensity', aggfunc='first')
        
        fig, ax = plt.subplots(figsize=(10, 5))
        im = ax.imshow(pivot.values, aspect='auto', cmap='magma', 
                       extent=[pivot.columns[0], pivot.columns[-1], len(pivot)-0.5, -0.5])
        
        plt.colorbar(im, label='Intensity (counts)')
        ax.set_xlabel('Wavelength (nm)')
        ax.set_ylabel('Measurement ID')
        ax.set_yticks(range(len(pivot)))
        ax.set_yticklabels(pivot.index)
        ax.set_title('Global Spectral Footprint')
        
        plt.tight_layout()
        output_path = self.output_dir / 'fig5_heatmap'
        plt.savefig(f'{output_path}.pdf')
        plt.savefig(f'{output_path}.png', dpi=600)
        plt.close()

    def generate_all(self):
        print("\n" + "="*50)
        print(" GENERATING CLEAN VISUAL SUITE")
        print("="*50)
        self.fig1_lttb_mechanism_clear()
        self.fig2_perfect_comparison()
        self.fig3_adaptive_zoom()
        self.fig4_peak_preservation()
        self.fig5_heatmap()
        print("\n[SUCCESS] Clean, publisher-ready figures saved.")

if __name__ == "__main__":
    data_path = r"D:\ch3_libs\lib-v2\data\calibrated\20230825\ch3_lib_002_20230825T104221_00_l1\cleaned_libs_data\cleaned_spectra\ch3_lib_002_20230825T104221_00_l1_cleaned.csv"
    viz = EnhancedLTTBVisualizer(data_path)
    viz.generate_all()