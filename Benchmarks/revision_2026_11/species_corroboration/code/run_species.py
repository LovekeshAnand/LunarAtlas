#!/usr/bin/env python3
"""
Stage 2: species-level corroboration scoring.
Reads the A4 reference catalogue READ-ONLY (RULES.md G1). Peak detection, noise
estimate and tolerance are imported from revision_v2/analysis.py unchanged.

Matching is MEMBER-LEVEL (A4.4). One peak supports at most one group per
species (A4.5). Null is a species-specific rigid shift of that species' own
grouped pattern, applied with the identical matching rule.

  python run_species.py --tag expanded_v4_A4rep
  python run_species.py --tag expanded_v4_A4rep --axis subfile
"""
import argparse, json, sys, time
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
OUT  = BASE / "outputs"
REPO = BASE.parents[2]   # repository root (ported from the co-author's layout)
for p in ("revision_v2", "Pipeline", "core/server"):
    sys.path.insert(0, str(REPO / p))
import analysis as A                                     # noqa: E402

FWHM = A.S["fwhm_upper_bound_nm"]
TOL  = A.S["match_tol_nm"]


def holm(p):
    p = np.asarray(p, float); m = len(p); o = np.argsort(p); adj = np.empty(m); run = 0.0
    for i, j in enumerate(o):
        run = max(run, (m - i) * p[j]); adj[j] = min(run, 1.0)
    return adj


