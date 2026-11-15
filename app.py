"""MONTERO CRYPTO INTELLIGENCE (MCI) v0.3 — investigación cripto basada en evidencia. Solo UI; la lógica está en mci/."""
import os
import re

import pandas as pd
import streamlit as st

from mci.analysis.classify import NON_GROWTH, classify
from mci.analysis.evidence import build_evidence
from mci.analysis.rules import THRESHOLDS, evaluate
from mci.analysis.verdict import DIMENSIONS, assess_dimensions, build_verdict
from mci.formatting import fmt_dt, money
from mci.sources import coingecko as cg

st.set_page_config(page_title="MCI | Montero Crypto Intelligence", page_icon="◈", layout="wide")
st.markdown("<style>.block-container{max-width:1450px;padding-top:2rem}"
            "div[data-testid='stMetric']{background:#111c2e;border:1px solid #24334a;padding:14px;border-radius:12px}"
            "</style>", unsafe_allow_html=True)


def get_api_key():
    try:
        key = st.secrets.get("COINGECKO_API_KEY", "")
    except Exception:
        key = ""
    return (key or os.getenv("COINGECKO_API_KEY", "")).strip()


@st.cache_data(ttl=300, show_spinner=False)
def load_markets(vs, pages, api_key):
    return cg.fetch_markets(vs, pages, api_key)


@st.cache_data(ttl=600, show_spinner=False)
def load_coin(coin_id, api_key):
    return cg.fetch_coin(coin_id, api_key)


API_KEY = get_api_key()

st.title("MONTERO CRYPTO INTELLIGENCE")
st.caption("Investigación cripto basada en evidencia · v0.3 · No emite señales de compra ni asesoramiento financiero")

with st.sidebar:
    st.header("Configuración")
    currency = st.selectbox("Moneda de referencia", ["usd", "ars", "eur"], index=0)
    pages = st.slider("Universo (páginas de 250 activos)", 1, 2, 1,
                      help="Más páginas = más consultas a CoinGecko y más riesgo de límite de uso.")
    min_volume = st.number_input("Volumen mínimo 24 h", min_value=0, step=100_000,
                                 value=1_000_000 if currency == "usd" else 0, key=f"minvol_{currency}")
    include_non_growth = st.checkbox("Incluir stablecoins y wrapped/derivados", value=False)
    if st.button("Actualizar datos", width="stretch"):
        st.cache_data.clear()
        st.rerun()
    st.caption("Fuente: CoinGecko API pública. Puede haber retrasos, campos incompletos y límites de uso.")
    st.caption("MCI no ejecuta operaciones ni se conecta a wallets.")

try:
    with st.spinner("Consultando mercado..."):
        rows, markets_at = load_markets(currency, pages, API_KEY)
except cg.SourceError as e:
    st.error(f"No se pudieron obtener los mercados: {e}")
    st.info("MCI no completa datos faltantes con estimaciones. Reintentá en unos minutos.")
    st.stop()

if not rows:
    st.warning("La fuente no devolvió activos.")
    st.stop()

df = pd.DataFrame(rows)
df["clasificacion"] = [classify(r) for r in rows]
for col in ("market_cap", "total_volume"):
    df[col] = pd.to_numeric(df[col], errors="coerce")
df = df[df["total_volume"].fillna(0) >= min_volume]
if not include_non_growth:
    df = df[~df["clasificacion"].isin(NON_GROWTH)]
df = df.sort_values("market_cap", ascending=False)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Activos en el universo", f"{len(df):,}")
m2.metric("Capitalización agregada", money(df["market_cap"].sum(), currency))
m3.metric("Volumen 24 h agregado", money(df["total_volume"].sum(), currency))
m4.metric("Datos consultados", fmt_dt(markets_at))

tab1, tab2, tab3 = st.tabs(["Radar de activos", "Dossier de investigación", "Metodología y límites"])

