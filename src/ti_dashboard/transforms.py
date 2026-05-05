from __future__ import annotations

import json

import pandas as pd


def parse_json_list(value) -> list:
    if value is None:
        return []
    if isinstance(value, float) and pd.isna(value):
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return []
        return parsed if isinstance(parsed, list) else [parsed]
    return []


def build_portaria_grain(df: pd.DataFrame) -> pd.DataFrame:
    """Reduce repeated entity rows to one row per URL for KPIs/timeline."""
    key_cols = [c for c in ["url", "date", "portaria", "event_type", "processo_numero", "processo_tipo", "datas_mencionadas"] if c in df.columns]
    return df[key_cols].drop_duplicates(subset=["url"]).copy()


def normalize_key(text: str) -> str:
    return " ".join(str(text).strip().lower().split())
