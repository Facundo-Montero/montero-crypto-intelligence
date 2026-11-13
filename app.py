import datetime as dt
import requests
import pandas as pd
import streamlit as st

st.set_page_config(page_title="MCI | Montero Crypto Intelligence", page_icon="◈", layout="wide")

BG = "#0B1220"
PANEL = "#111C2E"
MUTED = "#9AA9BD"
ACCENT = "#62D6C5"

st.markdown("""
<style>
.stApp {background: linear-gradient(135deg,#09111f 0%,#0d1728 55%,#101b2d 100%); color:#edf3fb;}
.block-container {padding-top:2rem; max-width:1450px;}
[data-testid="stMetric"] {background:#111c2e; border:1px solid #24334a; padding:16px; border-radius:14px;}
div[data-testid="stDataFrame"] {border:1px solid #24334a; border-radius:12px;}
h1,h2,h3 {letter-spacing:-.03em;}
.mci-kicker {color:#62d6c5; font-size:.78rem; font-weight:700; letter-spacing:.18em;}
.mci-muted {color:#9aa9bd;}
.mci-card {background:#111c2e; border:1px solid #24334a; border-radius:14px; padding:18px;}
</style>
""", unsafe_allow_html=True)

STABLE_SYMBOLS = {"usdt","usdc","dai","busd","tusd","usde","fdusd","usds","usdd","pyusd","frax","lusd","susd","eurc","eurs"}
WRAPPED_SYMBOLS = {"wbtc","weth","steth","wsteth","cbeth","reth","wavax","wftm"}
SYNTHETIC_HINTS = ("tokenized","wrapped","bridged","3x long","3x short","etf")

@st.cache_data(ttl=300, show_spinner=False)
def fetch_markets(currency, pages, min_volume):
    rows = []
    for page in range(1, pages + 1):
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": currency, "order": "market_cap_desc",
            "per_page": 250, "page": page, "sparkline": "false",
            "price_change_percentage": "24h,7d,30d"
        }
        response = requests.get(url, params=params, timeout=25,
                                headers={"accept": "application/json", "User-Agent": "MCI-research-dashboard/0.1"})
        response.raise_for_status()
        batch = response.json()
        if not batch:
            break
        rows.extend(batch)
    df = pd.DataFrame(rows)
    if not df.empty:
        df["total_volume"] = pd.to_numeric(df["total_volume"], errors="coerce")
        df = df[df["total_volume"].fillna(0) >= min_volume]
    return df

def classify(row):
    symbol = str(row.get("symbol", "")).lower()
    name = str(row.get("name", "")).lower()
    if symbol in STABLE_SYMBOLS or "stablecoin" in name:
        return "Stablecoin"
    if symbol in WRAPPED_SYMBOLS or any(x in name for x in SYNTHETIC_HINTS):
        return "Wrapped / sintético"
    cap = row.get("market_cap") or 0
    if cap >= 10_000_000_000:
        return "Consolidado"
    if cap >= 1_000_000_000:
        return "Intermedio"
    return "Emergente"

def money(value, currency):
    if pd.isna(value):
        return "—"
    symbol = "$" if currency == "usd" else "€" if currency == "eur" else currency.upper() + " "
    return f"{symbol}{value:,.2f}" if value < 1000 else f"{symbol}{value:,.0f}"

