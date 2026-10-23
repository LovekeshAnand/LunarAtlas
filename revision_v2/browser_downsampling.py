#!/usr/bin/env python3
"""
Web-viewer downsampling as actually configured, evaluated with the viewer's own code.

  implementation : TypeScript lttb() from core/client/src/workers/downsampleWorker.ts (run in Node)
  reference list : ELEMENT_PEAKS in core/client/src/utils/spectralUtils.ts (33 lines, element = All)
  input range    : viewer default 164.35-878.26 nm (2,094 channels) and a 220-800 nm viewport
  budget         : useDownsampling.ts, ratio 0.1 -> threshold = min(max(3, floor(2094*0.1)), n) = 209
                   (plus a k=4 budget, 130, for comparison with the server-side table; not a viewer setting)

Also checks that the Python server implementation returns the same channels for the same inputs.
Output: outputs/analysis/C_browser_viewer.csv, C_browser_viewer_targets.json
"""
import json
import math
import subprocess

import numpy as np
import pandas as pd

from analysis import OUT, S, V2, cleaned, detect, prod, score, wr

VIEWER_RATIO = 0.1


def viewer_threshold(n, ratio=VIEWER_RATIO):
    t = min(max(3, math.floor(2094 * ratio)), n)
    return n if t >= n or ratio >= 0.99 else t


def main():
    cl = cleaned(S["worked_obs"], "20230825")
    jobs, meta = [], {}
    for mid in S["eval_ids"]:
        g = cl[mid]
        wl_full, y_full = g.Wavelength_nm.to_numpy(), g.Cleaned_Intensity.to_numpy()
        pk_full, _, _ = detect(wl_full, y_full)
        for rng, (lo, hi) in {"viewer_default_164-878": (164.35, 878.26), "viewport_220-800": (220.0, 800.0)}.items():
            c = (wl_full >= lo) & (wl_full <= hi)
            wl, y = wl_full[c], y_full[c]
            pk = np.searchsorted(wl, wl_full[pk_full])
            for budget, t in [("viewer ratio 0.1", viewer_threshold(len(wl))), ("k=4 (comparison only)", 130)]:
                for tg in ["none", "viewer"]:
                    key = f"{mid}|{rng}|{budget}|{tg}"
                    jobs.append({"key": key, "wavelength": wl.tolist(), "intensity": y.tolist(), "threshold": t,
                                 "targets": None if tg == "none" else "viewer"})
                    meta[key] = (mid, rng, wl, y, pk, budget, t, tg)

    out = json.loads(subprocess.run(["node", str(V2 / "browser_lttb.mjs")], input=json.dumps(jobs),
                                    capture_output=True, text=True, check=True).stdout)
    targets = np.array(out["viewer_targets"])
    rows = []
    for key, idx in out["results"].items():
        mid, rng, wl, y, pk, budget, t, tg = meta[key]
        idx = np.array(idx)
        in_rng = targets[(targets >= wl[0]) & (targets <= wl[-1])]
        matched = pk[(np.abs(wl[pk][:, None] - in_rng[None, :]) < S["match_tol_nm"]).any(axis=1)]
        py = prod(wl, y, 0, targets=None if tg == "none" else targets, threshold=t)
        rows.append({"measurement_id": mid, "input_range": rng, "n_channels": len(wl), "budget": budget,
                     "threshold": t, "targets": "none" if tg == "none" else "viewer 33-line list",
                     "targets_in_range": len(in_rng), "n_peaks": len(pk),
                     **score(wl, y, idx, pk, matched),
                     "python_server_identical": bool(np.array_equal(np.unique(idx), np.unique(py)))})
    wr(pd.DataFrame(rows), "C_browser_viewer.csv")
    (OUT / "C_browser_viewer_targets.json").write_text(json.dumps(
        {"source": "core/client/src/utils/spectralUtils.ts ELEMENT_PEAKS", "n": len(targets),
         "wavelengths_nm": targets.tolist(), "viewer_ratio": VIEWER_RATIO}, indent=2))
    print(pd.DataFrame(rows).to_string())


if __name__ == "__main__":
    main()
