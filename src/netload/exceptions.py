"""Public exceptions for :mod:`netload`."""

from __future__ import annotations

from typing import Optional


class VisumNetError(Exception):
    """Base exception for all errors raised by :mod:`netload`."""


class VisumNetParseError(VisumNetError):
    """Raised when a ``.net`` file cannot be parsed correctly.

    Attributes
    ----------
    source:
        Path of the file being parsed.
    line:
        Line number where the problem occurred (1-based), if known.
    message:
        Human readable description of the problem.
    """

    def __init__(self, source: str, message: str, line: Optional[int] = None) -> None:
        self.source = source
        self.line = line
        self.message = message
        location = f"{source}:{line}" if line is not None else source
        super().__init__(f"{location}: {message}")


class VisumNetEncodingError(VisumNetError):
    """Raised when the encoding of a ``.net`` file cannot be determined/decoded.

    Attributes
    ----------
    source:
        Path of the file being parsed.
    """

    def __init__(self, source: str, message: str) -> None:
        self.source = source
        self.message = message
        super().__init__(f"{source}: {message}")