"""High-level :class:`Network` object built from parsed tables."""

from __future__ import annotations

import os
from typing import Dict, List, Optional, Sequence

import pandas as pd

from .exceptions import VisumNetError
from .table import Table

_SHORTCUTS = {
    "nodes": "NODE",
    "links": "LINK",
    "zones": "ZONE",
    "turns": "TURN",
}


class Network:
    """A parsed PTV Visum network.

    Wraps the ordered dict of parsed tables and offers both generic and
    convenient accessors.

    Attributes
    ----------
    source:
        Path of the source file.
    encoding:
        Encoding that was actually used to decode the file.
    """

    def __init__(self, tables: Dict[str, Table], source: str, encoding: str) -> None:
        self._tables = tables
        self.source = source
        self.encoding = encoding

    # -- generic access ----------------------------------------------------

    @property
    def tables(self) -> Dict[str, Table]:
        """Ordered mapping of table name → :class:`Table`."""
        return self._tables

    @property
    def table_names(self) -> List[str]:
        """Names of all parsed tables, in file order."""
        return list(self._tables.keys())

    def has_table(self, name: str) -> bool:
        """Return ``True`` if a table named ``name`` was parsed."""
        return name in self._tables

    def get_table(self, name: str) -> pd.DataFrame:
        """Return the DataFrame of table ``name``."""
        return self._tables[name].df

    def __getitem__(self, name: str) -> pd.DataFrame:
        return self.get_table(name)

    def __contains__(self, name: object) -> bool:
        return name in self._tables

    def __len__(self) -> int:
        return len(self._tables)

    # -- shortcuts ----------------------------------------------------------

    @property
    def nodes(self) -> pd.DataFrame:
        """DataFrame of the ``NODE`` table."""
        return self._shortcut("NODE")

    @property
    def links(self) -> pd.DataFrame:
        """DataFrame of the ``LINK`` table."""
        return self._shortcut("LINK")

    @property
    def zones(self) -> pd.DataFrame:
        """DataFrame of the ``ZONE`` table."""
        return self._shortcut("ZONE")

    @property
    def turns(self) -> pd.DataFrame:
        """DataFrame of the ``TURN`` table."""
        return self._shortcut("TURN")

    def _shortcut(self, name: str) -> pd.DataFrame:
        if name not in self._tables:
            raise VisumNetError(
                f"table {name!r} is not present in the network "
                f"(tables: {', '.join(self.table_names) or 'none'})"
            )
        return self._tables[name].df

    # -- misc ---------------------------------------------------------------

    def to_dict(self) -> Dict[str, pd.DataFrame]:
        """Return all tables as ``{name: DataFrame}``."""
        return {name: table.df for name, table in self._tables.items()}

    def info(self) -> Dict[str, int]:
        """Return ``{table_name: row_count}`` for every table."""
        return {name: len(table.df) for name, table in self._tables.items()}

    def export_csv(
        self,
        output_dir: str | os.PathLike[str],
        sep: str = ";",
        encoding: str = "utf-8",
        skip_empty: bool = True,
        tables: Optional[Sequence[str]] = None,
    ) -> List[str]:
        """Export tables to CSV files inside ``output_dir``.

        The directory is created if needed. Files are named after the table
        (e.g. ``NODE.csv``). When ``tables`` is given (e.g.
        ``["NODE", "LINK"]``) only those tables are exported, otherwise every
        table is exported. Tables without any data row are skipped when
        ``skip_empty`` is ``True``.

        Returns
        -------
        List of written CSV file paths.
        """
        from .exporters import export_tables

        return export_tables(
            self,
            output_dir=output_dir,
            sep=sep,
            encoding=encoding,
            skip_empty=skip_empty,
            tables=tables,
        )

    def export_json(
        self,
        output_dir: str | os.PathLike[str],
        encoding: str = "utf-8",
        skip_empty: bool = True,
        tables: Optional[Sequence[str]] = None,
    ) -> List[str]:
        """Export tables to JSON files inside ``output_dir``.

        Each file contains a JSON array of records named after the table
        (e.g. ``NODE.json``). When ``tables`` is given only those tables are
        exported, otherwise every table is exported.

        Returns
        -------
        List of written JSON file paths.
        """
        from .exporters import export_json

        return export_json(
            self,
            output_dir=output_dir,
            encoding=encoding,
            skip_empty=skip_empty,
            tables=tables,
        )

    def export_geojson(
        self,
        output_dir: str | os.PathLike[str],
        encoding: str = "utf-8",
        skip_empty: bool = True,
        tables: Optional[Sequence[str]] = None,
    ) -> List[str]:
        """Export tables that have geometry to GeoJSON files.

        Tables with a WKT column (``WKTSURFACE``, ``WKTPOLY``, ``GEOMETRY``)
        or with ``XCOORD``/``YCOORD`` columns are written as
        ``<NAME>.geojson`` ``FeatureCollection`` files. When ``tables`` is
        given only those tables are considered, otherwise every table is
        considered.

        Returns
        -------
        List of written GeoJSON file paths.
        """
        from .exporters import export_geojson

        return export_geojson(
            self,
            output_dir=output_dir,
            encoding=encoding,
            skip_empty=skip_empty,
            tables=tables,
        )

    def __repr__(self) -> str:
        return (
            f"Network(source={self.source!r}, encoding={self.encoding!r}, "
            f"tables={len(self._tables)})"
        )