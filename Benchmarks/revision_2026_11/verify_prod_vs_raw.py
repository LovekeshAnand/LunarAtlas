"""Point 2: production cleaned spectra == max(0, P - last preceding B) recomputed from the raw PRADAN CSVs.
Also prints production table counts (current schema `public` and the pre-migration `legacy_20261028`).
The session is forced READ ONLY. The DB URL is read from core/server/.env and never printed.

usage: verify_prod_vs_raw.py <core/server/.env> <datasets/uploads>
"""
import sys, re, csv
from pathlib import Path
import psycopg2

env = dict(re.findall(r'^\s*([A-Z_]+)\s*=\s*(.*?)\s*$', open(sys.argv[1]).read(), re.M))
raw = {p.stem: p for p in Path(sys.argv[2]).rglob("*_l1.csv")}
conn = psycopg2.connect(env["DATABASE_URL"].strip('"\''), connect_timeout=30)
conn.set_session(readonly=True, autocommit=True)
cur = conn.cursor()

cur.execute("select version()"); print("server:", cur.fetchone()[0][:40])
for schema in ("public", "legacy_20261028"):
    counts = {}
    for t in ("observation", "measurement_raw", "measurement_clean", "spectral_data_clean"):
        cur.execute(f'select count(*) from "{schema}"."{t}"'); counts[t] = cur.fetchone()[0]
    print(schema, counts)
cur.execute("select count(*) filter (where background_subtracted), count(*) filter (where clip_fraction > 0.5) from public.measurement_clean")
print("public: background_subtracted / clip_fraction>0.5:", cur.fetchone())


def expected(path):
    rows = list(csv.reader(path.read_text(encoding="utf-8").splitlines()))
    hdr, data = rows[0], rows[1:]
    wl = [float(h) for h in hdr[6:-8]]
    out, bg, n = {}, None, 0
    for r in data:
        F, L = r[4].strip(), r[5].strip()
        I = [float(v) for v in r[6:-8]]
        if (F, L) == ("1", "0"):
            bg = I
        elif (F, L) == ("0", "1"):
            n += 1
            if bg is not None:
                out[n] = [max(0.0, p - b) for p, b in zip(I, bg)]
    return wl, out


cur.execute("select file_info_id, base_file_name from public.observation_file_info order by 1")
files = cur.fetchall()
n_meas = n_pts = bad = 0; maxdiff = 0.0; missing = []; setdiff = []
for fid, base in files:
    stem = Path(base).stem.removesuffix("_cleaned")
    if stem not in raw:
        missing.append(base); continue
    wl, exp = expected(raw[stem])
    cur.execute("""select m.measurement_index, s.wavelength_nm, s.intensity
                   from public.measurement_clean m join public.spectral_data_clean s using (measurement_id)
                   where m.file_info_id=%s order by 1, 2""", (fid,))
    got = {}
    for idx, w, i in cur.fetchall():
        got.setdefault(idx, []).append((round(float(w), 2), float(i)))
    if set(got) != set(exp):
        setdiff.append((base, sorted(got), sorted(exp)))
    for idx, pts in got.items():
        if idx not in exp: continue
        n_meas += 1
        e = dict(zip(wl, exp[idx]))
        bad += abs(len(pts) - len(wl))
        for w, i in pts:
            d = abs(i - e[w]) if w in e else float("inf")
            n_pts += 1
            if d > 1e-9: bad += 1
            maxdiff = max(maxdiff, d)
print(f"products checked: {len(files)}; raw file not found: {len(missing)}")
print(f"products whose stored measurement set differs from raw pairing: {len(setdiff)} {setdiff[:2]}")
print(f"measurements compared: {n_meas}; points compared: {n_pts}; mismatching points: {bad}; max |diff|: {maxdiff}")
