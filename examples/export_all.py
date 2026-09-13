"""Example: export tables to CSV, JSON and GeoJSON."""

from __future__ import annotations

import sys

from netload import read_net


def main(path: str, output_dir: str) -> None:
    network = read_net(path)

    csv_files = network.export_csv(output_dir)
    print(f"CSV: {len(csv_files)} files")

    json_files = network.export_json(output_dir)
    print(f"JSON: {len(json_files)} files")

    geojson_files = network.export_geojson(output_dir)
    print(f"GeoJSON: {len(geojson_files)} files")

    for name in ("NODE", "ZONE", "LINK"):
        if network.has_table(name):
            frame = network[name]
            from netload.exporters import export_table_geojson

            ok = export_table_geojson(frame, f"{output_dir}/{name}_single.geojson")
            print(f"{name}_single.geojson: {'written' if ok else 'no geometry'}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: python export_all.py model.net ./output")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])