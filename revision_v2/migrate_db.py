#!/usr/bin/env python3
"""
Reversible migration of a LunarAtlas database from legacy ingestion to the revision-v2 pipeline.

Nothing is modified in place. The corrected data are built in a separate database <db>_v2, the
legacy database is kept intact, and the switch is two database renames, so rollback is two renames.

  python revision_v2/migrate_db.py <phase> --server postgresql://admin@host:port --db lunaratlas --out DIR
  phases, in order:
    snapshot  row counts of every table + digests of every non-ingestion table      -> DIR/snapshot_<db>.json
    backup    pg_dump -Fc <db>, restore into <db>_restorecheck, compare with the snapshot, drop the scratch DB
    build     create <db>_v2 and ingest the revision outputs with the corrected pipeline, then verify it
    cutover   (API stopped) copy every non-ingestion table (users, API keys, usage log, alembic_version, ...)
              from <db> into <db>_v2, verify digests, rename <db> -> <db>_legacy and <db>_v2 -> <db>
    rollback  rename <db> -> <db>_v2 and <db>_legacy -> <db>
    verify    data checks on <db> (counts, duplicates, quality fields, SQL subtraction, files vs DB, linkage)

After cutover or rollback the Redis response cache must be emptied before the API is restarted:
  redis-cli --scan --pattern 'lunaratlas_v2:*' | xargs -r redis-cli del
(/api/v1/cache/clear cannot do this: it scans 'lunaratlas:*' while keys are written as 'lunaratlas_v2:*'.)

Requires a role that may CREATE/RENAME databases and the PostgreSQL client tools on PG_BIN.
"""
import argparse
import contextlib
import io
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import psycopg2

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "Pipeline"))
PG_BIN = Path(os.environ.get("PG_BIN", r"C:\Program Files\PostgreSQL\18\bin"))

# Tables written by Pipeline/optional_db_ingestion.py. Everything else is application state and is carried over.
INGESTION_TABLES = ["mission", "instrument", "instrument_spec_libs", "dataset_version", "observation_session",
                    "observation", "observation_file_info", "measurement_raw", "spectral_data_raw",
                    "measurement_clean", "spectral_data_clean", "nist_lines"]


def url(server, db):
    return f"{server.rstrip('/')}/{db}"


def tool(name, *args):
    return subprocess.run([str(PG_BIN / name), *args], check=True, capture_output=True, text=True)


def admin(server, sql):
    with contextlib.closing(psycopg2.connect(url(server, "postgres"))) as c:
        c.autocommit = True
        with c.cursor() as cur:
            cur.execute(sql)


def exists(server, db):
    with contextlib.closing(psycopg2.connect(url(server, "postgres"))) as c, c.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db,))
        return cur.fetchone() is not None


def kick(server, db):
    """Terminate other sessions on db (the API must already be stopped; this closes stragglers)."""
    admin(server, f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{db}' "
                  f"AND pid <> pg_backend_pid()")


def tables(cur):
    cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY 1")
    return [r[0] for r in cur.fetchall()]


def snapshot(server, db):
    """Row count of every table; content digest of every non-ingestion (application) table."""
    with contextlib.closing(psycopg2.connect(url(server, db))) as c, c.cursor() as cur:
        out = {"counts": {}, "app_digests": {}}
        for t in tables(cur):
            cur.execute(f'SELECT COUNT(*) FROM "{t}"')
            out["counts"][t] = cur.fetchone()[0]
            if t not in INGESTION_TABLES:
                cur.execute(f'SELECT md5(COALESCE(string_agg(x::text, \'|\' ORDER BY x::text), \'\')) FROM "{t}" x')
                out["app_digests"][t] = cur.fetchone()[0]
        return out


