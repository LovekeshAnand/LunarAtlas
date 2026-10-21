"""
Stage-2 plasma/background pairing on a synthetic L1 file, run through the real
L1DataProcessor. Plasma shots without a preceding background must be excluded,
and Measurement_ID must keep the plasma sequence index so cleaned rows stay
linked to measurement_raw ({file_info_id}-{plasma_count}).

Run with: pytest tests/ -v
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "Pipeline"))
from step2_process_l1_data import EXPECTED_TRAILING_COLS, L1DataProcessor  # noqa: E402

WAVELENGTHS = ["300.0", "300.34", "300.68"]


def write_l1(folder: Path, rows):
    """rows: list of (force_reset, laser_fire, [intensities])."""
    folder.mkdir(parents=True)
    records = []
    for i, (frs, lfs, spectrum) in enumerate(rows):
        rec = {"Time": f"2023-08-25T10:42:{i:02d}", "Measurement Count": i + 1,
               "Operation Mode": "ASLF", "Measurement Type": "L",
               "Force Reset Status": frs, "Laser Fire Status": lfs}
        rec.update(dict(zip(WAVELENGTHS, spectrum)))
        rec.update({c: 1 for c in EXPECTED_TRAILING_COLS})
        records.append(rec)
    csv = folder / "ch3_lib_999_20230825T104221_00_l1.csv"
    pd.DataFrame(records).to_csv(csv, index=False)
    xml = csv.with_suffix(".xml")
    xml.write_text("<Product_Observational/>", encoding="utf-8")
    return csv, xml


def run(tmp_path, rows):
    csv, xml = write_l1(tmp_path / "raw", rows)
    out = tmp_path / "out"
    proc = L1DataProcessor(tmp_path / "raw", out)
    proc.clean_libs_pair(csv, xml, out)
    cleaned = out / f"{csv.stem}_cleaned.csv"
    return proc, (pd.read_csv(cleaned) if cleaned.exists() else None)


def test_unpaired_plasma_excluded_and_ids_keep_plasma_index(tmp_path):
    bg, plasma = [10, 10, 10], [50, 5, 30]
    proc, df = run(tmp_path, [(0, 1, plasma),   # plasma 1: no background yet → excluded
                              (1, 0, bg),
                              (0, 1, plasma),   # plasma 2
                              (0, 1, plasma)])  # plasma 3 (reuses last background)
    assert proc.stats["plasma_no_background"] == 1
    assert sorted(df["Measurement_ID"].unique()) == [2, 3]
    assert df["Background_Subtracted"].all()
    m2 = df[df["Measurement_ID"] == 2].sort_values("Wavelength_nm")["Cleaned_Intensity"].tolist()
    assert m2 == [40, 0, 20]   # max(0, P - B)


def test_file_without_any_background_writes_no_output(tmp_path):
    proc, df = run(tmp_path, [(0, 1, [50, 5, 30]), (0, 1, [60, 6, 31])])
    assert df is None
    assert proc.stats["plasma_no_background"] == 2
    assert proc.stats["plasma_only_files"] == 1


def test_clip_fraction_counts_negative_residuals_before_clamping(tmp_path):
    # residuals: +40, 0 (exact match, not clipping), -5 -> clamped
    proc, df = run(tmp_path, [(1, 0, [10, 10, 10]), (0, 1, [50, 10, 5])])
    params = pd.read_csv(tmp_path / "out" / "ch3_lib_999_20230825T104221_00_l1_instrument_params.csv")
    assert params["Clip_Fraction"].tolist() == [round(1 / 3, 4)]
    assert df.sort_values("Wavelength_nm")["Cleaned_Intensity"].tolist() == [40, 0, 0]


def test_background_row_records_last_preceding_background(tmp_path):
    proc, df = run(tmp_path, [(1, 0, [10, 10, 10]),   # row 1
                              (1, 0, [20, 20, 20]),   # row 2: last background wins
                              (0, 1, [50, 50, 50]),   # row 3 -> paired with row 2
                              (0, 1, [60, 60, 60])])  # row 4 -> still row 2
    params = pd.read_csv(tmp_path / "out" / "ch3_lib_999_20230825T104221_00_l1_instrument_params.csv")
    assert params["Background_Row"].tolist() == [2, 2]
    m1 = df[df["Measurement_ID"] == 1]["Cleaned_Intensity"].tolist()
    assert m1 == [30, 30, 30]


def test_ambiguous_flags_are_skipped_and_do_not_consume_plasma_index(tmp_path):
    proc, df = run(tmp_path, [(1, 0, [10, 10, 10]),
                              (1, 1, [99, 99, 99]),   # ambiguous
                              (0, 0, [99, 99, 99]),   # ambiguous
                              (0, 1, [50, 50, 50])])
    assert proc.stats["ambiguous_rows"] == 2
    assert df["Measurement_ID"].unique().tolist() == [1]
