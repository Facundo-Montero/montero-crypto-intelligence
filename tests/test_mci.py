from datetime import datetime, timezone

from mci.analysis.classify import classify, NON_GROWTH
from mci.analysis.evidence import build_evidence
from mci.analysis.rules import evaluate, Thresholds
from mci.analysis.verdict import assess_dimensions, build_verdict

T = datetime(2026, 11, 14, 12, 0, tzinfo=timezone.utc)


def row(**kw):
    base = {"id": "x", "name": "X", "symbol": "x", "market_cap": 5e9, "total_volume": 1e9,
            "current_price": 2.0, "circulating_supply": 900.0, "max_supply": 1000.0,
            "fully_diluted_valuation": 5.5e9}
    base.update(kw)
    return base


def test_classify_tiers_and_derivatives():
    assert classify({"name": "Solana", "symbol": "sol", "market_cap": 8e10}) == "Consolidado"
    assert classify({"name": "Chain", "symbol": "lnk", "market_cap": 5e9}) == "Intermedio"
    assert classify({"name": "Small", "symbol": "sm", "market_cap": 5e8}) == "Emergente"
    assert classify({"name": "Tether", "symbol": "usdt", "market_cap": 1e11}) == "Stablecoin"
    assert classify({"name": "Lido Staked Ether", "symbol": "steth", "market_cap": 2e10}) in NON_GROWTH
    assert classify({"name": "Wrapped Bitcoin", "symbol": "wbtc", "market_cap": 1e10}) in NON_GROWTH
    assert classify({"name": "Nuevo", "symbol": "nw", "market_cap": None}) == "Sin capitalización"
    assert classify({"name": "Algo", "symbol": "alg", "market_cap": 1e9}, categories=["Stablecoins"]) == "Stablecoin"


def test_evidence_estimates_and_provenance():
    ev = build_evidence(row(), None, "usd", T, T)
    assert abs(ev["vol_cap"].value - 0.2) < 1e-9
    assert abs(ev["circ_max"].value - 0.9) < 1e-9
    assert ev["vol_cap"].kind == "estimación" and ev["cap"].kind == "hecho"
    assert ev["cap"].fetched_at == T and ev["cap"].url.startswith("https://")
    assert "commits" not in ev  # sin detalle no se inventa nada


def test_zero_or_missing_values_do_not_crash():
    ev = build_evidence(row(market_cap=0, total_volume=None, max_supply=None, fully_diluted_valuation=None), None, "usd", T, T)
    assert "vol_cap" not in ev and "circ_max" not in ev and "fdv_cap" not in ev
    assert evaluate(ev) == []


def test_rules_fire_on_thresholds():
    ev = build_evidence(row(), None, "usd", T, T)
    pols = {(f.dimension, f.polarity) for f in evaluate(ev)}
    assert ("liquidez", "a_favor") in pols and ("oferta_dilucion", "a_favor") in pols
    ev2 = build_evidence(row(circulating_supply=100.0, total_volume=1e6), None, "usd", T, T)
    pols2 = {(f.dimension, f.polarity) for f in evaluate(ev2)}
    assert ("oferta_dilucion", "cautela") in pols2 and ("liquidez", "cautela") in pols2
    assert all(f.invalidation and f.rule for f in evaluate(ev2))


def test_momentum_is_context_not_evidence_in_favor():
    ev = build_evidence(row(price_change_percentage_7d_in_currency=10, price_change_percentage_30d_in_currency=20), None, "usd", T, T)
    price = [f for f in evaluate(ev) if f.dimension == "precio"]
    assert price and all(f.polarity == "contexto" for f in price)


def test_verdict_is_no_concluyente_with_only_coingecko():
    ev = build_evidence(row(), {"developer_data": {"commits_last_4_weeks": 30}}, "usd", T, T)
    v = build_verdict("Consolidado", assess_dimensions(ev))
    assert v.level == "no_concluyente" and v.label == "NO CONCLUYENTE"
    assert any("Adopción" in r for r in v.reasons)


def test_verdict_levels_with_future_sources():
    ev = build_evidence(row(), None, "usd", T, T)
    full = {k: ("cubierta", "ok") for k in ("oferta_dilucion", "adopcion_uso", "ingresos_fees", "seguridad", "tokenomics_unlocks")}
    assert build_verdict("Consolidado", assess_dimensions(ev, full)).level == "suficiente"
    part = dict(full, seguridad=("parcial", "auditoría parcial"))
    assert build_verdict("Consolidado", assess_dimensions(ev, part)).level == "parcial"
    assert build_verdict("Stablecoin", assess_dimensions(ev, full)).level == "fuera_de_alcance"


def test_non_usd_currency_picks_matching_value():
    detail = {"market_data": {"current_price": {"usd": 1.0, "ars": 1400.0}, "market_cap": {"usd": 1e9, "ars": 1.4e12}}}
    ev = build_evidence(row(), detail, "ars", T, T)
    assert ev["price"].value == 1400.0 and "AR$" in ev["price"].display
