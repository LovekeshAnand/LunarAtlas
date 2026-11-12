# Pre-specified rule set: species-level corroboration analysis
# LunarAtlas / Chandrayaan-3 LIBS. Status: DRAFT, awaiting author approval.
# Nothing in this file may be changed after the first analysis run.

## 0. Provenance of fixed settings
Peak detection, noise estimation and matching settings are reproduced verbatim from
revision_v2/outputs/analysis/settings.json of the submitted revision. revision_v2/ is no
longer present in the working tree, so analysis.py is REIMPLEMENTED to that recorded
specification rather than imported. Any future restoration of revision_v2 should be used
to verify equivalence.

## 1. Axes
Primary   : parent-table axis, = Annexure-I spectrometric calibration polynomial
            lambda(p) = 163.9731 + 0.38172 p - 1.48482e-5 p^2 - 2.17022e-9 p^3, p = 1..2094
            (ch3_lib_pds_data_user_manual.pdf, Annexure-I; reproduces the archived header
             to 0.005 nm, i.e. the CSV rounding).
Sensitivity: single-shot subfile axis (undocumented; 153.21-873.30 nm). Reported separately
            and labelled a sensitivity check. No manuscript conclusion rests on it.
The axis is NOT chosen on the basis of match count.

## 2. Species and ionisation stages
Neutral and singly ionised only. Doubly ionised excluded: the available spectra cannot
constrain the plasma conditions required to justify them.

Target species (carried from the current reference list):
  Fe I, Fe II, Mg I, Mg II, Si I, Si II, Al I, Al II, Ti I, Ti II,
  Ca I, Ca II, Na I, H I, O I
Competitor species (added so the competing-species check can fire; scored on equal terms):
  Cr I, Cr II, Mn I, Mn II, K I, C I, N I, S I
Every species listed is tested and reported, including those that score zero.

## 3. Wavelength range
220-800 nm (instrument stated calibrated range; cal_min/cal_max of the submitted settings).
Lines outside this range are excluded, including Ca II 849.80 / 854.21 / 866.21.

## 4. Definition of a usable reference line
A line is usable only if ALL hold:
  U1  an OBSERVED wavelength is present (Ritz-only entries excluded);
  U2  the observed wavelength lies in 220-800 nm (air);
  U3  at least one of {relative intensity, Aki} is present;
  U4  where NIST quotes a wavelength uncertainty, it is <= 0.05 nm (one seventh of a channel);
  U5  where NIST quotes an accuracy grade, it is C or better.
Lines with no quoted uncertainty or no accuracy grade are RETAINED and flagged
(no_uncertainty_quoted / no_accuracy_quoted) rather than dropped.

## 5. Deduplication
Deduplicate on (species, observed wavelength rounded to 0.001 nm). Where duplicates differ,
keep the better accuracy grade; ties broken by larger relative intensity, then by first
occurrence in the export. Every removal logged.

## 6. Grouping (unresolved lines)
Within a species, sort usable lines by wavelength and merge any two consecutive lines
separated by < 1.1 nm into one group (the instrument resolution upper bound, fwhm_upper_bound_nm).
Merging is transitive along the chain. A group's nominal wavelength is the intensity-weighted
mean of its members where intensities exist, otherwise the arithmetic mean.
A GROUP IS THE UNIT OF EVIDENCE. A group is supported at most once, by its single
best-matching peak, regardless of how many lines it contains.
Sensitivity run at 0.7 nm grouping, reported alongside.

## 7. Cap per species
At most 30 independent usable GROUPS per species (not 30 lines). Where a species yields more,
rank groups by the maximum relative intensity among their members (falling back to maximum Aki
where no intensity is quoted) and keep the strongest 30. The cap is identical for every species.
Ranking uses NIST-quoted quantities only and never the observed spectra.

## 8. Matching
|lambda_obs - lambda_ref| < 0.5 nm, strict, against any member line of a group.
Unchanged from the submitted analysis so results remain comparable.

## 9. Peak detection (reproduced from settings.json)
Cleaned spectra, parent axis. Array sliced to 220-800 nm BEFORE find_peaks, matching
analysis.py detect(). Prominence >= 3 * sigma; sigma = numpy std (ddof=0) of the cleaned
intensity over 560-580 nm; minimum separation 5 channels.
Acquisitions: IDs 1, 3, 4 of ch3_lib_002_20230825T104221_00_l1. ID 2 excluded
(clip fraction 0.77), matching eval_ids of the submitted settings.

