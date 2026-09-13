"""Tests for the low-level parser."""

from __future__ import annotations

import pandas as pd
import pytest

from netload import (
    VisumNetEncodingError,
    VisumNetError,
    VisumNetParseError,
    read_net,
)


def test_read_net_detects_tables(sample_net):
    network = read_net(sample_net)
    names = network.table_names
    assert "VERSION" in names
    assert "USERATTDEF" in names
    assert "NODE" in names
    assert "ZONE" in names
    assert "TURN" in names
    assert "VISION" in names


def test_columns_detected(sample_net):
    network = read_net(sample_net)
    assert list(network.nodes.columns) == [
        "NO",
        "NAME",
        "CONTROLTYPE",
        "T0PRT",
        "CAPPRT",
        "TYPENO",
        "ЗАДЕРЖКАЖД",
        "XCOORD",
        "YCOORD",
    ]


def test_row_counts(sample_net):
    network = read_net(sample_net)
    assert len(network.nodes) == 3
    assert len(network.zones) == 2
    assert len(network.turns) == 2


def test_russian_characters_preserved(sample_net):
    network = read_net(sample_net)
    names = network.nodes["NAME"].tolist()
    assert names[0] == "Узел один"
    assert names[2] == "Узел три"

    attr = network["USERATTDEF"]
    assert "ГОД" in attr["ATTID"].tolist()
    assert attr["NAME"].tolist() == [
        "ГОД",
        "Проверено",
        "Задержка при переезде ЖД",
    ]


def test_missing_values_become_empty(sample_net):
    network = read_net(sample_net)
    row = network.nodes.iloc[1]
    assert row["NAME"] == ""


def test_unknown_table_is_parsed(sample_net):
    network = read_net(sample_net)
    assert network.has_table("FANCYTABLE")
    assert list(network["FANCYTABLE"]["CODE"]) == ["A", "B", "C"]


def test_values_kept_as_strings_by_default(sample_net):
    network = read_net(sample_net)
    assert pd.api.types.is_string_dtype(network.nodes["NO"])
    assert network.nodes.iloc[0]["XCOORD"] == "60.0106626"


def test_infer_types_numeric(sample_net):
    network = read_net(sample_net, infer_types=True)
    assert network.nodes["NO"].dtype.kind == "i"
    assert network.nodes["XCOORD"].dtype.kind == "f"
    assert pd.api.types.is_string_dtype(network.nodes["NAME"])


def test_infer_types_coerces_partially_numeric_column(tmp_path):
    file = tmp_path / "mix.net"
    file.write_text(
        "$T:NO;NAME;LINKNO\n"
        "1;Centre;10\n"
        "2;;\n"
        "3;Nord;30\n"
        "4;Sud;40\n"
        "5;;50\n",
        encoding="utf-8",
    )
    network = read_net(str(file), infer_types=True)
    t = network["T"]
    # LINKNO: 4/5 non-empty values numeric -> coerced (blanks become NaN)
    assert t["LINKNO"].dtype.kind == "f"
    assert pd.isna(t["LINKNO"].iloc[1])
    # NAME: mostly text -> kept as strings, empty stays a string
    assert pd.api.types.is_string_dtype(t["NAME"])
    assert t["NAME"].iloc[1] == ""


def test_cp1251_encoding_detected(cp1251_net):
    network = read_net(cp1251_net)
    assert network.encoding == "cp1251"
    assert network.nodes["NAME"].tolist()[0] == "Узел один"


def test_utf8_bom_encoding_detected(utf8_bom_net):
    network = read_net(utf8_bom_net)
    assert network.encoding == "utf-8-sig"
    assert network.nodes.iloc[0]["NAME"] == "Узел один"


def test_file_not_found():
    with pytest.raises(FileNotFoundError):
        read_net("does/not/exist.net")


def test_parse_error_on_ragged_row(tmp_path):
    bad = tmp_path / "bad.net"
    bad.write_text(
        "$NODE:NO;NAME\n"
        "1;Alpha\n"
        "2;Beta;EXTRA\n",
        encoding="utf-8",
    )
    with pytest.raises(VisumNetParseError) as excinfo:
        read_net(str(bad))
    assert "bad.net" in str(excinfo.value)
    assert "3" in str(excinfo.value)  # line number


def test_encoding_error(sample_net):
    with pytest.raises(VisumNetEncodingError):
        read_net(sample_net, encoding="not-a-real-codec")


def test_errors_are_netload_errors(tmp_path):
    bad = tmp_path / "bad.net"
    bad.write_text("$NODE:NO;NAME\n1;Alpha;EXTRA\n", encoding="utf-8")
    with pytest.raises(VisumNetError):
        read_net(str(bad))


def test_empty_file_yields_no_tables(tmp_path):
    empty = tmp_path / "empty.net"
    empty.write_text("", encoding="utf-8")
    network = read_net(str(empty))
    assert network.table_names == []


def test_only_comments_yield_no_tables(tmp_path):
    file = tmp_path / "comments.net"
    file.write_text("* just a comment\n\n* another\n", encoding="utf-8")
    network = read_net(str(file))
    assert network.table_names == []


def test_table_without_columns(sample_net):
    network = read_net(sample_net)
    vision = network["VISION"]
    assert vision.shape == (0, 0)