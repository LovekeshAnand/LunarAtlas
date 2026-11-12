# Final validation package
Catalogue A5 (tag expanded_v5_A5ritz) == A4 group set exactly; scoring unaffected.
No manuscript or revision_v2 file has been changed. No archive-wide run performed.

## 1. O I 777.19 vs 777.42 - RECONCILED, not an inconsistency
They are different quantities reported by different columns.

  group_id            O I#23
  members (observed)  777.1940, 777.4170, 777.5390 nm   (the O I 777 nm triplet)
  Ritz                777.1944, 777.4166, 777.5388 nm
  NIST intensity      870, 810, 750 ; Aki 3.69e7 for all three ; accuracy grade A
  Ei / Ek             73768.200 -> 86631.454 / 86627.778 / 86625.757 cm-1
  span                0.3450 nm  (well inside the 1.1 nm span-limited grouping convention)
  group_nm            777.4170 nm  = REPRESENTATIVE wavelength (median of members)
  777.19              = matched_ref_nm, the single MEMBER line a given peak fell nearest to

Matches, parent axis:
  ID 1   peak 777.05   nearest member 777.194   offset -0.144 nm   competitors none
  ID 3   peak 777.67   nearest member 777.539   offset +0.131 nm   competitor Mg II 778.65
  ID 4   peak 777.05   nearest member 777.194   offset -0.144 nm   competitors none

Notes. (a) The three members share one upper-level multiplet and differ by 0.345 nm,
far below the instrument resolution; counting them once is exactly the behaviour the
grouping rule exists for. The pilot counted only 777.19 and so tested one line of
three. (b) The matched member differs between acquisitions (777.194 in IDs 1 and 4,
777.539 in ID 3) because matching is member-level (A4.4); this is expected, not an
error. (c) The group is uncontested in IDs 1 and 4 and contested in ID 3 only, which
is why the recurrence table flags ever_contested = True.

## 2. Status of the calibration claim - CORRECTED WORDING
The parent axis is INDEPENDENTLY CORROBORATED WITHIN THE ARCHIVE. It is NOT
independently corroborated within the archive.

What ch3_lib_pds_cal_res.csv DOES establish:
  - A second archive product, generated for radiometric calibration with a
    deuterium-halogen source, carries a wavelength column over pixels 147-1832 that
    agrees with the Annexure-I dispersion polynomial to <= 0.0005 nm (its rounding).
  - The two products are therefore mutually consistent, so the parent L1 header is
    not a transcription error or a one-off, and the single-shot subfile axis
    (disagreeing by 7.47-8.90 nm) is the outlier among archive products.

What it does NOT establish:
  - It does not measure wavelength. Its own axis was almost certainly produced BY
    the same Annexure-I polynomial, so the agreement demonstrates internal
    consistency of the archive's pipeline, NOT accuracy against a physical standard.
  - It carries no independent wavelength standard, no calibration-target spectrum,
    and no accuracy statement.
  - It cannot detect a systematic error common to both products, which is precisely
    what an unapplied temperature or working-distance shift would be.

External validation would require a measured spectrum of a known emission standard
through the flight instrument, or published Chandrayaan-3 LIBS spectra with stated
wavelength solutions. Neither is in the archive. Mourlin et al. (EPSC-DPS 2025)
report discrepancies up to 8 nm against their own calibration, which is consistent
in magnitude with the parent-vs-subfile difference but is not an external standard.

