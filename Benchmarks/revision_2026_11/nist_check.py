"""Point 5: NIST wavelength-coincidence matching — reproduce the submitted numbers, check the old claims,
and run a random-shift null model (worked example + archive) and a wavelength-axis comparison.

Peak rule (as in the submitted paper): scipy find_peaks on the cleaned spectrum within 220-800 nm,
prominence >= 3 sigma (sigma = population std, ddof=0, of the cleaned spectrum over 560-580 nm),
distance >= 5 channels. Reference list: the 24 lines of Pipeline/step4_nist_verification_logs.py
within 220-800 nm. A peak is a candidate coincidence if some reference lies within the tolerance;
each peak counts once.

Null model: per draw one common shift s of the whole reference list, |s| ~ U(2, 20) nm, random sign;
p = (1 + k) / (1 + N), k = draws with count >= observed. Archive: the same shift for every spectrum,
statistic = sum of per-spectrum counts.

usage: nist_check.py <repo> <stage-2 output dir> <datasets/uploads> <out_dir>
"""
import sys, json, csv as csvmod
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.signal import find_peaks

repo, proc, raw, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4])
out.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(repo / "Pipeline"))
from step4_nist_verification_logs import NIST_DB  # noqa: E402

CAL = (220.0, 800.0); NOISE = (560.0, 580.0); TOL = 0.5; NEAR = 1.1
SEED_W, SEED_A, N_W, N_A, N_AX = 20261021, 20261022, 10000, 1000, 300
NIST = pd.DataFrame(NIST_DB).rename(columns={"element": "species", "wavelength": "ref"})
REF_ALL = NIST.ref.to_numpy()
CALREF = NIST[(NIST.ref >= CAL[0]) & (NIST.ref <= CAL[1])].reset_index(drop=True)
REF = CALREF.ref.to_numpy()
WORKED = "ch3_lib_002_20230825T104221_00_l1"
log = open(out / "nist_check.txt", "w", encoding="utf-8")


def say(*a):
    s = " ".join(str(x) for x in a); print(s); log.write(s + "\n")


def detect(wl, y):
    n = (wl >= NOISE[0]) & (wl <= NOISE[1])
    sig = float(np.std(y[n], ddof=0))
    c = (wl >= CAL[0]) & (wl <= CAL[1])
    idx, pr = find_peaks(y[c], prominence=3 * sig, distance=5)
    return np.flatnonzero(c)[idx], pr["prominences"], sig


def matched(pwl, ref, tol=TOL, strict=True):
    if len(pwl) == 0: return 0
    d = np.abs(pwl[:, None] - ref[None, :])
    return int(((d < tol) if strict else (d <= tol)).any(axis=1).sum())


def p_emp(null, obs):
    k = int((null >= obs).sum()); return k, (1 + k) / (1 + len(null))


def shifts(n, seed):
    rng = np.random.default_rng(seed)
    return rng.uniform(2.0, 20.0, n) * rng.choice([-1, 1], n)


say(f"reference lines: {len(REF_ALL)} in list, {len(REF)} within 220-800 nm")

# ── all cleaned spectra ─────────────────────────────────────────────────────
spectra = {}
for f in sorted(proc.rglob("*_cleaned.csv")):
    d = pd.read_csv(f)
    for m, g in d.groupby("Measurement_ID"):
        g = g.sort_values("Wavelength_nm")
        spectra[(f.name[:-len("_cleaned.csv")], int(m))] = (g.Wavelength_nm.to_numpy(), g.Cleaned_Intensity.to_numpy())
say("cleaned spectra:", len(spectra))
peaks = {k: detect(*v) for k, v in spectra.items()}

# ── worked example: reproduce the submitted numbers + per-peak table ───────
sh_w = shifts(N_W, SEED_W)
summary, per_peak = [], []
for mid in (1, 3, 4):
    wl, y = spectra[(WORKED, mid)]
    pk, prom, sig = peaks[(WORKED, mid)]
    pwl = wl[pk]
    o_strict, o_le = matched(pwl, REF), matched(pwl, REF, strict=False)
    null = np.array([matched(pwl, REF + s) for s in sh_w])
    k, p = p_emp(null, o_strict)
    summary.append(dict(evaluation=f"ID {mid}", spectra=1, peaks=len(pk), draws=N_W, observed=o_strict,
                        null_mean=round(null.mean(), 2), k=k, p=round(p, 4)))
    say(f"ID {mid}: 3sigma={3*sig:.2f} peaks={len(pk)} matched(<0.5)={o_strict} matched(<=0.5)={o_le} "
        f"null mean={null.mean():.2f} k={k} p={p:.4f}")
    for i, pr in zip(pk, prom):
        d = wl[i] - REF_ALL
        near = NIST[np.abs(d) < NEAR]
        cand = NIST[np.abs(d) < TOL]
        best = NIST.iloc[int(np.argmin(np.abs(d)))]
        per_peak.append(dict(measurement_id=mid, observed_nm=wl[i], intensity=y[i], prominence=round(pr, 1),
                             prominence_over_sigma=round(pr / sig, 2), nearest_species=best.species,
                             nearest_ref_nm=best.ref, offset_nm=round(wl[i] - best.ref, 2),
                             candidate=len(cand) > 0,
                             refs_within_0p5=("; ".join(f"{r.species} {r.ref}" for r in cand.itertuples())),
                             refs_within_1p1=("; ".join(f"{r.species} {r.ref}" for r in near.itertuples()))))
