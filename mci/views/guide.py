"""Pantalla Guía: cómo leer MCI, en poco texto."""
import pandas as pd
import streamlit as st

from mci.analysis.rules import THRESHOLDS
from mci.analysis.verdict import DIMENSIONS
from mci.formatting import fmt_dt
from mci.ui.components import chip, esc, grid, md, section


def render(ctx):
    section("Cómo usarla")
    grid([
        '<div class="mci-kpi"><div class="l">1 · Mercado</div><div class="s" style="color:var(--text);font-size:.92rem">Mirá el panorama: mapa, sentimiento y mayores movimientos.</div></div>',
        '<div class="mci-kpi"><div class="l">2 · Radar</div><div class="s" style="color:var(--text);font-size:.92rem">Filtrá y ordenás. Tocá una fila para abrir el dossier.</div></div>',
        '<div class="mci-kpi"><div class="l">3 · Activo</div><div class="s" style="color:var(--text);font-size:.92rem">Leé la conclusión, la cobertura de evidencia y lo que falta verificar.</div></div>',
        '<div class="mci-kpi"><div class="l">4 · Comparar</div><div class="s" style="color:var(--text);font-size:.92rem">Poné 2 a 4 activos lado a lado.</div></div>',
    ], wide=True)

    section("Cómo leer los datos")
    md(f'<div class="mci-grid w2"><div class="mci-kpi">{chip("hecho", "accent")}<div class="s">Dato reportado por una fuente, con enlace y fecha de consulta.</div></div>'
       f'<div class="mci-kpi">{chip("estimación", "info")}<div class="s">Cálculo de MCI sobre hechos. La fórmula está a la vista.</div></div>'
       f'<div class="mci-kpi">{chip("hipótesis", "warn")}<div class="s">Interpretación posible. Siempre indica qué la invalidaría.</div></div></div>')
    md('<div class="mci-note">Barra de evidencia: segmento lleno = cubierta · rayado = parcial · gris = sin datos. '
       '★ marca las dimensiones esenciales. Un dato parcial nunca vale como prueba completa.</div>')
    md('<div class="mci-note" style="margin-top:6px"><b>Conclusiones posibles:</b> NO CONCLUYENTE (falta evidencia esencial) · '
       'EVIDENCIA PARCIAL (tesis preliminar) · EVIDENCIA SUFICIENTE · FUERA DE ALCANCE (stablecoins y derivados). '
       'Ninguna es una recomendación ni una probabilidad de rentabilidad.</div>')

    section("Qué se mira", "★ = esencial")
    st.dataframe(pd.DataFrame([{"Dimensión": d[1], "Esencial": "★" if d[2] else ""} for d in DIMENSIONS]),
                 hide_index=True, width="stretch")

    section("Criterios de MCI", "editables · no son hechos del mercado")
    T = THRESHOLDS
    st.dataframe(pd.DataFrame([
        {"Criterio": "Volumen / capitalización alto · bajo", "Valor": f"≥ {T.vol_cap_high:.0%} · < {T.vol_cap_low:.0%}"},
        {"Criterio": "Circulante / oferta máxima alto · bajo", "Valor": f"≥ {T.circ_max_high:.0%} · < {T.circ_max_low:.0%}"},
        {"Criterio": "FDV / capitalización que sugiere dilución", "Valor": f"> {T.fdv_cap_high}x"},
        {"Criterio": "Capitalización / comisiones anualizadas moderada · exigente", "Valor": f"≤ {T.cap_fees_low:.0f}x · > {T.cap_fees_high:.0f}x"},
        {"Criterio": "Caída del TVL en 7 días", "Valor": f"≤ {T.tvl_drop_7d:.0f}%"},
        {"Criterio": "Caída profunda desde el máximo", "Valor": f"≤ {T.ath_deep:.0f}%"},
    ]), hide_index=True, width="stretch")

    section("Estado de las fuentes")
    rows = [{"Fuente": "CoinGecko (mercado)", "Estado": "OK", "Consultado": fmt_dt(ctx.markets_at)}]
    rows.append({"Fuente": "CoinGecko (mercado global)", "Estado": "OK" if ctx.glob.data else f"Sin datos: {ctx.glob.error}",
                 "Consultado": fmt_dt(ctx.glob.at)})
    errs = ctx.llama["errors"]
    rows.append({"Fuente": "DefiLlama (TVL, comisiones, ingresos)",
                 "Estado": "OK" if not errs else "Parcial: " + "; ".join(f"{k}: {v}" for k, v in errs.items()),
                 "Consultado": fmt_dt(ctx.llama["at"])})
    rows.append({"Fuente": "alternative.me (miedo y codicia)", "Estado": "OK" if ctx.fng.data else f"Sin datos: {ctx.fng.error}",
                 "Consultado": fmt_dt(ctx.fng.at)})
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    md('<div class="mci-note">Todo en USD. Los precios en ARS y EUR se muestran en el dossier cuando CoinGecko los informa. '
       'No incluye desbloqueos de tokens (dato de pago).</div>')
    st.warning("MCI es una herramienta de investigación, no asesoramiento financiero. Las criptomonedas son de alto riesgo. "
               "No ejecuta operaciones ni se conecta a wallets.")
