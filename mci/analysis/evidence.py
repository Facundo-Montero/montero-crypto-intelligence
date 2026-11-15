"""Construye el dict de evidencias (con fuente y fecha) para un activo. Todo en USD."""
from mci.formatting import money, pct, ratio_pct, number
from mci.models import Evidence, HECHO, ESTIMACION
from mci.sources import coingecko as cg
from mci.sources import defillama as dl

# clave, etiqueta, clave en market_data, clave en fila de /coins/markets, formato
_SPECS = [
    ("price", "Precio", "current_price", "current_price", "money"),
    ("cap", "Capitalización", "market_cap", "market_cap", "money"),
    ("fdv", "Valoración totalmente diluida (FDV)", "fully_diluted_valuation", "fully_diluted_valuation", "money"),
    ("vol", "Volumen 24 h", "total_volume", "total_volume", "money"),
    ("circ", "Oferta circulante", "circulating_supply", "circulating_supply", "number"),
    ("total", "Oferta total", "total_supply", "total_supply", "number"),
    ("max", "Oferta máxima", "max_supply", "max_supply", "number"),
    ("ath_change", "Distancia al máximo histórico", "ath_change_percentage", "ath_change_percentage", "pct"),
    ("p24", "Variación 24 h", "price_change_percentage_24h_in_currency", "price_change_percentage_24h_in_currency", "pct"),
    ("p7", "Variación 7 días", "price_change_percentage_7d_in_currency", "price_change_percentage_7d_in_currency", "pct"),
    ("p30", "Variación 30 días", "price_change_percentage_30d_in_currency", "price_change_percentage_30d_in_currency", "pct"),
    ("p1y", "Variación 1 año", "price_change_percentage_1y_in_currency", "price_change_percentage_1y_in_currency", "pct"),
]
_FMT = {"money": money, "pct": pct, "number": number}


def _pick(md, row, md_key, row_key):
    if md:
        v = md.get(md_key)
        if isinstance(v, dict):
            v = v.get("usd")
        if v is not None:
            return v, "coin"
    v = row.get(row_key)
    return (v, "markets") if v is not None else (None, None)


