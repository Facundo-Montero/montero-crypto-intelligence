"""Respuestas simuladas de las fuentes (CoinGecko, DefiLlama, alternative.me) para probar sin red."""
import requests


class Resp:
    def __init__(self, code, data):
        self.status_code, self._d = code, data

    def json(self):
        return self._d


def mk(i, name, sym, rank, cap, vol, **kw):
    r = {"id": i, "name": name, "symbol": sym, "image": f"https://img.example/{i}.png", "market_cap_rank": rank,
         "current_price": 100.0, "market_cap": cap, "total_volume": vol, "fully_diluted_valuation": cap * 1.2,
         "circulating_supply": 600.0, "total_supply": 1000.0, "max_supply": 1000.0, "ath_change_percentage": -30.0,
         "price_change_percentage_24h_in_currency": 1.2, "price_change_percentage_7d_in_currency": 3.0,
         "price_change_percentage_30d_in_currency": -2.0, "price_change_percentage_1y_in_currency": 50.0,
         "sparkline_in_7d": {"price": [100 + k % 7 for k in range(168)]}}
    r.update(kw)
    return r


MARKETS = [
    mk("bitcoin", "Bitcoin", "btc", 1, 1.3e12, 3e10, max_supply=21e6, circulating_supply=19e6),
    mk("ethereum", "Ethereum", "eth", 2, 4e11, 1.5e10, max_supply=None),
    mk("tether", "Tether", "usdt", 3, 1.8e11, 5e10),
    mk("uniswap", "Uniswap", "uni", 20, 6e9, 3e8),
    mk("wrapped-bitcoin", "Wrapped Bitcoin", "wbtc", 15, 1e10, 2e8),
    mk("tiny", "Tiny Coin", "tny", 900, 2e6, 5e5),
]
DETAIL = {"description": {"en": "<p>Un <b>proyecto</b> de prueba.</p>"}, "categories": ["Cryptocurrency"],
          "links": {"homepage": ["https://example.org"], "repos_url": {"github": ["https://github.com/x/y"]},
                    "whitepaper": "https://example.org/wp.pdf", "blockchain_site": ["https://scan.example"]},
          "developer_data": {"commits_last_4_weeks": 42}, "community_data": {"twitter_followers": 1000},
          "market_data": {"current_price": {"usd": 100.0, "ars": 140000.0, "eur": 92.0}}}
CHART = {"prices": [[1_700_000_000_000 + i * 86_400_000, 100 + (i % 20)] for i in range(365)]}
GLOBAL = {"data": {"total_market_cap": {"usd": 2.4e12}, "total_volume": {"usd": 1e11},
                   "market_cap_percentage": {"btc": 54.2, "eth": 11.0}, "market_cap_change_percentage_24h_usd": -1.5}}
FNG = {"data": [{"value": str(30 + i), "value_classification": "Fear", "timestamp": str(1_700_000_000 - i * 86400)} for i in range(31)]}
PROTOCOLS = [{"id": "2", "name": "Uniswap", "slug": "uniswap", "gecko_id": "uniswap", "category": "Dexs", "tvl": 5e9,
              "change_1d": 1.0, "change_7d": -25.0, "audits": "2", "url": "https://uniswap.org"}]
CHAINS = [{"gecko_id": "ethereum", "name": "Ethereum", "tvl": 6e10}]
FEES = {"protocols": [{"defillamaId": "2", "name": "Uniswap", "slug": "uniswap", "total24h": 3e6, "total7d": 2e7, "total30d": 9e7}]}
REVENUE = {"protocols": [{"defillamaId": "2", "name": "Uniswap", "slug": "uniswap", "total24h": 1e5, "total7d": 7e5, "total30d": 3e6}]}
LL_DETAIL = {"tvl": [{"date": 1_700_000_000 + i * 86400, "totalLiquidityUSD": 4e9 + i * 1e6} for i in range(200)],
             "audit_links": ["https://audits.example/uni.pdf"]}
LL_FEES = {"totalDataChart": [[1_700_000_000 + i * 86400, 3e6 + i * 1e4] for i in range(120)]}


def make_fake(fail=(), markets=None):
    """fail: fragmentos de URL que deben devolver error. Devuelve (fake_get, lista_de_urls_llamadas)."""
    calls = []

    def fake_get(url, params=None, headers=None, timeout=None):
        calls.append(url)
        for frag in fail:
            if frag in url:
                code = 429 if frag.startswith("429:") else 500
                return Resp(code, {})
        if url.endswith("/coins/markets"):
            return Resp(200, markets or MARKETS)
        if url.endswith("/market_chart"):
            return Resp(200, CHART)
        if url.endswith("/global"):
            return Resp(200, GLOBAL)
        if "/coins/" in url:
            return Resp(200, DETAIL)
        if "alternative.me" in url:
            return Resp(200, FNG)
        if url.endswith("/protocols"):
            return Resp(200, PROTOCOLS)
        if url.endswith("/v2/chains"):
            return Resp(200, CHAINS)
        if url.endswith("/overview/fees"):
            return Resp(200, REVENUE if (params or {}).get("dataType") == "dailyRevenue" else FEES)
        if "/summary/fees/" in url:
            return Resp(200, LL_FEES)
        if "/protocol/" in url:
            return Resp(200, LL_DETAIL)
        return Resp(404, {})

    return fake_get, calls
