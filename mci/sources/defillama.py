"""DefiLlama (API gratuita, sin clave): TVL, comisiones e ingresos de protocolos y cadenas.
Los desbloqueos de tokens son un endpoint de pago y NO se usan."""
from datetime import datetime, timezone
from urllib.parse import quote

from mci.sources.base import SourceError, get_json

BASE = "https://api.llama.fi"
SOURCE_NAME = "DefiLlama"


def _now():
    return datetime.now(timezone.utc)


def _num(x):
    if isinstance(x, bool):
        return None
    try:
        f = float(x)
    except (TypeError, ValueError):
        return None
    return None if f != f else f


def fetch_protocols():
    data = get_json(f"{BASE}/protocols", source=SOURCE_NAME, timeout=45)
    if not isinstance(data, list):
        raise SourceError("Formato inesperado en DefiLlama /protocols.")
    return data, _now()


def fetch_chains():
    data = get_json(f"{BASE}/v2/chains", source=SOURCE_NAME, timeout=30)
    if not isinstance(data, list):
        raise SourceError("Formato inesperado en DefiLlama /v2/chains.")
    return data, _now()


def fetch_fees(data_type="dailyFees"):
    data = get_json(f"{BASE}/overview/fees", {
        "dataType": data_type, "excludeTotalDataChart": "true", "excludeTotalDataChartBreakdown": "true",
    }, source=SOURCE_NAME, timeout=45)
    items = data.get("protocols") if isinstance(data, dict) else data
    if not isinstance(items, list):
        raise SourceError("Formato inesperado en DefiLlama /overview/fees.")
    return items, _now()


def fetch_protocol_detail(slug):
    data = get_json(f"{BASE}/protocol/{quote(str(slug), safe='')}", source=SOURCE_NAME, timeout=30)
    if not isinstance(data, dict):
        raise SourceError("Formato inesperado en DefiLlama /protocol.")
    return data, _now()


def fetch_fees_summary(slug, data_type="dailyFees"):
    data = get_json(f"{BASE}/summary/fees/{quote(str(slug), safe='')}",
                    {"dataType": data_type, "excludeTotalDataChartBreakdown": "true"},
                    source=SOURCE_NAME, timeout=30)
    if not isinstance(data, dict):
        raise SourceError("Formato inesperado en DefiLlama /summary/fees.")
    return data, _now()


# ------------------------------------------------------------------ índice
def _fees_index(items):
    idx = {"id": {}, "slug": {}, "name": {}, "parent": {}}
    for it in items or []:
        if not isinstance(it, dict):
            continue
        if it.get("defillamaId") is not None:
            idx["id"][str(it["defillamaId"])] = it
        if it.get("slug"):
            idx["slug"][str(it["slug"]).lower()] = it
        for n in (it.get("name"), it.get("displayName")):
            if n:
                idx["name"][str(n).lower()] = it
        if it.get("parentProtocol"):
            idx["parent"].setdefault(str(it["parentProtocol"]), []).append(it)
    return idx


def _sum(items):
    out, seen = {}, False
    for k in ("total24h", "total7d", "total30d"):
        vals = [_num(i.get(k)) for i in items]
        vals = [v for v in vals if v is not None]
        out[k] = sum(vals) if vals else None
        seen = seen or bool(vals)
    return out if seen else None


def _fees_for(idx, pid, slug, name):
    if pid and pid in idx["id"]:
        return _sum([idx["id"][pid]])
    if slug and slug.lower() in idx["slug"]:
        return _sum([idx["slug"][slug.lower()]])
    if pid and pid in idx["parent"]:
        return _sum(idx["parent"][pid])
    if name and name.lower() in idx["name"]:
        return _sum([idx["name"][name.lower()]])
    return None


def build_index(protocols, chains, fees, revenue):
    """Devuelve {gecko_id: registro}. Cada fuente puede ser None (falló): ese dato queda sin dato."""
    f_idx, r_idx = _fees_index(fees), _fees_index(revenue)
    out = {}
    for p in protocols or []:
        if not isinstance(p, dict) or not p.get("gecko_id"):
            continue
        pid = str(p["id"]) if p.get("id") is not None else None
        slug, name = p.get("slug"), p.get("name")
        f = _fees_for(f_idx, pid, slug, name)
        r = _fees_for(r_idx, pid, slug, name)
        rec = {
            "kind": "protocol", "id": pid, "slug": slug, "name": name, "category": p.get("category"),
            "url": p.get("url"), "tvl": _num(p.get("tvl")),
            "tvl_change_1d": _num(p.get("change_1d")), "tvl_change_7d": _num(p.get("change_7d")),
            "audits": p.get("audits"), "audit_note": p.get("audit_note"),
            "fees_24h": f and f["total24h"], "fees_7d": f and f["total7d"], "fees_30d": f and f["total30d"],
            "rev_24h": r and r["total24h"], "rev_7d": r and r["total7d"], "rev_30d": r and r["total30d"],
        }
        gid = p["gecko_id"]
        if gid not in out or (rec["tvl"] or -1) > (out[gid]["tvl"] or -1):
            out[gid] = rec
    for c in chains or []:
        if not isinstance(c, dict) or not c.get("gecko_id") or c["gecko_id"] in out:
            continue
        name = c.get("name")
        f = _fees_for(f_idx, None, None, name)
        r = _fees_for(r_idx, None, None, name)
        out[c["gecko_id"]] = {
            "kind": "chain", "id": None, "slug": None, "name": name, "category": "Chain", "url": None,
            "tvl": _num(c.get("tvl")), "tvl_change_1d": None, "tvl_change_7d": None,
            "audits": None, "audit_note": None,
            "fees_24h": f and f["total24h"], "fees_7d": f and f["total7d"], "fees_30d": f and f["total30d"],
            "rev_24h": r and r["total24h"], "rev_7d": r and r["total7d"], "rev_30d": r and r["total30d"],
        }
    return out


def tvl_history(detail):
    """Historial de TVL: lista de (timestamp_ms, usd)."""
    out = []
    for e in (detail or {}).get("tvl") or []:
        if isinstance(e, dict):
            d, v = _num(e.get("date")), _num(e.get("totalLiquidityUSD"))
            if d is not None and v is not None:
                out.append((int(d * 1000), v))
    return out


def fees_history(summary):
    """Historial diario de comisiones: lista de (timestamp_ms, usd)."""
    out = []
    for e in (summary or {}).get("totalDataChart") or []:
        if isinstance(e, (list, tuple)) and len(e) >= 2:
            d, v = _num(e[0]), _num(e[1])
            if d is not None and v is not None:
                out.append((int(d * 1000), v))
    return out
