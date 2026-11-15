"""Piezas HTML reutilizables. TODO texto externo se escapa con esc()."""
import html

import streamlit as st

from mci.formatting import price as fmt_price

LOGO_HEIGHTS = (30, 6, 10, 15, 21, 26, 30)


def esc(x):
    return html.escape(str(x), quote=True)


def md(h):
    st.markdown(h, unsafe_allow_html=True)


def brand():
    bars = "".join(f'<i style="height:{h}px;opacity:{0.45 + i * 0.09:.2f}"></i>' for i, h in enumerate((6, 10, 15, 21, 26, 30)))
    md(f'<div class="mci-brand"><div class="logo">{bars}</div><b>MCI</b><span>Montero Crypto Intelligence</span></div>')


def section(title, hint=""):
    md(f'<div class="mci-sec">{esc(title)}<small>{esc(hint)}</small></div>')


def chip(text, tone=""):
    return f'<span class="mci-chip {tone}">{esc(text)}</span>'


def change_chip(v):
    if v is None:
        return chip("—")
    return chip(f"{'▲' if v >= 0 else '▼'} {abs(v):.2f}%", "up" if v >= 0 else "down")


def kpi(label, value, sub_html="", hl=False):
    return (f'<div class="mci-kpi{" hl" if hl else ""}"><div class="l">{esc(label)}</div>'
            f'<div class="v">{esc(value)}</div><div class="s">{sub_html}</div></div>')


def grid(cards, wide=False):
    md(f'<div class="mci-grid{" w2" if wide else ""}">{"".join(cards)}</div>')


def evidence_bar(dims, show_count=True):
    cls = {"cubierta": "on", "parcial": "part", "sin_datos": ""}
    segs = "".join(f'<i class="{cls[d.status]}" title="{esc(d.label)}: {esc(d.status.replace("_", " "))}"></i>' for d in dims)
    covered = sum(1 for d in dims if d.status != "sin_datos")
    count = f"<em>{covered}/{len(dims)}</em>" if show_count else ""
    return f'<div class="mci-bar">{segs}{count}</div>'


def verdict_banner(verdict, dims):
    md(f'<div class="mci-verdict {esc(verdict.level)}"><div class="k">Conclusión de MCI</div>'
       f'<div class="t">{esc(verdict.label)}</div><div class="r">{esc(" ".join(verdict.reasons))}</div>'
       f'{evidence_bar(dims)}<div class="mci-note" style="margin-top:8px">'
       'Mide cuánta evidencia hay, no el atractivo del activo ni una probabilidad de rentabilidad.</div></div>')


def dim_cards(dims):
    tone = {"cubierta": ("Cubierta", "up"), "parcial": ("Parcial", "warn"), "sin_datos": ("Sin datos", "")}
    cards = []
    for d in dims:
        t, c = tone[d.status]
        star = " ★" if d.essential else ""
        cards.append(f'<div class="mci-dim {d.status}"><div class="h"><span>{esc(d.label)}{star}</span>{chip(t, c)}</div>'
                     f'<div class="d">{esc(d.detail)}</div></div>')
    grid(cards)
    md('<div class="mci-note">★ = esencial para sostener una tesis</div>')


def finding_card(f):
    return (f'<div class="mci-find {esc(f.polarity)}"><div class="o">{esc(f.observation)}</div>'
            f'<div class="i">{esc(f.implication)}</div>'
            f'<details><summary>¿Qué lo invalidaría?</summary>{esc(f.invalidation)}<br><i>{esc(f.rule)}</i></details></div>')


def findings(items, empty):
    if not items:
        md(f'<div class="mci-note">{esc(empty)}</div>')
        return
    md("".join(finding_card(f) for f in items))


def hero(row, cls, rank, watching, extra_prices=""):
    img = f'<img src="{esc(row.get("image"))}" alt="">' if str(row.get("image") or "").startswith("https://") else ""
    p, ch = row.get("current_price"), row.get("price_change_percentage_24h_in_currency")
    md(f'<div class="mci-hero">{img}<div><div class="nm">{esc(row.get("name"))} <span style="color:var(--muted);font-weight:500">'
       f'{esc(str(row.get("symbol")).upper())}</span></div><div class="sub">{chip("#" + str(rank) if rank else "Sin rank")}'
       f'{chip(cls, "accent")}{chip("★ En tu lista", "warn") if watching else ""}</div></div>'
       f'<div class="px">{esc(fmt_price(p))}<small>{change_chip(ch)} 24 h{extra_prices}</small></div></div>')
