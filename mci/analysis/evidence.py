"""Construye la lista de evidencias (con fuente y fecha) para un activo."""
from mci.formatting import money, pct, ratio_pct, number
from mci.models import Evidence, HECHO, ESTIMACION
from mci.sources.coingecko import BASE, SOURCE_NAME

# clave, etiqueta, clave en market_data, clave en fila de /coins/markets, ¿depende de la moneda?, formato
_SPECS = [
    ("price", "Precio", "current_price", "current_price", True, "money"),
    ("cap", "Capitalización", "market_cap", "market_cap", True, "money"),
    ("fdv", "Valoración totalmente diluida (FDV)", "fully_diluted_valuation", "fully_diluted_valuation", True, "money"),
    ("vol", "Volumen 24 h", "total_volume", "total_volume", True, "money"),
    ("circ", "Oferta circulante", "circulating_supply", "circulating_supply", False, "number"),
    ("total", "Oferta total", "total_supply", "total_supply", False, "number"),
    ("max", "Oferta máxima", "max_supply", "max_supply", False, "number"),
    ("ath_change", "Distancia al máximo histórico", "ath_change_percentage", "ath_change_percentage", True, "pct"),
    ("p24", "Variación 24 h", "price_change_percentage_24h_in_currency", "price_change_percentage_24h_in_currency", True, "pct"),
    ("p7", "Variación 7 días", "price_change_percentage_7d_in_currency", "price_change_percentage_7d_in_currency", True, "pct"),
    ("p30", "Variación 30 días", "price_change_percentage_30d_in_currency", "price_change_percentage_30d_in_currency", True, "pct"),
    ("p1y", "Variación 1 año", "price_change_percentage_1y_in_currency", "price_change_percentage_1y_in_currency", True, "pct"),
]


def _fmt(kind, v, cur):
    return {"money": lambda: money(v, cur), "pct": lambda: pct(v), "number": lambda: number(v)}[kind]()


def _pick(md, row, md_key, row_key, per_cur, cur):
    if md:
        v = md.get(md_key)
        if per_cur and isinstance(v, dict):
            v = v.get(cur)
        if v is not None and not isinstance(v, dict):
            return v, "coin"
    v = row.get(row_key)
    return (v, "markets") if v is not None else (None, None)


def build_evidence(row, detail, currency, markets_at, coin_at):
    """row: fila de /coins/markets. detail: /coins/{id} o None si falló. Devuelve dict key -> Evidence."""
    md = (detail or {}).get("market_data") or {}
    coin_id = row.get("id", "")
    src = {
        "markets": (f"{SOURCE_NAME} · /coins/markets", f"{BASE}/coins/markets", markets_at),
        "coin": (f"{SOURCE_NAME} · /coins/{{id}}", f"{BASE}/coins/{coin_id}", coin_at),
    }
    ev = {}
    for key, label, md_key, row_key, per_cur, kind in _SPECS:
        v, where = _pick(md, row, md_key, row_key, per_cur, currency)
        if v is None:
            continue
        s, u, t = src[where]
        ev[key] = Evidence(key, label, v, _fmt(kind, v, currency), HECHO, s, u, t)

    def est(key, label, value, display, formula, parts):
        used = [ev[p] for p in parts]
        ev[key] = Evidence(key, label, value, display, ESTIMACION, "Cálculo MCI sobre datos de CoinGecko",
                           used[0].url, max(e.fetched_at for e in used), formula)

    cap, vol, fdv, circ, mx = (ev[k].value if k in ev else None for k in ("cap", "vol", "fdv", "circ", "max"))
    if cap and cap > 0 and vol is not None:
        est("vol_cap", "Volumen / capitalización", vol / cap, ratio_pct(vol / cap),
            "volumen 24 h ÷ capitalización", ("vol", "cap"))
    if circ and mx and mx > 0:
        est("circ_max", "Circulante / oferta máxima", circ / mx, ratio_pct(circ / mx),
            "oferta circulante ÷ oferta máxima", ("circ", "max"))
    if cap and cap > 0 and fdv:
        est("fdv_cap", "FDV / capitalización", fdv / cap, f"{fdv / cap:.2f}x",
            "FDV ÷ capitalización", ("fdv", "cap"))

    if detail:
        s, u, t = src["coin"]
        dev = detail.get("developer_data") or {}
        if dev.get("commits_last_4_weeks") is not None:
            c = dev["commits_last_4_weeks"]
            ev["commits"] = Evidence("commits", "Commits en GitHub (últimas 4 semanas)", c, f"{c:,}", HECHO, s, u, t,
                                     "Reportado por CoinGecko a partir de GitHub. No mide calidad ni progreso.")
        com = detail.get("community_data") or {}
        for key, label, field in (("twitter", "Seguidores en X/Twitter", "twitter_followers"),
                                  ("reddit", "Suscriptores en Reddit", "reddit_subscribers")):
            if com.get(field):
                ev[key] = Evidence(key, label, com[field], f"{com[field]:,}", HECHO, s, u, t,
                                   "Audiencia reportada; no es evidencia de adopción real.")
    return ev
