from __future__ import annotations

import html
import json
import re
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Generator, Iterator, Protocol

from textual_fastdatatable.backend import ArrowBackend

from harlequin.exception import HarlequinCopyError

if TYPE_CHECKING:
    import pyarrow as pa

    from harlequin.components.results_viewer import ResultsTable

_DEFAULT_FILENAME_STEM_RE = re.compile(
    r"^[0-9]{8}T[0-9]{6}\.[0-9]{3}\.out\.(?P<suffix>[A-Za-z0-9_-]+)$"
)


def default_export_filename(format_suffix: str) -> str:
    """
    Default export basename: ``{YYYYMMDDThhmmss.mmm}.out.{suffix}`` using local time
    and three-digit milliseconds (no timezone suffix in the stem).
    """
    clean = format_suffix.lstrip(".")
    now = datetime.now()
    ms = now.microsecond // 1000
    prefix = now.strftime("%Y%m%dT%H%M%S") + f".{ms:03d}"
    return f"{prefix}.out.{clean}"


class ExporterCallable(Protocol):
    def __call__(self, data: "pa.Table", dest_path: str, **kwargs: Any) -> None: ...


def copy(
    table: "ResultsTable", path: Path, format_name: str, options: dict[str, Any]
) -> None:
    if table.row_count == 0:
        raise HarlequinCopyError("Cannot export empty table.")

    assert isinstance(table.backend, ArrowBackend)
    if table.plain_column_labels:
        # Arrow allows duplicate field names, but DuckDB will typically throw an error
        # when trying to export CSV, JSON, or PQ files with those dupe field names.
        export_names: list[str] = []
        for label in table.plain_column_labels:
            export_label = label
            n = 0
            while export_label in export_names:
                export_label = f"{label}_{n}"
                n += 1
            export_names.append(export_label)
        data = table.backend.source_data.rename_columns(export_names)
    else:
        data = table.backend.source_data

    dest_path = str(path.expanduser())
    # only include options that aren't None/Empty
    kwargs = {k: v for k, v in options.items() if v}
    exporters: dict[str, ExporterCallable] = {
        "csv": _export_csv,
        "tsv": _export_tsv,
        "parquet": _export_parquet,
        "json": _export_json,
        "jsonl": _export_jsonl,
        "markdown": _export_markdown,
        "html": _export_html,
        "excel": _export_excel,
        "iceberg": _export_iceberg,
        "arrow": _export_arrow_ipc,
        "duckdb": _export_duckdb_file,
        "orc": _export_orc,
        "feather": _export_feather,
    }
    try:
        exporter = exporters[format_name]
    except KeyError as e:
        raise HarlequinCopyError(
            f"Unknown export format {format_name!r}.",
            title="Unsupported export format",
        ) from e
    exporter(data, dest_path, **kwargs)


def _export_csv(
    data: "pa.Table",
    dest_path: str,
    **kwargs: Any,
) -> None:
    import duckdb

    if kwargs.get("quoting"):
        kwargs["quoting"] = "ALL"
    if "header" not in kwargs:
        kwargs["header"] = False
    try:
        relation = duckdb.arrow(data)
        relation.write_csv(file_name=dest_path, **kwargs)
    except (duckdb.Error, OSError) as e:
        raise HarlequinCopyError(
            str(e),
            title=("DuckDB raised an error when writing your query to a CSV file."),
        ) from e


def _export_tsv(
    data: "pa.Table",
    dest_path: str,
    **kwargs: Any,
) -> None:
    if "sep" not in kwargs:
        kwargs["sep"] = "\t"
    _export_csv(data, dest_path, **kwargs)


def _export_parquet(
    data: "pa.Table",
    dest_path: str,
    **kwargs: Any,
) -> None:
    import duckdb

    try:
        relation = duckdb.arrow(data)
        relation.write_parquet(
            file_name=dest_path, compression=kwargs.get("compression")
        )
    except (duckdb.Error, OSError) as e:
        raise HarlequinCopyError(
            str(e),
            title=("DuckDB raised an error when writing your query to a Parquet file."),
        ) from e