def backup(server, db, out):
    snap = snapshot(server, db)
    dump = out / f"{db}.dump"
    tool("pg_dump", "-Fc", "-f", str(dump), url(server, db))
    check = f"{db}_restorecheck"
    admin(server, f'DROP DATABASE IF EXISTS "{check}"')
    admin(server, f'CREATE DATABASE "{check}"')
    try:
        tool("pg_restore", "--no-owner", "-d", url(server, check), str(dump))
        restored = snapshot(server, check)
    finally:
        admin(server, f'DROP DATABASE IF EXISTS "{check}"')
    return {"dump": str(dump), "dump_bytes": dump.stat().st_size, "restore_matches_source": restored == snap}


def build(server, db, processed, raw):
    from optional_db_ingestion import ingest_cleaned_datasets
    cand = f"{db}_v2"
    if exists(server, cand):
        raise SystemExit(f"{cand} already exists; drop it deliberately before rebuilding")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):  # creates the database, schema, NIST seed, then ANALYZE
        m = ingest_cleaned_datasets(str(processed), db_url=url(server, cand), raw_dir=str(raw))
    return {"ingestion": m, "log_tail": buf.getvalue()[-2000:]}


def cutover(server, db):
    cand, legacy = f"{db}_v2", f"{db}_legacy"
    if exists(server, legacy):
        raise SystemExit(f"{legacy} exists: an earlier cutover was not rolled back")
    kick(server, db)
    src = snapshot(server, db)
    app = [t for t in src["counts"] if t not in INGESTION_TABLES]
    with contextlib.closing(psycopg2.connect(url(server, cand))) as c, c.cursor() as cur:
        for t in app:  # a repeated cutover after a rollback replaces the earlier copy
            cur.execute(f'DROP TABLE IF EXISTS "{t}" CASCADE')
        c.commit()
    if app:
        dump = subprocess.run([str(PG_BIN / "pg_dump"), "-Fc", *sum((["-t", f'public."{t}"'] for t in app), []),
                               url(server, db)], check=True, capture_output=True).stdout
        subprocess.run([str(PG_BIN / "pg_restore"), "--no-owner", "-d", url(server, cand)], input=dump,
                       check=True, capture_output=True)
    copied = snapshot(server, cand)
    ok = all(copied["app_digests"].get(t) == src["app_digests"][t] for t in app)
    if not ok:
        raise SystemExit("application tables differ after copy; nothing renamed")
    kick(server, db)
    admin(server, f'ALTER DATABASE "{db}" RENAME TO "{legacy}"')
    admin(server, f'ALTER DATABASE "{cand}" RENAME TO "{db}"')
    return {"app_tables_copied": app, "app_digests_equal": ok, "legacy_kept_as": legacy}


def rollback(server, db):
    cand, legacy = f"{db}_v2", f"{db}_legacy"
    if not exists(server, legacy):
        raise SystemExit(f"{legacy} not found; nothing to roll back")
    kick(server, db)
    admin(server, f'ALTER DATABASE "{db}" RENAME TO "{cand}"')
    admin(server, f'ALTER DATABASE "{legacy}" RENAME TO "{db}"')
    return {"restored": db, "candidate_kept_as": cand}


