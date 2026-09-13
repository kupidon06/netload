# netload

A lightweight, dependency-light **Python parser for `.net` network files** (PTV Visum / Simetra
and other `.net` text exports).

It reads the structured text tables of a `.net` file directly, without requiring PTV Visum to be
installed, exposes every table as a **Pandas `DataFrame`**, and can transform any table (or the whole
file) into **CSV**, **JSON** or **GeoJSON**.

> **Disclaimer:** This project is **independent** and is **not affiliated with, endorsed by, or
> supported by PTV Group** or its partners. `PTV Visum` is a registered trademark of PTV Group.

---

## Features

- Parses `.net` files generically: `NODE`, `LINK`, `ZONE`, `TURN`, `USERATTDEF` and **any other table**
  present in the file.
- No PTV Visum required.
- Every table is exposed as a real `pandas.DataFrame`.
- Automatic encoding detection (UTF-8 with/without BOM, Windows-1251/CP1251, UTF-16), so Russian and
  other non-ASCII content is read correctly.
- Robust to comments (`*`), blank lines, BOM markers and missing values.
- Export the whole file to **CSV**, **JSON** or **GeoJSON** in one call.
- Transform a single table to CSV / JSON / GeoJSON (via the API or the CLI).
- GeoJSON conversion uses WKT columns (`WKTSURFACE`, `WKTPOLY`, `GEOMETRY`) or `XCOORD`/`YCOORD`
  with a built-in WKT parser (no shapely needed).
- List every table with its fields (columns).
- Small command-line interface.

## Installation

```bash
pip install netload
```

## Quick example

```python
from netload import read_net

network = read_net("model.net")

print(network.table_names)

print(network.nodes.head())

network.export_csv("./output")
```

Resulting files:

```text
output/
├── NODE.csv
├── LINK.csv
├── ZONE.csv
└── TURN.csv
```

## API

### Reading

```python
from netload import read_net

network = read_net("model.net")                 # auto-detect encoding
network = read_net("model.net", encoding="cp1251")
network = read_net("model.net", infer_types=True)  # light numeric inference
```

The returned `Network` object:

| Member                 | Description                                            |
| ---------------------- | ------------------------------------------------------ |
| `network.tables`       | `dict` of table name → `Table` (preserves file order)  |
| `network.table_names`  | `list[str]` of table names                             |
| `network.has_table(x)` | whether table `x` exists                               |
| `network.get_table(x)` | DataFrame of table `x`                                 |
| `network[x]`           | DataFrame of table `x`                                 |
| `network.nodes`        | DataFrame of `NODE` (if present)                       |
| `network.links`        | DataFrame of `LINK` (if present)                       |
| `network.zones`        | DataFrame of `ZONE` (if present)                       |
| `network.turns`        | DataFrame of `TURN` (if present)                       |
| `network.to_dict()`    | `dict[str, pd.DataFrame]`                              |
| `network.export_csv()` | writes one CSV per table (see below)                   |
| `network.export_json()`| writes one JSON per table (see below)                  |
| `network.export_geojson()` | writes GeoJSON for tables with geometry (see below) |

### Export CSV

```python
network.export_csv("./output", sep=";", encoding="utf-8")
```

Tables without any data row are skipped by default (`skip_empty=False` to include them).

### Export a single table (or a subset)

By default **all tables** are exported. Pass `tables=[...]` to export only specific tables:

```python
network.export_csv("./output", tables=["NODE"])          # NODE.csv only
network.export_csv("./output", tables=["NODE", "LINK"])  # NODE.csv + LINK.csv
network.export_json("./output", tables=["ZONE"])
network.export_geojson("./output", tables=["ZONE", "LINK"])
```

The same applies to the CLI with `--tables NODE,LINK`.

### Export JSON

```python
network.export_json("./output")   # writes NODE.json, LINK.json, ZONE.json, ...
```

Each file contains a JSON array of records (Russian characters are kept as-is, not escaped).