# ---------------------------------------------------------------- Radar
with tab1:
    st.subheader("Explorador de mercado")
    st.caption("El orden por capitalización no representa potencial de rentabilidad. Los cambios de precio son contexto, no fundamento.")
    c1, c2 = st.columns(2)
    chosen = c1.selectbox("Clasificación", ["Todas"] + sorted(df["clasificacion"].unique().tolist()))
    query = c2.text_input("Buscar por nombre o ticker", placeholder="Ej.: Bitcoin, ETH, LINK")
    view = df if chosen == "Todas" else df[df["clasificacion"] == chosen]
    if query:
        view = view[view["name"].str.contains(query, case=False, na=False) | view["symbol"].str.contains(query, case=False, na=False)]
    table = pd.DataFrame({
        "Rank": view["market_cap_rank"], "Activo": view["name"], "Ticker": view["symbol"].str.upper(),
        "Clasificación (heurística)": view["clasificacion"],
        "Precio": view["current_price"].map(lambda x: money(x, currency)),
        f"Capitalización ({currency.upper()})": view["market_cap"],
        f"Volumen 24 h ({currency.upper()})": view["total_volume"],
        "24 h %": view.get("price_change_percentage_24h_in_currency"),
        "7 d %": view.get("price_change_percentage_7d_in_currency"),
        "30 d %": view.get("price_change_percentage_30d_in_currency"),
    })
    st.dataframe(table, width="stretch", hide_index=True, column_config={
        f"Capitalización ({currency.upper()})": st.column_config.NumberColumn(format="%.0f"),
        f"Volumen 24 h ({currency.upper()})": st.column_config.NumberColumn(format="%.0f"),
        "24 h %": st.column_config.NumberColumn(format="%+.2f%%"),
        "7 d %": st.column_config.NumberColumn(format="%+.2f%%"),
        "30 d %": st.column_config.NumberColumn(format="%+.2f%%"),
    })
    st.caption(f"{len(view)} activos. Fuente: CoinGecko /coins/markets, consultado el {fmt_dt(markets_at)}.")

# ---------------------------------------------------------------- Dossier
with tab2:
    st.subheader("Dossier de investigación")
    if df.empty:
        st.info("No hay activos con los filtros actuales.")
    else:
        labels = {f"{r['name']} ({str(r['symbol']).upper()})": r["id"] for _, r in df.iterrows()}
        keys = list(labels)
        default = next((i for i, k in enumerate(keys) if k.startswith("Bitcoin (")), 0)
        pick = st.selectbox("Seleccioná un activo", keys, index=default)
        coin_id = labels[pick]
        row = next(r for r in rows if r["id"] == coin_id)

        detail, coin_at = None, markets_at
        try:
            with st.spinner("Reuniendo evidencia..."):
                detail, coin_at = load_coin(coin_id, API_KEY)
        except cg.SourceError as e:
            st.warning(f"No se pudo obtener la ficha detallada ({e}). Se muestran solo los datos del listado de mercado; "
                       "la evidencia de desarrollo y comunidad queda sin dato.")

        ev = build_evidence(row, detail, currency, markets_at, coin_at)
        cls = classify(row, (detail or {}).get("categories"))
        findings = evaluate(ev)
        dims = assess_dimensions(ev)
        verdict = build_verdict(cls, dims)

        st.markdown(f"### {row['name']} ({str(row['symbol']).upper()})")
        st.caption(f"Clasificación heurística: {cls} · Rank: {row.get('market_cap_rank') or 'Sin dato'} · ID CoinGecko: {coin_id}")

        # Veredicto primero
        box = st.info if verdict.level in ("suficiente", "fuera_de_alcance") else st.warning
        box(f"**Conclusión de MCI: {verdict.label}**\n\n" + "\n".join(f"- {r}" for r in verdict.reasons)
            + f"\n\nCobertura de evidencia: {verdict.covered} de {verdict.total} dimensiones con algún dato. "
              "Esto mide cuánta evidencia hay, **no** el atractivo del activo ni una probabilidad de rentabilidad.")

        k = st.columns(4)
        for col, key in zip(k, ("price", "cap", "vol", "ath_change")):
            col.metric(ev[key].label if key in ev else "Sin dato", ev[key].display if key in ev else "Sin dato")

        st.markdown("#### Qué dice el proyecto de sí mismo (autodeclarado, no verificado)")
        desc = ((detail or {}).get("description") or {}).get("en") or ((detail or {}).get("description") or {}).get("es") or ""
        desc = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", desc)).strip()
        if desc:
            st.write(desc[:1500] + ("..." if len(desc) > 1500 else ""))
            st.caption("Texto de la ficha de CoinGecko, escrito por el proyecto o la comunidad. No constituye evidencia.")
        else:
            st.info("La fuente no proporciona descripción para este activo.")

        st.markdown("#### Evidencia observada (hechos y estimaciones)")
        ev_df = pd.DataFrame([{
            "Dato": e.label, "Valor": e.display, "Tipo": e.kind, "Fuente": e.source,
            "Consultado (UTC)": fmt_dt(e.fetched_at), "Nota": e.note, "Enlace": e.url,
        } for e in ev.values()])
        st.dataframe(ev_df, width="stretch", hide_index=True,
                     column_config={"Enlace": st.column_config.LinkColumn("Enlace", display_text="abrir")})

        def render(pol, empty):
            items = [f for f in findings if f.polarity == pol]
            if not items:
                st.write(empty)
            for f in items:
                with st.container(border=True):
                    st.markdown(f"**{f.observation}**")
                    st.write(f.implication)
                    st.caption(f"Se invalidaría si: {f.invalidation}")
                    st.caption(f.rule)

        st.markdown("#### Indicios a favor (hipótesis a verificar)")
        render("a_favor", "Con los datos disponibles no hay indicios a favor que superen los criterios de MCI.")
        st.markdown("#### Riesgos y señales de cautela")
        render("cautela", "No se activó ninguna alerta básica. Eso no significa que el activo sea seguro: "
                          "solo se revisan pocos indicadores.")
        st.markdown("#### Contexto de precio (no es fundamento)")
        render("contexto", "Sin datos de precio suficientes.")

        st.markdown("#### Cobertura de evidencia por dimensión")
        icon = {"cubierta": "✅", "parcial": "🟡", "sin_datos": "⬜"}
        st.dataframe(pd.DataFrame([{
            "Dimensión": d.label, "Esencial para una tesis": "Sí" if d.essential else "No",
            "Estado": f"{icon[d.status]} {d.status.replace('_', ' ')}", "Detalle": d.detail} for d in dims]),
            width="stretch", hide_index=True)

        st.markdown("#### Fuentes para continuar la due diligence")
        links = (detail or {}).get("links") or {}
        urls = [u for u in (links.get("homepage") or []) if u]
        urls += [u for u in (links.get("blockchain_site") or []) if u]
        urls += [u for u in ((links.get("repos_url") or {}).get("github") or []) if u]
        if links.get("whitepaper"):
            urls.append(links["whitepaper"])
        if urls:
            for u in list(dict.fromkeys(urls))[:8]:
                st.markdown(f"- {u}")
            st.caption(f"Enlaces informados por CoinGecko el {fmt_dt(coin_at)}. MCI no verificó su vigencia ni su autenticidad.")
        else:
            st.write("La ficha no incluye enlaces oficiales.")