def propose(members_pad, valid, P, rep):
    """A4.4 + A4.5, vectorised over draws.
    members_pad : (D, G, M) shifted member wavelengths, NaN-padded
    valid       : (G, M) bool, real members
    P           : (K,) peak wavelengths
    rep         : (G,) representative wavelength, for deterministic tie-break
    returns     : (D,) number of supported groups
    """
    D, G, M = members_pad.shape
    K = len(P)
    if K == 0:
        return np.zeros(D, int)
    # nearest peak to every member
    diff = np.abs(members_pad[:, :, :, None] - P[None, None, None, :])   # (D,G,M,K)
    diff[~np.broadcast_to(valid, (D, G, M))] = np.inf
    best_k = diff.reshape(D, G, M * K).argmin(axis=2)
    best_d = diff.reshape(D, G, M * K).min(axis=2)
    peak_idx = best_k % K                                                # (D,G)
    hit = best_d < TOL                                                   # (D,G)
    # A4.5: within a species one peak supports at most one group. Whichever group
    # wins a contested peak, exactly one group per claimed peak survives, so the
    # supported count equals the number of DISTINCT peaks claimed by hit groups.
    # (The offset/representative ordering decides WHICH group, reported separately
    # in the per-feature table; it cannot change the COUNT.)
    claimed = np.where(hit, peak_idx, -1)
    claimed.sort(axis=1)
    newv = np.empty_like(claimed, dtype=bool)
    newv[:, 0] = claimed[:, 0] >= 0
    newv[:, 1:] = (claimed[:, 1:] >= 0) & (claimed[:, 1:] != claimed[:, :-1])
    return newv.sum(axis=1).astype(int)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--axis", choices=["parent", "subfile"], default="parent")
    ap.add_argument("--draws", type=int, default=None)
    ap.add_argument("--chunk", type=int, default=250)
    a = ap.parse_args()
    draws = a.draws or A.S["null_draws"]
    rng = np.random.default_rng(A.S["null_seed"])
    shifts = rng.uniform(A.S["null_shift_min_nm"], A.S["null_shift_max_nm"], draws) * rng.choice([-1, 1], draws)

    G = pd.read_csv(OUT / f"E_line_groups__{a.tag}.csv")
    L = pd.read_csv(OUT / f"E_reference_lines__{a.tag}.csv")
    G["members"] = G.members_nm.map(lambda s: np.array([float(x) for x in str(s).split(";")]))
    species = sorted(G.species.unique())
    cl = A.cleaned(A.S["worked_obs"], "20230825")
    if a.axis == "subfile":
        obs = A.S["worked_obs"]
        sub = pd.read_csv(sorted((A.RAW / "20230825" / obs).glob(f"{obs}_*.csv"))[0]).iloc[:, 0].to_numpy(float)
    suffix = a.tag + ("__subfile_axis" if a.axis == "subfile" else "__parent_axis")

    scores, feats = [], []
    t0 = time.time()
    for mid in A.S["eval_ids"]:
        g = cl[mid]
        wl = sub if a.axis == "subfile" else g.Wavelength_nm.to_numpy(float)
        y = g.Cleaned_Intensity.to_numpy(float)
        pk, prom, sig = A.detect(wl, y)
        P = wl[pk]
        for sp in species:
            sg = G[G.species == sp].reset_index(drop=True)
            Mmax = int(sg.n_lines.max())
            mem = np.full((len(sg), Mmax), np.nan)
            for i, m in enumerate(sg.members):
                mem[i, :len(m)] = m
            valid = ~np.isnan(mem)
            mem0 = np.nan_to_num(mem, nan=1e9)
            rep = sg.group_nm.to_numpy(float)

            obs_n = int(propose(mem0[None], valid, P, rep)[0])
            null = np.empty(draws, int)
            for s0 in range(0, draws, a.chunk):
                sl = shifts[s0:s0 + a.chunk]
                null[s0:s0 + a.chunk] = propose(mem0[None] + sl[:, None, None], valid, P, rep)
            p = (1 + int((null >= obs_n).sum())) / (1 + draws)
            scores.append(dict(measurement_id=mid, species=sp, n_groups=len(sg), n_supported=obs_n,
                               null_mean=round(float(null.mean()), 3),
                               null_p95=float(np.percentile(null, 95)), p_raw=p,
                               n_peaks=len(P), sigma=round(float(sig), 2), axis=a.axis))
            # per-feature detail for the observed data, same rule
            d0 = np.abs(mem[:, :, None] - P[None, None, :])
            d0[~np.broadcast_to(valid[:, :, None], d0.shape)] = np.inf
            flat = d0.reshape(len(sg), -1)
            bk, bd = flat.argmin(axis=1), flat.min(axis=1)
            hit = np.flatnonzero(bd < TOL)
            hit = hit[np.lexsort((rep[hit], bd[hit]))]
            used = set()
            for gi in hit:
                k = bk[gi] % len(P)
                if k in used:
                    continue
                used.add(k)
                mi = bk[gi] // len(P)
                ref, pw = mem[gi, mi], P[k]
                near = L[(np.abs(L.obs_nm - pw) < FWHM) & (L.species != sp)]
                feats.append(dict(measurement_id=mid, species=sp, group_id=sg.group_id[gi],
                                  group_nm=sg.group_nm[gi], bin=sg.bin[gi],
                                  n_lines_in_group=int(sg.n_lines[gi]),
                                  matched_ref_nm=round(float(ref), 4), peak_nm=round(float(pw), 4),
                                  offset_nm=round(float(pw - ref), 4), n_competitors=len(near),
                                  competitors="; ".join(f"{r.species} {r.obs_nm:.2f}" for r in near.itertuples()) or "none",
                                  unresolved_interference=bool(len(near) > 0)))
        print(f"  ID {mid}: {len(P)} peaks, {len(species)} species done  [{time.time()-t0:.0f}s]", flush=True)

    S_ = pd.DataFrame(scores)
    S_["p_holm_global"] = holm(S_.p_raw.values)
    S_["significant_after_holm"] = S_.p_holm_global < 0.05
    F = pd.DataFrame(feats)
    if len(F):
        R = (F.groupby(["species", "group_id", "group_nm"])
               .agg(n_acquisitions=("measurement_id", "nunique"),
                    acquisitions=("measurement_id", lambda s: ",".join(map(str, sorted(set(s))))),
                    offset_min=("offset_nm", "min"), offset_max=("offset_nm", "max"),
                    ever_contested=("unresolved_interference", "any")).reset_index())
        R["recurring"] = R.n_acquisitions >= 2
    else:
        R = pd.DataFrame(columns=["species", "group_id", "group_nm", "n_acquisitions", "recurring"])

    S_.to_csv(OUT / f"E_species_scores__{suffix}.csv", index=False)
    F.to_csv(OUT / f"E_feature_matches__{suffix}.csv", index=False)
    (F[F.unresolved_interference] if len(F) else F).to_csv(OUT / f"E_competing_species__{suffix}.csv", index=False)
    R.to_csv(OUT / f"E_recurrence__{suffix}.csv", index=False)
    np.savez_compressed(OUT / f"E_null_shifts__{suffix}.npz", shifts=shifts)
    (OUT / f"E_run_manifest__{suffix}.json").write_text(json.dumps(dict(
        tag=a.tag, axis=a.axis, draws=draws, seed=A.S["null_seed"], tol_nm=TOL, fwhm_nm=FWHM,
        matching="member-level (A4.4); one peak per group per species (A4.5)",
        eval_ids=A.S["eval_ids"], holm_family="global: all species x acquisition",
        n_tests=len(S_), n_significant=int(S_.significant_after_holm.sum()),
        runtime_s=round(time.time() - t0, 1)), indent=2))
    print(f"\n[{suffix}] {len(S_)} tests, {int(S_.significant_after_holm.sum())} significant after global Holm "
          f"({time.time()-t0:.0f}s)")


if __name__ == "__main__":
    main()
