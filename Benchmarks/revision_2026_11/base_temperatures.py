"""Base temperature per calibrated product, from the archive's operational table
(lib-v2/miscellaneous/ch3_lib_pds_functional_operational_table.pdf; Data User Manual §4.2.2 step 1).
A product belongs to the operation whose start file has the same timestamp and the largest start index <= its own.
usage: python -P base_temperatures.py <ch3_libs/lib-v2> <out.csv>
"""
import re, sys
from pathlib import Path
import fitz, pandas as pd

B = Path(sys.argv[1])
num = lambda c: re.fullmatch(r"-?\d+(\.\d+)?", (c or "").strip())
ops = []
for pg in fitz.open(B / "miscellaneous" / "ch3_lib_pds_functional_operational_table.pdf"):
    for t in pg.find_tables().tables:
        for r in t.extract():
            cells = [(c or "").replace("\n", " ") for c in r]
            fi = next((i for i, c in enumerate(cells) if "ch3 lib" in c), None)
            if fi is None:
                continue
            m = re.search(r"ch3 lib (\d+) (\d{8}T\d{6}) (\d+) l1", cells[fi])
            vals = [float(c) for c in cells[fi + 1:] if num(c)]
            opno = next((c for c in cells[:fi] if re.fullmatch(r"\d{1,2}", c.strip())), "?")
            ops.append(dict(op=opno.strip(), ts=m.group(2), start_idx=int(m.group(3)),
                            sun=vals[0] if len(vals) >= 4 else None,
                            base_temp_c=vals[1] if len(vals) >= 4 else None, n_numeric=len(vals)))
O = pd.DataFrame(ops)
# op 60: PyMuPDF returns empty sun/temp cells; the PDF text layer (pdftotext -layout) reads
# "60 13.56.30 13.57.02 ch3_lib_041_20230901T131919_03_l1 to 12.1 25.57 -0.16789 14.21029"
O.loc[(O.op == "60") & O.base_temp_c.isna(), ["sun", "base_temp_c"]] = [12.1, 25.57]
rows = []
for f in sorted((B / "data" / "calibrated").rglob("*_l1.csv")):
    m = re.search(r"(\d{8}T\d{6})_(\d+)_l1", f.name)
    c = O[(O.ts == m.group(1)) & (O.start_idx <= int(m.group(2)))]
    op = c.loc[c.start_idx.idxmax()] if len(c) else None
    rows.append(dict(product=f.stem, op=None if op is None else op.op,
                     base_temp_c=None if op is None else op.base_temp_c))
R = pd.DataFrame(rows)
R.to_csv(sys.argv[2], index=False)
print(O.to_string(index=False))
print(f"\nproducts {len(R)}; with base temperature {R.base_temp_c.notna().sum()}; "
      f"range {R.base_temp_c.min()}-{R.base_temp_c.max()} C; unmatched: {R[R.base_temp_c.isna()]['product'].tolist()}")
