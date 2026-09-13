"""Command line interface for :mod:`netload`."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="netload",
        description=(
            "Read and transform any PTV Visum/Simetra .net network file "
            "into CSV, JSON or GeoJSON."
        ),
    )
    parser.add_argument("input", help="Path to the .net file")
    parser.add_argument(
        "--list-tables",
        action="store_true",
        help="List the parsed tables with their fields (columns)",
    )
    parser.add_argument(
        "--export-csv",
        metavar="DIR",
        help="Export every table to CSV files inside DIR",
    )
    parser.add_argument(
        "--export-json",
        metavar="DIR",
        help="Export every table to JSON files inside DIR",
    )
    parser.add_argument(
        "--export-geojson",
        metavar="DIR",
        help="Export tables with geometry to GeoJSON files inside DIR",
    )
    parser.add_argument(
        "--tables",
        metavar="NAME[,NAME...]",
        help=(
            "Limit the export to specific tables (comma-separated, e.g. "
            "NODE,LINK). Default: all tables."
        ),
    )
    parser.add_argument(
        "--table",
        metavar="NAME",
        help="Select a single table to transform (used with --to-*)",
    )
    parser.add_argument(
        "--to-csv",
        metavar="FILE",
        help="Write the selected table to a CSV file",
    )
    parser.add_argument(
        "--to-json",
        metavar="FILE",
        help="Write the selected table to a JSON file",
    )
    parser.add_argument(
        "--to-geojson",
        metavar="FILE",
        help="Write the selected table to a GeoJSON file",
    )
    parser.add_argument(
        "--sep",
        default=";",
        help="Field separator used by the file and CSV export (default: ';')",
    )
    parser.add_argument(
        "--encoding",
        default=None,
        help="Force a file encoding (default: auto-detect)",
    )
    return parser


def _print_summary(tables: dict) -> None:
    print("Visum network loaded successfully")
    print()
    print("Tables:")
    for name, table in tables.items():
        print(f"- {name}: {len(table.df)} rows")


def _print_tables_with_fields(tables: dict) -> None:
    print("Visum network loaded successfully")
    print()
    print("Tables and fields:")
    for name, table in tables.items():
        fields = ", ".join(table.df.columns) or "(no columns)"
        print(f"- {name}: {len(table.df)} rows")
        print(f"    fields: {fields}")


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    from .parser import parse_net

    try:
        tables = parse_net(args.input, encoding=args.encoding, sep=args.sep)
    except FileNotFoundError:
        print(f"error: file not found: {args.input}", file=sys.stderr)
        return 2

    from .network import Network

    network = Network(tables, source=args.input, encoding="")

    if args.table is not None:
        return _transform_single_table(network, args)

    if args.list_tables:
        _print_tables_with_fields(network.tables)
    else:
        _print_summary(network.tables)

    written = []
    selected = None
    if args.tables:
        selected = [name.strip() for name in args.tables.split(",") if name.strip()]

    if args.export_csv:
        written += network.export_csv(args.export_csv, sep=args.sep, tables=selected)
        print(f"\nExported {len(written)} CSV files to {args.export_csv}")
    if args.export_json:
        written += network.export_json(args.export_json, tables=selected)
        print(f"\nExported {len(written)} JSON files to {args.export_json}")
    if args.export_geojson:
        written += network.export_geojson(args.export_geojson, tables=selected)
        print(f"\nExported {len(written)} GeoJSON files to {args.export_geojson}")

    return 0


def _transform_single_table(network: Network, args: argparse.Namespace) -> int:
    from .exceptions import VisumNetError
    from .exporters import export_table_csv, export_table_geojson, export_table_json

    if args.table not in network:
        print(
            f"error: table {args.table!r} not found. Available: "
            f"{', '.join(network.table_names)}",
            file=sys.stderr,
        )
        return 2

    targets = [
        flag
        for flag in ("to_csv", "to_json", "to_geojson")
        if getattr(args, flag) is not None
    ]
    if not targets:
        print("error: --table requires at least one of --to-csv/--to-json/--to-geojson",
              file=sys.stderr)
        return 2

    df = network[args.table]
    for flag in targets:
        path = getattr(args, flag)
        if flag == "to_csv":
            export_table_csv(df, path, sep=args.sep)
        elif flag == "to_json":
            export_table_json(df, path)
        else:
            if not export_table_geojson(df, path):
                print(
                    f"warning: table {args.table!r} has no geometry; "
                    f"GeoJSON not written",
                    file=sys.stderr,
                )
                continue
        print(f"Exported table {args.table} -> {path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())