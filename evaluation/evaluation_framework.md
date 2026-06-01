# Quantitative Evaluation Framework

This document outlines the formal evaluation framework and metrics used to assess the quality of downsampled LIBS spectral lines inside the `LunarAtlas` platform. These metrics form the basis of our analytical validity for planetary geology research.

---

## 1. Primary Evaluation Metrics

We define three core metrics to quantitatively compare downsampling algorithms (e.g., Decimation, LTTB, Visvalingam-Whyatt, and Adaptive Min-Max).

### 1.1 Peak Intensity Error ($\epsilon_{I}$)
The deviation in height (intensity) of the downsampled emission peaks compared to the raw physical measurements.
$$\epsilon_{I} = \frac{1}{N_{p}} \sum_{k=1}^{N_{p}} \frac{|I_{raw}^{(k)} - I_{down}^{(k)}|}{I_{raw}^{(k)}}$$
Where $N_{p}$ is the number of target emission peaks, $I_{raw}^{(k)}$ is the physical peak height in the raw dataset, and $I_{down}^{(k)}$ is the corresponding height in the downsampled curve.
* **Acceptance Criterion:** $\epsilon_{I} < 1.0\%$ for focused research elements.

### 1.2 Peak Position Shift ($\delta_{\lambda}$)
The wavelength offset of the identified peak center after downsampling. A shift in peak wavelength leads to incorrect element/isotope identification.
$$\delta_{\lambda} = \max_{k} |\lambda_{raw}^{(k)} - \lambda_{down}^{(k)}|$$
* **Acceptance Criterion:** $\delta_{\lambda} = 0.0$ nm (Zero-shift guarantee). Wavelength values must remain locked to their exact raw spectral coordinates.

### 1.3 Signal-to-Noise Ratio (SNR) Maintenance ($\Delta_{SNR}$)
Ensures that the statistical noise floor is not artificially smoothed or amplified, preserving the true physical SNR of the spectrometer.
$$\Delta_{SNR} = |SNR_{raw} - SNR_{down}|$$
* **Acceptance Criterion:** $\Delta_{SNR} < 0.5$ dB.

---

## 2. Visual Reconstruction Validity

To evaluate visual structural integrity, we compute the **Mean Absolute Error (MAE)** and the **Root Mean Squared Error (RMSE)** between the interpolated downsampled spectrum and the raw spectrum:

$$MAE = \frac{1}{M} \sum_{i=1}^{M} |y_{raw}^{(i)} - y_{interp}^{(i)}|$$

Where $M$ is the original number of points, and $y_{interp}^{(i)}$ is the linear interpolation of the downsampled spectrum evaluated at $\lambda^{(i)}$.

---

## 3. Computational Complexity & Efficiency

We record the **Data Compression Ratio (DCR)** alongside execution latency:
$$DCR = \frac{\text{Bytes of Raw Dataset}}{\text{Bytes of Downsampled Dataset}}$$

A DCR of **10:1** ($10\%$ retention) must be achieved while maintaining:
- Runtime downsample execution latency of **$< 15$ ms** inside Web Workers.
- Browser UI frame rate of **$60$ FPS** during interactive zooming and panning.
