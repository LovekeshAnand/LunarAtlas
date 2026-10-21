#!/usr/bin/env python3
"""
Archive audit for the Chandrayaan-3 LIBS L1 copy in datasets/uploads (revision v2).

Independent of the pipeline code: re-reads every raw product, checks it against the
checksum/size/record count declared in its own PDS4 label, classifies every row by the
(Force Reset, Laser Fire) flags, replays the pairing rule, and reconciles the counts with
datasets/processed (current) and datasets/processed_backup_20261020 (pre-fix output).

Usage: python revision_v2/audit_archive.py
Writes revision_v2/outputs/archive_audit/*.csv|json
"""
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "datasets" / "uploads"
PROCESSED = {"current": ROOT / "datasets" / "processed",
             "backup_20261020": ROOT / "datasets" / "processed_backup_20261020"}
OUT = Path(__file__).resolve().parent / "outputs" / "archive_audit"
TRAILING = ['Delay Time', 'Integration Time', 'Number of Pulses', 'X Factor',
            'Laser Energy', 'Laser Pump Current', 'PRR', 'On Off Status']
OBS_RE = re.compile(r'^ch3_lib_\d{3}_\d{8}T\d{6}_\d{2}_l1$')


def md5(p):
    return hashlib.md5(p.read_bytes()).hexdigest()


def label_fields(xml_path):
    x = xml_path.read_text(encoding='utf-8')
    get = lambda t: re.findall(rf'<{t}[^>]*>([^<]*)</{t}>', x)
    return {'label_md5': (get('md5_checksum') or [None])[0],
            'label_file_size': int((get('file_size') or [-1])[0]),
            'label_records': int((get('records') or [-1])[0]),
            'label_file_name': (get('file_name') or [None])[0],
            'logical_identifier': (get('logical_identifier') or [None])[0],
            'start_date_time': (get('start_date_time') or [None])[0],
            'stop_date_time': (get('stop_date_time') or [None])[0]}


def check_file(csv_path):
    xml_path = csv_path.with_suffix('.xml')
    rec = {'file': csv_path.relative_to(RAW).as_posix(), 'xml_present': xml_path.exists(),
           'actual_md5': md5(csv_path), 'actual_size': csv_path.stat().st_size}
    if rec['xml_present']:
        rec.update(label_fields(xml_path))
        rec['md5_match'] = rec['actual_md5'] == rec['label_md5']
        rec['size_match'] = rec['actual_size'] == rec['label_file_size']
    return rec


def replay_pairing(df):
    """Row-level replay of the documented rule (independent re-implementation)."""
    wl_cols = df.columns[6:-8]
    rows, last_bg, last_bg_row, plasma_idx = [], None, None, 0
    for i, r in df.iterrows():
        f, l = r['Force Reset Status'], r['Laser Fire Status']
        rec = {'row': i + 1, 'F': f, 'L': l, 'time': r['Time'],
               'laser_energy': r['Laser Energy'],
               'n_nan_intensity': int(r[wl_cols].isna().sum())}
        if pd.isna(f) or pd.isna(l):
            rec['cls'] = 'nan_status'
        elif (int(f), int(l)) == (1, 0):
            rec['cls'] = 'background'
            if rec['n_nan_intensity'] == 0:
                last_bg, last_bg_row = r, i + 1
        elif (int(f), int(l)) == (0, 1):
            plasma_idx += 1
            rec['cls'] = 'plasma'
            rec['plasma_index'] = plasma_idx
            rec['paired'] = last_bg is not None
            if last_bg is not None:
                rec['bg_row'] = last_bg_row
                rec['bg_immediately_preceding'] = last_bg_row == i
                t0, t1 = pd.to_datetime(last_bg['Time']), pd.to_datetime(r['Time'])
                rec['pair_gap_s'] = (t1 - t0).total_seconds()
        else:
            rec['cls'] = 'ambiguous'
        # rule used by optional_db_ingestion.py for measurement_raw IDs
        lfs = 0 if pd.isna(l) else int(l)
        le = 0.0 if pd.isna(r['Laser Energy']) else float(r['Laser Energy'])
        rec['ingest_rule_plasma'] = (lfs == 1) or (le > 0.0)
        rows.append(rec)
    return rows