## 10. Null model
Per species, rigid shift of that species' OWN grouped pattern. Shift s drawn as
|s| ~ U(2, 20) nm with equiprobable sign; 10,000 draws; seed 20261021. Shifted groups leaving
220-800 nm cannot match (boundary = "drop"). Statistic = number of supported groups.
Empirical p = (1 + #{null >= observed}) / (1 + draws).

## 11. Multiple testing
Holm correction across the GLOBAL family of every species x acquisition test
(all species, all of IDs 1/3/4 together), not within acquisitions. A result is called
significant only after this global correction. The sensitivity runs (0.7 nm grouping,
single-shot axis) are corrected within their own families and never pooled with the primary.

## 12. Competing species
For each supported group, every line of a DIFFERENT species within 1.1 nm of the matching peak
is recorded. A group with one or more competitors is labelled unresolved interference.

## 13. Recurrence
A group is counted as recurring if it is supported in >= 2 of the usable acquisitions.
Species-level recurrence is reported as the number of distinct recurring groups.

## 14. Guardrails
G1 Reference lines are selected by rules 4-7 alone, applied to the raw exports BEFORE any
   spectrum is read. E_reference_lines.csv and E_line_groups.csv are written and checksummed
   first; the analysis step reads them read-only.
G2 No line, grouping width, tolerance, axis or null setting is adjusted after seeing results.
G3 Every excluded line is written to E_reference_exclusions.csv with the rule that excluded it.
   Counts must reconcile: exported = usable + excluded.
G4 All species are reported, including zero scores and weakened labels.
G5 No claim of elemental identification, and no claim that false positives are eliminated.
G6 No line-ratio analysis unless a same-upper-level pair is separately verified.
G7 No synthetic-spectrum comparison without explicit author approval.
G8 The 27-line pilot results are preserved unmodified for comparison.

================================================================================
## AMENDMENT A2 - stratified wavelength cap (supersedes rule 7)
Status: adopted BEFORE any spectral scoring. Author-approved 2026-11-07.
The v1 intensity-ranked catalogue (tag expanded_g1p1) and all 27-line pilot
outputs are preserved on disk unchanged for comparison.

### A2.0 Why
Rule 7 v1 ranked groups by NIST relative intensity alone. On the dense species
this concentrated the retained groups into a narrow contiguous wavelength band
(Fe I 344-649 nm, Fe II 225-276 nm, Cr II 252-343 nm, Mn II 243-349 nm,
Ti I 391-521 nm), so those species were not tested across the instrument range.

### A2.1 Binning
220-800 nm is divided into six fixed bins:
  220-300, 300-400, 400-500, 500-600, 600-700, 700-800 nm.
A group is assigned by its representative wavelength group_nm (the
intensity-weighted mean of its member observed wavelengths, or the arithmetic
mean where no member carries an intensity). Bins are half-open [lo, hi); the
final bin is closed [700, 800]. Bin membership is never decided by any member
line individually, only by group_nm.

### A2.2 Quota
At most 5 retained groups per species per bin, hence at most 30 per species.
A bin holding fewer than 5 usable groups contributes all of them. Unused quota
is NOT reallocated to other bins, so a species may retain fewer than 30 groups.
A species with fewer than 30 usable groups overall retains all of them.

### A2.3 Ranking within a bin (strict priority order)
  a. smaller minimum member wavelength uncertainty (min_unc_nm), ascending.
     INTERPRETATION: "when available" is implemented as groups carrying a quoted
     uncertainty ranking AHEAD of groups carrying none. Groups with no quoted
     uncertainty fall through to key (b).
  b. larger maximum member transition probability (max_aki), descending.
     Groups with no Aki rank last on this key.
  c. larger maximum member NIST relative intensity (max_intensity), descending.
     Groups with no intensity rank last on this key.
  d. smaller representative Ritz wavelength (ritz_rep_nm = the minimum Ritz
     wavelength among members, falling back to the minimum observed wavelength
     where no member has a Ritz value), ascending. Final deterministic tie-break.
The sort is a single stable mergesort on these keys, so the result is
reproducible and independent of input file order.

### A2.4 Status of NIST relative intensity
Relative intensity is a CATALOGUE-RANKING INPUT ONLY. It is per-spectrum,
in arbitrary units, not comparable between species, and is NOT treated as a
prediction of lunar LIBS line brightness anywhere in this analysis.

### A2.5 Unchanged
Greedy span-limited grouping (rule 6) is retained exactly: no group may span
more than 1.1 nm. Bins, quotas and ranking keys were fixed before any spectrum
was read and are not revisable on the basis of which lines match.

================================================================================
## AMENDMENT A3 - ranking order and representative wavelength (supersedes A2.3)
Status: adopted BEFORE any spectral scoring. Author-approved 2026-11-07.
A2 catalogue (tag expanded_v2_stratified), v1 catalogue (tag expanded_g1p1) and
all 27-line pilot outputs are preserved unchanged. Nothing is overwritten.
Binning (A2.1), quota (A2.2) and span-limited grouping (rule 6) are unchanged.

### A3.1 Ranking within a bin, strict priority order
  a. larger maximum member NIST relative intensity, descending
  b. larger maximum member transition probability Aki, descending
  c. smaller minimum member wavelength uncertainty - see A3.2
  d. smaller representative wavelength (A3.4), ascending: deterministic tie-break
Uncertainty no longer ranks first. It is a measurement-quality criterion, not a
detectability criterion, and must not decide which lines are tested for presence.

### A3.2 Missing uncertainty is NEUTRAL
If both groups quote an uncertainty, the smaller wins. If only one quotes an
uncertainty, that fact does not distinguish them and comparison proceeds to the
next criterion. A missing uncertainty is neither an advantage nor a penalty.

### A3.3 Implementation and determinism
Keys (a) and (b) are total orders and are applied by a stable mergesort. Key (c)
is NOT a total order under A3.2 (a group with no uncertainty can tie with two
groups that differ from each other), so it is applied pairwise, by an explicit
comparator, only WITHIN an exact (species, bin, a, b) tie-group, over an input
already sorted by key (d). The comparator falls through to key (d) whenever (c)
cannot distinguish two groups. The result is therefore deterministic and
independent of input file order; this is asserted by a unit test.

### A3.4 Representative wavelength
ritz_rep_nm = the MEDIAN Ritz wavelength of the group's member lines. Where no
member carries a Ritz wavelength, the median observed wavelength is used instead.
Where only some members carry Ritz wavelengths, the median is taken over those
present. NOTE: this quantity is used for tie-break (d) only. Bin assignment
continues to use group_nm as defined in A2.1 (the intensity-weighted mean of
member observed wavelengths), which A3 did not revise.

### A3.5 Float guard on the span boundary
Rule 6's inclusive boundary is implemented as (candidate - group_min) >
MAX_SPAN + 1e-9. Without the guard, binary floating point makes a span of
exactly 1.1 nm compare as greater than 1.1 and wrongly open a new group
(401.1 - 400.0 evaluates to 1.1000000000000227). Found by unit test.

### A3.6 Tests
code/test_build_reference.py asserts grouping (no chaining, inclusive boundary,
span bound on random input), binning (edges, closure at 800, totality), A3
ranking (each key in priority order, neutral missing uncertainty, missing values
ranking last, permutation invariance), representative wavelength (median, even
counts, fallbacks) and NIST field parsing. All pass.

================================================================================
## AMENDMENT A4 - single representative wavelength (supersedes A2.1 / A3.4)
Status: adopted BEFORE any spectral scoring. Author-approved 2026-11-07.
A3, A2, v1 catalogues and all pilot outputs preserved unchanged.

### A4.1 Definition
representative_wavelength (column group_nm) =
    median(Ritz wavelengths of the group's member lines)
    fallback, where no member carries a Ritz wavelength:
    median(observed wavelengths of the group's member lines)
Where only some members carry Ritz wavelengths the median is taken over those
present. The intensity-weighted mean of member observed wavelengths, used for
bin assignment under A2.1, is REMOVED and no longer computed anywhere.

### A4.2 Scope
The same representative wavelength is used for bin assignment (A2.1), for
ranking tie-break d (A3.1), and for any group-level matching rule. The column
ritz_rep_nm is retained for column stability and is identical to group_nm.

### A4.3 Observed delta
Rebuild under A4 changed no group and no bin: 471 groups before and after, zero
groups added or removed, zero bin reassignments, per-species-per-bin counts
identical. Representative wavelengths moved by a median of 0.0252 nm (maximum
0.8055 nm), with no group crossing a bin edge. Maximum group span 1.0993 nm,
zero violations. All unit tests pass.

### A4.4 Matching is member-level (RESOLVED, author decision)
Group matching is member-level. The group representative wavelength is used for
catalogue binning and ranking tie-breaking only.
A peak matches a group if it lies within +/-0.5 nm of ANY MEMBER LINE of that
group. Section 8 and the pilot rule are preserved unchanged. The representative
wavelength is NOT used for spectral matching.

### A4.5 One peak supports at most one group per species (operationalisation)
Each group proposes the single peak nearest to any of its member lines, by
smallest |peak - member|. Within one species, if two groups propose the SAME
peak, only the group with the smaller |offset| is counted as supported; the
other is not. Ties in |offset| are broken by smaller representative wavelength.
Groups of DIFFERENT species are independent and may both use the same peak -
that is precisely what the competing-species report records.
This rule is applied identically to the observed data and to every null draw.
