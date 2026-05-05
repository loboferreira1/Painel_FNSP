from __future__ import annotations

import sys
import re
import unicodedata
from pathlib import Path

import streamlit as st

# Handle both package and direct execution
_pkg_root = Path(__file__).resolve().parent.parent.parent
if str(_pkg_root) not in sys.path:
    sys.path.insert(0, str(_pkg_root))

from src.ti_dashboard.config import DEFAULT_CONFIG
from src.ti_dashboard.loaders import load_portarias_csv, load_ti_municipio_table
from src.ti_dashboard.map_view import render_ti_map
from src.ti_dashboard.timeline import derive_validity_windows, filter_by_period
from src.ti_dashboard.transforms import build_portaria_grain, normalize_key, parse_json_list
from src.ti_dashboard.ui import render_filters


st.set_page_config(page_title="Forca Nacional - Mapa de TIs", layout="wide")


MISSING_UF_LABEL = "Sem UF informado"
ALL_STATES_LABEL = "Todos"


def _strip_accents(text: str) -> str:
    return "".join(
        ch for ch in unicodedata.normalize("NFKD", text) if not unicodedata.combining(ch)
    )


def _normalize_ti_key(value: str) -> str:
    text = normalize_key(_strip_accents(str(value or "")))
    for prefix in ("terra indigena ", "ti "):
        if text.startswith(prefix):
            text = text[len(prefix):]
    text = text.replace("-", " ").replace("/", " ")
    return normalize_key(text)


def _extract_admin_processes(df) -> list[str]:
    if "processo_tipo" not in df.columns or "processo_numero" not in df.columns:
        return []

    proc_df = df.copy()
    proc_df = proc_df[
        proc_df["processo_tipo"].astype(str).str.contains("administr", case=False, na=False)
    ]

    values = set()
    for raw in proc_df["processo_numero"].tolist():
        parsed = parse_json_list(raw)
        if parsed:
            for item in parsed:
                item_str = str(item).strip()
                if item_str:
                    values.add(item_str)
            continue

        raw_str = str(raw).strip()
        if raw_str and raw_str not in {"[]", "nan", "None"}:
            values.add(raw_str)

    return sorted(values)


def _clean_ti_display_name(value: str) -> str:
    text = str(value or "").strip()
    text = re.sub(r"^terra\s+ind[ií]gena\s+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^ti\s+", "", text, flags=re.IGNORECASE)
    return text.strip()


def _extract_affected_tis(df) -> list[str]:
    if df.empty or not {"tipo_informacao", "informacao"}.issubset(df.columns):
        return []

    ti_values = df.loc[
        df["tipo_informacao"].astype(str).str.lower() == "terra_indigena", "informacao"
    ].dropna()

    by_key: dict[str, str] = {}
    for raw in ti_values:
        raw_str = str(raw).strip()
        if not raw_str:
            continue
        key = _normalize_ti_key(raw_str)
        if not key:
            continue
        candidate = _clean_ti_display_name(raw_str)
        chosen = by_key.get(key)
        if chosen is None or len(candidate) < len(chosen):
            by_key[key] = candidate

    return sorted(set(by_key.values()))


def _build_ti_portaria_map(df) -> dict[str, str]:
    if "tipo_informacao" not in df.columns or "informacao" not in df.columns:
        return {}

    ti_df = df[df["tipo_informacao"].astype(str).str.lower() == "terra_indigena"].copy()
    if ti_df.empty:
        return {}

    ti_df["ti_key"] = ti_df["informacao"].astype(str).map(_normalize_ti_key)
    ti_df["portaria_label"] = ti_df.get("portaria", "").fillna("").astype(str).str.strip()

    out: dict[str, str] = {}
    for ti_key, group in ti_df.groupby("ti_key"):
        labels = sorted({v for v in group["portaria_label"].tolist() if v})
        if not labels:
            out[ti_key] = "Sem portaria no periodo"
            continue

        shown = labels[:3]
        suffix = " ..." if len(labels) > 3 else ""
        out[ti_key] = ", ".join(shown) + suffix

    return out


def _build_state_options(df) -> list[str]:
    if "uf" not in df.columns:
        return []

    uf_series = df["uf"].fillna("").astype(str).str.strip().str.upper()
    options = sorted({value for value in uf_series if value})
    if (uf_series == "").any():
        options.append(MISSING_UF_LABEL)
    return options


