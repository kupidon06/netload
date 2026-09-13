"""Tests for CSV / JSON / GeoJSON export."""

from __future__ import annotations

import json

import pandas as pd
import pytest

from netload import VisumNetError, read_net


def test_export_creates_directory(sample_net, tmp_path):
    network = read_net(sample_net)
    out = tmp_path / "nested" / "output"
    network.export_csv(str(out))
    assert out.is_dir()


def test_export_skips_empty_tables(sample_net, tmp_path):
    network = read_net(sample_net)
    written = network.export_csv(tmp_path)
    assert "VISION.csv" not in written
    assert (tmp_path / "NODE.csv").exists()
    assert (tmp_path / "ZONE.csv").exists()
    assert (tmp_path / "TURN.csv").exists()


def test_export_without_skipping_empty(sample_net, tmp_path):
    network = read_net(sample_net)
    written = network.export_csv(tmp_path, skip_empty=False)
    assert (tmp_path / "VISION.csv").exists()
    assert (tmp_path / "NODE.csv").exists()


def test_export_semicolon_separator(sample_net, tmp_path):
    network = read_net(sample_net)
    network.export_csv(tmp_path, sep=";")
    content = (tmp_path / "NODE.csv").read_text(encoding="utf-8")
    assert content.startswith("NO;NAME;CONTROLTYPE")
    assert ";60.0106626;57.90244280000001" in content


def test_export_comma_separator(sample_net, tmp_path):
    network = read_net(sample_net)
    network.export_csv(tmp_path, sep=",")
    content = (tmp_path / "NODE.csv").read_text(encoding="utf-8")
    assert content.startswith("NO,NAME,CONTROLTYPE")


def test_export_utf8_preserves_russian(sample_net, tmp_path):
    network = read_net(sample_net)
    network.export_csv(tmp_path)
    content = (tmp_path / "NODE.csv").read_text(encoding="utf-8")
    assert "Узел один" in content


def test_export_round_trip(sample_net, tmp_path):
    network = read_net(sample_net)
    network.export_csv(tmp_path)
    reloaded = pd.read_csv(tmp_path / "NODE.csv", sep=";", dtype=str)
    assert list(reloaded.columns) == list(network.nodes.columns)
    assert len(reloaded) == len(network.nodes)
    assert reloaded.iloc[0]["NAME"] == "Узел один"


def test_export_cp1251_round_trip(sample_net, tmp_path):
    network = read_net(sample_net)
    network.export_csv(tmp_path, encoding="cp1251")
    reloaded = pd.read_csv(tmp_path / "NODE.csv", sep=";", encoding="cp1251", dtype=str)
    assert reloaded.iloc[0]["NAME"] == "Узел один"


def test_export_filenames_match_tables(sample_net, tmp_path):
    network = read_net(sample_net)
    written = network.export_csv(tmp_path)
    names = {str(p).rsplit("/", 1)[-1] for p in written}
    assert "USERATTDEF.csv" in names
    assert "FANCYTABLE.csv" in names


# -- selective export (single / subset of tables) ----------------------------


def test_export_csv_single_table(sample_net, tmp_path):
    network = read_net(sample_net)
    written = network.export_csv(tmp_path, tables=["NODE"])
    assert len(written) == 1
    assert (tmp_path / "NODE.csv").exists()
    assert not (tmp_path / "ZONE.csv").exists()
    assert not (tmp_path / "LINK.csv").exists()


def test_export_csv_several_tables(sample_net, tmp_path):
    network = read_net(sample_net)
    written = network.export_csv(tmp_path, tables=["NODE", "LINK"])
    names = {str(p).rsplit("/", 1)[-1] for p in written}
    assert names == {"NODE.csv", "LINK.csv"}


def test_export_json_single_table(sample_net, tmp_path):
    network = read_net(sample_net)
    network.export_json(tmp_path, tables=["ZONE"])
    assert (tmp_path / "ZONE.json").exists()
    assert not (tmp_path / "NODE.json").exists()


