# Branching-ratio feasibility screening
Parent-table axis only. A4 catalogue, grouping, member-level matching and peak
detection used unchanged. No catalogue, bin, cap, tolerance or null model altered.
NO RATIO WAS CALCULATED. No manuscript or revision_v2 file touched.

## Result
859 same-upper-level pairs were examined across the 19 species of the A4 catalogue.
ZERO pairs cleared every feasibility gate. No branching-ratio check is available
on this product.

## Gates applied, in the order specified
  G1  both lines share the same upper level Ek (matched to 0.001 cm-1)
  G2  both lines fall within 220-800 nm
  G3  both lines have a quoted Aki
  G4  separation exceeds the 1.1 nm span-limited grouping convention, so the pair
      is potentially resolvable at this instrument's sampling
  G5  a supported observed peak exists for each member line
  G6  both lines are supported in the SAME acquisition
  G7  no competing species within 1.1 nm of either matched line
  G8  neither line sits inside a blended (multi-member) group
  G9  a defensible detector-response treatment exists
  G10 optical-depth assumptions can be assessed

## Blocking census (a pair may fail several gates)
  line sits in a blended group                              1,673 instances
  no supported observed peak for one or both lines            851
  Aki missing for one or both lines                           557
  separation <= 1.1 nm, not resolvable                        249
  both lines supported, but never in the same acquisition       5
  competing species within 1.1 nm of a matched line             3
  Pairs failing exactly one gate: 7. Two gates: 17. Three or more: 835.

## Gate 9, detector response: NOT the blocker
ch3_lib_pds_cal_res.csv supplies a radiometric transfer function in
(mW/cm^2)/counts over 219.76-800.11 nm, 1,686 points, covering every candidate
line. This is a defensible response treatment and is the one requirement that is
already met. Two caveats attach to it: it was derived on the ground before flight,
so it does not account for any in-flight responsivity change, and its own
wavelength column derives from the same Annexure-I polynomial, so it inherits the
axis uncertainty documented in the calibration audit.

## Gate 10, optical depth: NOT ASSESSABLE
Self-absorption cannot be evaluated from a single set of acquisitions at one
unknown plasma condition. Assessing it would require either measurements at
materially different plasma conditions, a curve-of-growth analysis over several
lines of known relative strength, or an independent plasma diagnostic. None is
available. Every pair therefore fails G10 even where all other gates pass.

## The seven near misses
These pairs are sound on atomic physics (same upper level, both Aki quoted,
separation above the grouping convention, neither line blended) and fail only on
what the data provide:

  Al I   394.4006 / 396.1520 nm   Ek 25347.756   sep 1.751 nm   no supported peak for one line
  Ca I   610.2720 / 612.2220 nm   Ek 31539.495   sep 1.950 nm   no supported peak for one line
  Ca I   610.2720 / 616.2170 nm   Ek 31539.495   sep 5.945 nm   no supported peak for one line
  Ca I   612.2220 / 616.2170 nm   Ek 31539.495   sep 3.995 nm   no supported peak for one line
  Si I   288.1579 / 390.5523 nm   Ek 40991.884   sep 102.39 nm  no supported peak for one line
  Si II  595.7560 / 597.8930 nm   Ek 97972.090   sep 2.137 nm   no supported peak for one line
  O I    297.2290 / 557.7340 nm   Ek 33792.583   sep 260.51 nm  both supported, DIFFERENT acquisitions

The O I pair is the closest to usable: both lines are supported, both unblended,
both resolvable, both with Aki, response available. It fails only because the
support occurs in different acquisitions, so no single spectrum carries both.

Three further pairs have both lines supported within one acquisition (ID 4) but are
blocked by blending or interference: Mg II 317.578 / 681.927 (both blended, and the
matched line is contested), Si I 244.336 / 288.158 (244.336 blended, contested), and
Ti I 721.335 / 725.375 (no Aki, both blended, contested).

## Recommendation
No ratio check is scientifically defensible on this product, and none should be
attempted or reported. The limitation is not the method and not the detector
response; it is that this instrument's 1.1 nm span-limited grouping convention
places most same-upper-level partners inside blended groups, and that the three
usable acquisitions do not carry supported peaks for both members of any clean pair
simultaneously. Forcing a ratio from any pair above would require relaxing a rule
already fixed before spectral scoring, which guardrail G2 forbids.

## What would be required
  1. A spectrum in which both members of one clean pair are detected above the
     3 sigma prominence criterion simultaneously. The O I 297.229 / 557.734 pair is
     the specific target; extending the screening across the other 300 archive
     products would establish whether any acquisition satisfies this.
  2. A means of assessing optical depth, which at minimum means acquisitions at
     materially different plasma conditions or a curve-of-growth over several lines.
  3. An in-flight or post-flight check on detector responsivity, since the supplied
     transfer function is pre-flight only.
  4. Resolution of the wavelength-axis uncertainty documented in the calibration
     audit, because a 4-8 nm bound in the 300-500 nm region makes line
     identification for ratio purposes insecure in exactly the region where several
     candidate pairs sit.
  Items 1 and 2 are the binding constraints. Item 1 is testable with data already
  in the archive; item 2 is not.
