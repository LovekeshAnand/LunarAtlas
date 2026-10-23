#!/usr/bin/env python3
"""
Clean-checkout reproduction test. Clones the committed HEAD into revision_v2/_clean_checkout (git-ignored),
links the three external dataset folders (not in Git) into the clone, runs the README steps there, and
lists every tracked file the rerun changed (`git status` in the clone).

Skipped: step 6 (local benchmark; timings differ by nature, ~15 min) and step 9 (migration rehearsal;
run separately, see outputs/migration_rehearsal/). Writes outputs/clean_checkout/{report.json, environment.txt,
<step>.log}.
"""
import json
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLONE = ROOT / "revision_v2" / "_clean_checkout"
OUT = ROOT / "revision_v2" / "outputs" / "clean_checkout"
PY = sys.executable
STEPS = [
    ("1_audit", [PY, "revision_v2/audit_archive.py"], "."),
    ("2_determinism", [PY, "revision_v2/run_determinism.py"], "."),
    ("3_isolated_ingestion", [PY, "revision_v2/run_isolated_ingestion.py"], "."),
    ("4_analysis", [PY, "revision_v2/analysis.py"], "."),
    ("5_browser_downsampling", [PY, "browser_downsampling.py"], "revision_v2"),
    ("7_figures", [PY, "revision_v2/figures.py"], "."),
    ("8_tests", [PY, "-m", "pytest", "tests", "-q"], "."),
    ("10_paper", ["wsl", "-e", "bash", "-lc", "latexmk -pdf -interaction=nonstopmode -halt-on-error paper.tex"],
     "revision_v2/paper"),
]


def run(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    if CLONE.exists():
        for d in (CLONE / "datasets").glob("*"):  # drop the junctions themselves first, never their targets
            subprocess.run(["cmd", "/c", "rmdir", str(d)], check=True)
        shutil.rmtree(CLONE)
    head = run(["git", "rev-parse", "HEAD"], ROOT).stdout.strip()
    dirty = run(["git", "status", "--porcelain", "--untracked-files=no"], ROOT).stdout.strip()
    subprocess.run(["git", "clone", "--quiet", "--no-hardlinks", str(ROOT), str(CLONE)], check=True)
    subprocess.run(["git", "checkout", "--quiet", head], cwd=CLONE, check=True)
    (CLONE / "datasets").mkdir()
    for d in ["uploads", "processed", "processed_backup_20261020"]:  # inputs outside Git, linked read-only by use
        subprocess.run(["cmd", "/c", "mklink", "/J", str(CLONE / "datasets" / d), str(ROOT / "datasets" / d)],
                       check=True, capture_output=True)
    env = [f"commit {head}{' (working tree had uncommitted changes)' if dirty else ''}",
           f"python {platform.python_version()} ({PY})", f"platform {platform.platform()}"]
    for name, cmd in [("node", ["node", "--version"]),
                      ("postgres", [r"C:\Program Files\PostgreSQL\18\bin\postgres", "--version"]),
                      ("latexmk", ["wsl", "-e", "latexmk", "-v"])]:
        r = run(cmd, ROOT)
        env.append(f"{name} {(r.stdout or r.stderr).strip().splitlines()[0] if (r.stdout or r.stderr) else '?'}")
    pkgs = run([PY, "-m", "pip", "freeze"], ROOT).stdout
    env += [l for l in pkgs.splitlines() if l.split("==")[0].lower() in
            {"numpy", "pandas", "scipy", "matplotlib", "psycopg2", "psycopg2-binary", "requests", "pytest",
             "fastapi", "sqlalchemy"}]
    (OUT / "environment.txt").write_text("\n".join(env) + "\n", encoding="utf-8")

    report = {"commit": head, "steps": {}}
    for name, cmd, cwd in STEPS:
        t = time.time()
        r = run(cmd, CLONE / cwd)
        (OUT / f"{name}.log").write_text(r.stdout + r.stderr, encoding="utf-8")
        report["steps"][name] = {"returncode": r.returncode, "seconds": round(time.time() - t, 1)}
        print(name, r.returncode, report["steps"][name]["seconds"], "s", flush=True)
    report["tracked_files_changed_by_rerun"] = run(["git", "status", "--porcelain", "--untracked-files=no"],
                                                   CLONE).stdout.splitlines()
    (OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
