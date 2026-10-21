#!/usr/bin/env python3
"""
Runs the (revised) stage-2 processor twice on datasets/uploads into
revision_v2/processed_run1 and processed_run2, then compares file checksums between the
runs and the cleaned values with the existing datasets/processed output.

Writes revision_v2/outputs/determinism/{summary.json, file_compare.csv, run*.log}
"""
import contextlib
import hashlib
import io
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "Pipeline"))
from step2_process_l1_data import L1DataProcessor  # noqa: E402

V2 = Path(__file__).resolve().parent
OUT = V2 / "outputs" / "determinism"
RAW = ROOT / "datasets" / "uploads"
OLD = ROOT / "datasets" / "processed"


def md5(p):
    return hashlib.md5(p.read_bytes()).hexdigest()


def run(n):
    dst = V2 / f"processed_run{n}"
    if dst.exists():
        shutil.rmtree(dst)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        proc = L1DataProcessor(RAW, dst)
        proc.run()
    (OUT / f"run{n}.log").write_text(buf.getvalue(), encoding="utf-8")
    return dst, proc.stats


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (d1, s1), (d2, s2) = run(1), run(2)
    rows = []
    files1 = sorted(p.relative_to(d1) for p in d1.rglob("*") if p.is_file())
    files2 = sorted(p.relative_to(d2) for p in d2.rglob("*") if p.is_file())
    for rel in sorted(set(files1) | set(files2)):
        a, b = d1 / rel, d2 / rel
        rows.append({"file": rel.as_posix(), "in_run1": a.exists(), "in_run2": b.exists(),
                     "identical": a.exists() and b.exists() and md5(a) == md5(b)})
    fc = pd.DataFrame(rows)
    fc.to_csv(OUT / "file_compare.csv", index=False)
    fc["kind"] = fc.file.str.extract(r"_(cleaned\.csv|instrument_params\.csv|metadata\.json|l1\.xml)$")[0]

    # Cleaned intensities vs the existing datasets/processed output (independent of column changes)
    max_abs, n_cmp, missing = 0.0, 0, []
    for new in sorted(d1.glob("calibrated/*/*/*_cleaned.csv")):
        old = OLD / new.relative_to(d1)
        if not old.exists():
            missing.append(new.name)
            continue
        a = pd.read_csv(new, usecols=["Measurement_ID", "Wavelength_nm", "Cleaned_Intensity"])
        b = pd.read_csv(old, usecols=["Measurement_ID", "Wavelength_nm", "Cleaned_Intensity"])
        if a.shape != b.shape or not (a[["Measurement_ID", "Wavelength_nm"]].values == b[["Measurement_ID", "Wavelength_nm"]].values).all():
            missing.append(new.name + " (layout differs)")
            continue
        max_abs = max(max_abs, float(np.abs(a.Cleaned_Intensity.values - b.Cleaned_Intensity.values).max()))
        n_cmp += 1

    summary = {
        "stats_run1": s1, "stats_run2": s2, "stats_equal": s1 == s2,
        "files_run1": len(files1), "files_run2": len(files2),
        "identical_by_kind": {k: f"{int(g.identical.sum())}/{len(g)}" for k, g in fc.groupby("kind")},
        "non_identical_files": fc.loc[~fc.identical, "file"].tolist()[:10],
        "non_identical_count": int((~fc.identical).sum()),
        "cleaned_vs_datasets_processed": {"files_compared": n_cmp, "max_abs_intensity_diff": max_abs,
                                          "not_compared": missing},
        "note": "metadata.json embeds processing_timestamp, so it differs between runs by design",
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
