"""Pantalla Mercado: panorama general en un vistazo."""
import streamlit as st

from mci.formatting import short_money, price
from mci.sources.sentiment import LABELS_ES
from mci.state import open_asset
from mci.ui import charts
from mci.ui.components import change_chip, chip, esc, grid, kpi, md, section


def _movers(df, ascending, key):
    d = df[df["price_change_percentage_24h_in_currency"].notna()].sort_values(
        "price_change_percentage_24h_in_currency", ascending=ascending).head(5)
    for _, r in d.iterrows():
        a, b = st.columns([6, 1])
        a.markdown(f'<div class="mci-mover"><span><b>{esc(str(r["symbol"]).upper())}</b> '
                   f'<span class="mci-note">{esc(r["name"])} · {esc(price(r["current_price"]))}</span></span>'
                   f'{change_chip(r["price_change_percentage_24h_in_currency"])}</div>', unsafe_allow_html=True)
        b.button("→", key=f"{key}_{r['id']}", on_click=open_asset, args=(r["id"],), help="Abrir dossier")


def render(ctx):
    g = ctx.glob.data
    if g:
        cap = (g.get("total_market_cap") or {}).get("usd")
        vol = (g.get("total_volume") or {}).get("usd")
        chg = g.get("market_cap_change_percentage_24h_usd")
        btc = (g.get("market_cap_percentage") or {}).get("btc")
        eth = (g.get("market_cap_percentage") or {}).get("eth")
        src = "Mercado total"
    else:
        cap, vol, chg, btc, eth = ctx.all_df["market_cap"].sum(), ctx.all_df["total_volume"].sum(), None, None, None
        src = f"Top {len(ctx.all_df)} activos"
    grid([
        kpi(src + " · capitalización", short_money(cap), change_chip(chg) + " 24 h" if chg is not None else ""),
        kpi("Volumen 24 h", short_money(vol)),
        kpi("Dominancia de Bitcoin", f"{btc:.1f}%" if btc is not None else "—", f"Ethereum {eth:.1f}%" if eth is not None else ""),
        kpi("Activos en tu radar", f"{len(ctx.df):,}", f'<span class="mci-note">de {len(ctx.all_df):,} consultados</span>'),
    ])

    left, right = st.columns([2.3, 1])
    with left:
        section("Mapa del mercado", "tamaño = capitalización · color = variación 24 h")
        top = ctx.df.head(60)
        if len(top):
            st.plotly_chart(charts.treemap(top), config=charts.CONFIG)
    with right:
        section("Sentimiento", "no es un fundamento")
        fng = ctx.fng.data
        if fng:
            now = fng[0]
            st.plotly_chart(charts.fear_gauge(now["value"]), config=charts.CONFIG)
            md(f'<div style="text-align:center">{chip(LABELS_ES.get(now["label"].lower(), now["label"]), "accent")}</div>')
            extra = []
            if len(fng) > 1:
                extra.append(f"Ayer: {fng[1]['value']}")
            if len(fng) > 7:
                extra.append(f"Hace 7 d: {fng[7]['value']}")
            if len(fng) > 29:
                extra.append(f"Hace 30 d: {fng[-1]['value']}")
            md(f'<div class="mci-note" style="text-align:center;margin-top:6px">{esc(" · ".join(extra))}<br>Fuente: alternative.me</div>')
        else:
            md('<div class="mci-note">Índice de miedo y codicia no disponible ahora.</div>')

    c1, c2 = st.columns(2)
    with c1:
        section("Mayores subas", "24 h · universo filtrado")
        _movers(ctx.df, False, "up")
    with c2:
        section("Mayores bajas", "24 h · universo filtrado")
        _movers(ctx.df, True, "dn")
    md('<div class="mci-note">Una suba o baja fuerte de precio no es un fundamento. Abrí el dossier para ver qué evidencia hay.</div>')
