from datetime import datetime


def money(v, cur="usd"):
    """Formato largo (para tablas de evidencia)."""
    if v is None:
        return "Sin dato"
    s = {"usd": "US$", "eur": "€", "ars": "AR$"}.get(cur, cur.upper())
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


def short_money(v):
    """Formato compacto (para tarjetas): US$1.29T, US$86.9B, US$215M."""
    if v is None:
        return "—"
    a = abs(v)
    if a >= 1e12:
        return f"US${v / 1e12:.2f}T"
    if a >= 1e9:
        return f"US${v / 1e9:.1f}B"
    if a >= 1e6:
        return f"US${v / 1e6:.1f}M"
    if a >= 1e3:
        return f"US${v / 1e3:.0f}K"
    return f"US${v:,.0f}"


def price(v, sym="US$"):
    if v is None:
        return "—"
    if v >= 1000:
        return f"{sym}{v:,.0f}"
    if v >= 1:
        return f"{sym}{v:,.2f}"
    if v >= 0.01:
        return f"{sym}{v:.4f}"
    return f"{sym}{v:.8f}"


def pct(v):
    return "Sin dato" if v is None else f"{v:+.2f}%"


def ratio_pct(v):
    return "Sin dato" if v is None else f"{v:.1%}"


def number(v):
    return "Sin dato" if v is None else f"{v:,.0f}"


def fmt_dt(d: datetime):
    return d.strftime("%d/%m/%Y %H:%M UTC")
