"""Pantalla Activo: dossier de investigación."""
import pandas as pd
import streamlit as st

from mci.analysis.classify import classify
from mci.analysis.evidence import build_evidence
from mci.analysis.report import dossier_markdown, evidence_csv
from mci.analysis.rules import evaluate
from mci.analysis.verdict import assess_dimensions, build_verdict
from mci.data import load_chart, load_coin, load_llama_detail
from mci.formatting import fmt_dt, price, short_money
from mci.sources import defillama as dl
from mci.sources.base import SourceError
from mci.state import open_asset, toggle_watch
from mci.ui import charts
from mci.ui.components import dim_cards, esc, evidence_bar, findings, grid, hero, kpi, md, section, verdict_banner, chip

KEYS = [  # etiqueta corta, clave de evidencia, formato
    ("Capitalización", "cap", "money"), ("Volumen 24 h", "vol", "money"), ("FDV / cap.", "fdv_cap", "disp"),
    ("Circulante / máx.", "circ_max", "disp"), ("TVL", "tvl", "money"), ("Comisiones 30 d", "fees_30d", "money"),
    ("Ingresos 30 d", "rev_30d", "money"), ("Cap. / comisiones", "cap_fees", "disp"), ("Cap. / TVL", "cap_tvl", "disp"),
    ("Commits 4 sem.", "commits", "disp"),
]


def _empty(ctx):
    md('<div class="mci-note" style="margin:1.2rem 0 .6rem">Elegí un activo arriba, o tocá una fila en el Radar. Algunos para empezar:</div>')
    ids = ctx.all_ids[:8]
    cols = st.columns(4)
    for i, cid in enumerate(ids):
        cols[i % 4].button(ctx.labels[cid], key=f"sug_{cid}", on_click=open_asset, args=(cid,), width="stretch")


