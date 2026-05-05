from __future__ import annotations

from pathlib import Path

import pandas as pd

from .contracts import validate_portaria_schema, validate_relation_schema


def load_portarias_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return validate_portaria_schema(df)


def load_ti_municipio_table(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix in {".xlsx", ".xls"}:
        df = pd.read_excel(path)
    else:
        df = pd.read_csv(path)
    return validate_relation_schema(df)


def load_geo_layer(path: Path):
    """Lazy GeoPandas import to avoid hard dependency when not rendering map yet."""
    import geopandas as gpd  # type: ignore

    gdf = gpd.read_file(path)
    if gdf.crs is None:
        gdf = gdf.set_crs(epsg=4326)
    return gdf.to_crs(epsg=4326)
