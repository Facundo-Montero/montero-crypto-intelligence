from datetime import datetime

_SYMBOLS = {"usd": "US$", "eur": "€", "ars": "AR$"}


def money(v, cur="usd"):
    if v is None:
        return "Sin dato"
    s = _SYMBOLS.get(cur, cur.upper())
    a = abs(v)
    if a >= 1e12:
        return f"{s} {v / 1e12:,.2f} billones"
    if a >= 1e9:
        return f"{s} {v / 1e9:,.2f} mil millones"
    if a >= 1e6:
        return f"{s} {v / 1e6:,.2f} millones"
    if a >= 1:
        return f"{s} {v:,.2f}"
    return f"{s} {v:.8f}"


def pct(v):
    return "Sin dato" if v is None else f"{v:+.2f}%"


def ratio_pct(v):
    return "Sin dato" if v is None else f"{v:.1%}"


def number(v):
    return "Sin dato" if v is None else f"{v:,.0f}"


def fmt_dt(d: datetime):
    return d.strftime("%d/%m/%Y %H:%M UTC")
