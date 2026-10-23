# Draft inquiry to ISSDC / PRADAN — Chandrayaan-3 LIBS L1 wavelength axes

**Status:** draft for the authors to review and send; it has not been sent.
**To:** ISSDC/PRADAN data support (Chandrayaan-3 LIBS, `lib-v2` calibrated collection)

---

**Subject:** Chandrayaan-3 LIBS L1 (lib-v2, calibrated): two wavelength axes for the same acquisitions

Dear ISSDC/PRADAN team,

We are processing the Chandrayaan-3 LIBS Level-1 calibrated collection (`lib-v2`, labels created
2024-05-16; 301 products, 25 August–2 September 2023). We found two different wavelength axes for the
same acquisitions and would be grateful for guidance on which one to use.

1. **Parent table** (for example `ch3_lib_002_20230825T104221_00_l1.csv`): 2,094 wavelength columns from
   164.35 to 878.26 nm. The axis is identical in all 301 products.
2. **Single-shot tables** (for example `ch3_lib_002_20230825T104221_00_l1_1_2.csv`; 1,281 files, two
   columns Wavelength / Response count, 2,094 rows): the wavelength column runs from 153.21 to 873.30 nm.
   It is identical in all 1,281 files.

In every one of the 1,281 single-shot files, the response counts equal those of a parent-table row
exactly; the file-name suffix `_a_b` identifies the row: `a` = 0 background / 1 plasma, `b` = row number.
Only the wavelength assigned to each channel differs. The single-shot axis minus the parent axis is
between −11.14 and −4.96 nm, depending on channel:

| Wavelength (parent axis) | Single-shot − parent |
|---|---|
| ≈ 220 nm | −8.89 nm |
| 589 nm | −7.48 nm |
| ≈ 800 nm | −8.05 nm |

All data files match the MD5 checksums, sizes and record counts declared in their PDS4 labels.
(91 label checksums are written without leading zeros; all match once left-padded to 32 hex digits.)

Our questions:

1. Which wavelength axis is the calibrated one for these products — the parent-table columns, the
   single-shot Wavelength column, or neither?
2. If the two axes come from different calibration versions, is there documentation describing the
   calibration (reference lines, date, version) and the expected wavelength accuracy?
3. Is a revised collection planned, or is there an erratum we should cite?
4. Separately: is printing label MD5 values without leading zeros intended?

The comparison script and per-file results are available on request. Thank you for making these data
public.

Kind regards,
[authors, affiliation, contact]

---

*Source of every number:* `revision_v2/outputs/archive_audit/subfiles.csv` (columns `sub_wl_min`,
`sub_wl_max`, `dw_min`, `dw_max`, `dw_at_220`, `dw_at_589`, `dw_at_800`, `name_b_row_matches`) and
`summary.json`, produced by `revision_v2/audit_archive.py`.
