"""
Stage-7 ingestion against a disposable PostgreSQL database.

Skipped unless LUNARATLAS_TEST_DB_URL points at a database that may be written to
(never a production URL). revision_v2/run_isolated_ingestion.py starts a throwaway
cluster and sets it.

Checks: raw/clean IDs name the same shot, quality fields survive ingestion, and a second
ingestion of the same files adds no rows (idempotent, no table drops).
"""

import os
import sys
from pathlib import Path

import pandas as pd
import pytest

DB_URL = os.environ.get("LUNARATLAS_TEST_DB_URL")
pytestmark = pytest.mark.skipif(not DB_URL, reason="LUNARATLAS_TEST_DB_URL not set")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "Pipeline"))
from step2_process_l1_data import EXPECTED_TRAILING_COLS, L1DataProcessor  # noqa: E402

OBS = "ch3_lib_999_20990101T000000_00_l1"
WL = ["300.0", "300.34", "300.68"]


def make_raw(raw_dir: Path):
    folder = raw_dir / "20990101" / OBS
    folder.mkdir(parents=True)
    rows = [(0, 1, 0, [50, 5, 30]),      # plasma 1, no background -> excluded
            (1, 0, 2, [10, 10, 10]),     # background with non-zero Laser Energy (as in 35 archive rows)
            (0, 1, 3300, [50, 5, 30]),   # plasma 2 -> paired
            (0, 1, 3300, [5, 5, 5])]     # plasma 3 -> paired, 100% clipped
    recs = []
    for i, (f, l, energy, spec) in enumerate(rows):
        r = {"Time": f"2099-01-01 00:00:{i:02d}", "Measurement Count": i + 1, "Operation Mode": "ASLF",
             "Measurement Type": "EP", "Force Reset Status": f, "Laser Fire Status": l}
        r.update(dict(zip(WL, spec)))
        r.update({c: 1 for c in EXPECTED_TRAILING_COLS})
        r["Laser Energy"] = energy
        recs.append(r)
    pd.DataFrame(recs).to_csv(folder / f"{OBS}.csv", index=False)
    (folder / f"{OBS}.xml").write_text(
        '<Product_Observational xmlns="http://pds.nasa.gov/pds4/pds/v1"><Identification_Area>'
        f'<logical_identifier>urn:test:{OBS}</logical_identifier><version_id>1.0</version_id></Identification_Area>'
        '<Time_Coordinates><start_date_time>2099-01-01T00:00:00Z</start_date_time>'
        '<stop_date_time>2099-01-01T00:00:03Z</stop_date_time></Time_Coordinates>'
        '<File><records>4</records></File></Product_Observational>', encoding="utf-8")


def test_ingestion_links_quality_and_is_idempotent(tmp_path):
    import psycopg2
    from optional_db_ingestion import ingest_cleaned_datasets

    raw, processed = tmp_path / "raw", tmp_path / "processed"
    make_raw(raw)
    L1DataProcessor(raw, processed).run()

    first = ingest_cleaned_datasets(str(processed), db_url=DB_URL, raw_dir=str(raw))
    second = ingest_cleaned_datasets(str(processed), db_url=DB_URL, raw_dir=str(raw))
    assert first["newly_ingested_measurements"] == 2
    assert second["newly_ingested_measurements"] == 0

    fi = "FI-20990101-000000-00"
    with psycopg2.connect(DB_URL) as conn, conn.cursor() as cur:
        cur.execute("SELECT measurement_id, background_subtracted, background_row, clip_fraction "
                    "FROM measurement_clean WHERE file_info_id=%s ORDER BY measurement_id", (fi,))
        clean = cur.fetchall()
        cur.execute("SELECT measurement_id FROM measurement_raw WHERE file_info_id=%s ORDER BY measurement_index", (fi,))
        raw_ids = [r[0] for r in cur.fetchall()]
        cur.execute("SELECT COUNT(*), COUNT(DISTINCT (measurement_id, wavelength_nm)) FROM spectral_data_clean "
                    "WHERE measurement_id LIKE %s", (fi + "-%",))
        n_rows, n_distinct = cur.fetchone()
        # cleaned shot 2 must join to the raw plasma row it came from (row 3, not the background)
        cur.execute("SELECT r.response_count - c.intensity FROM spectral_data_clean c JOIN spectral_data_raw r "
                    "ON r.measurement_id=c.measurement_id AND r.wavelength_nm=c.wavelength_nm "
                    "WHERE c.measurement_id=%s AND c.wavelength_nm=300.0", (fi + "-2",))
        diff = cur.fetchone()[0]

    assert clean == [(fi + "-2", True, 2, 0.3333), (fi + "-3", True, 2, 1.0)]   # residuals +40, -5, +20 -> 1/3 clipped
    assert raw_ids == [fi + "-1", fi + "-bg-2", fi + "-2", fi + "-3"]
    assert n_rows == n_distinct == 6
    assert diff == 10   # raw 50 - cleaned 40 = paired background value
