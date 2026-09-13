"""Table object representing a single ``$`` section of a ``.net`` file."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import pandas as pd


@dataclass
class Table:
    """One parsed table of a Visum ``.net`` file.

    A ``Table`` wraps a ``pandas.DataFrame`` together with metadata about where
    the table came from. The public API of :class:`~netload.network.Network`
    returns the underlying DataFrame, while ``network.tables`` exposes these
    ``Table`` objects for advanced use.

    Attributes
    ----------
    name:
        Table name as found in the file (e.g. ``"NODE"``).
    df:
        The parsed data as a ``pandas.DataFrame``.
    line:
        1-based line number of the ``$`` header in the source file.
    source:
        Path of the source file.
    """

    name: str
    df: pd.DataFrame
    line: int
    source: str

    @property
    def columns(self) -> List[str]:
        """Column names of the table."""
        return list(self.df.columns)

    @property
    def nrows(self) -> int:
        """Number of data rows in the table."""
        return len(self.df)

    def head(self, n: int = 5) -> pd.DataFrame:
        """Return the first ``n`` rows of the underlying DataFrame."""
        return self.df.head(n)

    def __len__(self) -> int:
        return len(self.df)

    def __repr__(self) -> str:
        return f"Table(name={self.name!r}, rows={len(self.df)}, line={self.line})"