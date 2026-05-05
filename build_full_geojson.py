"""Convert tis_poligonais.csv → full GeoJSON with reduced coordinate precision."""
from __future__ import annotations

import json
import sys
import unicodedata
from pathlib import Path

import pandas as pd
from shapely import wkt as shapely_wkt


PRECISION = 3  # decimal places for coordinates


def normalize_name(text: str) -> str:
    text = str(text or "").strip().lower()
    text = "".join(
        ch for ch in unicodedata.normalize("NFKD", text) if not unicodedata.combining(ch)
    )
    for prefix in ("terra indigena ", "ti "):
        if text.startswith(prefix):
            text = text[len(prefix):]
    text = text.replace("-", " ").replace("/", " ")
    return " ".join(text.split())


def round_coords(obj, precision: int):
    """Recursively round all coordinates in a GeoJSON geometry dict."""
    if isinstance(obj, list):
        if obj and isinstance(obj[0], (int, float)):
            return [round(c, precision) for c in obj]
        return [round_coords(item, precision) for item in obj]
    return obj


def geom_to_dict(geom, precision: int) -> dict:
    from shapely.geometry import mapping
    d = json.loads(json.dumps(mapping(geom)))
    d["coordinates"] = round_coords(d["coordinates"], precision)
    return d


def main() -> None:
    precision = PRECISION
    if len(sys.argv) > 1:
        try:
            precision = int(sys.argv[1])
        except ValueError:
            print(f"Invalid precision '{sys.argv[1]}', using default {PRECISION}")

    csv_path = Path("data/tis_poligonais.csv")
    out_path = Path("analysis_2025/outputs/dashboard_ready/tis_poligonais_raw.geojson")

    print(f"Reading {csv_path} ...")
    df = pd.read_csv(csv_path)
    print(f"  {len(df)} rows loaded")

    features = []
    errors = 0

    for _, row in df.iterrows():
        geom_wkt = row.get("the_geom")
        if not geom_wkt or pd.isna(geom_wkt):
            errors += 1
            continue
        try:
            geom = shapely_wkt.loads(str(geom_wkt))
        except Exception:
            errors += 1
            continue

        geom_dict = geom_to_dict(geom, precision)
        nome = str(row.get("terrai_nome", ""))
        feature = {
            "type": "Feature",
            "geometry": geom_dict,
            "properties": {
                "nome_exibicao": nome,
                "nome_canonico": normalize_name(nome),
                "uf": str(row.get("uf_sigla", "") or ""),
                "fase": str(row.get("fase_ti", "") or ""),
                "impacto": None,
            },
        }
        features.append(feature)

    print(f"  {len(features)} features built, {errors} skipped")

    geojson = {"type": "FeatureCollection", "features": features}

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, separators=(",", ":"))

    size_mb = out_path.stat().st_size / 1_048_576
    print(f"Written: {out_path}  ({size_mb:.1f} MB) with precision={precision}")


if __name__ == "__main__":
    main()
