from __future__ import annotations

import pandas as pd


REQUIRED_PORTARIA_COLUMNS = {
    "url",
    "date",
    "event_type",
    "portaria",
    "tipo_informacao",
    "informacao",
    "uf",
    "processo_numero",
    "processo_tipo",
    "datas_mencionadas",
}

REQUIRED_RELATION_COLUMNS = {
    "ti_nome",
    "municipio",
}


class SchemaError(ValueError):
    pass


def _check_required(df: pd.DataFrame, required: set[str], source_name: str) -> None:
    missing = required - set(df.columns)
    if missing:
        raise SchemaError(f"{source_name} is missing required columns: {sorted(missing)}")


def validate_portaria_schema(df: pd.DataFrame) -> pd.DataFrame:
    _check_required(df, REQUIRED_PORTARIA_COLUMNS, "portaria dataset")
    return df


def validate_relation_schema(df: pd.DataFrame) -> pd.DataFrame:
    _check_required(df, REQUIRED_RELATION_COLUMNS, "TI-municipio relation dataset")
    return df