def test_export_geojson_single_table(sample_net, tmp_path):
    network = read_net(sample_net)
    written = network.export_geojson(tmp_path, tables=["NODE"])
    assert len(written) == 1
    assert (tmp_path / "NODE.geojson").exists()
    assert not (tmp_path / "LINK.geojson").exists()


def test_export_unknown_table_raises(sample_net, tmp_path):
    network = read_net(sample_net)
    with pytest.raises(VisumNetError):
        network.export_csv(tmp_path, tables=["NOPE"])


def test_export_geojson_selection_without_geometry(sample_net, tmp_path):
    network = read_net(sample_net)
    written = network.export_geojson(tmp_path, tables=["ZONE"])
    assert len(written) == 1
    assert (tmp_path / "ZONE.geojson").exists()


# -- JSON -------------------------------------------------------------------


def test_export_json(sample_net, tmp_path):
    network = read_net(sample_net)
    written = network.export_json(tmp_path)
    assert (tmp_path / "NODE.json").exists()
    assert "VISION.json" not in written

    data = json.loads((tmp_path / "NODE.json").read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert len(data) == 3
    assert data[0]["NAME"] == "Узел один"
    assert data[0]["NO"] == "1"


def test_export_json_ensure_ascii_false(sample_net, tmp_path):
    network = read_net(sample_net)
    network.export_json(tmp_path)
    content = (tmp_path / "NODE.json").read_text(encoding="utf-8")
    assert "Узел один" in content


def test_export_json_skip_empty_false(sample_net, tmp_path):
    network = read_net(sample_net)
    written = network.export_json(tmp_path, skip_empty=False)
    assert (tmp_path / "VISION.json").exists()


def test_export_json_infer_types_numeric(sample_net, tmp_path):
    network = read_net(sample_net, infer_types=True)
    network.export_json(tmp_path)
    data = json.loads((tmp_path / "NODE.json").read_text(encoding="utf-8"))
    assert data[0]["NO"] == 1
    assert isinstance(data[0]["XCOORD"], float)


# -- GeoJSON ----------------------------------------------------------------


def test_export_geojson_point_from_xy(sample_net, tmp_path):
    network = read_net(sample_net)
    written = network.export_geojson(tmp_path)
    assert (tmp_path / "NODE.geojson").exists()

    fc = json.loads((tmp_path / "NODE.geojson").read_text(encoding="utf-8"))
    assert fc["type"] == "FeatureCollection"
    assert len(fc["features"]) == 3
    first = fc["features"][0]
    assert first["geometry"]["type"] == "Point"
    assert first["geometry"]["coordinates"] == [60.0106626, 57.90244280000001]
    assert first["properties"]["NO"] == "1"
    assert "XCOORD" not in first["properties"]
    assert "YCOORD" not in first["properties"]


def test_export_geojson_wkt_linestring(sample_net, tmp_path):
    network = read_net(sample_net)
    network.export_geojson(tmp_path)
    fc = json.loads((tmp_path / "LINK.geojson").read_text(encoding="utf-8"))
    assert fc["type"] == "FeatureCollection"
    assert fc["features"][0]["geometry"]["type"] == "LineString"
    assert fc["features"][0]["geometry"]["coordinates"] == [
        [60.01, 57.9],
        [60.02, 57.91],
    ]
    assert "WKTPOLY" not in fc["features"][0]["properties"]


def test_export_geojson_wkt_multipolygon(sample_net, tmp_path):
    network = read_net(sample_net)
    network.export_geojson(tmp_path)
    fc = json.loads((tmp_path / "ZONE.geojson").read_text(encoding="utf-8"))
    assert fc["features"][0]["geometry"]["type"] == "MultiPolygon"
    assert fc["features"][0]["properties"]["NAME"] == "Дзержинский район"
    assert "WKTSURFACE" not in fc["features"][0]["properties"]


def test_export_geojson_skips_tables_without_geometry(sample_net, tmp_path):
    network = read_net(sample_net)
    written = network.export_geojson(tmp_path)
    names = {str(p).rsplit("/", 1)[-1] for p in written}
    assert "NODE.geojson" in names
    assert "LINK.geojson" in names
    assert "ZONE.geojson" in names
    assert "VERSION.geojson" not in names
    assert "USERATTDEF.geojson" not in names