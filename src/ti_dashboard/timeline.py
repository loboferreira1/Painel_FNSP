from __future__ import annotations

import pandas as pd


def derive_validity_windows(portaria_df: pd.DataFrame) -> pd.DataFrame:
    """Initial heuristic: use publication date as both start and end.

    This is a placeholder until explicit data_inicio/data_fim extraction is available.
    """
    df = portaria_df.copy()
    if "date" in df.columns:
        df["valid_from"] = pd.to_datetime(df["date"], errors="coerce")
        df["valid_to"] = pd.to_datetime(df["date"], errors="coerce")
    else:
        df["valid_from"] = pd.NaT
        df["valid_to"] = pd.NaT
    return df


def filter_by_period(df: pd.DataFrame, start_date, end_date) -> pd.DataFrame:
    mask = (df["valid_from"] <= pd.to_datetime(end_date)) & (df["valid_to"] >= pd.to_datetime(start_date))
    return df.loc[mask].copy()
