import datetime as dt
from unittest.mock import patch

from harlequin.export import (
    default_export_filename,
    export_path_matches_default_generated_stem,
    next_default_export_path,
)


def test_default_export_filename_pattern() -> None:
    with patch("harlequin.export.datetime") as m_dt:
        m_dt.now.return_value = dt.datetime(2025, 5, 5, 14, 30, 22, 456000)
        assert default_export_filename("csv") == "20250505T143022.456.out.csv"
        assert default_export_filename("md") == "20250505T143022.456.out.md"
        assert default_export_filename(".parquet") == "20250505T143022.456.out.parquet"


def test_export_path_matches_default_generated_stem() -> None:
    assert export_path_matches_default_generated_stem("")
    assert export_path_matches_default_generated_stem(
        "/tmp/20250505T143022.456.out.csv"
    )
    assert not export_path_matches_default_generated_stem("/tmp/manual_name.csv")


def test_next_default_export_path() -> None:
    p = "/data/20250505T143022.456.out.csv"
    assert next_default_export_path(p, "parquet") == (
        "/data/20250505T143022.456.out.parquet"
    )
    with patch("harlequin.export.datetime") as m_dt:
        m_dt.now.return_value = dt.datetime(2025, 5, 5, 14, 30, 22, 456000)
        expected_md = "20250505T143022.456.out.md"
        assert (
            next_default_export_path("/data/myfile.csv", "md")
            == f"/data/{expected_md}"
        )
