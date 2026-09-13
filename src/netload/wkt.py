"""Minimal Well-Known-Text (WKT) to GeoJSON geometry conversion.

PTV Visum/Simetra stores geometry in WKT-like columns such as
``WKTSURFACE`` (``MULTIPOLYGON(...)``) or ``WKTPOLY`` (``LINESTRING(...)``).
This module parses the subset of WKT used by ``.net`` files without any
external dependency (e.g. shapely) and returns GeoJSON geometry dicts.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

_COORD_SPLIT = re.compile(r"[\s,]+")

_HEADER_RE = re.compile(
    r"(?P<type>POINT|LINESTRING|POLYGON|MULTIPOINT|MULTILINESTRING|MULTIPOLYGON)"
    r"\s*(?:Z|M|ZM)?\s*\((?P<body>.*)\)\s*$",
    re.S | re.I,
)

_POINT_TYPES = {"POINT", "MULTIPOINT", "LINESTRING", "MULTILINESTRING", "POLYGON", "MULTIPOLYGON"}


def _coord(part: str) -> List[float]:
    numbers = [float(x) for x in _COORD_SPLIT.split(part.strip()) if x]
    return numbers


def _split_top(text: str) -> List[str]:
    """Split on top-level commas (ignoring commas inside parentheses)."""
    parts: List[str] = []
    depth = 0
    current: List[str] = []
    for char in text:
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        if char == "," and depth == 0:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    parts.append("".join(current).strip())
    return [p for p in parts if p]


def _unwrap(text: str) -> str:
    """Strip one outer layer of parentheses if present."""
    text = text.strip()
    if text.startswith("(") and text.endswith(")"):
        return text[1:-1].strip()
    return text


def _parse_polygon(body: str) -> List[List[List[float]]]:
    rings = _split_top(body)
    return [[_coord(c) for c in _split_top(_unwrap(ring))] for ring in rings]


def parse_wkt(text: str) -> Optional[Dict[str, Any]]:
    """Parse a WKT geometry string into a GeoJSON geometry dict.

    Returns ``None`` when the input is empty or cannot be recognised.

    Examples
    --------
    >>> parse_wkt("POINT(1 2)")
    {'type': 'Point', 'coordinates': [1.0, 2.0]}
    """
    if text is None:
        return None
    text = text.strip()
    if not text:
        return None

    match = _HEADER_RE.match(text)
    if not match:
        return None

    geometry_type = match.group("type").upper()
    if geometry_type not in _POINT_TYPES:
        return None

    body = match.group("body")

    if geometry_type == "POINT":
        return {"type": "Point", "coordinates": _coord(body)}

    if geometry_type == "LINESTRING":
        return {
            "type": "LineString",
            "coordinates": [_coord(p) for p in _split_top(body)],
        }

    if geometry_type == "MULTIPOINT":
        return {
            "type": "MultiPoint",
            "coordinates": [_coord(_unwrap(p)) for p in _split_top(body)],
        }

    if geometry_type == "POLYGON":
        return {"type": "Polygon", "coordinates": _parse_polygon(body)}

    if geometry_type == "MULTILINESTRING":
        return {
            "type": "MultiLineString",
            "coordinates": [
                [_coord(c) for c in _split_top(_unwrap(line))]
                for line in _split_top(body)
            ],
        }

    # MULTIPOLYGON
    return {
        "type": "MultiPolygon",
        "coordinates": [_parse_polygon(_unwrap(poly)) for poly in _split_top(body)],
    }