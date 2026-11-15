"""Pantalla Radar: explorar, filtrar y abrir un activo con un toque."""
import pandas as pd
import streamlit as st

from mci.state import open_asset

SORTS = {
    "Capitalización": ("market_cap", False),
    "Más evidencia": ("cov", False),
    "Mayor suba 24 h": ("price_change_percentage_24h_in_currency", False),
    "Mayor suba 7 d": ("price_change_percentage_7d_in_currency", False),
    "Mayor suba 30 d": ("price_change_percentage_30d_in_currency", False),
    "Más volumen / capitalización": ("vol_cap", False),
    "Menor capitalización / comisiones": ("cap_fees", True),
}


def _on_select():
    ss = st.session_state
    key = f"radar_{ss['radar_nonce']}"
    try:
        rows = ss[key]["selection"]["rows"]
    except Exception:
        return
    ids = ss.get("_radar_ids", [])
    if rows and rows[0] < len(ids):
        ss["radar_nonce"] += 1          # limpia la selección al volver
        open_asset(ids[rows[0]])


def render(ctx):
    df = ctx.df.copy()
    c1, c2 = st.columns([2, 3])
    q = c1.text_input("Buscar", placeholder="Buscar: Bitcoin, ETH, LINK…", label_visibility="collapsed")
    tipos = sorted(df["clasificacion"].unique().tolist())
    chosen = c2.pills("Tipo", tipos, selection_mode="multi", default=tipos, label_visibility="collapsed")
    t1, t2, t3 = st.columns([1, 1, 2])
    only_fund = t1.toggle("Con fundamentos", help="Solo activos con TVL o comisiones en DefiLlama")
    only_watch = t2.toggle("Mi lista ★")
    order = t3.selectbox("Ordenar por", list(SORTS), label_visibility="collapsed")

    if chosen:
        df = df[df["clasificacion"].isin(chosen)]
    if q:
        df = df[df["name"].str.contains(q, case=False, na=False) | df["symbol"].str.contains(q, case=False, na=False)]
    if only_fund:
        df = df[df["tvl"].notna() | df["fees_30d"].notna()]
    if only_watch:
        df = df[df["id"].isin(st.session_state.get("watch", []))]
    col, asc = SORTS[order]
    df = df.sort_values([col, "market_cap"], ascending=[asc, False], na_position="last")

    if df.empty:
        st.info("Ningún activo coincide con los filtros.")
        return
    df = df.head(250).reset_index(drop=True)
    st.session_state["_radar_ids"] = df["id"].tolist()

    table = pd.DataFrame({
        "Activo": df["name"] + " · " + df["symbol"].str.upper(), "Tipo": df["clasificacion"],
        "Precio (US$)": df["current_price"],
        "7 d": df["spark"],
        "24 h": df["price_change_percentage_24h_in_currency"],
        "7 d %": df["price_change_percentage_7d_in_currency"],
        "Cap. (US$)": df["market_cap"], "Volumen (US$)": df["total_volume"],
        "TVL (US$)": df["tvl"], "Cap./comisiones": df["cap_fees"], "Evidencia": df["cov"],
    })
    cc = st.column_config
    st.dataframe(
        table, hide_index=True, height=min(600, 38 + 35 * len(table)), key=f"radar_{st.session_state['radar_nonce']}",
        on_select=_on_select, selection_mode="single-row",
        column_config={
            "Activo": cc.TextColumn(width="medium"), "Tipo": cc.TextColumn(width="medium"),
            "Precio (US$)": cc.NumberColumn(format="$%.6g"),
            "7 d": cc.LineChartColumn(width="small"),
            "24 h": cc.NumberColumn("24 h %", format="%+.1f%%"),
            "7 d %": cc.NumberColumn(format="%+.1f%%"),
            "Cap. (US$)": cc.NumberColumn(format="compact"), "Volumen (US$)": cc.NumberColumn(format="compact"),
            "TVL (US$)": cc.NumberColumn(format="compact"),
            "Cap./comisiones": cc.NumberColumn(format="%.0fx", help="Capitalización ÷ comisiones anualizadas (DefiLlama). Menor = valoración más baja frente a la actividad."),
            "Evidencia": cc.ProgressColumn(width="small", min_value=0, max_value=7, format="%d/7",
                                           help="Dimensiones con algún dato. Desarrollo se evalúa al abrir el dossier."),
        })
    st.caption(f"{len(df)} activos · tocá una fila para abrir su dossier · datos de CoinGecko y DefiLlama")
