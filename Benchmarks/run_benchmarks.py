"""
Computational Benchmark Suite for LIBS Spectrum Downsampling
Author: LunarAtlas Research Team

This script simulates a 16,384-point raw LIBS spectrum containing simulated Gaussian 
elemental peaks (Fe, Ca, Mg) and benchmarks the computational throughput (latency, 
reduction ratio, and peak retention) of the downsampling algorithm.
"""

import time
import math
import random

def generate_mock_libs_spectrum(num_points=16384):
    """
    Generates a realistic mock LIBS spectrum with noise and several emission peaks.
    """
    print(f"[INFO] Generating mock LIBS spectrum with {num_points:,} points...")
    start_wl = 164.35
    end_wl = 878.26
    step = (end_wl - start_wl) / num_points
    
    data = []
    # Define some strong elemental lines: (wavelength, peak_intensity, width_nm)
    peaks = [
        (279.553, 5000.0, 0.4),  # Mg II
        (288.158, 3500.0, 0.3),  # Si I
        (393.366, 8000.0, 0.5),  # Ca II
        (404.581, 2500.0, 0.3),  # Fe I
        (588.995, 6000.0, 0.4),  # Na I
        (656.281, 4500.0, 0.6),  # H-alpha
    ]
    
    for i in range(num_points):
        wl = start_wl + i * step
        # Base background noise
        intensity = 100.0 + random.uniform(0, 50.0) + math.sin(wl / 100.0) * 20.0
        
        # Add gaussian emission peaks
        for peak_wl, peak_int, width in peaks:
            distance = wl - peak_wl
            intensity += peak_int * math.exp(-0.5 * (distance / width) ** 2)
            
        data.append((wl, intensity))
        
    return data, peaks

def run_lttb_downsample(data, threshold=1600):
    """
    Largest Triangle Three Buckets (LTTB) downsampling algorithm in Python.
    Reduces data down to `threshold` points.
    """
    data_length = len(data)
    if threshold >= data_length or threshold == 0:
        return data

    sampled = []
    
    # Bucket size. Leave room for start and end points
    bucket_size = (data_length - 2) / (threshold - 2)

    # Always add the first point
    sampled.append(data[0])

    a = 0  # Index of the first point in the previous bucket
    
    for i in range(threshold - 2):
        # Calculate range for current bucket
        bin_start = int(math.floor((i + 1) * bucket_size)) + 1
        bin_end = int(math.floor((i + 2) * bucket_size)) + 1
        bin_end = min(bin_end, data_length)

        # Calculate range for next bucket to compute average (c)
        next_bin_start = int(math.floor((i + 2) * bucket_size)) + 1
        next_bin_end = int(math.floor((i + 3) * bucket_size)) + 1
        next_bin_end = min(next_bin_end, data_length)

        # Point c is the average of the next bucket
        avg_x = 0
        avg_y = 0
        bin_length = next_bin_end - next_bin_start
        if bin_length > 0:
            for k in range(next_bin_start, next_bin_end):
                avg_x += data[k][0]
                avg_y += data[k][1]
            avg_x /= bin_length
            avg_y /= bin_length
        else:
            avg_x, avg_y = data[bin_end - 1]

        # Point a is the previously selected point
        ax, ay = data[a]

        # Find the point in current bucket that forms the largest triangle with a and c
        max_area = -1
        next_a = bin_start

        for j in range(bin_start, bin_end):
            # Calculate triangle area
            bx, by = data[j]
            area = abs((ax - avg_x) * (by - ay) - (ax - bx) * (avg_y - ay)) * 0.5
            if area > max_area:
                max_area = area
                next_a = j

        sampled.append(data[next_a])
        a = next_a  # This selected point becomes the next 'a'

    # Always add the last point
    sampled.append(data[-1])
    return sampled

def benchmark():
    print("====================================================")
    print(" LUNARATLAS DOWNSAMPLING BENCHMARK SUITE")
    print("====================================================")
    
    raw_data, true_peaks = generate_mock_libs_spectrum(16384)
    raw_count = len(raw_data)
    
    target_sizes = [3200, 1600, 800, 400]
    
    for size in target_sizes:
        print(f"\n[RUN] Running benchmark for target size: {size} points (Ratio {raw_count/size:.1f}x reduction)...")
        
        t0 = time.perf_counter()
        downsampled = run_lttb_downsample(raw_data, size)
        t1 = time.perf_counter()
        
        latency_ms = (t1 - t0) * 1000.0
        
        # Verify peak preservation
        peaks_preserved = 0
        for peak_wl, peak_int, _ in true_peaks:
            # Check if there is a point in the downsampled spectrum very close to the peak
            closest_point = min(downsampled, key=lambda p: abs(p[0] - peak_wl))
            distance = abs(closest_point[0] - peak_wl)
            intensity_ratio = closest_point[1] / (peak_int + 100.0) # Adjust for noise background
            
            if distance < 0.8 and intensity_ratio > 0.90:
                peaks_preserved += 1
                
        preservation_rate = (peaks_preserved / len(true_peaks)) * 100.0
        
        print(f"  Execution Latency: {latency_ms:.3f} ms")
        print(f"  Retained Points: {len(downsampled)} / {raw_count}")
        print(f"  Peak Retention Accuracy: {preservation_rate:.1f}% ({peaks_preserved}/{len(true_peaks)} lines verified)")

    print("\n[SUCCESS] Benchmark execution complete.")
    print("====================================================")

if __name__ == "__main__":
    benchmark()