def _resolve_text_compression(dest_path: str, compression: str | None) -> str:
    comp = (compression or "auto").lower()
    if comp not in ("auto", "", "detect"):
        if comp == "uncompressed":
            return "none"
        return comp
    lower = dest_path.lower()
    if lower.endswith(".gz"):
        return "gzip"
    if lower.endswith(".zst") or lower.endswith(".zstd"):
        return "zstd"
    return "none"


@contextmanager
def _utf8_text_writer(dest_path: str, compression: str) -> Iterator[Any]:
    comp = compression.lower()
    if comp in ("none", "uncompressed"):
        with open(dest_path, "w", encoding="utf-8") as f:
            yield f
    elif comp == "gzip":
        import gzip

        with gzip.open(dest_path, "wt", encoding="utf-8") as f:
            yield f
    elif comp == "zstd":
        try:
            import zstandard as zstd
        except ImportError as e:
            raise HarlequinCopyError(
                "Writing zstd-compressed JSON requires the optional 'zstandard' "
                "package. Install it or choose gzip / no compression.",
                title="Missing dependency",
            ) from e
        with zstd.open(dest_path, mode="wt", encoding="utf-8") as f:
            yield f
    else:
        raise HarlequinCopyError(
            f"Unsupported JSON compression mode {compression!r}.",
            title="Unsupported compression",
        )


def _make_json_default(date_format: str | None, timestamp_format: str | None):
    import datetime as dt
    import decimal

    df = date_format or ""
    tf = timestamp_format or ""

    def default(obj: object) -> Any:
        if isinstance(obj, dt.datetime):
            if tf:
                return obj.strftime(tf)
            return obj.isoformat(sep=" ", timespec="milliseconds")
        if isinstance(obj, dt.date):
            return obj.strftime(df) if df else obj.isoformat()
        if isinstance(obj, dt.time):
            return obj.isoformat()
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        if isinstance(obj, (bytes, bytearray)):
            return obj.decode("utf-8", errors="replace")
        try:
            import numpy as np

            if isinstance(obj, np.generic):
                return obj.item()
        except ImportError:
            pass
        return str(obj)

    return default


def _iter_row_dicts(data: "pa.Table") -> Generator[dict[str, Any], None, None]:
    columns = data.column_names
    for batch in data.to_batches():
        pyd = batch.to_pydict()
        n = batch.num_rows
        for i in range(n):
            yield {c: pyd[c][i] for c in columns}


def _export_json(
    data: "pa.Table",
    dest_path: str,
    **kwargs: Any,
) -> None:
    array = bool(kwargs.get("array"))
    compression = _resolve_text_compression(
        dest_path, kwargs.get("compression") or "auto"
    )
    default = _make_json_default(
        kwargs.get("date_format"),
        kwargs.get("timestamp_format"),
    )
    try:
        with _utf8_text_writer(dest_path, compression) as fh:
            if array:
                fh.write("[")
                first = True
                for row in _iter_row_dicts(data):
                    if not first:
                        fh.write(",")
                    json.dump(row, fh, ensure_ascii=False, default=default)
                    first = False
                fh.write("]")
            else:
                for row in _iter_row_dicts(data):
                    json.dump(row, fh, ensure_ascii=False, default=default)
                    fh.write("\n")
    except HarlequinCopyError:
        raise
    except OSError as e:
        raise HarlequinCopyError(
            str(e),
            title=("Harlequin could not write your JSON file."),
        ) from e


def _export_jsonl(
    data: "pa.Table",
    dest_path: str,
    **kwargs: Any,
) -> None:
    kw = {k: v for k, v in kwargs.items() if k != "array"}
    _export_json(data, dest_path, array=False, **kw)


