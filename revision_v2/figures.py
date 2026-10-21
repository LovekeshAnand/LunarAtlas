#!/usr/bin/env python3
"""
Revision v2 figures. Reads only the inputs and tables written by analysis.py, so every
plotted number has a row in revision_v2/outputs/analysis/.

  fig2_downsampling        production lttb_downsample, ID 3, k = 1-4, LTTB+Peaks vs LTTB
  fig3_background_subtraction  raw plasma, paired background, cleaned (ID 3)
  fig4_nist_annotated      candidate wavelength coincidences (ID 3), zoomed windows
  fig5_clipping            archive clip-fraction histogram, threshold sensitivity, vs cleaned level
  fig6_random_shift        null distributions of the random-shift test

Output: revision_v2/figures/*.png|pdf
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

V2 = Path(__file__).resolve().parent
sys.path.insert(0, str(V2))
from analysis import NIST_CAL, OUT as TAB, RAW, S, cleaned, detect, prod, raw_pairs  # noqa: E402

FIG = V2 / "figures"
OBS, MID = S["worked_obs"], 3
C_REF, C_BG, C_CLEAN, C_CAND, C_NIST = "#64748b", "#d97706", "#1d4ed8", "#dc2626", "#0d9488"
plt.rcParams.update({"font.size": 9, "axes.titlesize": 9.5, "axes.labelsize": 9, "legend.fontsize": 8,
                     "xtick.labelsize": 8, "ytick.labelsize": 8, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.5})


def save(fig, name):
    FIG.mkdir(exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(FIG / f"{name}.{ext}", dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("saved", name)


def worked(mid):
    g = cleaned(OBS, "20230825")[mid]
    return g.Wavelength_nm.to_numpy(), g.Cleaned_Intensity.to_numpy()


def fig2():
    wl, y = worked(MID)
    c = (wl >= S["cal_min"]) & (wl <= S["cal_max"])
    wl, y = wl[c], y[c]
    pk, _, _ = detect(wl, y)
    d = pd.read_csv(TAB / "C_downsampling.csv")
    fig, axes = plt.subplots(4, 1, figsize=(7.2, 5.4), sharex=True)
    for ax, k in zip(axes, [1, 2, 3, 4]):
        lp = prod(wl, y, k, targets=wl[pk])
        lt = prod(wl, y, k)
        row = d[(d.measurement_id == MID) & (d.range == "calibrated") & (d.zoom_k == k)
                & (d.algorithm == "LTTB+Peaks") & (d.budget == "T + peaks")].iloc[0]
        assert row.n_out == len(lp)
        ax.plot(wl, y, color="#cbd5e1", lw=0.6, label="Full resolution (1,684 ch.)")
        ax.plot(wl[lp], y[lp], color=C_CLEAN, lw=0.8, label="LTTB+Peaks output")
        ax.plot(wl[pk], y[pk], "v", color=C_CAND, ms=3, label="Detected peaks (kept by construction)")
        ax.set_title(f"({'abcd'[k - 1]}) k = {k}: {len(lp)} points ({row.density_pct:.1f}%) = LTTB T = {int(row['T'])} "
                     f"∪ {len(pk)} peaks; LTTB alone keeps {len(np.intersect1d(lt, pk))}/{len(pk)} peaks",
                     loc="left", fontsize=8.5)
        ax.set_ylabel("Intensity (a.u.)")
    axes[0].legend(loc="lower left", bbox_to_anchor=(0, 1.18), frameon=False, ncol=3)
    axes[-1].set_xlabel("Wavelength (nm, L1 parent-table axis)")
    axes[-1].set_xlim(S["cal_min"], S["cal_max"])
    save(fig, "fig2_downsampling")


def fig3():
    for k, pr, br, bg_row, wl, P, B in raw_pairs(RAW / "20230825" / OBS / f"{OBS}.csv"):
        if k == MID:
            break
    cwl, cy = worked(MID)
    fig, (a, b) = plt.subplots(2, 1, figsize=(7.2, 4.8), sharex=True, gridspec_kw={"height_ratios": [1.2, 1]})
    a.plot(wl, P, color=C_REF, lw=0.6, label=f"Plasma acquisition $I_P$ (row {int(pr.name) + 1}, {pr['Time']})")
    a.plot(wl, B, color=C_BG, lw=0.6, label=f"Paired background $I_B$ (row {bg_row}, {br['Time']})")
    a.set_ylabel("L1 response (a.u.)")
    a.legend(loc="upper right", frameon=False)
    a.set_title("(a) Measured inputs (timestamps have 1 s resolution)", loc="left")
    b.plot(cwl, cy, color=C_CLEAN, lw=0.6, label=r"$\max(0, I_P - I_B)$")
    b.axvspan(S["noise_min"], S["noise_max"], color="#e2e8f0", label="560–580 nm window")
    b.set_ylabel("Cleaned (a.u.)")
    b.set_xlabel("Wavelength (nm, L1 parent-table axis)")
    b.legend(loc="upper right", frameon=False)
    b.set_title("(b) Measured-frame subtraction with zero-clamping", loc="left")
    for ax in (a, b):
        for lo, hi in [(wl[0], S["cal_min"]), (S["cal_max"], wl[-1])]:
            ax.axvspan(lo, hi, color="#f1f5f9", zorder=0)
        ax.set_xlim(wl[0], wl[-1])
    b.text(0.003, 0.9, "outside 220–800 nm", transform=b.transAxes, fontsize=7, color=C_REF)
    save(fig, "fig3_background_subtraction")


def fig4():
    wl, y = worked(MID)
    c = (wl >= S["cal_min"]) & (wl <= S["cal_max"])
    pk, _, sig = detect(wl, y)
    lines = pd.read_csv(TAB / "D_per_line_candidates.csv")
    lines = lines[lines.measurement_id == MID]

    def label(r):
        refs = [t.strip().rsplit(" ", 1) for t in r.refs_within_1p1nm.split(";")]
        txt = (f"{refs[0][0]} " + "/".join(f"{float(w):.1f}" for _, w in refs) if len({sp for sp, _ in refs}) == 1
               else "/".join(f"{sp} {float(w):.1f}" for sp, w in refs))
        return txt + " ?" if r.possible_blend else txt

    windows = [(270, 292), (383, 400), (580, 598), (768, 786)]
    fig = plt.figure(figsize=(7.2, 7.4))
    gs = fig.add_gridspec(2, 4, height_ratios=[1.5, 1], hspace=0.75, wspace=0.4)
    top = fig.add_subplot(gs[0, :])
    top.plot(wl[c], y[c], color=C_CLEAN, lw=0.6)
    top.plot(wl[pk], y[pk], "v", color=C_REF, ms=2.5, label=f"Detected peak ({len(pk)}; prominence ≥ 3σ = {3 * sig:.0f} a.u.)")
    top.plot(lines.observed_nm, lines.intensity, "v", color=C_CAND, ms=4.5,
             label=f"Candidate coincidence, |Δλ| < 0.5 nm ({len(lines)})")
    for x in NIST_CAL.ref_nm:
        top.axvline(x, color=C_NIST, ls=":", lw=0.6)
    top.plot([], [], ls=":", color=C_NIST, label="Reference wavelength (list in Pipeline/step4)")
    last = -1e9
    for r in lines.sort_values("observed_nm").itertuples():
        xt = max(r.observed_nm, last + 34)
        last = xt
        top.annotate(label(r), (r.observed_nm, r.intensity), xytext=(xt, y[c].max() * 1.08), rotation=90,
                     ha="center", va="bottom", fontsize=6.5, color="#1e293b",
                     arrowprops=dict(arrowstyle="-", color=C_CAND, lw=0.4))
    top.set_ylim(0, y[c].max() * 2.25)
    top.set_xlim(S["cal_min"], S["cal_max"])
    top.set_ylabel("Cleaned (a.u.)")
    top.set_xlabel("Wavelength (nm, L1 parent-table axis)")
    top.set_title(f"(a) Measurement ID {MID}: wavelength coincidences, not confirmed identifications", loc="left")
    top.legend(loc="upper right", frameon=True, framealpha=0.95, edgecolor="none", fontsize=6.5, ncol=1)
    for i, (lo, hi) in enumerate(windows):
        ax = fig.add_subplot(gs[1, i])
        m = (wl >= lo) & (wl <= hi)
        ax.plot(wl[m], y[m], color=C_CLEAN, lw=0.7, drawstyle="steps-mid")
        pm = pk[(wl[pk] >= lo) & (wl[pk] <= hi)]
        ax.plot(wl[pm], y[pm], "v", color=C_REF, ms=3)
        lm = lines[(lines.observed_nm >= lo) & (lines.observed_nm <= hi)]
        ax.plot(lm.observed_nm, lm.intensity, "v", color=C_CAND, ms=4.5)
        groups = []   # references closer than 1.1 nm share one label (possibly unresolved)
        for r in NIST_CAL[(NIST_CAL.ref_nm >= lo) & (NIST_CAL.ref_nm <= hi)].sort_values("ref_nm").itertuples():
            ax.axvline(r.ref_nm, color=C_NIST, ls=":", lw=0.8)
            if groups and r.ref_nm - groups[-1][-1].ref_nm < S["fwhm_upper_bound_nm"]:
                groups[-1].append(r)
            else:
                groups.append([r])
        for g in groups:
            sp = {r.species for r in g}
            txt = (f"{g[0].species} " + "/".join(f"{r.ref_nm:.1f}" for r in g) if len(sp) == 1
                   else "/".join(f"{r.species} {r.ref_nm:.1f}" for r in g))
            ax.text(np.mean([r.ref_nm for r in g]), 1.01, txt,
                    transform=ax.get_xaxis_transform(), rotation=90, fontsize=6, ha="center", va="bottom",
                    color="#1e293b")
        top.axvspan(lo, hi, color="#fef3c7", zorder=0)
        ax.set_xlim(lo, hi)
        ax.set_title(f"({'bcde'[i]}) {lo}–{hi} nm", loc="left", pad=78, fontsize=8)
        ax.set_xlabel("nm", fontsize=7)
        ax.tick_params(labelsize=6.5)
    save(fig, "fig4_nist_annotated")


def fig5():
    sh = pd.read_csv(TAB / "B_archive_paired_shots.csv")
    thr = pd.read_csv(TAB / "B_clip_threshold_sensitivity.csv")
    fig, (a, b, c) = plt.subplots(1, 3, figsize=(7.2, 2.6), gridspec_kw={"width_ratios": [1.2, 1, 1.2]})
    a.hist(sh.clip_frac_full, bins=np.linspace(0, 1, 21), color=C_CLEAN, edgecolor="white", linewidth=1)
    for t in S["clip_thresholds"]:
        a.axvline(t, color=C_REF if t != 0.5 else C_CAND, ls="--", lw=0.9)
    a.set_xlabel("Clip fraction (negative before clamping,\n2,094 channels)")
    a.set_ylabel("Paired shots")
    a.set_title(f"(a) n = {len(sh)}", loc="left")
    t = thr[thr.definition == "clip_frac_full"]
    bars = b.bar([f"> {x:.0%}" for x in t.threshold], t.flagged, color=C_CLEAN, width=0.6)
    for bar, (n, p) in zip(bars, zip(t.flagged, t.flagged_pct)):
        b.text(bar.get_x() + bar.get_width() / 2, n, f"{n}\n({p:.0f}%)", ha="center", va="bottom", fontsize=7)
    b.set_ylim(0, len(sh))
    b.set_ylabel("Shots flagged")
    b.set_title("(b) Threshold sensitivity", loc="left")
    c.scatter(sh.clip_frac_full, sh.mean_clean_cal, s=4, color=C_CLEAN, alpha=0.5, linewidths=0)
    c.set_yscale("symlog", linthresh=10)
    c.axvline(0.5, color=C_CAND, ls="--", lw=0.9)
    c.set_xlabel("Clip fraction")
    c.set_ylabel("Mean cleaned, 220–800 nm (a.u.)")
    c.set_title("(c) Descriptive only", loc="left")
    fig.tight_layout()
    save(fig, "fig5_clipping")


def fig6():
    z = np.load(TAB / "D_null_distributions.npz")
    w = pd.read_csv(TAB / "D_null_worked_example.csv").set_index("measurement_id")
    ar = pd.read_csv(TAB / "D_null_archive.csv").set_index("set")
    panels = [(f"id{m}_drop", w.loc[m, "observed_matched_peaks"], w.loc[m, "p_drop"], f"ID {m}") for m in S["eval_ids"]]
    panels.append(("archive_all_paired", ar.loc["all_paired", "observed_matched_peaks"], ar.loc["all_paired", "p_drop"],
                   f"Archive, {int(ar.loc['all_paired', 'n_spectra'])} paired shots"))
    fig, axes = plt.subplots(1, 4, figsize=(7.2, 2.3))
    for ax, (key, obs, p, title) in zip(axes, panels):
        null = z[key]
        if key.startswith("id"):
            ax.hist(null, bins=np.arange(-0.5, max(null.max(), obs) + 1.5), color=C_REF, edgecolor="white", linewidth=1)
        else:
            ax.hist(null, bins=30, color=C_REF, edgecolor="white", linewidth=0.5)
        ax.axvline(obs, color=C_CAND, lw=1.5)
        ax.set_title(f"{title}\nobserved {int(obs)}, p = {p:.2g}", loc="left", fontsize=8)
        ax.set_xlabel("Matched peaks")
    axes[0].set_ylabel("Draws")
    fig.tight_layout()
    save(fig, "fig6_random_shift")


if __name__ == "__main__":
    for f in (fig2, fig3, fig4, fig5, fig6):
        f()
