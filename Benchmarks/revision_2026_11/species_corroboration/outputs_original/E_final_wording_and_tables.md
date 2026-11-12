# Final package: test summary, corrected wording, figures and tables
Status: for author review. No manuscript file and no revision_v2 file has been changed.
No archive-wide run has been performed. Worked example only:
ch3_lib_002_20230825T104221_00_l1, measurement IDs 1, 3, 4 (ID 2 excluded, clip 0.77).

Applied wording rules: "constructed under pre-specified rules before spectral scoring"
(never "pre-registered"); "conservative span-limited grouping convention" (never
"resolution upper bound"); "independently corroborated within the archive" (never
"independently validated"); "no species-level assignment was statistically supported
in the evaluated acquisitions" (never "no elements were detected").

================================================================================
## 1. Summary of every test performed

| # | Test | Question | Result | Verdict |
|---|------|----------|--------|---------|
| 1 | PDS4 label and documentation audit | Which axis does each product declare? Air or vacuum? Stated accuracy? | Parent header carries no unit and sits in an opaque Header object; the subfile label declares a Wavelength field; no accuracy and no air/vacuum convention stated in SIS, user manual, intensity-calibration note or payload note | Inconclusive from labels alone |
| 2 | Annexure-I polynomial vs parent L1 header | Does the header reproduce the documented dispersion solution? | Max abs residual 0.0050 nm over all 2,094 columns, equal to the CSV rounding half-step | Parent header matches the documented solution |
| 3 | Radiometric transfer-function table vs Annexure-I | Does a second archive product agree? (pixels 147-1832) | Max abs residual 0.00050 nm, equal to that file's own rounding | Internal corroboration within the archive; NOT external validation |
| 4 | Single-shot subfile axis characterisation | Is it a shift or reparameterisation of the parent axis? | Departs by 4.96-11.14 nm; best integer pixel offset leaves 2.04 nm; best cubic in pixel index leaves 1.21 nm; offset shape does not match the working-distance term | Undocumented and unexplained; outlier among archive products |
| 5 | Application Note-2 marker test | Do peaks reach the five reference markers within +/-0.17 nm after temperature and fitted working-distance correction? | Best RMS 0.87 nm; 1 of 5 markers inside tolerance; implied working distance 184.7 mm, outside the 205 +/- 10 mm specification | Marker test does not close; residual error beyond the two documented corrections |
| 6 | Uncertainty budget from the archive's own equations | What bound applies to an observed peak wavelength? | 300-500 nm approx 4.5-8.4 nm; 700-800 nm approx 1.0-1.1 nm (see T-A) | Exceeds the +/-0.5 nm matching tolerance except near 700-800 nm |
| 7 | Pilot species test, 27-line list | Species-level support under the original reference list | 33 species-acquisition tests; smallest uncorrected p 0.0161 (Mg I, ID 4); none significant after global Holm | No species-level support |
| 8 | Expanded species test, 471 groups, 19 species | Species-level support under the expanded catalogue | 57 species-acquisition tests; smallest uncorrected p 0.0256 (O I, ID 3); all 57 adjusted p-values equal 1.000 | No species-level support |
| 9 | Competing-species assessment | How many supported features are uniquely attributable? | 186 of 210 supported features (89 per cent) have a line of a different species within 1.1 nm; 8 of 19 species have no uncontested feature in any acquisition | Attribution largely ambiguous at this resolution |
| 10 | Recurrence across acquisitions | Do supported groups recur across IDs 1, 3 and 4? | 41 of 167 distinct supported groups recur in two or more; 2 recur in all three. BUT 17 of the 41 match peaks separated by more than one detector channel between acquisitions (see section 4) | Limited repeatable structure, and weaker than the raw count suggests |
| 11 | Single-shot axis sensitivity arm | Are species conclusions stable against the axis ambiguity? | 57 tests; none significant; the leading species change entirely (Cr I, Mn I, H I rather than O I, Mg I, Fe I) | Species conclusions are not axis-stable |
| 12 | Catalogue QA and unit tests | Does the catalogue obey its own construction rules? | 471 groups, max span 1.0993 nm, zero violations; 27,656 exported = 2,261 usable + 25,395 excluded; 29 unit tests pass | Catalogue internally consistent |

================================================================================
## 2. The six distinctions, stated separately

1. INTERNAL CORROBORATION OF THE PARENT AXIS. The L1 parent-table axis reproduces
   the Annexure-I dispersion polynomial to 0.0050 nm, and a second archive product
   generated for radiometric calibration agrees with that polynomial to 0.00050 nm
   over pixels 147-1832. The two products are mutually consistent.
