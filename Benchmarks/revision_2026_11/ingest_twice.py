"""Point 2: ingest the full processed archive twice into a THROWAWAY database; check counts, idempotency,
duplicates, quality fields and SQL recomputation of max(0, P - B) from the stored raw rows.
Never point db_url at production.

usage: ingest_twice.py <repo> <processed_dir> <datasets/uploads> <db_url>
"""
import sys, contextlib, io
from pathlib import Path
import psycopg2

repo, processed, raw, url = sys.argv[1:5]
assert "supabase" not in url, "refusing to run against production"
sys.path.insert(0, str(Path(repo) / "Pipeline"))
from optional_db_ingestion import ingest_cleaned_datasets  # noqa: E402


def counts(cur):
    out = {}
    for t in ("observation", "observation_file_info", "measurement_raw", "spectral_data_raw",
              "measurement_clean", "spectral_data_clean"):
        cur.execute(f"select count(*) from {t}"); out[t] = cur.fetchone()[0]
    return out


conn = psycopg2.connect(url); conn.autocommit = True; cur = conn.cursor()
for run in (1, 2):
    with contextlib.redirect_stdout(io.StringIO()):
        m = ingest_cleaned_datasets(processed, db_url=url, raw_dir=raw)
    print(f"run {run}: newly ingested {m['newly_ingested_measurements']} measurements, "
          f"{m['newly_ingested_spectral_points']} points; table counts {counts(cur)}")

cur.execute("select count(*) from (select measurement_id, wavelength_nm from spectral_data_clean group by 1,2 having count(*)>1) d")
print("duplicate (measurement, wavelength):", cur.fetchone()[0])
cur.execute("select count(*) filter (where not background_subtracted), count(*) filter (where clip_fraction is null or background_row is null) from measurement_clean")
print("not subtracted / missing quality fields:", cur.fetchone())
# raw plasma row shares the clean measurement_id; paired background is stored as {file_info_id}-bg-{row}
cur.execute("""
select count(*), max(abs(s.intensity - greatest(0, p.response_count - b.response_count)))
from measurement_clean c
join spectral_data_clean s on s.measurement_id = c.measurement_id
join spectral_data_raw p on p.measurement_id = c.measurement_id and p.wavelength_nm = s.wavelength_nm
join spectral_data_raw b on b.measurement_id = c.file_info_id || '-bg-' || c.background_row
                        and b.wavelength_nm = s.wavelength_nm
""")
print("SQL recomputation (points, max |diff|):", cur.fetchone())