# ---------------------------------------------------------------- Metodología
with tab3:
    st.subheader("Cómo razona MCI")
    st.markdown("""
**Tres tipos de información, siempre rotulados**
- **Hecho:** dato reportado por una fuente identificada, con enlace y fecha de consulta.
- **Estimación:** cálculo de MCI sobre hechos, con la fórmula visible.
- **Hipótesis:** interpretación posible. Nunca se presenta como hecho y siempre trae qué la invalidaría.

**El veredicto mide calidad de evidencia, no atractivo.** Si falta evidencia esencial, la conclusión es **NO CONCLUYENTE**.
No hay puntajes de compra ni probabilidades de rentabilidad. Stablecoins y wrapped/derivados quedan fuera de alcance porque
no tienen una tesis de crecimiento propia.

**Dimensiones esenciales para sostener una tesis:** """ + ", ".join(d[1] for d in DIMENSIONS if d[2]) + """.

**Hoy MCI solo integra CoinGecko**, por eso casi todo activo termina NO CONCLUYENTE. Eso es lo correcto: todavía no hay datos de adopción,
ingresos, seguridad ni desbloqueos.
""")
    st.markdown("**Criterios de MCI (editables, no son hechos del mercado)**")
    st.dataframe(pd.DataFrame([
        {"Criterio": "Volumen/capitalización alto", "Valor": f"≥ {THRESHOLDS.vol_cap_high:.0%}"},
        {"Criterio": "Volumen/capitalización bajo", "Valor": f"< {THRESHOLDS.vol_cap_low:.0%}"},
        {"Criterio": "Circulante/oferta máxima alto", "Valor": f"≥ {THRESHOLDS.circ_max_high:.0%}"},
        {"Criterio": "Circulante/oferta máxima bajo", "Valor": f"< {THRESHOLDS.circ_max_low:.0%}"},
        {"Criterio": "FDV/capitalización que sugiere dilución", "Valor": f"> {THRESHOLDS.fdv_cap_high}x"},
        {"Criterio": "Caída profunda desde el máximo", "Valor": f"≤ {THRESHOLDS.ath_deep:.0f}%"},
    ]), width="stretch", hide_index=True)
    st.warning("No uses esta herramienta como única base para decidir una inversión. Las criptomonedas son de alto riesgo y "
               "MCI no es asesoramiento financiero.")
