"""Point 2: run stage 2 twice on the full archive and compare outputs byte by byte; also compare the
cleaned CSVs with datasets/processed (the output production was ingested from).
Metadata JSON is compared field by field (it carries a processing timestamp).

usage: determinism_check.py <repo> <datasets/uploads> <work_dir outside the repo>
"""
import sys, json, hashlib, subprocess
from pathlib import Path
from collections import Counter

repo, raw, work = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
for i in (1, 2):
    r = subprocess.run([sys.executable, str(repo / "Pipeline" / "step2_process_l1_data.py"), raw, str(work / f"run{i}")],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    (work / f"run{i}.log").write_text(r.stdout + r.stderr, encoding="utf-8")
    print(f"run{i}: exit {r.returncode}")
    print("\n".join(l for l in r.stdout.splitlines() if ":" in l and l.strip()[:1].isupper() and "[" not in l)[-900:])
    print("label checksum errors in log:", sum("does not match the MD5" in l for l in r.stdout.splitlines()),
          "| labels without checksum:", sum("No MD5 checksum in label" in l for l in r.stdout.splitlines()))

md5 = lambda p: hashlib.md5(p.read_bytes()).hexdigest()
f1 = {p.relative_to(work / "run1"): p for p in (work / "run1").rglob("*") if p.is_file()}
kinds, differ, json_fields = Counter(), Counter(), Counter()
for rel, p in f1.items():
    q = work / "run2" / rel
    kind = p.name.split("_l1")[-1]
    kinds[kind] += 1
    if not q.exists() or md5(p) != md5(q):
        differ[kind] += 1
        if p.suffix == ".json":
            a, b = json.loads(p.read_text()), json.loads(q.read_text())
            for k in set(a) | set(b):
                if a.get(k) != b.get(k): json_fields[k] += 1
print("files per kind:", dict(kinds))
print("differing between runs:", dict(differ), "| differing JSON fields:", dict(json_fields))

proc = {p.name: p for p in (repo / "datasets" / "processed").rglob("*_cleaned.csv")}
n = d = 0
for rel, p in f1.items():
    if p.name.endswith("_cleaned.csv") and p.name in proc:
        n += 1; d += md5(p) != md5(proc[p.name])
print(f"cleaned CSVs vs datasets/processed: compared {n}, differing {d}")
