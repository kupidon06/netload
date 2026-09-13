"""Low-level parsing of PTV Visum ``.net`` text files."""

from __future__ import annotations

import codecs
import os
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd

from .exceptions import VisumNetEncodingError, VisumNetParseError
from .table import Table

_STRIP_CHARS = " \t\ufeff"


def _detect_encoding(raw: bytes, source: str, hint: Optional[str]) -> str:
    """Determine the encoding of ``raw`` bytes.

    Order of preference:

    1. A BOM when present (UTF-8 / UTF-16 / UTF-32).
    2. A user supplied ``hint``.
    3. Strict UTF-8.
    4. Windows-1251 (CP1251).
    """
    if hint is not None:
        try:
            raw.decode(hint)
            return hint
        except (LookupError, UnicodeDecodeError) as exc:  # pragma: no cover - defensive
            raise VisumNetEncodingError(
                source, f"cannot decode file with requested encoding {hint!r}: {exc}"
            ) from exc

    if raw.startswith(codecs.BOM_UTF8):
        return "utf-8-sig"
    if raw.startswith(codecs.BOM_UTF32_LE) or raw.startswith(codecs.BOM_UTF32_BE):
        return "utf-32"
    if raw.startswith(codecs.BOM_UTF16_LE) or raw.startswith(codecs.BOM_UTF16_BE):
        return "utf-16"

    for encoding in ("utf-8", "cp1251"):
        try:
            raw.decode(encoding)
            return encoding
        except UnicodeDecodeError:
            continue

    raise VisumNetEncodingError(
        source,
        "unable to determine the file encoding "
        "(tried UTF-8 and Windows-1251). Pass an explicit 'encoding'.",
    )


def _read_text(path: Path, encoding: Optional[str]) -> Tuple[str, str]:
    raw = path.read_bytes()
    resolved = _detect_encoding(raw, str(path), encoding)
    try:
        return raw.decode(resolved), resolved
    except UnicodeDecodeError as exc:
        raise VisumNetEncodingError(str(path), f"failed to decode file as {resolved}: {exc}") from exc


class _ParsedTable:
    """Intermediate representation produced while scanning the file."""

    __slots__ = ("name", "line", "columns", "rows")

    def __init__(
        self, name: str, line: int, columns: Optional[Sequence[str]]
    ) -> None:
        self.name = name
        self.line = line
        self.columns: List[str] = list(columns) if columns is not None else []
        self.rows: List[List[str]] = []


def _start_table(
    line: str, lineno: int, sep: str
) -> Optional[_ParsedTable]:
    body = line[1:].strip(_STRIP_CHARS)
    name, sep_char, columns_part = body.partition(":")
    name = name.strip(_STRIP_CHARS)
    if not name:
        raise VisumNetParseError(
            "net", f"invalid table header on line {lineno}: missing table name",
            line=lineno,
        )
    columns: Optional[List[str]] = None
    if columns_part:
        columns = [c.strip(_STRIP_CHARS) for c in columns_part.split(sep)]
    return _ParsedTable(name, lineno, columns)


def _iter_parse(
    text: str, source: str, sep: str
) -> Dict[str, _ParsedTable]:
    tables: Dict[str, _ParsedTable] = {}
    current: Optional[_ParsedTable] = None
    used_names: Dict[str, int] = {}

    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip(_STRIP_CHARS)
        if not line:
            continue
        if line.startswith("*"):
            continue
        if line.startswith("$"):
            current = _start_table(line, lineno, sep)
            if current is not None:
                # Guard against duplicate table names by suffixing.
                base = current.name
                count = used_names.get(base, 0)
                used_names[base] = count + 1
                if count:
                    current.name = f"{base}#{count + 1}"
                tables[current.name] = current
            continue
        if current is None:
            continue

        cells = line.split(sep)
        ncols = len(current.columns)

        if ncols == 0:
            # A table header without declared columns: create an implicit one.
            current.columns = ["VALUE"]
            ncols = 1

        if len(cells) > ncols:
            raise VisumNetParseError(
                source,
                f"table '{current.name}' row has {len(cells)} values "
                f"but its header declares {ncols} columns",
                line=lineno,
            )
        if len(cells) < ncols:
            cells.extend([""] * (ncols - len(cells)))
        current.rows.append(cells)

    return tables


def _build_dataframe(table: _ParsedTable, infer_types: bool) -> pd.DataFrame:
    df = pd.DataFrame(table.rows, columns=table.columns)
    if infer_types:
        df = df.apply(_infer_series, axis=0)
    return df


def _infer_series(series: pd.Series) -> pd.Series:
    """Lightweight numeric inference that never corrupts text values."""
    if series.empty:
        return series
    non_empty = series.dropna()
    if len(non_empty) == 0:
        return series
    converted = pd.to_numeric(series, errors="coerce")
    if converted.notna().sum() == len(non_empty):
        return converted
    return series


def parse_net(
    path: str | os.PathLike[str],
    encoding: Optional[str] = None,
    sep: str = ";",
    infer_types: bool = False,
) -> Dict[str, Table]:
    """Parse a Visum ``.net`` file into a dict of :class:`Table`.

    Parameters
    ----------
    path:
        Path of the ``.net`` file.
    encoding:
        Force a specific encoding. When ``None`` the encoding is detected
        automatically (BOM, then UTF-8, then Windows-1251).
    sep:
        Field separator used inside tables (default ``";"``).
    infer_types:
        When ``True``, try a light numeric inference on every column. When
        ``False`` (default) the original string values are preserved.

    Returns
    -------
    Ordered dict mapping table names to :class:`Table` objects.
    """
    tables, _ = parse_net_with_encoding(
        path, encoding=encoding, sep=sep, infer_types=infer_types
    )
    return tables


def parse_net_with_encoding(
    path: str | os.PathLike[str],
    encoding: Optional[str] = None,
    sep: str = ";",
    infer_types: bool = False,
) -> Tuple[Dict[str, Table], str]:
    """Like :func:`parse_net`, but also return the encoding actually used."""
    source = os.fspath(path)
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"No such file: {source}")
    if not file_path.is_file():
        raise VisumNetParseError(source, "path does not point to a file")

    text, resolved_encoding = _read_text(file_path, encoding)

    parsed = _iter_parse(text, source, sep)

    tables: Dict[str, Table] = {}
    for name, table in parsed.items():
        df = _build_dataframe(table, infer_types)
        tables[name] = Table(name=name, df=df, line=table.line, source=source)

    return tables, resolved_encoding