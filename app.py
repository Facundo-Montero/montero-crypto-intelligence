"""MONTERO CRYPTO INTELLIGENCE (MCI) v1.0 — investigación cripto basada en evidencia.
app.py solo arma el contexto y navega; la lógica vive en mci/."""
import os
from types import SimpleNamespace

import pandas as pd
import streamlit as st

from mci import state
from mci.analysis.classify import NON_GROWTH, classify
from mci.analysis.evidence import build_evidence
from mci.analysis.verdict import assess_dimensions
from mci.data import load_fng, load_global, load_llama, load_markets
from mci.formatting import fmt_dt
from mci.sources.base import SourceError
from mci.ui.components import brand, esc, md
from mci.ui.theme import CSS
from mci.views import asset, compare, guide, market, radar

st.set_page_config(page_title="MCI | Montero Crypto Intelligence", page_icon="◈", layout="wide",
                   initial_sidebar_state="collapsed")
st.markdown(CSS, unsafe_allow_html=True)
state.init()


def get_api_key():
    try:
        key = st.secrets.get("COINGECKO_API_KEY", "")
    except Exception:
        key = ""
    return (key or os.getenv("COINGECKO_API_KEY", "")).strip()


API_KEY = get_api_key()
PCT_COLS = ["price_change_percentage_24h_in_currency", "price_change_percentage_7d_in_currency",
            "price_change_percentage_30d_in_currency", "price_change_percentage_1y_in_currency"]

# ------------------------------------------------------------------ sidebar
with st.sidebar:
    st.markdown("### Ajustes")
    if st.button("Actualizar datos", width="stretch"):
        st.cache_data.clear()
        st.rerun()
    pages = st.slider("Universo", 1, 2, 1, format="%d × 250 activos",
                      help="Más activos = más consultas a CoinGecko y más riesgo de límite de uso.")
    min_volume = st.number_input("Volumen mínimo 24 h (US$)", min_value=0, step=100_000, value=1_000_000)
    include_non_growth = st.toggle("Incluir stablecoins y derivados", value=False)
    sidebar_status = st.container()

# ------------------------------------------------------------------ datos
try:
    with st.spinner("Consultando mercado…"):
        rows, markets_at = load_markets(pages, API_KEY)
except SourceError as e:
    brand()
    st.error(f"No se pudieron obtener los mercados: {e}")
    st.info("MCI no completa datos faltantes con estimaciones. Reintentá en unos minutos.")
    st.stop()
if not rows:
    brand()
    st.warning("La fuente no devolvió activos.")
    st.stop()

llama = load_llama()
fng, glob = load_fng(), load_global(API_KEY)

all_df = pd.DataFrame(rows)
for col in ["market_cap", "total_volume", "current_price", "market_cap_rank"] + PCT_COLS:
    all_df[col] = pd.to_numeric(all_df.get(col), errors="coerce")
all_df["spark"] = [((r.get("sparkline_in_7d") or {}).get("price") or [])[::4] for r in rows]

quick, cls_list, cov, tvl, fees, capf, volcap = {}, [], [], [], [], [], []
for r in rows:
    ev = build_evidence(r, None, markets_at, markets_at, llama["index"].get(r["id"]), llama["at"])
    dims = assess_dimensions(ev)
    cls = classify(r)
    quick[r["id"]] = (ev, dims, cls)
    cls_list.append(cls)
    cov.append(sum(1 for d in dims if d.status != "sin_datos"))
    tvl.append(ev["tvl"].value if "tvl" in ev else None)
    fees.append(ev["fees_30d"].value if "fees_30d" in ev else None)
    capf.append(ev["cap_fees"].value if "cap_fees" in ev else None)
    volcap.append(ev["vol_cap"].value if "vol_cap" in ev else None)
all_df["clasificacion"], all_df["cov"], all_df["tvl"] = cls_list, cov, tvl
all_df["fees_30d"], all_df["cap_fees"], all_df["vol_cap"] = fees, capf, volcap

df = all_df[all_df["total_volume"].fillna(0) >= min_volume]
if not include_non_growth:
    df = df[~df["clasificacion"].isin(NON_GROWTH)]
df = df.sort_values("market_cap", ascending=False)

ctx = SimpleNamespace(
    rows=rows, by_id={r["id"]: r for r in rows}, all_df=all_df, df=df, markets_at=markets_at, api_key=API_KEY,
    llama=llama, fng=fng, glob=glob, quick=quick, all_ids=[r["id"] for r in rows],
    labels={r["id"]: f'{r["name"]} ({str(r["symbol"]).upper()})' for r in rows},
    watch=st.session_state.get("watch", []))

# ------------------------------------------------------------------ estado de fuentes (sidebar)
def _dot(ok, label, when):
    cls = "" if ok == "ok" else ("mid" if ok == "mid" else "bad")
    return f'<div class="mci-note"><span class="mci-dot {cls}"></span>{esc(label)} · {esc(when)}</div>'


with sidebar_status:
    st.markdown("### Fuentes")
    ll = "ok" if not llama["errors"] else ("mid" if llama["index"] else "bad")
    md(_dot("ok", "CoinGecko", fmt_dt(markets_at)) + _dot(ll, "DefiLlama", fmt_dt(llama["at"]))
       + _dot("ok" if fng.data else "bad", "Miedo y codicia", fmt_dt(fng.at))
       + _dot("ok" if glob.data else "bad", "Mercado global", fmt_dt(glob.at)))
    st.caption("MCI no opera ni se conecta a wallets. No es asesoramiento financiero.")

# ------------------------------------------------------------------ navegación
brand()
st.radio("Sección", state.VIEWS, horizontal=True, key="view", label_visibility="collapsed")
{"Mercado": market, "Radar": radar, "Activo": asset, "Comparar": compare, "Guía": guide}[st.session_state["view"]].render(ctx)
