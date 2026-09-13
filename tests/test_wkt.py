"""Tests for the WKT -> GeoJSON converter."""

from __future__ import annotations

import pytest

from netload.wkt import parse_wkt


def test_point():
    assert parse_wkt("POINT(1 2)") == {"type": "Point", "coordinates": [1.0, 2.0]}


def test_point_z():
    assert parse_wkt("POINT Z (1 2 3)") == {
        "type": "Point",
        "coordinates": [1.0, 2.0, 3.0],
    }


def test_linestring():
    geom = parse_wkt("LINESTRING(1 1,2 2,3 3)")
    assert geom["type"] == "LineString"
    assert geom["coordinates"] == [[1.0, 1.0], [2.0, 2.0], [3.0, 3.0]]


def test_polygon():
    geom = parse_wkt("POLYGON((0 0,1 0,1 1,0 0))")
    assert geom["type"] == "Polygon"
    assert geom["coordinates"] == [
        [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 0.0]]
    ]


def test_polygon_with_hole():
    geom = parse_wkt("POLYGON((0 0,2 0,2 2,0 0),(0.5 0.5,1 0.5,1 1,0.5 0.5))")
    assert len(geom["coordinates"]) == 2


def test_multipolygon():
    geom = parse_wkt(
        "MULTIPOLYGON(((0 0,1 1,1 0,0 0)),((2 2,3 3,3 2,2 2)))"
    )
    assert geom["type"] == "MultiPolygon"
    assert len(geom["coordinates"]) == 2
    assert len(geom["coordinates"][0][0]) == 4


def test_multilinestring():
    geom = parse_wkt("MULTILINESTRING((0 0,1 1),(2 2,3 3))")
    assert geom["type"] == "MultiLineString"
    assert geom["coordinates"] == [[[0.0, 0.0], [1.0, 1.0]], [[2.0, 2.0], [3.0, 3.0]]]


def test_empty_returns_none():
    assert parse_wkt("") is None
    assert parse_wkt(None) is None
    assert parse_wkt("   ") is None


def test_unknown_geometry_returns_none():
    assert parse_wkt("GEOMETRYCOLLECTION(POINT(0 0))") is None


def test_negative_and_decimal_coordinates():
    geom = parse_wkt("LINESTRING(-59.85 57.92,60.01 -57.90)")
    assert geom["coordinates"] == [[-59.85, 57.92], [60.01, -57.90]]