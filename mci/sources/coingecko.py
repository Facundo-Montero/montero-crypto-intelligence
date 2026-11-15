"""Cliente de CoinGecko API v3. Cada función devuelve (datos, momento_real_de_consulta)."""
from datetime import datetime, timezone

from mci.sources.base import SourceError, get_json  # noqa: F401  (SourceError se re-exporta)

BASE = "https://api.coingecko.com/api/v3"
SOURCE_NAME = "CoinGecko API v3"


def _now():
    return datetime.now(timezone.utc)


def _get(path, params, api_key=""):
    headers = {"accept": "application/json", "User-Agent": "MCI-research/1.0"}
    if api_key:
        headers["x-cg-demo-api-key"] = api_key
    return get_json(BASE + path, params, headers, source="CoinGecko")


def fetch_markets(vs_currency="usd", pages=1, api_key=""):
    rows = []
    for page in range(1, pages + 1):
        batch = _get("/coins/markets", {
            "vs_currency": vs_currency, "order": "market_cap_desc", "per_page": 250,
            "page": page, "sparkline": "true",
            "price_change_percentage": "24h,7d,30d,1y",
        }, api_key)
        if not isinstance(batch, list):
            raise SourceError("Formato inesperado en /coins/markets.")
        if not batch:
            break
        rows.extend(batch)
    return rows, _now()


def fetch_coin(coin_id, api_key=""):
    data = _get(f"/coins/{coin_id}", {
        "localization": "false", "tickers": "false", "market_data": "true",
        "community_data": "true", "developer_data": "true", "sparkline": "false",
    }, api_key)
    if not isinstance(data, dict):
        raise SourceError("Formato inesperado en /coins/{id}.")
    return data, _now()


def fetch_market_chart(coin_id, days=365, api_key=""):
    """Historial de precios en USD: lista de (timestamp_ms, precio)."""
    data = _get(f"/coins/{coin_id}/market_chart", {"vs_currency": "usd", "days": days}, api_key)
    prices = data.get("prices") if isinstance(data, dict) else None
    if not isinstance(prices, list):
        raise SourceError("Formato inesperado en /market_chart.")
    pts = [(int(p[0]), float(p[1])) for p in prices
           if isinstance(p, (list, tuple)) and len(p) >= 2 and p[1] is not None]
    if not pts:
        raise SourceError("CoinGecko no devolvió historial de precios para este activo.")
    return pts, _now()


def fetch_global(api_key=""):
    data = _get("/global", {}, api_key)
    d = data.get("data") if isinstance(data, dict) else None
    if not isinstance(d, dict):
        raise SourceError("Formato inesperado en /global.")
    return d, _now()