def verify(server, db, processed):
    """Data checks of a migrated database against the processed files it was built from."""
    with contextlib.closing(psycopg2.connect(url(server, db))) as c, c.cursor() as cur:
        def one(sql):
            cur.execute(sql)
            return cur.fetchone()

        s = {"counts": {t: one(f"SELECT COUNT(*) FROM {t}")[0] for t in INGESTION_TABLES}}
        s["duplicate_clean_points"] = one("""SELECT COUNT(*) FROM (SELECT 1 FROM spectral_data_clean
            GROUP BY measurement_id, wavelength_nm HAVING COUNT(*) > 1) d""")[0]
        s["clean_not_background_subtracted"] = one(
            "SELECT COUNT(*) FROM measurement_clean WHERE background_subtracted IS NOT TRUE")[0]
        s["quality_fields_null"] = one("""SELECT COUNT(*) FROM measurement_clean
            WHERE background_row IS NULL OR clip_fraction IS NULL""")[0]
        s["clean_without_raw_plasma_row"] = one("""SELECT COUNT(*) FROM measurement_clean m
            LEFT JOIN measurement_raw r USING (measurement_id) WHERE r.measurement_id IS NULL""")[0]
        s["clean_without_raw_background_row"] = one("""SELECT COUNT(*) FROM measurement_clean m
            LEFT JOIN measurement_raw r ON r.measurement_id = m.file_info_id || '-bg-' || m.background_row
            WHERE r.measurement_id IS NULL""")[0]
        diff, n = one("""SELECT MAX(ABS(c.intensity - GREATEST(0, rp.response_count - rb.response_count))), COUNT(*)
            FROM measurement_clean m
            JOIN spectral_data_clean c ON c.measurement_id = m.measurement_id
            JOIN spectral_data_raw rp ON rp.measurement_id = m.measurement_id AND rp.wavelength_nm = c.wavelength_nm
            JOIN spectral_data_raw rb ON rb.measurement_id = m.file_info_id || '-bg-' || m.background_row
                                     AND rb.wavelength_nm = c.wavelength_nm""")
        s["subtraction_recomputed"] = {"max_abs_diff": None if diff is None else float(diff), "points": n}
        cur.execute("SELECT measurement_id, SUM(intensity), COUNT(*) FROM spectral_data_clean GROUP BY 1")
        db_rows = pd.DataFrame(cur.fetchall(), columns=["mid", "db_sum", "db_n"])

    files = []
    for f in Path(processed).glob("calibrated/*/*/*_cleaned.csv"):
        obs = f.name.replace("_cleaned.csv", "").split("_")
        g = pd.read_csv(f, usecols=["Measurement_ID", "Cleaned_Intensity"]).groupby(
            "Measurement_ID").Cleaned_Intensity.agg(["sum", "count"]).reset_index()
        g["mid"] = f"FI-{obs[3].replace('T', '-')}-{obs[4]}-" + g.Measurement_ID.astype(str)
        files.append(g[["mid", "sum", "count"]])
    m = pd.concat(files).merge(db_rows, on="mid", how="outer", indicator=True)
    s["files_vs_db"] = {"only_in_files": int((m._merge == "left_only").sum()),
                        "only_in_db_stale": int((m._merge == "right_only").sum()),
                        "point_count_mismatch": int((m["count"] != m.db_n).sum()),
                        "max_abs_sum_diff": float(np.nanmax(np.abs(m["sum"] - m.db_sum)))}
    s["passed"] = (s["duplicate_clean_points"] == 0 and s["clean_not_background_subtracted"] == 0
                   and s["quality_fields_null"] == 0 and s["clean_without_raw_plasma_row"] == 0
                   and s["clean_without_raw_background_row"] == 0 and s["subtraction_recomputed"]["max_abs_diff"] == 0
                   and s["files_vs_db"]["only_in_files"] == 0 and s["files_vs_db"]["only_in_db_stale"] == 0
                   and s["files_vs_db"]["point_count_mismatch"] == 0 and s["files_vs_db"]["max_abs_sum_diff"] == 0)
    return s


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("phase", choices=["snapshot", "backup", "build", "cutover", "rollback", "verify"])
    ap.add_argument("--server", required=True, help="postgresql://user@host:port (no database name)")
    ap.add_argument("--db", default="lunaratlas")
    ap.add_argument("--processed", default=str(ROOT / "revision_v2" / "processed_run1"))
    ap.add_argument("--raw", default=str(ROOT / "datasets" / "uploads"))
    ap.add_argument("--out", default=str(ROOT / "revision_v2" / "outputs" / "migration"))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    r = {"snapshot": lambda: snapshot(a.server, a.db), "backup": lambda: backup(a.server, a.db, out),
         "build": lambda: build(a.server, a.db, a.processed, a.raw), "cutover": lambda: cutover(a.server, a.db),
         "rollback": lambda: rollback(a.server, a.db), "verify": lambda: verify(a.server, a.db, a.processed)}[a.phase]()
    (out / f"{a.phase}_{a.db}.json").write_text(json.dumps(r, indent=2, default=str))
    print(json.dumps(r, indent=2, default=str))


if __name__ == "__main__":
    main()
