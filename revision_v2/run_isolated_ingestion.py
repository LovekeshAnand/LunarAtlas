#!/usr/bin/env python3
"""
Isolated ingestion check: starts a throwaway PostgreSQL cluster (own data dir, port 55432),
ingests revision_v2/processed_run1 twice, reconciles database rows with the processed files,
runs tests/test_ingestion_db.py against it, then stops the cluster and deletes it.
No other database is contacted.

Writes revision_v2/outputs/ingestion/{summary.json, ingest_run*.log, pytest_db.log}
"""
import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import psycopg2

ROOT = Path(__file__).resolve().parent.parent
V2 = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "Pipeline"))
from optional_db_ingestion import ingest_cleaned_datasets  # noqa: E402

PG_BIN = Path(os.environ.get("PG_BIN", r"C:\Program Files\PostgreSQL\18\bin"))
PGDATA = V2 / "_pgdata_tmp"
PORT = 55432
URL = f"postgresql://postgres@localhost:{PORT}/lunaratlas_isolated"
PROCESSED = V2 / "processed_run1"
RAW = ROOT / "datasets" / "uploads"
OUT = V2 / "outputs" / "ingestion"


def pg_start(*a):
    """pg_ctl start: the postmaster inherits stdout, so never capture it (the pipe would never close)."""
    subprocess.run([str(PG_BIN / "pg_ctl"), *a], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def pg(*args, **kw):
    return subprocess.run([str(PG_BIN / args[0]), *args[1:]], check=True, capture_output=True, text=True, **kw)


def ingest(n):
    buf = io.StringIO()
    t = time.time()
    with contextlib.redirect_stdout(buf):
        m = ingest_cleaned_datasets(str(PROCESSED), db_url=URL, raw_dir=str(RAW))
    (OUT / f"ingest_run{n}.log").write_text(buf.getvalue(), encoding="utf-8")
    return {**m, "seconds": round(time.time() - t, 1)}


def q(cur, sql):
    cur.execute(sql)
    return cur.fetchall()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    if PGDATA.exists():
        shutil.rmtree(PGDATA)
    pg("initdb", "-D", str(PGDATA), "-U", "postgres", "-A", "trust", "-E", "UTF8")
    pg_start("-D", str(PGDATA), "-o", f"-p {PORT} -c listen_addresses=localhost", "-l", str(OUT / "postgres.log"), "-w", "start")
    try:
        s = {"db": f"throwaway cluster, PostgreSQL {pg('postgres', '--version').stdout.strip()}, port {PORT}"}
        s["run1"] = ingest(1)
        with psycopg2.connect(URL) as c, c.cursor() as cur:
            counts1 = {t: q(cur, f"SELECT COUNT(*) FROM {t}")[0][0] for t in
                       ["observation", "observation_file_info", "measurement_raw", "spectral_data_raw",
                        "measurement_clean", "spectral_data_clean", "nist_lines"]}
        s["run2"] = ingest(2)
        with psycopg2.connect(URL) as c, c.cursor() as cur:
            counts2 = {t: q(cur, f"SELECT COUNT(*) FROM {t}")[0][0] for t in counts1}
            s["row_counts_after_run1"], s["row_counts_after_run2"] = counts1, counts2
            s["second_ingestion_added_rows"] = {t: counts2[t] - counts1[t] for t in counts1}
            s["duplicate_clean_points"] = q(cur, """SELECT COUNT(*) FROM (SELECT measurement_id, wavelength_nm
                FROM spectral_data_clean GROUP BY 1,2 HAVING COUNT(*)>1) d""")[0][0]
            s["duplicate_raw_points"] = q(cur, """SELECT COUNT(*) FROM (SELECT measurement_id, wavelength_nm
                FROM spectral_data_raw GROUP BY 1,2 HAVING COUNT(*)>1) d""")[0][0]
            s["clean_measurements_with_n_points"] = dict(q(cur, """SELECT n, COUNT(*) FROM (SELECT measurement_id,
                COUNT(*) n FROM spectral_data_clean GROUP BY 1) x GROUP BY 1"""))
            s["quality_fields"] = dict(zip(["n", "bg_subtracted_true", "bg_row_notnull", "clip_notnull", "clip_gt_0_5"],
                q(cur, """SELECT COUNT(*), SUM(background_subtracted::int), COUNT(background_row), COUNT(clip_fraction),
                          SUM((clip_fraction>0.5)::int) FROM measurement_clean""")[0]))
            s["raw_plasma_vs_background_ids"] = dict(q(cur, """SELECT CASE WHEN measurement_id LIKE '%%-bg-%%'
                THEN 'non_plasma' ELSE 'plasma' END, COUNT(*) FROM measurement_raw GROUP BY 1"""))
            # every clean shot must equal max(0, raw plasma - raw paired background), channel by channel
            s["clean_vs_raw_recomputed_max_abs_diff"] = float(q(cur, """
                SELECT COALESCE(MAX(ABS(c.intensity - GREATEST(0, rp.response_count - rb.response_count))), -1)
                FROM measurement_clean m
                JOIN spectral_data_clean c ON c.measurement_id = m.measurement_id
                JOIN spectral_data_raw rp ON rp.measurement_id = m.measurement_id AND rp.wavelength_nm = c.wavelength_nm
                JOIN spectral_data_raw rb ON rb.measurement_id = m.file_info_id || '-bg-' || m.background_row
                                         AND rb.wavelength_nm = c.wavelength_nm""")[0][0])
            s["clean_points_joined_in_that_check"] = q(cur, """SELECT COUNT(*) FROM measurement_clean m
                JOIN spectral_data_clean c ON c.measurement_id = m.measurement_id
                JOIN spectral_data_raw rp ON rp.measurement_id = m.measurement_id AND rp.wavelength_nm = c.wavelength_nm
                JOIN spectral_data_raw rb ON rb.measurement_id = m.file_info_id || '-bg-' || m.background_row
                                         AND rb.wavelength_nm = c.wavelength_nm""")[0][0]
            db = pd.DataFrame(q(cur, """SELECT measurement_id, SUM(intensity), COUNT(*) FROM spectral_data_clean GROUP BY 1"""),
                              columns=["mid", "db_sum", "db_n"])
            raw_md5 = q(cur, "SELECT COUNT(*), COUNT(md5_checksum_raw) FROM observation_file_info")[0]
            s["file_info_rows_with_raw_md5"] = f"{raw_md5[1]}/{raw_md5[0]}"

        # files -> DB reconciliation per measurement
        files = []
        for f in PROCESSED.glob("calibrated/*/*/*_cleaned.csv"):
            obs = f.name.replace("_cleaned.csv", "").split("_")
            fi = f"FI-{obs[3].replace('T', '-')}-{obs[4]}"
            d = pd.read_csv(f, usecols=["Measurement_ID", "Cleaned_Intensity"])
            g = d.groupby("Measurement_ID").Cleaned_Intensity.agg(["sum", "count"]).reset_index()
            g["mid"] = fi + "-" + g.Measurement_ID.astype(str)
            files.append(g[["mid", "sum", "count"]])
        files = pd.concat(files)
        m = files.merge(db, on="mid", how="outer", indicator=True)
        s["files_vs_db"] = {"measurements_in_files": len(files), "in_db": len(db),
                            "only_in_files": int((m._merge == "left_only").sum()),
                            "only_in_db": int((m._merge == "right_only").sum()),
                            "point_count_mismatch": int((m["count"] != m.db_n).sum()),
                            "max_abs_sum_diff": float(np.abs(m["sum"] - m.db_sum).max())}

        env = {**os.environ, "LUNARATLAS_TEST_DB_URL": URL}
        r = subprocess.run([sys.executable, "-m", "pytest", "tests/test_ingestion_db.py", "-v"], cwd=ROOT,
                           env=env, capture_output=True, text=True)
        (OUT / "pytest_db.log").write_text(r.stdout + r.stderr, encoding="utf-8")
        s["pytest_db_returncode"] = r.returncode
        (OUT / "summary.json").write_text(json.dumps(s, indent=2, default=str))
        print(json.dumps(s, indent=2, default=str))
    finally:
        pg("pg_ctl", "-D", str(PGDATA), "-m", "fast", "-w", "stop")
        shutil.rmtree(PGDATA, ignore_errors=True)


if __name__ == "__main__":
    main()
