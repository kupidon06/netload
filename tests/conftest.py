"""Shared fixtures and path setup for the test suite."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent / "src"
FIXTURES = Path(__file__).resolve().parent / "fixtures"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


@pytest.fixture
def sample_net() -> str:
    return str(FIXTURES / "sample.net")


@pytest.fixture
def cp1251_net(tmp_path) -> str:
    """A copy of the sample fixture encoded in Windows-1251."""
    raw = (FIXTURES / "sample.net").read_bytes()
    text = raw.decode("utf-8")
    target = tmp_path / "sample_cp1251.net"
    target.write_bytes(text.encode("cp1251"))
    return str(target)


@pytest.fixture
def utf8_bom_net(tmp_path) -> str:
    """The sample fixture with a UTF-8 BOM."""
    raw = (FIXTURES / "sample.net").read_bytes()
    target = tmp_path / "sample_bom.net"
    target.write_bytes(b"\xef\xbb\xbf" + raw)
    return str(target)