def processed_counts(base, rel_obs):
    f = base / "calibrated" / rel_obs / f"{Path(rel_obs).name}_cleaned.csv"
    if not f.exists():
        return {'cleaned_file': False, 'n_meas': 0, 'n_points': 0, 'mids': ''}
    d = pd.read_csv(f)
    mids = sorted(d['Measurement_ID'].unique().tolist())
    # older outputs have no Background_Subtracted column -> status not recorded (NaN)
    nbs = (int(d.groupby('Measurement_ID')['Background_Subtracted'].first().eq(False).sum())
           if 'Background_Subtracted' in d else np.nan)
    return {'cleaned_file': True, 'n_meas': len(mids), 'n_points': len(d),
            'n_meas_not_bg_subtracted': nbs, 'columns': ';'.join(d.columns), 'mids': ';'.join(map(str, mids))}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    date_dirs = sorted(d for d in RAW.iterdir() if d.is_dir() and re.fullmatch(r'\d{8}', d.name))
    obs_dirs = [o for d in date_dirs for o in sorted(d.iterdir()) if o.is_dir() and OBS_RE.match(o.name)]
    other_dirs = [o for d in date_dirs for o in d.iterdir() if o.is_dir() and not OBS_RE.match(o.name)]

    files, products, rows_all, subfile_checks = [], [], [], []
    ref_axis = None
    for o in obs_dirs:
        parent = o / f"{o.name}.csv"
        subs = sorted(p for p in o.glob('*.csv') if p != parent)
        for p in [parent] + subs:
            files.append({**check_file(p), 'kind': 'parent' if p == parent else 'subfile'})
        prod = {'product': o.name, 'date': o.parent.name, 'n_subfiles': len(subs)}
        try:
            df = pd.read_csv(parent)
        except Exception as e:
            prod.update(status='failed', error=str(e)); products.append(prod); continue
        wl = np.array([float(c) for c in df.columns[6:-8]])
        if ref_axis is None:
            ref_axis = wl
        prod.update(status='parsed', n_rows=len(df), n_channels=len(wl),
                    trailing_ok=df.columns[-8:].tolist() == TRAILING,
                    axis_identical=bool(len(wl) == len(ref_axis) and np.array_equal(wl, ref_axis)),
                    axis_monotonic=bool(np.all(np.diff(wl) > 0)),
                    wl_min=wl.min(), wl_max=wl.max())
        rr = replay_pairing(df)
        for r in rr:
            r['product'] = o.name
        rows_all += rr
        cls = pd.Series([r['cls'] for r in rr])
        pl = [r for r in rr if r['cls'] == 'plasma']
        prod.update(n_background=int((cls == 'background').sum()), n_plasma=len(pl),
                    n_ambiguous=int((cls == 'ambiguous').sum()), n_nan_status=int((cls == 'nan_status').sum()),
                    n_paired=sum(r['paired'] for r in pl), n_unpaired=sum(not r['paired'] for r in pl),
                    n_ingest_rule_plasma=sum(r['ingest_rule_plasma'] for r in rr),
                    n_rows_nan_intensity=sum(r['n_nan_intensity'] > 0 for r in rr),
                    dup_timestamps=int(df['Time'].duplicated().sum()))
        # Subfiles are long-form (Wavelength, Response count) single-shot tables:
        # which parent row carries identical counts, and how does their wavelength axis compare?
        parent_vals = df.iloc[:, 6:-8].to_numpy(float)
        for s in subs:
            sd = pd.read_csv(s)
            v = sd.iloc[:, 1].to_numpy(float)
            sw = sd.iloc[:, 0].to_numpy(float)
            same = (len(v) == parent_vals.shape[1]) and np.isclose(parent_vals, v, equal_nan=True).all(axis=1)
            hits = (np.where(same)[0] + 1).tolist() if len(v) == parent_vals.shape[1] else []
            m = re.search(r'_(\d+)_(\d+)$', s.stem)
            b = int(m.group(2)) if m else None
            row_cls = rr[b - 1]['cls'] if b and b <= len(rr) else None
            dw = sw - wl if len(sw) == len(wl) else np.full(1, np.nan)
            subfile_checks.append({'product': o.name, 'subfile': s.name, 'sub_rows': len(sd),
                                   'name_a': int(m.group(1)) if m else None, 'name_b': b,
                                   'parent_rows_with_identical_counts': ';'.join(map(str, hits)),
                                   'name_b_row_matches': b in hits, 'parent_row_class': row_cls,
                                   'sub_wl_min': sw.min(), 'sub_wl_max': sw.max(),
                                   'dw_min': float(np.nanmin(dw)), 'dw_max': float(np.nanmax(dw)),
                                   'dw_at_220': float(np.interp(220, wl, dw)) if dw.size > 1 else np.nan,
                                   'dw_at_589': float(np.interp(589, wl, dw)) if dw.size > 1 else np.nan,
                                   'dw_at_800': float(np.interp(800, wl, dw)) if dw.size > 1 else np.nan})
        for name, base in PROCESSED.items():
            pc = processed_counts(base, f"{o.parent.name}/{o.name}")
            prod.update({f"{name}_{k}": v for k, v in pc.items()})
        products.append(prod)

    fdf, pdf, rdf, sdf = map(pd.DataFrame, (files, products, rows_all, subfile_checks))
    fdf.to_csv(OUT / 'input_manifest.csv', index=False)
    pdf.to_csv(OUT / 'products.csv', index=False)
    rdf.to_csv(OUT / 'rows.csv', index=False)
    sdf.to_csv(OUT / 'subfiles.csv', index=False)

    pl = rdf[rdf.cls == 'plasma']
    # Measurement IDs as built by ingestion: {file_info_id}-{plasma_index}
    gid = pl['product'] + '-' + pl['plasma_index'].astype(int).astype(str)
    s = {
        'generated_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'raw_root': str(RAW.relative_to(ROOT)),
        'archive': 'PRADAN ch3 LIBS calibrated (lib-v2), local copy; original mount D:/ch3_libs no longer present',
        'raw_copy_mtime_range': [min(datetime.fromtimestamp(p.stat().st_mtime).isoformat(timespec='seconds') for p in RAW.rglob('*.csv')),
                                 max(datetime.fromtimestamp(p.stat().st_mtime).isoformat(timespec='seconds') for p in RAW.rglob('*.csv'))],
        'label_creation_date_time': sorted(set(re.findall(r'<creation_date_time>([^<]*)<', ''.join(
            (o / f"{o.name}.xml").read_text(encoding='utf-8') for o in obs_dirs)))),
        'date_folders': len(date_dirs), 'unexpected_dirs': [str(d) for d in other_dirs],
        'products_discovered': len(obs_dirs),
        'products_parsed': int((pdf.status == 'parsed').sum()),
        'products_failed': int((pdf.status != 'parsed').sum()),
        'csv_files': len(fdf), 'parent_csv': int((fdf.kind == 'parent').sum()), 'subfile_csv': int((fdf.kind == 'subfile').sum()),
        'xml_missing': int((~fdf.xml_present).sum()),
        'md5_vs_label_checked': int(fdf.md5_match.notna().sum()), 'md5_vs_label_pass': int(fdf.md5_match.sum()),
        'size_vs_label_pass': int(fdf.size_match.sum()),
        'parent_records_vs_label_pass': int((pdf.n_rows.values == [label_fields(RAW / p.date / p.product / f"{p.product}.xml")['label_records'] for p in pdf.itertuples()]).sum()),
        'channels_expected': 2094,
        'products_with_2094_channels': int((pdf.n_channels == 2094).sum()),
        'products_axis_identical': int(pdf.axis_identical.sum()),
        'products_trailing_ok': int(pdf.trailing_ok.sum()),
        'rows_total': len(rdf),
        'rows_background': int((rdf.cls == 'background').sum()),
        'rows_plasma': len(pl),
        'rows_ambiguous': int((rdf.cls == 'ambiguous').sum()),
        'rows_nan_status': int((rdf.cls == 'nan_status').sum()),
        'rows_with_nan_intensity': int((rdf.n_nan_intensity > 0).sum()),
        'plasma_paired': int(pl.paired.sum()), 'plasma_unpaired': int((~pl.paired.astype(bool)).sum()),
        'paired_bg_immediately_preceding': int(pl.bg_immediately_preceding.fillna(False).astype(bool).sum()),
        'pair_gap_s_counts': {str(k): int(v) for k, v in pl.pair_gap_s.value_counts(dropna=True).sort_index().items()},
        'rows_plasma_by_ingest_rule': int(rdf.ingest_rule_plasma.sum()),
        'ingest_rule_vs_flag_rule_disagreements': int((rdf.ingest_rule_plasma != (rdf.cls == 'plasma')).sum()),
        'products_bg_only': int(((pdf.n_plasma == 0) & (pdf.n_background > 0)).sum()),
        'products_all_plasma_unpaired': int(((pdf.n_plasma > 0) & (pdf.n_paired == 0)).sum()),
        'products_with_paired_output_expected': int((pdf.n_paired > 0).sum()),
        'duplicate_logical_identifiers': int(fdf[fdf.kind == 'parent'].logical_identifier.duplicated().sum()),
        'duplicate_global_measurement_ids': int(gid.duplicated().sum()),
        'products_with_duplicate_timestamps': int((pdf.dup_timestamps > 0).sum()),
        'subfiles_whose_counts_match_parent_row_named_by_suffix': int(sdf.name_b_row_matches.sum()),
        'subfile_name_a_vs_row_class': {f'{a}/{c}': int(n) for (a, c), n in sdf.groupby(['name_a', 'parent_row_class']).size().items()},
        'subfile_wavelength_axes_distinct': int(sdf[['sub_wl_min', 'sub_wl_max']].drop_duplicates().shape[0]),
        'subfile_minus_parent_wavelength_nm': {k: [round(float(sdf[k].min()), 3), round(float(sdf[k].max()), 3)]
                                               for k in ['dw_min', 'dw_max', 'dw_at_220', 'dw_at_589', 'dw_at_800']},
    }
    for name in PROCESSED:
        s[f'{name}_cleaned_files'] = int(pdf[f'{name}_cleaned_file'].sum())
        s[f'{name}_measurements'] = int(pdf[f'{name}_n_meas'].sum())
        s[f'{name}_points'] = int(pdf[f'{name}_n_points'].sum())
        s[f'{name}_meas_not_bg_subtracted'] = int(pdf[f'{name}_n_meas_not_bg_subtracted'].fillna(0).sum())
        s[f'{name}_meas_vs_replay_paired_mismatch_products'] = int((pdf[f'{name}_n_meas'] != pdf.n_paired).sum())
    (OUT / 'summary.json').write_text(json.dumps(s, indent=2, default=str))
    print(json.dumps(s, indent=2, default=str))


if __name__ == '__main__':
    sys.exit(main())
