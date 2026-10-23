#!/usr/bin/env python3
"""
Migration rehearsal on a throwaway PostgreSQL cluster (own data dir, port 55435). No other database is contacted.

Legacy state: the ingestion code deployed before the revision (git d1f4e42, Pipeline/optional_db_ingestion.py; its
hard-coded raw path D:\\ch3_libs\\lib-v2\\data\\calibrated is redirected to datasets/uploads) applied to the
legacy processed outputs datasets/processed_backup_20261020 -> 779 cleaned records, the count the public
deployment reports. Application tables are then created from the server's SQLAlchemy models and filled with
synthetic users, API keys and usage rows; an alembic_version table stands in for any other application table.

Then: snapshot -> backup + restore check -> build -> verify -> cutover -> verify -> rollback -> cutover again.
Writes revision_v2/outputs/migration_rehearsal/summary.json
"""
import contextlib
import json
import shutil
import subprocess
import sys
import time
import types
from pathlib import Path

import psycopg2

import migrate_db as M

ROOT, V2 = M.ROOT, Path(__file__).resolve().parent
PGDATA, PORT = V2 / "_pgmig_tmp", 55435
SERVER = f"postgresql://postgres@localhost:{PORT}"
DB = "lunaratlas"
OUT = V2 / "outputs" / "migration_rehearsal"
LEGACY_COMMIT = "d1f4e42"


def legacy_ingest():
    src = subprocess.run(["git", "show", f"{LEGACY_COMMIT}:Pipeline/optional_db_ingestion.py"], cwd=ROOT,
                         check=True, capture_output=True, text=True).stdout
    old = r"D:\ch3_libs\lib-v2\data\calibrated"
    assert src.count(old) == 1, "legacy raw path not found exactly once"
    mod = types.ModuleType("legacy_ingestion")
    mod.__file__ = str(ROOT / "Pipeline" / "optional_db_ingestion.py")
    exec(compile(src.replace(old, str(ROOT / "datasets" / "uploads")), "legacy_ingestion.py", "exec"), mod.__dict__)
    buf = __import__("io").StringIO()
    with contextlib.redirect_stdout(buf):
        mod.ingest_cleaned_datasets(str(ROOT / "datasets" / "processed_backup_20261020"), db_url=M.url(SERVER, DB))
    (OUT / "legacy_ingest.log").write_text(buf.getvalue(), encoding="utf-8")


def app_tables():
    sys.path.insert(0, str(ROOT / "core" / "server"))
    from sqlalchemy import create_engine
    from app.models.base import Base
    from app.models import user  # noqa: F401  registers app_users, api_keys, api_usage_log
    eng = create_engine(M.url(SERVER, DB).replace("postgresql://", "postgresql+psycopg2://"))
    Base.metadata.create_all(eng, tables=[Base.metadata.tables[t] for t in ["app_users", "api_keys", "api_usage_log"]])
    eng.dispose()
    with contextlib.closing(psycopg2.connect(M.url(SERVER, DB))) as c, c.cursor() as cur:
        cur.execute("""INSERT INTO app_users (email, username, hashed_password) VALUES
                       ('a@example.org', 'a', 'x'), ('b@example.org', 'b', 'y')""")
        cur.execute("""INSERT INTO api_keys (user_id, key_hash, key_prefix) VALUES
                       (1, repeat('a', 64), 'la_aaaa'), (2, repeat('b', 64), 'la_bbbb')""")
        cur.execute("""INSERT INTO api_usage_log (api_key_id, user_id, endpoint, status_code, request_params)
                       SELECT 1 + i % 2, 1 + i % 2, '/api/v1/public/spectra', 200, '{"limit": 5}'::jsonb
                       FROM generate_series(1, 5) i""")
        cur.execute("CREATE TABLE alembic_version (version_num varchar(32) PRIMARY KEY)")
        cur.execute("INSERT INTO alembic_version VALUES ('23fd4d2169a9')")
        c.commit()


def clean_count(db):
    with contextlib.closing(psycopg2.connect(M.url(SERVER, db))) as c, c.cursor() as cur:
        cur.execute("SELECT COUNT(*), COUNT(*) FILTER (WHERE measurement_id LIKE 'FI-20230825-104221-00-%') "
                    "FROM measurement_clean")
        return cur.fetchone()


