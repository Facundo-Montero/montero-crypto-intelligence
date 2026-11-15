"""Pantalla Comparar: hasta 4 activos lado a lado."""
import pandas as pd
import streamlit as st

from mci.data import load_chart
from mci.formatting import price, short_money
from mci.ui import charts
from mci.ui.components import esc, evidence_bar, md, section

ROWS = [
    ("Precio", lambda r, e, d, c: price(r.get("current_price"))),
    ("Capitalización", lambda r, e, d, c: short_money(e["cap"].value) if "cap" in e else "—"),
    ("Volumen 24 h", lambda r, e, d, c: short_money(e["vol"].value) if "vol" in e else "—"),
    ("Volumen / cap.", lambda r, e, d, c: e["vol_cap"].display if "vol_cap" in e else "—"),
    ("FDV / cap.", lambda r, e, d, c: e["fdv_cap"].display if "fdv_cap" in e else "—"),
    ("Circulante / máx.", lambda r, e, d, c: e["circ_max"].display if "circ_max" in e else "—"),
    ("TVL", lambda r, e, d, c: short_money(e["tvl"].value) if "tvl" in e else "—"),
    ("Comisiones 30 d", lambda r, e, d, c: short_money(e["fees_30d"].value) if "fees_30d" in e else "—"),
    ("Cap. / comisiones anualiz.", lambda r, e, d, c: e["cap_fees"].display if "cap_fees" in e else "—"),
    ("Variación 30 d", lambda r, e, d, c: e["p30"].display if "p30" in e else "—"),
    ("Variación 1 año", lambda r, e, d, c: e["p1y"].display if "p1y" in e else "—"),
    ("Tipo (heurística)", lambda r, e, d, c: c),
    ("Evidencia (de 7)", lambda r, e, d, c: f"{sum(1 for x in d if x.status != 'sin_datos')}/7"),
]


def render(ctx):
    watch = [w for w in st.session_state.get("watch", []) if w in ctx.labels]
    default = (watch or [i for i in ("bitcoin", "ethereum") if i in ctx.labels] or ctx.all_ids[:2])[:4]
    picks = st.multiselect("Activos a comparar", ctx.all_ids, default=default, max_selections=4,
                           format_func=lambda i: ctx.labels[i], placeholder="Elegí 2 a 4 activos…",
                           label_visibility="collapsed")
    if len(picks) < 2:
        st.info("Elegí al menos 2 activos para compararlos.")
        return

    section("Rendimiento relativo", "base 100 al inicio del período")
    rng = st.radio("Período", ["30 d", "90 d", "1 año"], index=1, horizontal=True, key="cmp_range", label_visibility="collapsed")
    series, notes = {}, []
    for pid in picks:
        ch = load_chart(pid, ctx.api_key)
        if ch.data:
            series[ctx.by_id[pid]["symbol"].upper()] = ch.data
        else:
            notes.append(f"{ctx.labels[pid]}: {ch.error}")
    if series:
        st.plotly_chart(charts.compare_chart(series, {"30 d": 30, "90 d": 90, "1 año": 365}[rng]), config=charts.CONFIG)
    for n in notes:
        md(f'<div class="mci-note">Historial no disponible — {esc(n)}</div>')

    section("Datos lado a lado", "hechos y estimaciones con las fuentes ya integradas")
    data = {}
    for pid in picks:
        ev, dims, cls = ctx.quick[pid]
        data[ctx.by_id[pid]["symbol"].upper()] = [fn(ctx.by_id[pid], ev, dims, cls) for _, fn in ROWS]
    st.dataframe(pd.DataFrame(data, index=[n for n, _ in ROWS]), width="stretch", height=40 + 35 * len(ROWS))
    md("".join(f'<div style="margin:6px 0"><b>{esc(ctx.by_id[p]["symbol"].upper())}</b>'
               f'{evidence_bar(ctx.quick[p][1])}</div>' for p in picks))
    md('<div class="mci-note">Comparar números no equivale a elegir: sectores distintos tienen métricas distintas. '
       'Para el detalle y las fuentes, abrí cada dossier.</div>')