def _md_escape_cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def _export_markdown(
    data: "pa.Table",
    dest_path: str,
    **kwargs: Any,
) -> None:
    del kwargs
    headers = [_md_escape_cell(str(h)) for h in data.column_names]
    try:
        with open(dest_path, "w", encoding="utf-8") as fh:
            fh.write("| " + " | ".join(headers) + " |\n")
            fh.write("| " + " | ".join("---" for _ in headers) + " |\n")
            for row in _iter_row_dicts(data):
                cells = []
                for name in data.column_names:
                    val = row.get(name)
                    if val is None:
                        cells.append("")
                    else:
                        cells.append(_md_escape_cell(str(val)))
                fh.write("| " + " | ".join(cells) + " |\n")
    except OSError as e:
        raise HarlequinCopyError(
            str(e),
            title=("Harlequin could not write your Markdown file."),
        ) from e


def _export_html(
    data: "pa.Table",
    dest_path: str,
    **kwargs: Any,
) -> None:
    del kwargs
    headers = data.column_names
    parts = [
        "<!DOCTYPE html>",
        '<meta charset="utf-8">',
        "<table>\n<thead><tr>",
    ]
    for h in headers:
        parts.append(f"<th>{html.escape(str(h))}</th>")
    parts.append("</tr></thead>\n<tbody>")
    try:
        for row in _iter_row_dicts(data):
            parts.append("<tr>")
            for name in headers:
                val = row.get(name)
                if val is None:
                    parts.append("<td></td>")
                else:
                    parts.append(f"<td>{html.escape(str(val))}</td>")
            parts.append("</tr>")
        parts.append("</tbody>\n</table>\n")
        Path(dest_path).write_text("\n".join(parts), encoding="utf-8")
    except OSError as e:
        raise HarlequinCopyError(
            str(e),
            title=("Harlequin could not write your HTML file."),
        ) from e


def _export_excel(
    data: "pa.Table",
    dest_path: str,
    **kwargs: Any,
) -> None:
    try:
        from openpyxl import Workbook
    except ImportError as e:
        raise HarlequinCopyError(
            "Excel export requires openpyxl. "
            "It is included with the default harlequin install.",
            title="Missing dependency",
        ) from e

    sheet_name = str(kwargs.get("sheet_name") or "Results")
    invalid = '[]:*?/\\'
    title = "".join(c for c in sheet_name if c not in invalid)[:31] or "Results"
    try:
        wb = Workbook(write_only=True)
        ws = wb.create_sheet(title=title)
        headers = list(data.column_names)
        ws.append(headers)
        for batch in data.to_batches():
            pyd = batch.to_pydict()
            n = batch.num_rows
            for i in range(n):
                ws.append([pyd[col][i] for col in headers])
        wb.save(dest_path)
    except Exception as e:
        raise HarlequinCopyError(
            str(e),
            title=("Harlequin could not write your Excel file."),
        ) from e


def _export_iceberg(
    data: "pa.Table",
    dest_path: str,
    **kwargs: Any,
) -> None:
    _export_parquet(data, dest_path, **kwargs)


def _export_arrow_ipc(
    data: "pa.Table",
    dest_path: str,
    **kwargs: Any,
) -> None:
    del kwargs
    import pyarrow as pa_module
    import pyarrow.ipc as ipc
    import pyarrow.lib as pl

    try:
        with pa_module.OSFile(str(dest_path), "wb") as sink:
            with ipc.new_file(sink, data.schema) as writer:
                writer.write_table(data)
    except (pl.ArrowException, OSError, IOError, TypeError) as e:
        raise HarlequinCopyError(
            str(e),
            title=("Arrow raised an error when writing your Arrow IPC file."),
        ) from e


def _export_duckdb_file(
    data: "pa.Table",
    dest_path: str,
    **kwargs: Any,
) -> None:
    del kwargs
    import duckdb

    path = Path(dest_path)
    if path.exists() and path.is_dir():
        raise HarlequinCopyError(
            f"Cannot write DuckDB database to {path}: path is a directory.",
            title="Invalid path",
        )
    try:
        con = duckdb.connect(database=str(path))
        con.register("_hq_export_arrow", data)
        con.execute("CREATE TABLE results AS SELECT * FROM _hq_export_arrow")
        con.close()
    except (duckdb.Error, OSError) as e:
        raise HarlequinCopyError(
            str(e),
            title=("DuckDB could not write your database file."),
        ) from e


