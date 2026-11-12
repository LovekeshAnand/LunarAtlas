"""Point 10: time gap between each paired plasma acquisition and its background (archive-wide), from the
'Time' column of the raw parent tables (pairing = most recent preceding background row), plus the PRR column.

usage: pair_gaps.py <datasets/uploads>
"""
import sys
from collections import Counter
from pathlib import Path
import pandas as pd

gaps, prr, adjacent, n = Counter(), Counter(), 0, 0
for f in sorted(Path(sys.argv[1]).rglob("*_l1.csv")):
    df = pd.read_csv(f)
    t = pd.to_datetime(df["Time"])
    last = None
    for i, r in df.iterrows():
        fl = (int(r["Force Reset Status"]), int(r["Laser Fire Status"]))
        if fl == (1, 0):
            last = i
        elif fl == (0, 1) and last is not None:
            n += 1
            gaps[int((t[i] - t[last]).total_seconds())] += 1
            adjacent += (i - last == 1)
            prr[r["PRR"]] += 1
print("paired plasma acquisitions:", n)
print("timestamp resolution: values like", df["Time"].iloc[0])
print("gap (s) -> count:", dict(sorted(gaps.items())))
print(f"gap 0 s: {gaps[0]}, 1 s: {gaps[1]}, 2+ s: {sum(v for k, v in gaps.items() if k >= 2)}, max: {max(gaps)} s")
print("paired with the immediately preceding row:", adjacent)
print("PRR (Hz) of paired plasma rows:", dict(prr))