st.markdown('<div class="mci-kicker">MONTERO CRYPTO INTELLIGENCE</div>', unsafe_allow_html=True)
st.title("Investigación cripto basada en evidencia")
st.markdown('<p class="mci-muted">Un radar para investigar activos, entender qué muestran los datos y detectar qué todavía no sabemos.</p>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## Configuración")
    currency = st.selectbox("Moneda de referencia", ["usd", "ars", "eur"], index=0)
    pages = st.slider("Universo a consultar", 1, 4, 2, help="Hasta 1.000 activos por consulta. Más páginas pueden tardar y alcanzar límites de la API.")
    min_volume = st.number_input("Volumen mínimo 24 h", min_value=0, value=1_000_000 if currency == "usd" else 0, step=100_000)
    include_non_growth = st.checkbox("Incluir stablecoins y sintéticos", value=False)
    st.caption("Fuente de mercado: CoinGecko API pública. Datos sujetos a límites, retrasos y cobertura de terceros.")

try:
    with st.spinner("Consultando datos de mercado..."):
        data = fetch_markets(currency, pages, min_volume)
    if data.empty:
        st.warning("La fuente no devolvió activos para estos filtros.")
        st.stop()
except Exception as exc:
    st.error("No se pudieron obtener datos de mercado en este momento.")
    st.caption(f"Detalle técnico: {exc}")
    st.info("Probá nuevamente más tarde. MCI no completa datos faltantes con estimaciones inventadas.")
    st.stop()

data["classification"] = data.apply(classify, axis=1)
data["price_change_percentage_7d_in_currency"] = pd.to_numeric(data.get("price_change_percentage_7d_in_currency"), errors="coerce")
data["price_change_percentage_24h_in_currency"] = pd.to_numeric(data.get("price_change_percentage_24h_in_currency"), errors="coerce")
market_time = dt.datetime.now().astimezone().strftime("%d/%m/%Y %H:%M %Z")

universe = data.copy()
if not include_non_growth:
    universe = universe[~universe["classification"].isin(["Stablecoin", "Wrapped / sintético"])]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Activos analizados", f"{len(universe):,}")
c2.metric("Capitalización agregada", money(universe["market_cap"].sum(), currency))
c3.metric("Volumen 24 h", money(universe["total_volume"].sum(), currency))
c4.metric("Actualización", market_time)
st.caption("La hora indica cuándo MCI consultó la API; no garantiza que cada proveedor haya actualizado todos los mercados en ese instante.")

tab1, tab2, tab3 = st.tabs(["Radar de activos", "Dossier de investigación", "Metodología"])

with tab1:
    st.subheader("Explorador de mercado")
    st.markdown("El orden inicial prioriza capitalización, no potencial de rentabilidad. Los cambios de precio son contexto de mercado, no evidencia fundamental.")
    classes = ["Todas"] + sorted(universe["classification"].dropna().unique().tolist())
    chosen_class = st.selectbox("Clasificación", classes)
    search = st.text_input("Buscar activo", placeholder="Ej.: Bitcoin, Ethereum, Solana...")
    view = universe.copy()
    if chosen_class != "Todas":
        view = view[view["classification"] == chosen_class]
    if search:
        mask = view["name"].str.contains(search, case=False, na=False) | view["symbol"].str.contains(search, case=False, na=False)
        view = view[mask]
    view = view.sort_values("market_cap", ascending=False)
    table = pd.DataFrame({
        "Activo": view["name"], "Ticker": view["symbol"].str.upper(),
        "Tipo": view["classification"], "Precio": view["current_price"].map(lambda x: money(x, currency)),
        "Cap. mercado": view["market_cap"].map(lambda x: money(x, currency)),
        "Volumen 24 h": view["total_volume"].map(lambda x: money(x, currency)),
        "Cambio 24 h": view["price_change_percentage_24h_in_currency"].map(lambda x: f"{x:+.2f}%" if pd.notna(x) else "—"),
        "Cambio 7 d": view["price_change_percentage_7d_in_currency"].map(lambda x: f"{x:+.2f}%" if pd.notna(x) else "—")
    })
    st.dataframe(table, use_container_width=True, hide_index=True)
    st.caption(f"Mostrando {len(view)} activos. Los filtros de volumen y universo se aplican antes de esta tabla.")

with tab2:
    st.subheader("Dossier de investigación")
    options = universe.sort_values("market_cap", ascending=False)
    if options.empty:
        st.info("No hay activos en el radar con los filtros actuales.")
    else:
        labels = {f"{r['name']} ({str(r['symbol']).upper()})": r["id"] for _, r in options.iterrows()}
        selected_label = st.selectbox("Seleccionar activo", list(labels.keys()))
        asset = options[options["id"] == labels[selected_label]].iloc[0]
        left, right = st.columns([1.15, 1])
        with left:
            st.markdown(f"### {asset['name']} · {str(asset['symbol']).upper()}")
            st.write(f"**Clasificación MCI:** {asset['classification']}")
            st.metric("Precio actual", money(asset["current_price"], currency))
            st.metric("Capitalización", money(asset.get("market_cap"), currency))
            st.metric("Volumen 24 h", money(asset.get("total_volume"), currency))
        with right:
            st.markdown("#### Datos de oferta")
            st.write(f"Circulante: **{asset.get('circulating_supply'):,.0f}**" if pd.notna(asset.get("circulating_supply")) else "Circulante: **Sin dato**")
            st.write(f"Oferta total: **{asset.get('total_supply'):,.0f}**" if pd.notna(asset.get("total_supply")) else "Oferta total: **Sin dato**")
            st.write(f"Oferta máxima: **{asset.get('max_supply'):,.0f}**" if pd.notna(asset.get("max_supply")) else "Oferta máxima: **No informada**")
            fdv = asset.get("fully_diluted_valuation")
            st.write(f"Valoración totalmente diluida (FDV): **{money(fdv, currency)}**" if pd.notna(fdv) else "FDV: **Sin dato**")
        st.divider()
        st.markdown("#### Lectura de evidencia")
        st.warning("EVIDENCIA FUNDAMENTAL INSUFICIENTE — esta versión no verifica por sí sola adopción real, ingresos, comisiones, actividad de usuarios, auditorías, distribución de desbloqueos ni calidad de gobernanza.")
        st.markdown("**Lo que sí observamos**")
        st.write("- Precio, capitalización, volumen y variaciones de mercado reportados por CoinGecko.")
        st.write("- Datos de oferta cuando la fuente los publica.")
        st.markdown("**Lo que todavía hay que comprobar**")
        st.write("- Utilidad y demanda orgánica del protocolo, usuarios activos y retención.")
        st.write("- Fees, ingresos, TVL y actividad on-chain usando fuentes específicas del proyecto.")
        st.write("- Distribución de tokens, calendario de desbloqueos, concentración y presión potencial de venta.")
        st.write("- Auditorías, incidentes de seguridad, competencia, gobernanza y catalizadores verificables.")
        st.markdown("**Conclusión MCI**")
        st.info("Este dossier no emite una señal de compra. Con los datos actuales solo se puede describir el contexto de mercado; la tesis de inversión queda NO CONCLUYENTE hasta reunir evidencia fundamental independiente.")

with tab3:
    st.subheader("Cómo interpreta MCI la información")
    st.markdown("""
**1. Datos observables**  
Métricas obtenidas de una fuente identificada, con momento de consulta y limitaciones explícitas.

**2. Estimaciones**  
Cálculos derivados de datos observables. Deben mostrar fórmula, supuestos y margen de incertidumbre.

**3. Hipótesis**  
Posibles explicaciones, catalizadores o escenarios. No se presentan como hechos.

**4. Riesgos y evidencia contraria**  
Cada tesis debe incluir qué podría invalidarla: competencia, regulación, concentración, desbloqueos, vulnerabilidades, falta de adopción o deterioro de liquidez.

**5. Decisión**  
MCI separa calidad de evidencia de atractivo potencial. Si faltan datos esenciales, la conclusión es **NO CONCLUYENTE**, no una recomendación de compra.

### Limitaciones de esta versión
- Usa datos de mercado de CoinGecko; no constituye una auditoría de datos on-chain.
- La clasificación es heurística y puede requerir corrección manual.
- No incorpora todavía análisis de contratos, TVL, fees, revenue, auditorías ni calendario de vesting.
- No ofrece asesoramiento financiero ni ejecuta operaciones.
""")
st.divider()
st.caption("MONTERO CRYPTO INTELLIGENCE · Versión inicial · Solo investigación. No es asesoramiento financiero.");