def build_evidence(row, detail, markets_at, coin_at, llama=None, llama_at=None, llama_detail=None):
    """row: fila de /coins/markets. detail: /coins/{id} o None. llama: registro de DefiLlama o None."""
    md = (detail or {}).get("market_data") or {}
    coin_id = row.get("id", "")
    src = {
        "markets": (f"{cg.SOURCE_NAME} · /coins/markets", f"{cg.BASE}/coins/markets", markets_at),
        "coin": (f"{cg.SOURCE_NAME} · /coins/{{id}}", f"{cg.BASE}/coins/{coin_id}", coin_at),
    }
    ev = {}
    for key, label, md_key, row_key, kind in _SPECS:
        v, where = _pick(md, row, md_key, row_key)
        if v is None:
            continue
        s, u, t = src[where]
        ev[key] = Evidence(key, label, v, _FMT[kind](v), HECHO, s, u, t)

    def add(key, label, value, display, kind, source, url, at, note=""):
        ev[key] = Evidence(key, label, value, display, kind, source, url, at, note)

    def est(key, label, value, display, formula, parts):
        used = [ev[p] for p in parts]
        add(key, label, value, display, ESTIMACION, "Cálculo MCI sobre datos de las fuentes",
            used[0].url, max(e.fetched_at for e in used), formula)

    cap, vol, fdv, circ, mx = (ev[k].value if k in ev else None for k in ("cap", "vol", "fdv", "circ", "max"))
    if cap and cap > 0 and vol is not None:
        est("vol_cap", "Volumen / capitalización", vol / cap, ratio_pct(vol / cap), "volumen 24 h ÷ capitalización", ("vol", "cap"))
    if circ and mx and mx > 0:
        est("circ_max", "Circulante / oferta máxima", circ / mx, ratio_pct(circ / mx), "oferta circulante ÷ oferta máxima", ("circ", "max"))
    if cap and cap > 0 and fdv:
        est("fdv_cap", "FDV / capitalización", fdv / cap, f"{fdv / cap:.2f}x", "FDV ÷ capitalización", ("fdv", "cap"))

    if detail:
        s, u, t = src["coin"]
        commits = (detail.get("developer_data") or {}).get("commits_last_4_weeks")
        if commits is not None:
            add("commits", "Commits en GitHub (últimas 4 semanas)", commits, f"{commits:,}", HECHO, s, u, t,
                "Reportado por CoinGecko a partir de GitHub. No mide calidad ni progreso.")
        com = detail.get("community_data") or {}
        for key, label, field in (("twitter", "Seguidores en X/Twitter", "twitter_followers"),
                                  ("reddit", "Suscriptores en Reddit", "reddit_subscribers")):
            if com.get(field):
                add(key, label, com[field], f"{com[field]:,}", HECHO, s, u, t,
                    "Audiencia reportada; no es evidencia de adopción real.")

    if llama:
        t = llama_at or markets_at
        page = f"https://defillama.com/protocol/{llama['slug']}" if llama.get("slug") else f"{dl.BASE}/protocols"
        s_p, s_f = f"{dl.SOURCE_NAME} · /protocols", f"{dl.SOURCE_NAME} · /overview/fees"
        note = "Cruce por identificador de CoinGecko informado por DefiLlama; puede no incluir todas las versiones del protocolo."
        is_chain = llama.get("kind") == "chain"
        if llama.get("tvl") is not None:
            add("tvl", "TVL de la cadena" if is_chain else "TVL del protocolo", llama["tvl"], money(llama["tvl"]),
                HECHO, s_p, page, t, note)
        if llama.get("tvl_change_7d") is not None:
            add("tvl_7d", "Variación del TVL (7 días)", llama["tvl_change_7d"], pct(llama["tvl_change_7d"]), HECHO, s_p, page, t)
        if not is_chain and llama.get("audits") is not None:
            a = llama["audits"]
            none = str(a).strip() in ("", "0", "None")
            add("audits", "Auditorías listadas en DefiLlama", a,
                "Ninguna listada" if none else f"Listadas (nivel {a})", HECHO, s_p, page, t,
                "Que DefiLlama no liste auditorías no prueba que no existan; que las liste no prueba que sean suficientes.")
        for key, label, field in (("fees_30d", "Comisiones pagadas por usuarios (30 d)", "fees_30d"),
                                  ("rev_30d", "Ingresos retenidos por el protocolo (30 d)", "rev_30d")):
            if llama.get(field) is not None:
                add(key, label, llama[field], money(llama[field]), HECHO, s_f, f"{dl.BASE}/overview/fees", t,
                    "Agregado por DefiLlama; no verifica si las comisiones son orgánicas o incentivadas.")
        tvl_v = ev["tvl"].value if "tvl" in ev else None
        if cap and cap > 0 and tvl_v and tvl_v > 0:
            est("cap_tvl", "Capitalización / TVL", cap / tvl_v, f"{cap / tvl_v:.2f}x", "capitalización ÷ TVL", ("cap", "tvl"))
        for key, label, src_key in (("cap_fees", "Capitalización / comisiones anualizadas", "fees_30d"),
                                    ("cap_rev", "Capitalización / ingresos anualizados", "rev_30d")):
            v = ev[src_key].value if src_key in ev else None
            if cap and cap > 0 and v and v > 0:
                est(key, label, cap / (v * 365 / 30), f"{cap / (v * 365 / 30):,.1f}x",
                    "capitalización ÷ (valor de 30 d × 365/30)", ("cap", src_key))

    links = (llama_detail or {}).get("audit_links")
    if isinstance(links, list) and links:
        add("audit_links", "Informes de auditoría enlazados", len(links), f"{len(links)} enlaces", HECHO,
            f"{dl.SOURCE_NAME} · /protocol/{{slug}}", f"https://defillama.com/protocol/{(llama or {}).get('slug', '')}",
            llama_at or markets_at, "No se leyó el contenido de los informes.")
    return ev