def _export_orc(
    data: "pa.Table",
    dest_path: str,
    batch_size: int | str = 1024,
    stripe_size: int | str = 67108864,
    compression_block_size: int | str = 65536,
    row_index_stride: int | str = 10000,
    padding_tolerance: float | str = 0.0,
    dictionary_key_size_threshold: float | str = 0.0,
    bloom_filter_columns: list[str] | str | None = None,
    bloom_filter_fpp: float | str = 0.05,
    **kwargs: Any,
) -> None:
    import pyarrow.lib as pl
    import pyarrow.orc as po

    try:
        if bloom_filter_columns and isinstance(bloom_filter_columns, str):
            bloom_filter_columns = bloom_filter_columns.split(",")
        batch_size = int(batch_size)
        compression_block_size = int(compression_block_size)
        stripe_size = int(stripe_size)
        row_index_stride = int(row_index_stride)
        bloom_filter_fpp = float(bloom_filter_fpp)
        padding_tolerance = float(padding_tolerance)
        dictionary_key_size_threshold = float(dictionary_key_size_threshold)
    except (ValueError, TypeError, KeyError) as e:
        raise HarlequinCopyError(
            str(e),
            title=("Arrow raised an error when writing your data to an ORC file."),
        ) from e
    try:
        po.write_table(
            data,
            dest_path,
            batch_size=batch_size,
            compression_block_size=compression_block_size,
            stripe_size=stripe_size,
            row_index_stride=row_index_stride,
            bloom_filter_fpp=bloom_filter_fpp,
            padding_tolerance=padding_tolerance,
            dictionary_key_size_threshold=dictionary_key_size_threshold,
            bloom_filter_columns=bloom_filter_columns,  # type: ignore
            **kwargs,
        )
    except (pl.ArrowException, OSError, IOError, TypeError) as e:
        raise HarlequinCopyError(
            str(e),
            title=("Arrow raised an error when writing your data to an ORC file."),
        ) from e


def _export_feather(
    data: "pa.Table",
    dest_path: str,
    compression: str | None = None,
    compression_level: str | int | None = None,
    chunksize: str | int | None = None,
    **kwargs: Any,
) -> None:
    import pyarrow.feather as pf
    import pyarrow.lib as pl

    try:
        compression_level = int(compression_level) if compression_level else None
        chunksize = int(chunksize) if chunksize else None
    except (ValueError, TypeError, KeyError) as e:
        raise HarlequinCopyError(
            str(e),
            title=("Arrow raised an error when writing your data to a Feather file."),
        ) from e

    try:
        pf.write_feather(
            data,
            dest_path,
            compression=compression,
            compression_level=compression_level,
            chunksize=chunksize,
            **kwargs,
        )
    except (pl.ArrowException, OSError, IOError, TypeError) as e:
        raise HarlequinCopyError(
            str(e),
            title=("Arrow raised an error when writing your data to a Feather file."),
        ) from e


def export_path_matches_default_generated_stem(path_str: str) -> bool:
    """
    True if ``path_str`` basename looks like ``default_export_filename`` output
    (so the UI can safely refresh the suffix when the user changes format).
    """
    raw = path_str.strip()
    if not raw:
        return True
    try:
        stem = Path(raw).name
    except ValueError:
        return False
    return bool(_DEFAULT_FILENAME_STEM_RE.match(stem))


def next_default_export_path(current_input: str, filename_suffix: str) -> str:
    """
    Build the path to show after the user changes export format: keep the same parent
    directory and timestamp prefix when the current basename matches the generated
    pattern; otherwise prefer ``Path.cwd()`` / ``default_export_filename``.
    """
    raw = current_input.strip()
    parent = Path.cwd()
    if raw:
        path = Path(raw).expanduser()
        parent = path.parent
        stem = path.name
        if export_path_matches_default_generated_stem(raw) and ".out." in stem:
            prefix = stem.split(".out.", 1)[0]
            return str(parent / f"{prefix}.out.{filename_suffix.lstrip('.')}")
    return str(parent / default_export_filename(filename_suffix))
