from __future__ import annotations

import json
import unicodedata
from pathlib import Path

import pydeck as pdk
import streamlit as st


def _fill_color(feature: dict) -> list[int]:
    props = feature.get("properties", {})
    impacto = str(props.get("impacto", "")).lower()
    if impacto == "direto":
        return [204, 46, 64, 180]
    if impacto == "indireto":
        return [245, 158, 11, 170]
    return [55, 114, 255, 120]


def _normalize_ti_key(value: str) -> str:
    text = str(value or "").strip().lower()
    text = "".join(
        ch for ch in unicodedata.normalize("NFKD", text) if not unicodedata.combining(ch)
    )
    for prefix in ("terra indigena ", "ti "):
        if text.startswith(prefix):
            text = text[len(prefix):]
    text = text.replace("-", " ").replace("/", " ")
    return " ".join(text.split())


def render_ti_map(
    geojson_path: Path,
    ti_portaria_map: dict[str, str] | None = None,
    direto_tis: set[str] | None = None,
    indireto_tis: set[str] | None = None,
) -> None:
    if not geojson_path.exists():
        st.warning(f"GeoJSON nao encontrado: {geojson_path}")
        return

    with geojson_path.open("r", encoding="utf-8") as f:
        geojson = json.load(f)

    features = geojson.get("features", [])
    if not features:
        st.warning("O GeoJSON foi carregado, mas nao possui feicoes.")
        return

    # Attach precomputed color so the deck layer can consume it declaratively.
    direto_set: set[str] = direto_tis or set()
    indireto_set: set[str] = indireto_tis or set()
    visible_features: list[dict] = []

    for ft in features:
        props = ft.setdefault("properties", {})
        canonical_key = _normalize_ti_key(props.get("nome_canonico", ""))
        display_key = _normalize_ti_key(props.get("nome_exibicao", ""))

        if canonical_key in direto_set or display_key in direto_set:
            impacto = "direto"
        elif canonical_key in indireto_set or display_key in indireto_set:
            impacto = "indireto"
        else:
            impacto = ""
        props["impacto"] = impacto
        if impacto in {"direto", "indireto"}:
            props["fill_color"] = _fill_color(ft)
            visible_features.append(ft)

        if ti_portaria_map:
            canonical_key = _normalize_ti_key(props.get("nome_canonico", ""))
            display_key = _normalize_ti_key(props.get("nome_exibicao", ""))
            props["portaria_ref"] = ti_portaria_map.get(
                canonical_key,
                ti_portaria_map.get(display_key, "Sem portaria no periodo"),
            )
        else:
            props["portaria_ref"] = "Sem portaria no periodo"

    if not visible_features:
        st.info("Nenhuma TI direta/indireta no periodo selecionado.")
        return

    layer = pdk.Layer(
        "GeoJsonLayer",
        data={"type": "FeatureCollection", "features": visible_features},
        get_fill_color="properties.fill_color",
        get_line_color=[20, 20, 20, 180],
        line_width_min_pixels=1,
        pickable=True,
        auto_highlight=True,
        stroked=True,
        filled=True,
    )

    view_state = pdk.ViewState(latitude=-10.0, longitude=-55.0, zoom=3.8)

    tooltip = {
        "html": (
            "<b>{nome_exibicao}</b><br/>"
            "Portaria(s): {portaria_ref}"
        ),
        "style": {"backgroundColor": "#0f172a", "color": "white"},
    }

    st.pydeck_chart(
        pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            map_style="https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json",
            tooltip=tooltip,
        ),
        use_container_width=True,
    )

    st.caption(f"Poligonos de TIs renderizados: {len(visible_features)}")