def _filter_rows_by_state(df, selected_state: str) -> tuple:
    if df.empty or "uf" not in df.columns:
        return df.copy(), selected_state

    available_states = _build_state_options(df)
    normalized_selection = selected_state or ALL_STATES_LABEL
    if normalized_selection == ALL_STATES_LABEL:
        return df.copy(), ALL_STATES_LABEL

    uf_series = df["uf"].fillna("").astype(str).str.strip().str.upper()
    if normalized_selection == MISSING_UF_LABEL:
        mask = uf_series == ""
    else:
        mask = uf_series == normalized_selection

    matching_urls = set(df.loc[mask, "url"].dropna().astype(str))
    return df[df["url"].astype(str).isin(matching_urls)].copy(), normalized_selection


def _count_no_period_indicated(df) -> int:
    if df.empty or "url" not in df.columns or "datas_mencionadas" not in df.columns:
        return 0

    portaria_df = df[["url", "datas_mencionadas"]].drop_duplicates(subset=["url"]).copy()
    values = portaria_df["datas_mencionadas"].fillna("").astype(str).str.strip()
    empty_mask = values.isin({"", "[]", "nan", "None"})
    return int(empty_mask.sum())


def main() -> None:
    st.title("Forca Nacional - Mapa de Impacto em TIs")
    st.caption("Painel geoespacial de acompanhamento")

    portarias = load_portarias_csv(DEFAULT_CONFIG.portarias_csv)
    rel = load_ti_municipio_table(DEFAULT_CONFIG.ti_municipio_table)

    min_date = None
    max_date = None
    state_options = _build_state_options(portarias)
    if "date" in portarias.columns:
        valid_dates = portarias["date"].dropna()
        if not valid_dates.empty:
            min_date = valid_dates.min().date()
            max_date = valid_dates.max().date()

    filters = render_filters(
        default_start=min_date,
        default_end=max_date,
        state_options=state_options,
        default_state=ALL_STATES_LABEL,
    )

    portaria_grain = build_portaria_grain(portarias)
    timeline_df = derive_validity_windows(portaria_grain)

    if filters["mode"] == "single":
        start_date = filters["date"]
        end_date = filters["date"]
    else:
        start_date = filters["start"]
        end_date = filters["end"]

    period_timeline = filter_by_period(timeline_df, start_date, end_date)
    period_urls = set(period_timeline["url"].dropna().astype(str))
    period_rows = portarias[portarias["url"].astype(str).isin(period_urls)].copy()
    period_rows, active_state = _filter_rows_by_state(period_rows, filters.get("state", ALL_STATES_LABEL))
    selected_urls = set(period_rows["url"].dropna().astype(str))

    has_ti_by_url = (
        period_rows.assign(
            is_ti=period_rows.get("tipo_informacao", "").astype(str).str.lower() == "terra_indigena"
        )
        .groupby("url", dropna=False)["is_ti"]
        .any()
        if not period_rows.empty
        else None
    )
    no_ti_count = int((~has_ti_by_url).sum()) if has_ti_by_url is not None else 0
    no_period_count = _count_no_period_indicated(period_rows)

    affected_tis = _extract_affected_tis(period_rows)

    admin_processes = _extract_admin_processes(period_rows)
    ti_portaria_map = _build_ti_portaria_map(period_rows)

    st.sidebar.subheader("Resumo do periodo")
    st.sidebar.metric("Portarias no periodo", len(selected_urls))
    st.sidebar.metric("Sem indicacao de TI", no_ti_count)
    st.sidebar.metric("Sem periodo indicado", no_period_count)
    if active_state:
        st.sidebar.caption(f"Estado ativo: {active_state}")

    st.sidebar.subheader("TIs afetadas")
    if affected_tis:
        st.sidebar.write("\n".join(f"- {name}" for name in affected_tis))
    else:
        st.sidebar.caption("Nenhuma TI afetada no periodo selecionado.")

    st.sidebar.subheader("Processos administrativos")
    if admin_processes:
        st.sidebar.write("\n".join(f"- {proc}" for proc in admin_processes))
    else:
        st.sidebar.caption("Nenhum processo administrativo no periodo selecionado.")

    c1, c2, c3 = st.columns(3)
    c1.metric("Portarias (URL unica)", len(portaria_grain))
    c2.metric("Portarias no periodo", len(selected_urls))
    c3.metric("Sem indicacao de TI (periodo)", no_ti_count)

    st.caption(f"Relacoes TI-municipio carregadas: {len(rel)}")

    st.subheader("Mapa de Terras Indigenas")
    render_ti_map(DEFAULT_CONFIG.ti_shapefile, ti_portaria_map=ti_portaria_map)


if __name__ == "__main__":
    main()
