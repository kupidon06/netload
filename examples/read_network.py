"""Example: read a Visum .net file and print a summary."""

from __future__ import annotations

import sys

from netload import read_net


def main(path: str) -> None:
    network = read_net(path)
    print(f"Loaded: {path}")
    print(f"Encoding: {network.encoding}")
    print(f"Tables: {len(network.table_names)}")
    for name, table in network.tables.items():
        print(f"  - {name}: {len(table.df)} rows, {table.df.shape[1]} columns")

    for shortcut in ("nodes", "links", "zones", "turns"):
        if network.has_table(shortcut.upper()):
            frame = getattr(network, shortcut)
            print(f"\n{shortcut.upper()}.head():")
            print(frame.head())


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python read_network.py model.net")
        sys.exit(1)
    main(sys.argv[1])