### Export GeoJSON

```python
network.export_geojson("./output")  # writes NODE.geojson, ZONE.geojson, LINK.geojson, ...
```

Tables that have geometry are exported as GeoJSON `FeatureCollection` files:

- tables with a WKT column (`WKTSURFACE`, `WKTPOLY`, `GEOMETRY`) use its geometry
  (e.g. `ZONE` → `MultiPolygon`, `LINK` → `LineString`);
- tables with `XCOORD`/`YCOORD` become Point features (e.g. `NODE`);
- tables without any geometry are skipped.

### Transform a single table

```python
from netload.exporters import export_table_csv, export_table_json, export_table_geojson

export_table_json(network["NODE"], "node.json")
export_table_geojson(network["ZONE"], "zone.geojson")
export_table_csv(network["LINK"], "link.csv")
```

### Errors

```python
from netload import VisumNetError, VisumNetParseError, VisumNetEncodingError
```

- Missing file → `FileNotFoundError`
- Invalid structure → `VisumNetParseError` (includes file path and line number)
- Undecodable file → `VisumNetEncodingError`

## CLI

```bash
netload model.net
```

```text
Visum network loaded successfully

Tables:
- NODE: 1542 rows
- LINK: 3210 rows
- ZONE: 145 rows
- TURN: 872 rows
```

List tables with their fields:

```bash
netload model.net --list-tables
```

```text
Tables and fields:
- NODE: 1542 rows
    fields: NO, NAME, CONTROLTYPE, T0PRT, ...
```

Preview a table (fields + first 5 rows by default):

```bash
netload model.net --preview NODE
netload model.net --preview NODE --rows 10
```

Export everything:

```bash
netload model.net --export-csv ./output
netload model.net --export-json ./output
netload model.net --export-geojson ./output
```

Export only specific tables (default: all):

```bash
netload model.net --export-csv ./output --tables NODE,LINK
netload model.net --export-json ./output --tables ZONE
```

Transform a single table:

```bash
netload model.net --table NODE --to-csv node.csv
netload model.net --table NODE --to-json node.json
netload model.net --table ZONE --to-geojson zone.geojson
```

Force a file encoding:

```bash
netload model.net --encoding cp1251 --list-tables
```

## Tables

The parser is **generic**: it does not hard-code the set of supported tables. Any section starting
with `$` is parsed and made available, for example:

- `NODE`
- `LINK`
- `ZONE`
- `TURN`
- `MAINTURN`
- `CONNECTOR`
- `LINKTYPE`
- `TSYS`
- `LINE`, `LINEROUTE`, `TIMEPROFILE`, `VEHJOURNEY`, …
- `USERATTDEF`
- `VERSION`, `NETWORK`, …

If a file contains a table that is not listed here, it is parsed and exposed the same way.

## How it works

1. The file bytes are read and the encoding is detected (BOM first, then UTF-8, then CP1251).
2. The text is scanned line by line.
3. A line starting with `$NAME:COL1;COL2;...` opens a new table with its columns.
4. Following non-comment, non-blank lines are parsed as `;`-separated data rows.
5. Each table becomes a `pandas.DataFrame` (original string values are preserved by default).

## Limitations (v0.1.0)

- Values are treated as `;`-separated fields; quoted fields containing the separator character are
  not yet supported.
- Optional light numeric type inference is available via `infer_types=True`, but the default
  preserves the original string values to avoid any data corruption.
- Multi-line records and nested sub-tables are not supported yet.
- The built-in WKT parser covers `POINT`, `LINESTRING`, `POLYGON`, `MULTIPOINT`, `MULTILINESTRING`
  and `MULTIPOLYGON` (the geometry types used by `.net` files).

## Development

```bash
python -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/python -m pytest
```

## License

MIT. See [LICENSE](LICENSE).

## Disclaimer

This project is **independent** and **not affiliated with PTV Group**. PTV Visum is a registered
trademark of PTV Group. This package is provided "as is", without any warranty.