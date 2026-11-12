# Species corroboration (co-author analysis, ported)

Competitor-aware species test and branching-ratio feasibility screen for the worked example
(IDs 1, 3, 4), written by Dua Saeed. Rules: `RULES.md`. Ported to this repository on 2026-11-12:
- `code/analysis.py` replaces the removed `revision_v2/analysis.py` (settings and peak detection verbatim);
- NIST lists are read from `datasets/nist_asd_lines/` (identical to the original `reference/nist_raw/`);
- `outputs_original/` holds the co-author's outputs for comparison.

Run from `code/` (plain `python`, not `-P`, so the local `analysis.py` is found):

    python test_build_reference.py                      # 29 unit tests
    python build_reference.py --pilot
    python build_reference.py --tag expanded_v4_A4rep  # 27,656 -> 2,261 usable lines, 471 groups
    python run_species.py --tag pilot                   # 33 tests, 0 significant after Holm
    python run_species.py --tag expanded_v4_A4rep       # 57 tests, 0 significant; 186/210 contested
    CH3_LIBS_BUNDLE=<ch3_libs/lib-v2> python ratio_screen.py   # 0 usable branching-ratio pairs

Reproduction against `outputs_original/`: expanded test identical (all 57 p-values, counts, 186/210);
pilot counts identical, p within 0.006 (earlier seed/version); line groups identical in membership,
representative wavelength differs for 287 of 471 groups (tie-break only, no effect on counts).
`ratio_screen.py` as shipped examines 2,396 same-upper-level pairs (the original output lists 859,
from an earlier version); 0 pairs pass in both.
