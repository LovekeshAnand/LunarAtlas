# Response to Reviewers — second revision (draft)

We thank both reviewers. In this revision we re-audited every reported number against the data and
code, corrected the inconsistencies we found (some in our own previous revision), and re-generated
all tables and figures from one input version and one settings file. Scripts, settings, logs and
machine-readable outputs are in `revision_v2/` of the repository. Section numbers refer to the
revised manuscript. Where a result is not significant or a limitation remains, we say so.

## Corrections we found ourselves

- **Measurement counts.** An earlier response mentioned 779 ingested measurements. That figure came from
  an older processing version that stored 132 unpaired plasma acquisitions without subtraction and 34
  background frames as cleaned records (613 + 132 + 34). The archive contains 745 plasma acquisitions,
  of which 613 are paired; only these are stored as cleaned (§4.1, Table 3).
- **Downsampling comparison.** LTTB+Peaks received the detected peaks as preserved targets, so its 100 %
  peak retention holds by construction, and it used 147–167 points while the other methods used 130.
  We now report equal-budget and matched-size comparisons: at 130 points its RMSE exceeds plain LTTB
  by 9.0–22.0 a.u. (11.7–31.0 %), not 4.9–13.0 % (§4.3, Table 6, Fig. 4). The algorithm description now
  matches the implementation (it preserves caller-specified channels and does not detect peaks; the
  budget is ⌊2094·2⁻ᵏ⌋), and we state that the web viewer downsamples in the browser. The variant
  that fits LTTB+Peaks into 130 points is an evaluation construct, not production code, and §2.2.1
  now defines it. The web viewer's own configuration was evaluated by running its TypeScript
  function: all 2,094 channels, a 209-point threshold and its built-in 32-line list. It keeps
  55.9–71.4 % of detected peaks (50.8–69.0 % for LTTB alone). For the same inputs, the TypeScript
  and Python implementations returned identical channels in all 24 tested configurations (Table 6).
- **Noise argument.** The comparison with √2 assumed equal input variances. With the measured variances,
  independence predicts 1.37; the observed 1.31 is reproduced by the sample covariance, which is an
  algebraic identity rather than evidence. We removed the claims of correlated CCD readout and of
  independent support for correctness and report the statistics descriptively (§4.2, Table 4).
- **Ingestion code.** Re-ingestion dropped every table, including user and API-key tables; raw plasma
  rows were classified with a different rule from the cleaned rows (35 background rows with non-zero
  laser-energy readings were counted as plasma, shifting raw identifiers); and the pairing and
  clipping information was not stored. All three are fixed and covered by a database test (§2.2, §2.3).

## Reviewer 6

**R6.1 — WAN tests, concurrency.** We have not re-measured over the WAN or against the public service:
that requires load on a shared public deployment, which we have not done. The earlier WAN figures are
kept, marked as single-session values from the original campaign. New in this revision is a local
loopback sweep at concurrency 1–32, repeated in three fresh server sessions, with the cache disabled,
reporting percentiles, throughput and errors (§4.5, Table 8). We state that it does not address WAN
variability. Warm-cache conditions were not measured.

**R6.2 — False positives from wavelength-only matching.** We agree that wavelength coincidence is not
identification, and the manuscript now calls these "candidate coincidences" throughout (§2.2.2, §4.4).
- **Null model.** We re-implemented and documented it. Each draw shifts the whole reference list by
  one common offset of 2–20 nm with random sign, and p = (1+k)/(N+1), where k is the number of
  draws at or above the observed count. The worked-example spectra use 10,000 draws (seed 20261021).
  The archive-wide tests use 1,000 draws (seed 20261022). In each archive draw the same shift is
  applied to every spectrum and the per-spectrum counts are summed. The wavelength-axis comparison
  uses the first 300 archive draws. Table 7 lists N, k and p for every test.
- **Results.** Only one of three worked-example spectra exceeds chance:
  - ID 3: 0 of 10,000 draws reached the observed count, p = 0.0001.
  - ID 1: k = 3,419, p = 0.34.
  - ID 4: k = 617, p = 0.062.

  Archive-wide, coincidences do not exceed chance:
  - all 613 spectra: k = 95 of 1,000, p = 0.096;
  - the 357 with clip fraction ≤ 0.5: k = 79 of 1,000, p = 0.080.