## 3. Final uncertainty budget (parent axis, per observed peak)
These are BOUNDS derived from the archive's own equations and specifications.
They are NOT a measured error distribution: no term here has been verified against
a wavelength standard, and no covariance between terms is known. They must not be
combined in quadrature as if independent random errors.

  (a) dispersion-solution internal consistency        <= 0.005 nm, all wavelengths
      (parent header vs Annexure-I vs radiometric table)
  (b) air/vacuum convention unknown                    0.075 nm @250 -> 0.220 nm @800
  (c) temperature correction, Annexure-II, UNAPPLIED   0.77 - 0.95 nm
      worked example base temperature 8.95 C, dT = -16.05 C; sign is a blue shift
  (d) working-distance correction, App. Note-2, UNAPPLIED and D UNMEASURED
      sensitivity dlambda/dD:  ~0.11 nm/mm @250, 0.74 nm/mm @400, 0.75 nm/mm @417
                               0.62 nm/mm @500, 0.31 nm/mm @589, 0.03 nm/mm @777
      ITSD spec 205 +/- 6 mm (powders), 205 +/- 10 mm (hard surfaces)

  Combined plausible bound by region (|c| + |d| at the hard-surface spec):
      220 - 300 nm     ~1.0 - 4.6 nm
      300 - 500 nm     ~4.5 - 8.4 nm      <- worst region, peaks near 417 nm
      500 - 700 nm     ~1.6 - 7.1 nm
      700 - 800 nm     ~1.0 - 1.1 nm      <- best region, WD term nearly vanishes

  Consequence: in 300-500 nm the plausible wavelength uncertainty is an order of
  magnitude larger than the +/-0.5 nm matching tolerance. The 700-800 nm region is
  the only part of the band where the tolerance is comparable to the uncertainty.
  The marker test of Application Note-2 does not close on this product (best RMS
  0.87 nm, 1 of 5 markers inside +/-0.17 nm, implied WD 184.7 mm, outside spec),
  which indicates residual error beyond (c) and (d).

## 4. Final fingerprint classification (parent axis, 19 species)
Label rule: "multi-line-supported" is NEVER used standalone where every supported
feature is contested.

  multi-line-supported with unresolved interference   (>=2 distinct supported
  groups, >=1 of them uncontested in >=1 acquisition):
      Al I, Cr I, Fe II, Mg I, Mg II, Na I, O I, Si I, Si II, Ti I, Ti II   (11)

  multi-line-supported, ALL features contested  (>=2 distinct supported groups,
  zero uncontested in any acquisition):
      Ca I, Ca II, Cr II, Fe I, H I, K I, Mn I, Mn II                        (8)

  isolated candidate:     none
  unsupported / inconclusive: none

  CRITICAL QUALIFIER: no species in either class exceeds its own random-shift null
  after global Holm correction. Every Holm-adjusted p is 1.000; the smallest raw p
  is 0.0256 (O I, ID 3). These labels describe PATTERN SHAPE only. They are not
  evidence of presence, and must never be reported without the null result beside
  them.

  Only four groups are both recurring and uncontested in at least one acquisition:
      Fe II 754.87 nm - uncontested in ALL THREE acquisitions, no non-Fe II
                        reference line within 2.5 nm; members 754.3377, 754.8661,
                        755.3824 nm; offsets -0.236, -0.122, +0.074 nm
      O I   777.42 nm - uncontested in IDs 1 and 4, contested in ID 3
      Si II 566.51 nm - IDs 3 and 4
      Ti II 225.33 nm - IDs 3 and 4
  Fe II as a species still scores p_raw = 0.259: one clean feature, no pattern.

## 5. Figures and tables required (none yet produced)
  F-A  calibration cross-check. Residual of the parent L1 header and of the
       radiometric table against the Annexure-I polynomial, in pm, vs pixel;
       second panel, subfile-axis residual vs pixel in nm. Makes the 3-to-1
       outcome visible in one frame.
  T-A  uncertainty budget, section 3 above, as a table with a bounds caveat.
  T-B  fingerprint summary: species, groups, distinct supported, uncontested,
       recurring, best raw p, Holm p, label.
  F-B  focused spectral panels for Fe II 754.87 and O I 777.42: cleaned spectrum,
       3-sigma threshold, group member positions, matched peak, competitor lines
       within 1.1 nm, one row per acquisition.
  T-C  recurrence table, 41 recurring groups, with ever_contested.
  (Optional) F-C axis sensitivity: species leaderboard parent vs subfile axis.

## 6. Feasibility
All five required figures and tables can be produced from outputs already on disk
plus the cleaned spectra; no new computation beyond plotting is needed. The
archive-wide extension is NOT required for any statement in section 5 of the
reviewer response and has not been run.
