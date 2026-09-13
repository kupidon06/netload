"""Export helpers: CSV, JSON and GeoJSON."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Sequence

import pandas as pd

from .exceptions import VisumNetError
from .wkt import parse_wkt

if TYPE_CHECKING:  # pragma: no cover
    from .network import Network
    from .table import Table

# Column names that are known to hold WKT geometry in .net files.
_WKT_COLUMNS = ("WKTSURFACE", "WKTPOLY", "GEOMETRY")


def _resolve_tables(
    network: "Network", tables: Optional[Sequence[str]]
) -> List["Table"]:
    """Return the tables to export.

    When ``tables`` is ``None`` every table is returned (file order);
    otherwise only the requested table names (file order is preserved).
    """
    if tables is None:
        return list(network.tables.values())

    resolved: List["Table"] = []
    for name in tables:
        if name not in network.tables:
            raise VisumNetError(
                f"table {name!r} not found in the network "
                f"(tables: {', '.join(network.table_names) or 'none'})"
            )
        resolved.append(network.tables[name])
    return resolved


# -- small helpers ----------------------------------------------------------


def _records_to_jsonable(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Convert a DataFrame to a list of JSON-safe records (NaN -> None)."""
    object_frame = df.astype(object).where(pd.notna(df), None)
    return object_frame.to_dict("records")


def _geometry_for_row(row: pd.Series, geometry_col: Optional[str]) -> Optional[Dict[str, Any]]:
    if geometry_col is None:
        return None
    value = row.get(geometry_col)
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    return parse_wkt(str(value))


# -- single-table exporters -------------------------------------------------


def export_table_csv(
    df: pd.DataFrame,
    path: str | os.PathLike[str],
    sep: str = ";",
    encoding: str = "utf-8",
) -> None:
    """Write one DataFrame to a CSV file."""
    df.to_csv(
        path,
        sep=sep,
        index=False,
        encoding=encoding,
        lineterminator="\n",
    )


def export_table_json(
    df: pd.DataFrame,
    path: str | os.PathLike[str],
    encoding: str = "utf-8",
) -> None:
    """Write one DataFrame to a JSON array of records."""
    with open(path, "w", encoding=encoding) as handle:
        json.dump(
            _records_to_jsonable(df),
            handle,
            ensure_ascii=False,
            indent=2,
        )


def _pick_geometry_column(df: pd.DataFrame) -> Optional[str]:
    columns = set(df.columns)
    for candidate in _WKT_COLUMNS:
        if candidate in columns:
            return candidate
    return None


def table_geometry_kind(df: pd.DataFrame) -> Optional[str]:
    """Describe the geometry of a table.

    Returns ``"WKT"`` when a WKT geometry column exists, ``"XY"`` when the
    table has ``XCOORD``/``YCOORD`` columns, otherwise ``None``.
    """
    if _pick_geometry_column(df) is not None:
        return "WKT"
    if "XCOORD" in df.columns and "YCOORD" in df.columns:
        return "XY"
    return None


def export_table_geojson(
    df: pd.DataFrame,
    path: str | os.PathLike[str],
    encoding: str = "utf-8",
) -> bool:
    """Write one DataFrame to a GeoJSON ``FeatureCollection``.

    Geometry is taken from a WKT column (``WKTSURFACE``, ``WKTPOLY``,
    ``GEOMETRY``) when available, otherwise from ``XCOORD``/``YCOORD`` as
    Point features.

    Returns ``False`` when the table has no geometry and nothing is written.
    """
    geometry_col = _pick_geometry_column(df)

    if geometry_col is None and not (
        "XCOORD" in df.columns and "YCOORD" in df.columns
    ):
        return False

    geometry_keys = {geometry_col, "XCOORD", "YCOORD"} if geometry_col else {"XCOORD", "YCOORD"}
    property_columns = [c for c in df.columns if c not in geometry_keys]

    features: List[Dict[str, Any]] = []
    for _, row in df.iterrows():
        if geometry_col is not None:
            geometry = _geometry_for_row(row, geometry_col)
        else:
            x = row.get("XCOORD")
            y = row.get("YCOORD")
            if x is None or y is None or pd.isna(x) or pd.isna(y):
                geometry = None
            else:
                geometry = {"type": "Point", "coordinates": [float(x), float(y)]}
        properties = {
            col: row.get(col) for col in property_columns
        }
        for key in list(properties):
            value = properties[key]
            if value is not None and isinstance(value, float) and pd.isna(value):
                properties[key] = None
        features.append({"type": "Feature", "geometry": geometry, "properties": properties})

    feature_collection: Dict[str, Any] = {
        "type": "FeatureCollection",
        "features": features,
    }

    with open(path, "w", encoding=encoding) as handle:
        json.dump(feature_collection, handle, ensure_ascii=False, indent=2)

    return True


# -- network-level exporters -------------------------------------------------


def export_tables(
    network: "Network",
    output_dir: str | os.PathLike[str],
    sep: str = ";",
    encoding: str = "utf-8",
    skip_empty: bool = True,
    tables: Optional[Sequence[str]] = None,
) -> List[str]:
    """Write one CSV file per table of ``network`` into ``output_dir``.

    When ``tables`` is given (e.g. ``["NODE", "LINK"]``), only those tables
    are exported; by default every table is exported.
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    written: List[str] = []
    for table in _resolve_tables(network, tables):
        if skip_empty and len(table.df) == 0:
            continue
        path = out_dir / f"{table.name}.csv"
        export_table_csv(table.df, path, sep=sep, encoding=encoding)
        written.append(str(path))
    return written


def export_json(
    network: "Network",
    output_dir: str | os.PathLike[str],
    encoding: str = "utf-8",
    skip_empty: bool = True,
    tables: Optional[Sequence[str]] = None,
) -> List[str]:
    """Write one JSON file (array of records) per table into ``output_dir``.

    When ``tables`` is given, only those tables are exported; by default
    every table is exported.
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    written: List[str] = []
    for table in _resolve_tables(network, tables):
        if skip_empty and len(table.df) == 0:
            continue
        path = out_dir / f"{table.name}.json"
        export_table_json(table.df, path, encoding=encoding)
        written.append(str(path))
    return written


def export_geojson(
    network: "Network",
    output_dir: str | os.PathLike[str],
    encoding: str = "utf-8",
    skip_empty: bool = True,
    tables: Optional[Sequence[str]] = None,
) -> List[str]:
    """Write a GeoJSON file for every requested table that has geometry.

    When ``tables`` is given, only those tables are considered; by default
    every table is considered. Tables without any geometry (no WKT column,
    no ``XCOORD``/``YCOORD``) are skipped.
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    written: List[str] = []
    for table in _resolve_tables(network, tables):
        if skip_empty and len(table.df) == 0:
            continue
        path = out_dir / f"{table.name}.geojson"
        if export_table_geojson(table.df, path, encoding=encoding):
            written.append(str(path))
    return written