2. ABSENCE OF EXTERNAL WAVELENGTH VALIDATION. Both products derive from the same
   ground calibration, so their agreement demonstrates internal consistency of the
   archive's pipeline and cannot detect an error common to both. No wavelength
   standard, calibration-target spectrum or accuracy statement is distributed with
   the archive. The axis is therefore corroborated, not validated.
3. UNAPPLIED ARCHIVE-PRESCRIBED CORRECTIONS. The archive prescribes a base-
   temperature pixel shift (Annexure-II) and a working-distance shift (Application
   Note-2) before elemental analysis. Neither is applied in the L1 product, and the
   working distance was never measured in flight.
4. WAVELENGTH-UNCERTAINTY BOUNDS. Derived from the archive's own equations and
   specifications; these are bounds, not a measured error distribution, and must
   not be combined in quadrature as independent random errors.
5. SPECIES-LEVEL STATISTICAL NONSUPPORT. No species-acquisition test remained
   significant after global Holm correction over the full family of 57 tests; all
   57 adjusted p-values equal 1.000, and the smallest uncorrected p-value is 0.0256.
6. COMPETITOR CONTAMINATION. Independent of any significance test, 89 per cent of
   supported features admit at least one alternative species assignment within
   1.1 nm.

================================================================================
## 3. Corrected manuscript wording

### 3.1 Abstract sentence
Wavelength-coincidence annotation is provided for exploration only and is not
elemental identification. A species-level corroboration analysis against a
reference catalogue of 471 independent line groups across 19 species, constructed
under pre-specified rules before spectral scoring, found that no species-level
assignment was statistically supported in the evaluated acquisitions.

### 3.2 Methods paragraph
Wavelength annotation uses the L1 parent-table axis, which reproduces the
spectrometric calibration polynomial of Annexure-I of the archive user manual to
0.0050 nm and agrees to 0.00050 nm with the wavelength column of the radiometric
transfer-function table supplied in the archive's miscellaneous collection over
pixels 147-1832. We describe this as corroboration internal to the archive rather
than validation: both products derive from the same ground calibration, and no
external wavelength standard or calibration-target spectrum is distributed with the
archive. The single-shot subfile axis differs from both by 4.96-11.14 nm,
corresponds to no documented transformation, and is neither a pixel shift nor any
cubic reparameterisation of the parent solution; we therefore adopt the parent axis
throughout and report the subfile axis only as a sensitivity arm. We note an
unresolved inconsistency in the archive documentation: the file-layout figure of the
user manual shows an L1 payload header spanning 153.21-873.30 nm, matching the
subfile rather than the parent axis.

Two corrections the archive prescribes before elemental analysis are not applied in
the L1 product: a base-temperature pixel shift (Annexure-II) and a working-distance
shift (Application Note-2). For the worked example the temperature term is
0.77-0.95 nm, and the working-distance term reaches 0.75 nm per millimetre near
417 nm against an instrument-to-surface distance specified only as 205 +/- 10 mm
with no in-flight measurement. Fitting the working distance to the five reference
markers of Application Note-2 does not converge within the archive's own +/-0.17 nm
criterion (best RMS 0.87 nm, one of five markers inside tolerance, implied working
distance 184.7 mm). We therefore report wavelength uncertainty as bounds rather than
as a measured error distribution: approximately 1.0-4.6 nm below 300 nm, 4.5-8.4 nm
between 300 and 500 nm, and approximately 1.0-1.1 nm between 700 and 800 nm. In the
300-500 nm region this exceeds the +/-0.5 nm matching tolerance by an order of
magnitude.

Species-level corroboration was evaluated against a reference catalogue built from
NIST ASD air-wavelength exports for 19 species, including competitor species not
previously annotated, and constructed under pre-specified rules before spectral
scoring. Lines were grouped within species by a greedy span-limited rule bounded at
1.1 nm, a conservative span-limited grouping convention adopted so that an
unresolved blend contributes one unit of evidence rather than several; groups were
capped at five per 100 nm bin per species under a fixed priority order of relative
intensity, transition probability, wavelength uncertainty and representative
wavelength. Matching is member-level at +/-0.5 nm, with one peak supporting at most
one group per species. Each species was tested against a rigid random shift of its
own grouped pattern (|s| ~ U(2,20) nm, random sign, 10,000 draws) and the resulting
p-values corrected by the Holm procedure over the full family of 57 species-by-
acquisition tests. NIST relative intensity was used only as a catalogue-ranking
input and is not treated as a prediction of lunar LIBS line brightness.

