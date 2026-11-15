from datetime import datetime, timezone

from mci.analysis.classify import NON_GROWTH, classify
from mci.analysis.evidence import build_evidence
from mci.analysis.rules import evaluate
from mci.analysis.verdict import assess_dimensions, build_verdict
from mci.sources import defillama as dl

T = datetime(2026, 11, 14, 12, 0, tzinfo=timezone.utc)


def row(**kw):
    base = {"id": "x", "name": "X", "symbol": "x", "market_cap": 5e9, "total_volume": 1e9, "current_price": 2.0,
            "circulating_supply": 900.0, "max_supply": 1000.0, "fully_diluted_valuation": 5.5e9}
    base.update(kw)
    return base


LL = {"kind": "protocol", "slug": "x", "tvl": 2e9, "tvl_change_7d": -30.0, "audits": "0",
      "fees_30d": 5e7, "rev_30d": 1e7}


def test_classify():
    assert classify({"name": "Solana", "symbol": "sol", "market_cap": 8e10}) == "Consolidado"
    assert classify({"name": "Small", "symbol": "sm", "market_cap": 5e8}) == "Emergente"
    assert classify({"name": "Tether", "symbol": "usdt", "market_cap": 1e11}) == "Stablecoin"
    assert classify({"name": "Lido Staked Ether", "symbol": "steth", "market_cap": 2e10}) in NON_GROWTH
    assert classify({"name": "Figure Heloc", "symbol": "figr_heloc", "market_cap": 2.7e10}) in NON_GROWTH
    assert classify({"name": "Tether Gold", "symbol": "xaut", "market_cap": 2e9}) in NON_GROWTH
    assert classify({"name": "Nuevo", "symbol": "nw", "market_cap": None}) == "Sin capitalización"


def test_provenance_and_estimates():
    ev = build_evidence(row(), None, T, T)
    assert abs(ev["vol_cap"].value - 0.2) < 1e-9 and ev["vol_cap"].kind == "estimación"
    assert ev["cap"].kind == "hecho" and ev["cap"].fetched_at == T and ev["cap"].url.startswith("https://")
    assert "commits" not in ev and "tvl" not in ev


def test_missing_values_never_crash_or_invent():
    ev = build_evidence(row(market_cap=0, total_volume=None, max_supply=None, fully_diluted_valuation=None), None, T, T)
    assert not {"vol_cap", "circ_max", "fdv_cap"} & set(ev)
    assert evaluate(ev) == []


def test_defillama_evidence_and_findings():
    ev = build_evidence(row(), None, T, T, LL, T)
    assert abs(ev["cap_fees"].value - 5e9 / (5e7 * 365 / 30)) < 1e-6
    assert abs(ev["cap_tvl"].value - 2.5) < 1e-9
    pols = {(f.dimension, f.polarity) for f in evaluate(ev)}
    assert ("adopcion_uso", "cautela") in pols        # TVL -30% en 7 d
    assert ("seguridad", "cautela") in pols           # audits "0"
    assert all(f.invalidation and f.rule for f in evaluate(ev))


def test_momentum_is_context_only():
    ev = build_evidence(row(price_change_percentage_7d_in_currency=10, price_change_percentage_30d_in_currency=20), None, T, T)
    price = [f for f in evaluate(ev) if f.dimension == "precio"]
    assert price and all(f.polarity == "contexto" for f in price)


def test_verdict_levels():
    only_cg = build_evidence(row(), {"developer_data": {"commits_last_4_weeks": 3}}, T, T)
    assert build_verdict("Consolidado", assess_dimensions(only_cg)).level == "no_concluyente"
    full = build_evidence(row(), None, T, T, LL, T)
    v = build_verdict("Consolidado", assess_dimensions(full))
    assert v.level == "parcial" and v.covered >= 5
    allc = {k: ("cubierta", "ok") for k in ("oferta_dilucion", "adopcion_uso", "ingresos_fees", "seguridad")}
    assert build_verdict("Consolidado", assess_dimensions(full, allc)).level == "suficiente"
    assert build_verdict("Stablecoin", assess_dimensions(full, allc)).level == "fuera_de_alcance"


def test_defillama_index_joins_and_aggregates():
    protos = [{"id": "parent#aave", "name": "Aave", "slug": "aave", "gecko_id": "aave", "tvl": 9e9},
              {"id": "7", "name": "Small", "slug": "small", "gecko_id": "aave", "tvl": 1.0}]
    fees = [{"defillamaId": "11", "name": "Aave V2", "parentProtocol": "parent#aave", "total30d": 10.0},
            {"defillamaId": "12", "name": "Aave V3", "parentProtocol": "parent#aave", "total30d": 30.0}]
    idx = dl.build_index(protos, [{"gecko_id": "ethereum", "name": "Ethereum", "tvl": 5e10}], fees, None)
    assert idx["aave"]["tvl"] == 9e9 and idx["aave"]["fees_30d"] == 40.0 and idx["aave"]["rev_30d"] is None
    assert idx["ethereum"]["kind"] == "chain"
    assert dl.build_index(None, None, None, None) == {}


def test_histories_parse_defensively():
    assert dl.tvl_history({"tvl": [{"date": 10, "totalLiquidityUSD": 5}, {"bad": 1}, "x"]}) == [(10000, 5.0)]
    assert dl.fees_history({"totalDataChart": [[10, 2], ["a", 1], [5]]}) == [(10000, 2.0)]
    assert dl.tvl_history(None) == [] and dl.fees_history({}) == []