def step(log, name, fn):
    t = time.time()
    r = fn()
    log[name] = {"seconds": round(time.time() - t, 1), "result": r}
    print(f"[{name}] {log[name]['seconds']} s")
    return r


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    if PGDATA.exists():
        shutil.rmtree(PGDATA)
    M.tool("initdb", "-D", str(PGDATA), "-U", "postgres", "-A", "trust", "-E", "UTF8")
    subprocess.run([str(M.PG_BIN / "pg_ctl"), "-D", str(PGDATA), "-o", f"-p {PORT} -c listen_addresses=localhost",
                    "-l", str(OUT / "postgres.log"), "-w", "start"], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)  # never capture: postmaster keeps the pipe
    s = {"cluster": f"throwaway, {M.tool('postgres', '--version').stdout.strip()}, port {PORT}",
         "legacy_source": f"git {LEGACY_COMMIT} ingestion on datasets/processed_backup_20261020"}
    try:
        step(s, "legacy_ingest", legacy_ingest)
        step(s, "app_tables_with_synthetic_rows", app_tables)
        pre = step(s, "snapshot_before", lambda: M.snapshot(SERVER, DB))
        s["legacy_clean_measurements"] = clean_count(DB)[0]
        step(s, "backup_and_restore_check", lambda: M.backup(SERVER, DB, OUT))
        step(s, "build_candidate", lambda: M.build(SERVER, DB, M.ROOT / "revision_v2" / "processed_run1",
                                                   ROOT / "datasets" / "uploads"))
        step(s, "verify_candidate", lambda: M.verify(SERVER, f"{DB}_v2", ROOT / "revision_v2" / "processed_run1"))
        step(s, "cutover", lambda: M.cutover(SERVER, DB))
        post = step(s, "verify_after_cutover", lambda: M.verify(SERVER, DB, ROOT / "revision_v2" / "processed_run1"))
        after = M.snapshot(SERVER, DB)
        s["app_tables_preserved"] = all(after["app_digests"][t] == pre["app_digests"][t] for t in pre["app_digests"])
        s["legacy_db_untouched"] = M.snapshot(SERVER, f"{DB}_legacy") == pre
        with contextlib.closing(psycopg2.connect(M.url(SERVER, DB))) as c, c.cursor() as cur:
            cur.execute("INSERT INTO app_users (email, username, hashed_password) VALUES ('c@example.org','c','z') "
                        "RETURNING id")
            s["new_user_id_after_cutover (sequence carried over, expect 3)"] = cur.fetchone()[0]
            c.rollback()
        s["clean_measurements_after_cutover"] = clean_count(DB)[0]
        step(s, "rollback", lambda: M.rollback(SERVER, DB))
        s["after_rollback_equals_pre_migration"] = M.snapshot(SERVER, DB) == pre
        step(s, "cutover_again", lambda: M.cutover(SERVER, DB))
        s["verify_after_second_cutover_passed"] = M.verify(SERVER, DB, ROOT / "revision_v2" / "processed_run1")["passed"]
        s["app_tables_preserved_after_second_cutover"] = M.snapshot(SERVER, DB)["app_digests"] == pre["app_digests"]
        s["not_rehearsed"] = ["Redis cache flush (no Redis server locally)", "API restart against the renamed DB",
                              "managed-hosting privileges (CREATEDB / ALTER DATABASE RENAME)"]
        s["all_checks_passed"] = bool(post["passed"] and s["app_tables_preserved"] and s["legacy_db_untouched"]
                                      and s["after_rollback_equals_pre_migration"]
                                      and s["verify_after_second_cutover_passed"]
                                      and s["app_tables_preserved_after_second_cutover"])
    finally:
        (OUT / "summary.json").write_text(json.dumps(s, indent=2, default=str))
        M.tool("pg_ctl", "-D", str(PGDATA), "-m", "fast", "-w", "stop")
        shutil.rmtree(PGDATA, ignore_errors=True)
        for d in OUT.glob("*.dump"):
            d.unlink()  # the rehearsal dump is large and contains nothing beyond the inputs
    print(json.dumps({k: v for k, v in s.items() if not isinstance(v, dict)}, indent=2, default=str))


if __name__ == "__main__":
    main()