- **Per-peak table.** It is now in the repository, with signed offsets, prominence and all references
  within 0.5 and 1.1 nm.
- **Line ratios.** We did not add a line-ratio analysis. A meaningful one needs plasma conditions and
  instrument response, which are outside the scope of this software paper. We say this explicitly
  rather than present ratios of tabulated transition probabilities as expected intensities.
- **Wavelength-scale ambiguity.** The audit found that each acquisition's single-shot file carries the
  same counts on a wavelength axis offset by 5–11 nm from the parent table. With that axis the
  archive-wide coincidence count is below the chance mean (k = 215 of 300 draws, p = 0.72). The
  parent axis gives p = 0.10 with the same 300 draws. We report this as an unresolved property of
  the archive (§4.1).

**R6.3 — Validation on one file.** We now separate archive-wide ingestion validation (all 301 products)
from the worked-example spectral metrics (one product):
- **Integrity.** All 1,582 data files match the checksum, size and record count in their PDS4 labels;
  91 label checksums are printed without leading zeros, which we document.
- **Counts.** All counts reconcile (Table 3).
- **Determinism.** Two processing runs are byte-identical.
- **Ingestion.** Ingestion into a disposable database reproduces the files exactly. Re-ingestion adds
  no rows. Every stored cleaned value equals max(0, plasma − paired background) recomputed in SQL from
  the stored raw rows (1,283,622 points, maximum difference 0).

The worked-example metrics are still from one product and are labelled as such.

**R6.3 (threshold).** The clip fraction is now defined as the share of channels whose residual is negative
*before* clamping. With that definition:
- **Flagged counts:** 372 (25 % threshold), 256 (50 %) and 157 (75 %) of 613 acquisitions are flagged
  (Fig. 3).
- **Status of the 0.5 cut-off:** it is a convention, not an optimised or physically validated value.
- **Flagging excludes nothing:** every flagged acquisition stays stored. Its clip fraction and
  paired-background row are kept in the database and the parameter files, but no API endpoint returns
  them yet (§4.2).
- **Relation to other measures:** its correlations with other signal measures are reported
  descriptively, not as evidence of scientific usability.

We removed the sentence that used an external study to support the flagged proportion.

**R6.4 — Level 2.** Not implemented. Outputs are described as L1-derived throughout. Level-2 work is
listed as future work and depends on resolving the wavelength scale.

## Reviewer 4

**R4.1 — Spectra with assigned lines marked.** Figure 5 was regenerated from the verified outputs. It
marks detected peaks and coincidences. Labels list every reference within 1.1 nm and carry a "?" where
more than one reference applies. The text states that such labels do not imply that every listed
species is present. We also report the near-misses (0.79–0.83 nm) and the strongest unexplained
feature at 282.3 nm.

**R4.2 — Spectral resolution.**
- **Sampling vs. resolution:** the 0.34 nm figure is now described as label spacing (sampling), not
  resolution.
- **FWHM:** < 1.1 nm is treated as an upper bound from the instrument description, not a measured
  constant.
- **Close references:** references closer than 1.1 nm are flagged as possibly unresolved.

**R4.3 — Physical model for background correction.** The method is measured-frame subtraction. It
assumes the background is additive and unchanged between the two acquisitions. We now report the
actual pairing intervals instead of assuming 200 ms: label timestamps have 1 s resolution, and the
intervals are 0 s for 206 acquisitions, 1 s for 264 and 2–13 s for 143. We also state that clamping
biases low-signal spectra. Optional ALS/Savitzky–Golay filters are described separately as display-only.

**R4.4 — Spectra before and after background correction.** Figure 2 (regenerated) shows the raw plasma
acquisition, the paired background (with row numbers and timestamps) and the cleaned spectrum.

## Not done in this revision

- **Public database not updated:** the public demonstration database has not yet been re-ingested with
  the corrected pipeline. The API example (Listing 1) was checked against it. For the identifier used
  there, the served values equal the revision output on all 2,094 channels.
- **Quality fields not in API responses:** the clip fraction and pairing fields are stored but not
  yet exposed.
- **No new archived release:** no new archived code release has been made yet; the code-metadata table
  says so.
- **Measurements not repeated:** WAN, production and warm-cache latency.
