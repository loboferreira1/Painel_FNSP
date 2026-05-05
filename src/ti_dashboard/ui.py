from __future__ import annotations

from datetime import date

import streamlit as st


def render_filters(
    default_start: date | None = None,
    default_end: date | None = None,
    state_options: list[str] | None = None,
    default_state: str | None = None,
):
    st.sidebar.header("Filtros")

    start = default_start or date.today()
    end = default_end or date.today()
    if start > end:
        start, end = end, start

    available_states = state_options or []
    state_choices = ["Todos"] + available_states
    selected_state = st.sidebar.selectbox(
        "Estado",
        options=state_choices,
        index=state_choices.index(default_state) if default_state in state_choices else 0,
        help="Filtra as portarias, TIs e processos pelo estado selecionado.",
    )

    mode = st.sidebar.radio("Modo temporal", ["Data unica", "Periodo"], index=1)

    if mode == "Data unica":
        selected_date = st.sidebar.slider(
            "Data",
            min_value=start,
            max_value=end,
            value=end,
            format="DD/MM/YYYY",
        )
        return {"mode": "single", "date": selected_date, "state": selected_state}

    st.sidebar.caption("Arraste os controles para selecionar o periodo dentro da janela de dados.")
    start_date, end_date = st.sidebar.slider(
        "Periodo",
        min_value=start,
        max_value=end,
        value=(start, end),
        format="DD/MM/YYYY",
    )
    return {"mode": "range", "start": start_date, "end": end_date, "state": selected_state}
