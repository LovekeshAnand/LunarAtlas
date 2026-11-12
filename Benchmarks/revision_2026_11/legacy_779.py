"""Break down the 779 'cleaned' records of the legacy (v1.0.1) output by what they actually are, using the raw
archive: paired plasma, unpaired plasma, or other rows.

usage: legacy_779.py <datasets/processed_backup_20261020> <datasets/uploads>
"""
import sys
from collections import Counter
from pathlib import Path
import pandas as pd

legacy, raw = Path(sys.argv[1]), Path(sys.argv[2])
kinds = Counter()
by_product = Counter()
rawfiles = {p.stem: p for p in raw.rglob("*_l1.csv")}
for f in legacy.rglob("*_instrument_params.csv"):
    stem = f.name[:-len("_instrument_params.csv")]
    par = pd.read_csv(f)
    df = pd.read_csv(rawfiles[stem])
    flags = list(zip(df["Force Reset Status"].astype(int), df["Laser Fire Status"].astype(int)))
    n_bg = sum(fl == (1, 0) for fl in flags)
    n_pl = sum(fl == (0, 1) for fl in flags)
    kind = "background only" if n_pl == 0 else ("plasma, none paired" if all(
        not any(flags[j] == (1, 0) for j in range(i)) for i, fl in enumerate(flags) if fl == (0, 1)) else "with paired plasma")
    by_product[kind] += len(par)
    if "Background_Subtracted" in par:
        kinds[f"Background_Subtracted={bool(par.Background_Subtracted.iloc[0])}"] += 0
        for v in par.Background_Subtracted:
            kinds["subtracted" if bool(v) else "NOT subtracted"] += 1
print("legacy records:", sum(by_product.values()))
print("records by product kind:", dict(by_product))
print("records by Background_Subtracted:", {k: v for k, v in kinds.items() if v})