def render(ctx):
    ss = st.session_state
    cur = ss.get("asset_id")
    idx = ctx.all_ids.index(cur) if cur in ctx.labels else None
    choice = st.selectbox("Activo", ctx.all_ids, index=idx, format_func=lambda i: ctx.labels[i],
                          placeholder="Escribí un nombre o ticker…", label_visibility="collapsed")
    if choice != cur:
        ss["asset_id"] = choice
    if not choice:
        _empty(ctx)
        return

    aid, row = choice, ctx.by_id[choice]
    detail, coin_at = None, ctx.markets_at
    try:
        with st.spinner("Reuniendo evidencia…"):
            detail, coin_at = load_coin(aid, ctx.api_key)
    except SourceError as e:
        st.warning(f"Ficha detallada no disponible ({e}). Se usan solo datos del listado.")
    rec = ctx.llama["index"].get(aid)
    ldet = load_llama_detail(rec["slug"]) if rec and rec.get("kind") == "protocol" and rec.get("slug") else None
    ev = build_evidence(row, detail, ctx.markets_at, coin_at, rec, ctx.llama["at"], (ldet or {}).get("detail"))
    cls = classify(row, (detail or {}).get("categories"))
    items, dims = evaluate(ev), None
    dims = assess_dimensions(ev)
    verdict = build_verdict(cls, dims)

    cp = ((detail or {}).get("market_data") or {}).get("current_price") or {}
    extra = "".join(f" · {esc(price(cp[c], s))}" for c, s in (("ars", "AR$"), ("eur", "€")) if cp.get(c))
    watching = aid in ss.get("watch", [])
    hero(row, cls, row.get("market_cap_rank"), watching, extra)

    b1, b2, b3, _ = st.columns([1.3, 1.2, 1.2, 3])
    b1.button("★ Quitar de mi lista" if watching else "☆ Seguir", key="watch_btn", on_click=toggle_watch, args=(aid,), width="stretch")
    b2.download_button("⬇ Resumen", dossier_markdown(row["name"], row["symbol"], cls, verdict, dims, items, ev),
                       file_name=f"MCI_{aid}.md", mime="text/markdown", width="stretch")
    b3.download_button("⬇ Datos CSV", evidence_csv(ev), file_name=f"MCI_{aid}_evidencias.csv", mime="text/csv", width="stretch")

    verdict_banner(verdict, dims)

    section("Precio", "USD · CoinGecko")
    rng = st.radio("Período", ["30 d", "90 d", "1 año"], index=1, horizontal=True, key="asset_range", label_visibility="collapsed")
    chart = load_chart(aid, ctx.api_key)
    if chart.data:
        st.plotly_chart(charts.price_chart(chart.data, {"30 d": 30, "90 d": 90, "1 año": 365}[rng]), config=charts.CONFIG)
    else:
        md(f'<div class="mci-note">Historial no disponible: {esc(chart.error)}</div>')

    section("Cobertura de evidencia", "qué sabemos y qué no")
    dim_cards(dims)

    section("Números clave", "hecho o estimación, con fuente en el detalle")
    cards = []
    for label, key, fmt in KEYS:
        e = ev.get(key)
        if e is None:
            continue
        val = short_money(e.value) if fmt == "money" else e.display
        cards.append(kpi(label, val, chip(e.kind, "accent" if e.kind == "hecho" else "info")))
    grid(cards) if cards else md('<div class="mci-note">Sin números clave disponibles.</div>')

    if ldet and ldet.get("detail"):
        tvl_h = dl.tvl_history(ldet["detail"])
        fee_h = dl.fees_history(ldet.get("fees"))
        if tvl_h or fee_h:
            section("Uso real", "DefiLlama · 12 meses de TVL, 90 días de comisiones")
            a, b = st.columns(2)
            if tvl_h:
                a.markdown("**TVL**")
                a.plotly_chart(charts.line_area(tvl_h, days=365), config=charts.CONFIG)
            if fee_h:
                b.markdown("**Comisiones diarias**")
                b.plotly_chart(charts.bars(fee_h, days=90), config=charts.CONFIG)

    section("Lectura", "hipótesis a verificar, no conclusiones")
    l, r = st.columns(2)
    with l:
        md("<b>A favor</b>")
        findings([f for f in items if f.polarity == "a_favor"], "Ningún indicio supera los criterios de MCI.")
    with r:
        md("<b>Cautelas</b>")
        findings([f for f in items if f.polarity == "cautela"], "Sin alertas básicas. No significa que sea seguro.")
    ctxt = [f for f in items if f.polarity == "contexto"]
    if ctxt:
        with st.expander("Contexto de precio (no es fundamento)"):
            findings(ctxt, "")

    section("Para verificar vos", "enlaces oficiales")
    pend = [d.label for d in dims if d.essential and d.status != "cubierta"]
    if pend:
        md('<div class="mci-note">Pendiente de verificar: ' + esc(" · ".join(pend)) + "</div>")
    links = (detail or {}).get("links") or {}
    urls = [("Sitio oficial", u) for u in (links.get("homepage") or [])[:1] if u]
    urls += [("GitHub", u) for u in ((links.get("repos_url") or {}).get("github") or [])[:1] if u]
    if links.get("whitepaper"):
        urls.append(("Whitepaper", links["whitepaper"]))
    urls += [("Explorador", u) for u in (links.get("blockchain_site") or [])[:1] if u]
    if rec and rec.get("slug"):
        urls.append(("DefiLlama", f"https://defillama.com/protocol/{rec['slug']}"))
    urls.append(("CoinGecko", f"https://www.coingecko.com/en/coins/{aid}"))
    urls.append(("Desbloqueos (DefiLlama)", "https://defillama.com/unlocks"))
    for i, a in enumerate(((ldet or {}).get("detail") or {}).get("audit_links") or []):
        if i < 3:
            urls.append((f"Auditoría {i + 1}", a))
    cols = st.columns(4)
    for i, (label, url) in enumerate([u for u in urls if str(u[1]).startswith("https://")][:12]):
        cols[i % 4].link_button(label, url, width="stretch")
    md('<div class="mci-note">MCI no verificó la vigencia ni la autenticidad de estos enlaces.</div>')

    with st.expander("Qué dice el proyecto de sí mismo (autodeclarado, no verificado)"):
        import re
        d = (detail or {}).get("description") or {}
        text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", d.get("en") or d.get("es") or "")).strip()
        st.write(text[:1500] + ("…" if len(text) > 1500 else "") if text else "Sin descripción disponible.")
    with st.expander("Todas las evidencias, fuentes y fechas"):
        st.dataframe(pd.DataFrame([{
            "Dato": e.label, "Valor": e.display, "Tipo": e.kind, "Fuente": e.source,
            "Consultado": fmt_dt(e.fetched_at), "Nota": e.note, "Enlace": e.url} for e in ev.values()]),
            hide_index=True, column_config={"Enlace": st.column_config.LinkColumn("Enlace", display_text="abrir")})
    errs = (ldet or {}).get("errors") or []
    if errs:
        md('<div class="mci-note">DefiLlama (detalle): ' + esc(" · ".join(errs)) + "</div>")
