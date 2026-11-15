"""Capa de datos para Streamlit: carga con caché. Las fuentes opcionales devuelven Fetched (nunca rompen la app)."""
from datetime import datetime, timezone

import streamlit as st

from mci.models import Fetched
from mci.sources import coingecko as cg
from mci.sources import defillama as dl
from mci.sources import sentiment as sm
from mci.sources.base import SourceError


def _now():
    return datetime.now(timezone.utc)


def _safe(fn, *args):
    try:
        data, at = fn(*args)
        return Fetched(data, at, "")
    except SourceError as e:
        return Fetched(None, _now(), str(e))


@st.cache_data(ttl=300, show_spinner=False)
def load_markets(pages, api_key):
    return cg.fetch_markets("usd", pages, api_key)          # si falla, lanza SourceError (no se cachea)


@st.cache_data(ttl=600, show_spinner=False)
def load_coin(coin_id, api_key):
    return cg.fetch_coin(coin_id, api_key)                   # si falla, lanza SourceError


@st.cache_data(ttl=900, show_spinner=False)
def load_chart(coin_id, api_key):
    return _safe(cg.fetch_market_chart, coin_id, 365, api_key)


@st.cache_data(ttl=600, show_spinner=False)
def load_global(api_key):
    return _safe(cg.fetch_global, api_key)


@st.cache_data(ttl=1800, show_spinner=False)
def load_fng():
    return _safe(sm.fetch_fear_greed, 30)


@st.cache_data(ttl=1800, show_spinner=False)
def load_llama():
    parts = {"protocolos": _safe(dl.fetch_protocols), "cadenas": _safe(dl.fetch_chains),
             "comisiones": _safe(dl.fetch_fees, "dailyFees"), "ingresos": _safe(dl.fetch_fees, "dailyRevenue")}
    index = dl.build_index(parts["protocolos"].data, parts["cadenas"].data,
                           parts["comisiones"].data, parts["ingresos"].data)
    errors = {k: v.error for k, v in parts.items() if v.error}
    return {"index": index, "at": _now(), "errors": errors}


@st.cache_data(ttl=1800, show_spinner=False)
def load_llama_detail(slug):
    det = _safe(dl.fetch_protocol_detail, slug)
    fees = _safe(dl.fetch_fees_summary, slug, "dailyFees")
    return {"detail": det.data, "fees": fees.data, "at": _now(),
            "errors": [e for e in (det.error, fees.error) if e]}