### 3.3 Results sentence
No species-acquisition test remained significant after global Holm correction; the
smallest adjusted p-value was 1.000 and the smallest uncorrected p-value was 0.0256
(O I, measurement ID 3). Of 210 supported line groups, 186 (89 per cent) admit at
least one alternative species assignment within 1.1 nm, and eight of the nineteen
species tested have no uncontested supported feature in any acquisition. On the
single-shot axis the leading species change entirely and no test is significant,
indicating that species-level conclusions are not stable against the archive's
wavelength-axis ambiguity.

### 3.4 Conclusions sentence
No species-level assignment was statistically supported in the evaluated
acquisitions. The parent-table wavelength axis is independently corroborated within
the archive but has not been validated against any external standard, and two
corrections the archive prescribes before elemental analysis are absent from the L1
product, leaving wavelength uncertainty bounds that exceed the matching tolerance
over most of the band.

### 3.5 Reviewer response
We thank the reviewer for the observation that wavelength proximity alone cannot
establish elemental identity. We have implemented a species-level corroboration
analysis and report its outcome, which is negative.

On calibration, we located a second archive product, the radiometric transfer-
function table, whose wavelength column agrees with the documented dispersion
polynomial to 0.00050 nm, and we now cite that polynomial as the stated basis of the
parent-table axis. We describe this as corroboration internal to the archive, not
validation: both products derive from the same ground calibration and no external
standard is distributed. We disclose that the single-shot subfile axis disagrees by
4.96-11.14 nm and matches no documented transformation, and that the archive's own
documentation is internally inconsistent on this point. We further disclose that two
corrections the archive requires before elemental analysis, a base-temperature shift
and a working-distance shift, are absent from the L1 product; that the working
distance was never measured in flight; and that the resulting wavelength uncertainty
bound is of order 4.5-8.4 nm between 300 and 500 nm. This exceeds the matching
tolerance and is reported as a bound, not a measured error.

On species corroboration, we expanded the reference set from 27 lines to a catalogue
of 471 independent line groups across 19 species, constructed under pre-specified
rules before spectral scoring, adding competitor species (Cr, Mn, K and singly
ionised Fe, Si and Ti) so that alternative assignments can be detected rather than
assumed away. Unresolved transitions are grouped under a conservative 1.1 nm
span-limited convention and count once. Each species was tested against a rigid
shift of its own pattern, with Holm correction across all 57 species-by-acquisition
tests.

No species-acquisition test remained significant after global Holm correction; the
smallest adjusted p-value was 1.000 and the smallest uncorrected p-value was 0.0256.
Further, 186 of 210 supported features (89 per cent) have a line of a different
species within 1.1 nm, and eight species have no uncontested feature at all. The
three species that appeared strongest under the original 27-line list weaken
substantially once the larger catalogue is applied.

We therefore make no claim of elemental identification and state that no
species-level assignment was statistically supported in the evaluated acquisitions.
The revised manuscript reports the annotation explicitly as exploratory wavelength
coincidence, states the calibration basis and its uncertainty bounds, and reports the
species-level test and its negative result. We have retained the annotation because
it remains a useful exploratory product, but we have removed any language implying
verification.

================================================================================
## 4. New caveat found while producing the figures: recurrence is weaker than its count

F-B shows that a group counted as "recurring" is not necessarily the same observed
feature in each acquisition. The matched peak is free to move anywhere inside the
group window plus tolerance.

For the two groups recurring in all three acquisitions:
  Fe II 754.87 nm   matched peaks 754.63, 755.26, 754.94 nm   spread 0.63 nm
  O I   777.42 nm   matched peaks 777.05, 777.67, 777.05 nm   spread 0.62 nm
In both cases the ID 3 peak is roughly two detector channels away from the ID 1 and
ID 4 peaks, and in both cases a different member line was matched.

Across all 41 recurring groups, 17 have a peak spread exceeding 0.35 nm, which is
one detector channel. Recurrence as defined therefore means "the group window was
occupied in more than one acquisition", not "an identical feature reappeared".
T-C now carries peak_nm_min, peak_nm_max and peak_spread_nm so this is visible, and
the manuscript should state the definition explicitly rather than let "recurring"
imply positional agreement.

================================================================================
## 5. Figures and tables produced
  outputs/figures/F-A_calibration_cross_check.png
  outputs/figures/F-B_focused_panels_FeII_OI.png
  outputs/tables/T-A_uncertainty_budget.csv
  outputs/tables/T-B_fingerprint_summary.csv
  outputs/tables/T-C_recurrence.csv        (167 rows, 41 recurring)
  outputs/tables/T-D_test_summary.csv      (section 1 above)
