"""Point 1/2: independent archive count from the raw PRADAN files (stdlib only, read-only).

Parent table = <product>_l1.csv; every .csv (parent and single-shot) is checked against the MD5 and
size in its PDS4 label (label checksums printed without leading zeros are left-padded to 32 digits).
Flags: background (F=1,L=0), plasma (F=0,L=1). Pairing = most recent preceding background row.

usage: archive_count.py <datasets/uploads>
"""
import sys, csv, re, hashlib, math
from pathlib import Path
from collections import Counter

root = Path(sys.argv[1])
c = Counter()
axes, md5_bad, size_bad = set(), [], []
kinds = Counter()


def label_info(xml: Path, data_name: str):
    t = xml.read_text(encoding="utf-8", errors="replace")
    i = t.find(f"<file_name>{data_name}</file_name>")
    seg = t[i:i + 2000] if i >= 0 else t
    m = re.search(r"<md5_checksum>\s*([0-9a-fA-F]+)\s*</md5_checksum>", seg)
    s = re.search(r"<file_size[^>]*>\s*(\d+)\s*</file_size>", seg)
    return (m.group(1).lower().zfill(32) if m else None, int(s.group(1)) if s else None)


days = sorted(p.name for p in root.iterdir() if p.is_dir())
for csv_path in sorted(root.rglob("*.csv")):
    c["data_files"] += 1
    xml = csv_path.with_suffix(".xml")
    md5, size = label_info(xml, csv_path.name) if xml.exists() else (None, None)
    b = csv_path.read_bytes()
    if md5 is None or hashlib.md5(b).hexdigest() != md5: md5_bad.append(csv_path.name)
    if size is None or size != len(b): size_bad.append(csv_path.name)
    if not csv_path.name.endswith("_l1.csv"):
        continue  # single-shot file
    c["products"] += 1
    try:
        rows = list(csv.reader(b.decode("utf-8").splitlines()))
        hdr, data = rows[0], rows[1:]
        wl = hdr[6:-8]
        float(wl[0]); float(wl[-1])
        axes.add((len(wl), wl[0], wl[-1]))
    except Exception as e:
        c["products_failed"] += 1
        print("FAIL", csv_path.name, e)
        continue
    have_bg, n_pair, n_unp, n_bg = False, 0, 0, 0
    for r in data:
        c["acquisitions"] += 1
        F, L = r[4].strip(), r[5].strip()
        if any(not v.strip() or math.isnan(float(v)) for v in r[6:-8]): c["rows_with_nan"] += 1
        if (F, L) == ("1", "0"):
            n_bg += 1; have_bg = True
        elif (F, L) == ("0", "1"):
            c["plasma"] += 1
            if have_bg: n_pair += 1
            else: n_unp += 1
        else:
            c[f"flags_other_{F}{L}"] += 1
    c["background"] += n_bg; c["paired"] += n_pair; c["unpaired"] += n_unp
    if n_pair: kinds["with paired plasma"] += 1
    elif n_bg and not n_unp: kinds["background only"] += 1
    elif n_unp: kinds["plasma, none paired"] += 1
    else: kinds["other"] += 1

print("day folders:", len(days), days[0], "...", days[-1])
for k, v in sorted(c.items()): print(f"{k}: {v}")
print("rows_with_nan:", c["rows_with_nan"])
print("wavelength axes (n, first, last):", axes)
print("md5 mismatch vs label (after zero-pad):", len(md5_bad), md5_bad[:5])
print("size mismatch vs label:", len(size_bad), size_bad[:5])
print("products by kind:", dict(kinds))
