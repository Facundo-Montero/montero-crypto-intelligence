"""Cliente de CoinGecko API v3. Cada función devuelve (datos, momento_real_de_consulta)."""
from datetime import datetime, timezone

import requests

BASE = "https://api.coingecko.com/api/v3"
SOURCE_NAME = "CoinGecko API v3"


class SourceError(Exception):
    """Error legible al consultar una fuente externa."""


def _get(path, params, api_key=""):
    headers = {"accept": "application/json", "User-Agent": "MCI-research/0.3"}
    if api_key:
        headers["x-cg-demo-api-key"] = api_key
    try:
        r = requests.get(BASE + path, params=params, headers=headers, timeout=25)
    except requests.RequestException as exc:
        raise SourceError(f"No se pudo conectar con CoinGecko ({exc.__class__.__name__}).") from exc
    if r.status_code == 429:
        raise SourceError("CoinGecko limitó temporalmente las consultas. Esperá un minuto y reintentá.")
    if r.status_code >= 400:
        raise SourceError(f"CoinGecko respondió con error HTTP {r.status_code}.")
    try:
        return r.json()
    except ValueError as exc:
        raise SourceError("CoinGecko devolvió una respuesta que no es JSON válido.") from exc


def fetch_markets(vs_currency="usd", pages=1, api_key=""):
    rows = []
    for page in range(1, pages + 1):
        batch = _get("/coins/markets", {
            "vs_currency": vs_currency, "order": "market_cap_desc", "per_page": 250,
            "page": page, "sparkline": "false",
            "price_change_percentage": "24h,7d,30d,1y",
        }, api_key)
        if not isinstance(batch, list):
            raise SourceError("Formato inesperado en /coins/markets.")
        if not batch:
            break
        rows.extend(batch)
    return rows, datetime.now(timezone.utc)


def fetch_coin(coin_id, api_key=""):
    data = _get(f"/coins/{coin_id}", {
        "localization": "false", "tickers": "false", "market_data": "true",
        "community_data": "true", "developer_data": "true", "sparkline": "false",
    }, api_key)
    if not isinstance(data, dict):
        raise SourceError("Formato inesperado en /coins/{id}.")
    return data, datetime.now(timezone.utc)
