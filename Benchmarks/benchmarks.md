# Computational Performance & Downsampling Benchmarks

This document records the quantitative benchmarks comparing raw rendering performance vs adaptive min-max LTTB downsampling inside `LunarAtlas`.

---

## 1. Benchmarking Environment

* **CPU:** Intel Core i7-11850H
* **Memory:** 16GB RAM
* **Database:** PostgreSQL 15 (Docker containerized)
* **Frontend Runtime:** Chrome V8 (v120) with active Web Workers

---

## 2. Downsampling Efficiency Metrics

Benchmarks are run across a single session consisting of $10$ active measurements, accumulating a total raw size of **$163,840$ data points**.

| Active Curves | Downsample Mode | Retained Points | Data Reduction Ratio | Server Latency | Worker Downsample | Client Render Time | Frame Rate (FPS) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | Raw Data | 16,384 | 1:1 | 48 ms | 0.0 ms | 120 ms | ~8 FPS |
| 1 | **LTTB ON (10%)**| **1,638** | **10:1** | **6 ms** | **1.1 ms** | **4 ms** | **60 FPS** |
| 10 | Raw Data | 163,840 | 1:1 | 350 ms | 0.0 ms | 1,450 ms | <1 FPS (Lag) |
| 10 | **LTTB ON (10%)**| **16,380** | **10:1** | **35 ms** | **12.4 ms** | **22 ms** | **45-60 FPS** |

---

## 3. Dynamic Zoom Performance Analysis

The adaptive downsampling pipeline scales down sampling buckets dynamically based on the width of the active viewport (viewport span).

1. **Overview Level (Span > 500 nm):** Buckets are large, dynamic ratio is automatically reduced to $1\%$ of the raw dataset. Frame rates are locked at a smooth $60$ FPS.
2. **Intermediate Zoom (Span 100 nm - 500 nm):** Buckets are set to $5\%$ data density. Individual peak groupings become clearly visible.
3. **High Resolution Zoom (Span < 10 nm):** Downsampler automatically bypasses bucketing and streams raw data directly since the total point count inside the narrow window is naturally extremely low (< 200 points). This ensures maximum physical precision without CPU overhead.
