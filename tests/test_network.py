"""Tests for the Network public API."""

from __future__ import annotations

import pandas as pd
import pytest

from netload import Network, VisumNetError, read_net


def test_tables_is_mapping(sample_net):
    network = read_net(sample_net)
    assert isinstance(network.tables, dict)
    assert list(network.tables.keys())[0] == "VISION"


def test_has_table(sample_net):
    network = read_net(sample_net)
    assert network.has_table("NODE")
    assert network.has_table("LINK")
    assert network.has_table("NOPE") is False


def test_get_table_returns_dataframe(sample_net):
    network = read_net(sample_net)
    assert isinstance(network.get_table("NODE"), pd.DataFrame)


def test_getitem_returns_dataframe(sample_net):
    network = read_net(sample_net)
    assert isinstance(network["NODE"], pd.DataFrame)


def test_getitem_missing_raises_keyerror(sample_net):
    network = read_net(sample_net)
    with pytest.raises(KeyError):
        network["NOPE"]


def test_nodes_is_real_dataframe(sample_net):
    network = read_net(sample_net)
    assert isinstance(network.nodes, pd.DataFrame)
    assert network.nodes.head().shape == (3, 9)


def test_shortcuts(sample_net):
    network = read_net(sample_net)
    assert isinstance(network.nodes, pd.DataFrame)
    assert isinstance(network.zones, pd.DataFrame)
    assert isinstance(network.turns, pd.DataFrame)
    assert isinstance(network.links, pd.DataFrame)  # present in this fixture


def test_shortcut_missing_raises(sample_net, tmp_path):
    small = tmp_path / "small.net"
    small.write_text("$NODE:NO\n1\n", encoding="utf-8")
    network = read_net(str(small))
    with pytest.raises(VisumNetError):
        network.links


def test_to_dict(sample_net):
    network = read_net(sample_net)
    data = network.to_dict()
    assert set(data) == set(network.table_names)
    assert all(isinstance(v, pd.DataFrame) for v in data.values())
    assert data["NODE"] is network.nodes


def test_table_names(sample_net):
    network = read_net(sample_net)
    assert isinstance(network.table_names, list)
    assert network.table_names[0] == "VISION"


def test_info(sample_net):
    network = read_net(sample_net)
    info = network.info()
    assert info["NODE"] == 3
    assert info["ZONE"] == 2


def test_contains(sample_net):
    network = read_net(sample_net)
    assert "NODE" in network
    assert "NOPE" not in network


def test_network_repr(sample_net):
    network = read_net(sample_net)
    assert "NODE" in repr(network) or "tables=" in repr(network)