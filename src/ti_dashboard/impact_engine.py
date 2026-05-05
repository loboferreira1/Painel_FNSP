from __future__ import annotations

import pandas as pd

from .transforms import normalize_key


def classify_ti_impacts(
    selected_portarias: pd.DataFrame,
    ti_municipio_rel: pd.DataFrame,
) -> pd.DataFrame:
    """Classify TI impacts as direto/indireto based on selected records.

    Direct: TI named in selected rows where tipo_informacao == terra_indigena.
    Indirect: TI touches a selected municipio via relation table.
    """
    direct_tis = set(
        normalize_key(v)
        for v in selected_portarias.loc[
            selected_portarias.get("tipo_informacao", "") == "terra_indigena", "informacao"
        ].dropna().astype(str)
    )

    selected_municipios = set(
        normalize_key(v)
        for v in selected_portarias.loc[
            selected_portarias.get("tipo_informacao", "") == "municipio", "informacao"
        ].dropna().astype(str)
    )

    rel = ti_municipio_rel.copy()
    rel["ti_key"] = rel["ti_nome"].astype(str).map(normalize_key)
    rel["mun_key"] = rel["municipio"].astype(str).map(normalize_key)

    rel["impacto"] = "sem_impacto"
    rel.loc[rel["mun_key"].isin(selected_municipios), "impacto"] = "indireto"
    rel.loc[rel["ti_key"].isin(direct_tis), "impacto"] = "direto"

    return rel[["ti_nome", "municipio", "impacto"]].drop_duplicates()
