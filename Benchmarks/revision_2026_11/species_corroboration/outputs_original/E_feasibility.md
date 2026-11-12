# Species-level corroboration: results summary
Catalogue: A4 (tag expanded_v4_A4rep), 471 groups, 19 species, 2,261 usable lines.
Spectra: ch3_lib_002_20230825T104221_00_l1, measurement IDs 1, 3, 4 (ID 2 excluded,
clip fraction 0.77). Primary axis: parent table (Annexure-I). Peak detection, noise
and tolerance imported unchanged from revision_v2/analysis.py.
Null: species-specific rigid shift, |s| ~ U(2,20) nm, random sign, 10,000 draws,
seed 20261021. Correction: global Holm over all 57 species x acquisition tests.

## Headline
0 of 57 tests are significant after global Holm correction. The smallest raw
p-value is 0.0256 (O I, ID 3); the smallest Holm-adjusted p-value is 1.000.
No species-level assignment in this product is supported by the expanded test.

186 of 210 supported features (89%) have at least one line of a DIFFERENT species
within 1.1 nm. With a realistic competitor set in the catalogue, almost no feature
is uniquely attributable to one species.

## Relative to the 27-line pilot (33 common tests)
stronger 24, weaker 6, unchanged 3. All three pilot leaders weaken:
  Mg I  ID 4  p 0.0161 -> 0.2727
  Fe I  ID 3  p 0.0301 -> 0.1753
  Ca II ID 3  p 0.0442 -> 0.2759
O I strengthens: ID 3 p 0.0872 -> 0.0256, ID 4 -> 0.0492.
Neither the pilot (0/33) nor the expanded run (0/57) produces a significant result
after global Holm.

Caveat on comparability: five of the six pilot Fe I lines (274.95, 373.49, 385.99,
438.36, 495.76) fall outside the A4 catalogue, excluded by the stratified cap.
Only Fe I 404.58 is shared. The Fe I arm is therefore NOT a like-for-like
pilot-to-expanded comparison. 19 of the 24 in-range pilot lines are retained.

## Recurrence across IDs 1, 3, 4
41 of 167 distinct supported groups recur in >= 2 acquisitions; 126 appear once.
Two recur in all three: Fe II 754.87 nm (uncontested) and O I 777.42 nm (contested).

## Sensitivity arm: single-shot axis
0 of 57 significant after Holm. The leading species change completely
(Cr I, Mn I, H I instead of O I, Mg I, Fe I), confirming that species-level
conclusions are not stable against the archive's wavelength-axis ambiguity.
This arm is a sensitivity check only; no manuscript conclusion rests on it.

## What may NOT be concluded from this
- That any element is confirmed, or identified, in this product.
- That false positives have been eliminated.
- That a species is absent. A non-significant result is not evidence of absence,
  particularly for species with few groups in range (H I has 9).
- Anything about abundance. No line-ratio or synthetic-spectrum work was done.
