"""Example: export every table of a Visum .net file to CSV."""

from __future__ import annotations

import sys

from netload import read_net


def main(path: str, output_dir: str) -> None:
    network = read_net(path)
    written = network.export_csv(output_dir, sep=";", encoding="utf-8")
    for file in written:
        print(file)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: python export_csv.py model.net ./output")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])