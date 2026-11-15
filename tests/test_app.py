"""Ejecuta la app completa (Streamlit AppTest) con las fuentes simuladas."""
import os

import pytest
import requests
import streamlit as st
from streamlit.testing.v1 import AppTest

from tests import fakes

APP = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app.py")


@pytest.fixture(autouse=True)
def _clean():
    st.cache_data.clear()
    yield
    st.cache_data.clear()


def run(monkeypatch, fail=(), view=None, asset=None, markets=None):
    fake, calls = fakes.make_fake(fail, markets)
    monkeypatch.setattr(requests, "get", fake)
    at = AppTest.from_file(APP, default_timeout=60)
    if view:
        at.session_state["view"] = view
    if asset:
        at.session_state["asset_id"] = asset
    at.run()
    return at, calls


def text(at):
    return " ".join([m.value for m in at.markdown] + [m.value for m in at.info] + [m.value for m in at.warning]
                    + [m.value for m in at.error])


def test_mercado(monkeypatch):
    at, _ = run(monkeypatch)
    assert not at.exception, at.exception
    t = text(at)
    assert "Mapa del mercado" in t and "Mayores subas" in t and "Dominancia de Bitcoin" in t and "54.2%" in t


def test_radar(monkeypatch):
    at, _ = run(monkeypatch, view="Radar")
    assert not at.exception, at.exception
    assert len(at.dataframe) == 1
    names = at.dataframe[0].value["Activo"].tolist()
    joined = " | ".join(names)
    assert "Bitcoin · BTC" in names and "Tether" not in joined and "Tiny Coin" not in joined and "Wrapped" not in joined


def test_asset_no_concluyente_and_partial(monkeypatch):
    at, _ = run(monkeypatch, view="Activo", asset="bitcoin")
    assert not at.exception, at.exception
    assert "NO CONCLUYENTE" in text(at)
    st.cache_data.clear()
    at, _ = run(monkeypatch, view="Activo", asset="uniswap")
    assert not at.exception, at.exception
    t = text(at)
    assert "EVIDENCIA PARCIAL" in t and "Capitalización / comisiones" in t or "Cap. / comisiones" in t
    assert "El TVL cayó 25.0% en 7 días" in t and "AR$140,000" in t


def test_asset_out_of_scope(monkeypatch):
    at, _ = run(monkeypatch, view="Activo", asset="tether")
    assert not at.exception, at.exception
    assert "FUERA DE ALCANCE" in text(at)


def test_asset_empty_state_and_watchlist(monkeypatch):
    at, _ = run(monkeypatch, view="Activo")
    assert not at.exception, at.exception
    assert "Algunos para empezar" in text(at)
    at, _ = run(monkeypatch, view="Activo", asset="uniswap")
    at.button(key="watch_btn").click().run()
    assert at.session_state["watch"] == ["uniswap"]
    at.button(key="watch_btn").click().run()
    assert at.session_state["watch"] == []


def test_compare_and_guide(monkeypatch):
    at, _ = run(monkeypatch, view="Comparar")
    assert not at.exception, at.exception
    assert "Datos lado a lado" in text(at)
    at, _ = run(monkeypatch, view="Guía")
    assert not at.exception, at.exception
    t = text(at)
    assert "Estado de las fuentes" in t and "no asesoramiento financiero" in t.lower()


@pytest.mark.parametrize("fail", [
    ("api.llama.fi",), ("alternative.me",), ("/global",), ("/market_chart",), ("429:/coins/uniswap",),
])
def test_optional_sources_failing_never_break(monkeypatch, fail):
    for view, asset in (("Mercado", None), ("Activo", "uniswap"), ("Guía", None)):
        st.cache_data.clear()
        at, _ = run(monkeypatch, fail=fail, view=view, asset=asset)
        assert not at.exception, (fail, view, at.exception)


def test_llama_down_means_no_fundamentals_not_fake_ones(monkeypatch):
    at, _ = run(monkeypatch, fail=("api.llama.fi",), view="Activo", asset="uniswap")
    t = text(at)
    assert "NO CONCLUYENTE" in t and "EVIDENCIA PARCIAL" not in t


def test_markets_down_shows_clear_error(monkeypatch):
    at, _ = run(monkeypatch, fail=("/coins/markets",))
    assert not at.exception, at.exception
    assert any("No se pudieron obtener los mercados" in e.value for e in at.error)


def test_html_from_api_is_escaped(monkeypatch):
    evil = fakes.mk("evil", '<script>alert(1)</script>', "xss", 5, 5e9, 1e9, image="javascript:alert(1)")
    at, _ = run(monkeypatch, view="Activo", asset="evil", markets=fakes.MARKETS + [evil])
    assert not at.exception, at.exception
    t = text(at)
    assert "<script>" not in t and "&lt;script&gt;" in t and "javascript:" not in t