pp = pd.DataFrame(per_peak)
pp.to_csv(out / "nist_per_peak_worked_example.csv", index=False)

say("\nID 3 candidate coincidences:")
for r in pp[(pp.measurement_id == 3) & pp.candidate].itertuples():
    say(f"  {r.observed_nm:.2f} nm  {r.nearest_species} {r.nearest_ref_nm}  offset {r.offset_nm:+.2f}  "
        f"prom/sigma {r.prominence_over_sigma}  within 1.1 nm: {r.refs_within_1p1}")
say("\nNear-misses (0.5 <= |offset| < 1.1 nm), IDs 1/3/4:")
for r in pp[(~pp.candidate) & (pp.offset_nm.abs() < NEAR)].itertuples():
    say(f"  ID {r.measurement_id}: {r.observed_nm:.2f} nm  {r.nearest_species} {r.nearest_ref_nm}  offset {r.offset_nm:+.2f}")

# Old claim: "five further NIST lines have sub-threshold prominence" (ID 3): reference lines in 220-800 nm
# with no candidate peak, but a local maximum within 0.5 nm whose intensity exceeds 3 sigma
wl, y = spectra[(WORKED, 3)]; pk, prom, sig = peaks[(WORKED, 3)]
lm = find_peaks(y)[0]
hit = {r for r in REF if (np.abs(wl[pk] - r) < TOL).any()}
sub = [r for r in REF if r not in hit and any(abs(wl[i] - r) < TOL and y[i] > 3 * sig for i in lm)]
say(f"\nID 3: reference lines without a candidate peak but with a local maximum > 3 sigma within 0.5 nm: "
    f"{len(sub)} {sub}")

# ── archive aggregate ──────────────────────────────────────────────────────
params = {}
for f in proc.rglob("*_instrument_params.csv"):
    for r in pd.read_csv(f).itertuples():
        params[(f.name[:-len("_instrument_params.csv")], int(r.Measurement_ID))] = r.Clip_Fraction
sh_a = shifts(N_A, SEED_A)
for label, keys in [("Archive, all paired", list(spectra)),
                    ("Archive, clip <= 0.5", [k for k in spectra if params[k] <= 0.5])]:
    pw = [spectra[k][0][peaks[k][0]] for k in keys]
    o = sum(matched(p, REF) for p in pw)
    null = np.array([sum(matched(p, REF + s) for p in pw) for s in sh_a])
    k, p = p_emp(null, o)
    summary.append(dict(evaluation=label, spectra=len(keys), peaks=sum(len(p_) for p_ in pw), draws=N_A,
                        observed=o, null_mean=round(null.mean(), 1), k=k, p=round(p, 4)))
    say(f"{label}: spectra={len(keys)} peaks={sum(len(p_) for p_ in pw)} observed={o} null mean={null.mean():.1f} k={k} p={p:.4f}")

# ── wavelength-axis comparison: same detected channels, single-shot axis ────
sub_files = sorted(raw.rglob("*_l1_*.csv"))
axes = {tuple(pd.read_csv(f, usecols=[0]).iloc[:, 0].round(2)) for f in sub_files}
say(f"\nsingle-shot files: {len(sub_files)}, distinct wavelength axes: {len(axes)}")
ss_axis = np.array(next(iter(axes)))
parent_axis = next(iter(spectra.values()))[0]
diff = ss_axis - parent_axis
say(f"single-shot axis {ss_axis[0]:.2f}-{ss_axis[-1]:.2f} nm; offset vs parent axis {diff.min():.2f} to {diff.max():.2f} nm; "
    f"at 589 nm: {diff[np.argmin(np.abs(parent_axis - 589))]:.2f} nm")
# counts identical? compare each single-shot file with its parent-table row (row index = file suffix order)
same = tot = 0
for f in sub_files:
    parent = f.with_name(f.name.rsplit("_", 2)[0] + ".csv")
    prow = int(f.stem.split("_")[-1]) - 1
    pv = pd.read_csv(parent).iloc[prow, 6:-8].to_numpy(float)
    sv = pd.read_csv(f).iloc[:, 1].to_numpy(float)
    tot += 1; same += int(np.array_equal(pv, sv))
say(f"single-shot counts identical to parent row: {same}/{tot}")
for name, ax in [("Archive, parent axis (axis comparison)", parent_axis), ("Archive, single-shot axis", ss_axis)]:
    pw = [ax[peaks[k][0]] for k in spectra]
    o = sum(matched(p, REF) for p in pw)
    null = np.array([sum(matched(p, REF + s) for p in pw) for s in sh_a[:N_AX]])
    k, p = p_emp(null, o)
    summary.append(dict(evaluation=name, spectra=len(spectra), peaks=sum(len(p_) for p_ in pw), draws=N_AX,
                        observed=o, null_mean=round(null.mean(), 1), k=k, p=round(p, 4)))
    say(f"{name}: observed={o} null mean={null.mean():.1f} k={k} p={p:.4f}")

pd.DataFrame(summary).to_csv(out / "nist_null_summary.csv", index=False)
say("\n" + pd.DataFrame(summary).to_string(index=False))
log.close()
