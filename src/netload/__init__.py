"""netload: a lightweight parser for PTV Visum ``.net`` files."""

from __future__ import annotations

from .exceptions import (
    VisumNetEncodingError,
    VisumNetError,
    VisumNetParseError,
)
from .network import Network
from .parser import parse_net, parse_net_with_encoding
from .table import Table

__version__ = "0.1.0"

__all__ = [
    "Network",
    "Table",
    "VisumNetEncodingError",
    "VisumNetError",
    "VisumNetParseError",
    "parse_net",
    "read_net",
]


def read_net(
    path: str,
    encoding: str | None = None,
    sep: str = ";",
    infer_types: bool = False,
) -> Network:
    """Read a PTV Visum ``.net`` file and return a :class:`Network`.

    Parameters
    ----------
    path:
        Path of the ``.net`` file.
    encoding:
        Optional explicit encoding. When omitted, the encoding is detected
        automatically (BOM, then UTF-8, then Windows-1251).
    sep:
        Field separator used inside tables (default ``";"``).
    infer_types:
        When ``True``, apply a light numeric type inference on every column.
        The default preserves the original string values.

    Returns
    -------
    A :class:`Network` exposing every parsed table as a
    ``pandas.DataFrame``.

    Raises
    ------
    FileNotFoundError
        If ``path`` does not exist.
    netload.exceptions.VisumNetEncodingError
        If the file cannot be decoded.
    netload.exceptions.VisumNetParseError
        If the file structure is invalid.
    """
    tables, resolved_encoding = parse_net_with_encoding(
        path,
        encoding=encoding,
        sep=sep,
        infer_types=infer_types,
    )
    return Network(tables, source=path, encoding=resolved_encoding)