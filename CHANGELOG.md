# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-09-13

### Added

- `read_net()` public API to parse `.net` network files (PTV Visum / Simetra and other exports).
- Generic table parser supporting any `$` section (NODE, LINK, ZONE, TURN, USERATTDEF, …).
- Automatic encoding detection: UTF-8 (with/without BOM), Windows-1251/CP1251, UTF-16.
- Pandas `DataFrame` representation for every table.
- CSV export via `network.export_csv()`.
- JSON export via `network.export_json()`.
- GeoJSON export via `network.export_geojson()` (WKT columns or XCOORD/YCOORD as Points).
- Single-table transforms: `export_table_csv`, `export_table_json`, `export_table_geojson`.
- Built-in WKT → GeoJSON parser (`netload.wkt`), no shapely required.
- Convenience API: `tables`, `table_names`, `has_table`, `get_table`, `to_dict`, shortcuts
  `nodes`/`links`/`zones`/`turns`.
- Explicit exceptions: `VisumNetError`, `VisumNetParseError`, `VisumNetEncodingError`.
- Command-line interface `netload`: summary, `--list-tables` (with fields), `--preview NAME [--rows N]`,
  `--export-csv/--export-json/--export-geojson`, and `--table … --to-csv/--to-json/--to-geojson`.
- Test suite covering parsing, encoding, edge cases, CSV/JSON/GeoJSON export and WKT conversion.