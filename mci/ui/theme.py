"""Estilos de MCI. Paleta: azul tinta + turquesa; verde/rojo solo para variación; ámbar para cautela."""

CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700;12..96,800&family=DM+Sans:wght@400;500;700&display=swap');
:root{--bg:#0A0F1C;--panel:#111826;--panel2:#161F31;--line:#223049;--text:#E7EDF7;--muted:#8795AE;
--accent:#5EEAD4;--up:#34D399;--down:#F87171;--warn:#FBBF24;--info:#60A5FA;}
.stApp,.stApp *:not([data-testid="stIconMaterial"]):not([class*="material"]){font-family:'DM Sans',system-ui,-apple-system,'Segoe UI',sans-serif}
.mci-display,.mci-brand b,.mci-kpi .v,.mci-hero .px,.mci-verdict .t,h1,h2,h3{font-family:'Bricolage Grotesque','DM Sans',sans-serif!important;letter-spacing:-.02em}
.block-container{max-width:1240px;padding-top:1.1rem;padding-bottom:4rem}
header[data-testid="stHeader"]{background:transparent}
#MainMenu,footer{visibility:hidden}
/* marca */
.mci-brand{display:flex;align-items:center;gap:12px;margin:0 0 .4rem 0}
.mci-brand .logo{display:flex;align-items:flex-end;gap:3px;height:30px}
.mci-brand .logo i{display:block;width:5px;border-radius:2px;background:var(--accent)}
.mci-brand b{font-size:1.55rem;font-weight:800;color:var(--text)}
.mci-brand span{color:var(--muted);font-size:.82rem;margin-left:2px}
/* navegación (st.radio horizontal como pestañas) */
div[data-testid="stRadio"] > div[role="radiogroup"]{gap:.35rem;flex-wrap:wrap}
div[data-testid="stRadio"] label{background:var(--panel);border:1px solid var(--line);border-radius:999px;padding:.38rem 1.05rem;cursor:pointer;transition:all .15s}
div[data-testid="stRadio"] label:hover{border-color:var(--accent)}
div[data-testid="stRadio"] label > div:first-child{display:none}
div[data-testid="stRadio"] label:has(input:checked){background:var(--accent);border-color:var(--accent)}
div[data-testid="stRadio"] label:has(input:checked) *{color:#06201C!important;font-weight:700}
/* tarjetas */
.mci-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px;margin:.4rem 0 1rem}
.mci-grid.w2{grid-template-columns:repeat(auto-fit,minmax(260px,1fr))}
.mci-kpi,.mci-dim,.mci-find,.mci-hero,.mci-mover{background:var(--panel);border:1px solid var(--line);border-radius:14px}
.mci-kpi{padding:14px 16px}
.mci-kpi .l{color:var(--muted);font-size:.78rem;text-transform:uppercase;letter-spacing:.06em}
.mci-kpi .v{font-size:1.55rem;font-weight:700;color:var(--text);margin-top:2px;white-space:nowrap}
.mci-kpi .s{margin-top:4px;font-size:.82rem;color:var(--muted)}
.mci-kpi.hl{border-color:var(--accent)}
.mci-hero{padding:18px 20px;display:flex;gap:16px;align-items:center;flex-wrap:wrap}
.mci-hero img{width:52px;height:52px;border-radius:50%;background:#fff1}
.mci-hero .nm{font-size:1.5rem;font-weight:800;line-height:1.1}
.mci-hero .sub{color:var(--muted);font-size:.85rem;margin-top:4px;display:flex;gap:6px;flex-wrap:wrap;align-items:center}
.mci-hero .px{margin-left:auto;text-align:right;font-size:2rem;font-weight:800}
.mci-hero .px small{display:block;font-size:.78rem;color:var(--muted);font-weight:500;font-family:'DM Sans',sans-serif}
/* chips */
.mci-chip{display:inline-block;padding:2px 10px;border-radius:999px;font-size:.76rem;font-weight:700;border:1px solid var(--line);color:var(--muted);background:var(--panel2)}
.mci-chip.up{color:var(--up);border-color:#1d5c46;background:#0f2a22}
.mci-chip.down{color:var(--down);border-color:#6b2a2a;background:#2b1616}
.mci-chip.warn{color:var(--warn);border-color:#6b5217;background:#2a2210}
.mci-chip.info{color:var(--info);border-color:#244a7a;background:#101f35}
.mci-chip.accent{color:var(--accent);border-color:#1b5a52;background:#0e2523}
/* barra de evidencia: el rasgo propio de MCI */
.mci-bar{display:flex;gap:4px;align-items:center}
.mci-bar i{display:block;width:100%;min-width:14px;height:8px;border-radius:3px;background:var(--line)}
.mci-bar i.on{background:var(--accent)}
.mci-bar i.part{background:repeating-linear-gradient(135deg,var(--accent) 0 3px,#0e3b36 3px 6px)}
.mci-bar em{font-style:normal;color:var(--muted);font-size:.78rem;margin-left:8px;white-space:nowrap}
/* veredicto */
.mci-verdict{border-radius:16px;padding:18px 22px;margin:1rem 0;border:1px solid var(--line);background:var(--panel)}
.mci-verdict .k{font-size:.74rem;text-transform:uppercase;letter-spacing:.1em;color:var(--muted)}
.mci-verdict .t{font-size:1.7rem;font-weight:800;margin:2px 0 6px}
.mci-verdict .r{color:var(--text);opacity:.88;font-size:.92rem;margin-bottom:12px}
.mci-verdict.no_concluyente{border-color:#6b5217;background:linear-gradient(135deg,#1c1807,#111826 60%)}
.mci-verdict.no_concluyente .t{color:var(--warn)}
.mci-verdict.parcial{border-color:#244a7a;background:linear-gradient(135deg,#0c1a2e,#111826 60%)}
.mci-verdict.parcial .t{color:var(--info)}
.mci-verdict.suficiente{border-color:#1d5c46;background:linear-gradient(135deg,#0b2019,#111826 60%)}
.mci-verdict.suficiente .t{color:var(--up)}
.mci-verdict.fuera_de_alcance .t{color:var(--muted)}
/* dimensiones y hallazgos */
.mci-dim{padding:12px 14px}
.mci-dim .h{display:flex;justify-content:space-between;align-items:center;gap:8px;font-weight:700;font-size:.92rem}
.mci-dim .d{color:var(--muted);font-size:.78rem;margin-top:6px;line-height:1.35}
.mci-dim.sin_datos{opacity:.6}
.mci-find{padding:12px 14px;margin-bottom:10px;border-left:3px solid var(--line)}
.mci-find.a_favor{border-left-color:var(--up)}
.mci-find.cautela{border-left-color:var(--warn)}
.mci-find .o{font-weight:600;font-size:.92rem}
.mci-find .i{color:var(--muted);font-size:.85rem;margin-top:4px}
.mci-find details{margin-top:6px;font-size:.8rem;color:var(--muted)}
.mci-find summary{cursor:pointer;color:var(--accent)}
.mci-sec{font-family:'Bricolage Grotesque',sans-serif;font-size:1.15rem;font-weight:700;margin:1.4rem 0 .5rem}
.mci-sec small{color:var(--muted);font-family:'DM Sans',sans-serif;font-weight:400;font-size:.8rem;margin-left:8px}
.mci-mover{padding:8px 12px;display:flex;justify-content:space-between;align-items:center;margin-bottom:6px}
.mci-note{color:var(--muted);font-size:.78rem}
.mci-dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:8px;background:var(--up)}
.mci-dot.bad{background:var(--down)}.mci-dot.mid{background:var(--warn)}
section[data-testid="stSidebar"]{background:var(--panel);border-right:1px solid var(--line)}
div[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:12px;overflow:hidden}
.stButton>button,.stDownloadButton>button,.stLinkButton>a{border-radius:10px}
</style>"""
