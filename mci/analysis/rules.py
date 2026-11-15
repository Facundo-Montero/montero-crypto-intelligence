"""Reglas de lectura de MCI. Los umbrales son CRITERIOS de MCI (editables), no hechos del mercado."""
from dataclasses import dataclass

from mci.models import Finding


@dataclass(frozen=True)
class Thresholds:
    vol_cap_high: float = 0.15   # volumen/capitalización considerado activo
    vol_cap_low: float = 0.02    # volumen/capitalización considerado bajo
    circ_max_high: float = 0.80  # proporción de oferta máxima ya circulando (alta)
    circ_max_low: float = 0.40   # proporción de oferta máxima ya circulando (baja)
    fdv_cap_high: float = 1.8    # FDV/capitalización que sugiere dilución pendiente
    ath_deep: float = -75.0      # caída desde máximo histórico considerada profunda (%)
    cap_fees_low: float = 30.0   # capitalización / comisiones anualizadas considerada moderada (≤)
    cap_fees_high: float = 200.0 # capitalización / comisiones anualizadas considerada exigente (>)
    tvl_drop_7d: float = -20.0   # caída del TVL en 7 días considerada relevante (%)


THRESHOLDS = Thresholds()


def evaluate(ev, th=THRESHOLDS):
    """Devuelve lista de Finding a partir del dict de Evidence. Si falta un dato, la regla no se aplica."""
    def v(k):
        return ev[k].value if k in ev else None

    out = []

    vc = v("vol_cap")
    if vc is not None and vc >= th.vol_cap_high:
        out.append(Finding(
            "liquidez", "a_favor",
            f"El volumen de 24 h reportado equivale al {vc:.1%} de la capitalización.",
            "Hipótesis: hay actividad de negociación suficiente como para que entrar y salir no sea trivialmente costoso.",
            "Si el volumen está concentrado en pocos exchanges, incluye wash trading o la profundidad real del libro de órdenes es baja.",
            f"Criterio MCI: volumen/capitalización ≥ {th.vol_cap_high:.0%}", ("vol_cap",)))
    elif vc is not None and vc < th.vol_cap_low:
        out.append(Finding(
            "liquidez", "cautela",
            f"El volumen de 24 h reportado equivale solo al {vc:.1%} de la capitalización.",
            "Hipótesis: la liquidez podría ser baja y el costo de entrada o salida, alto.",
            "Si el volumen real fuera de los exchanges agregados resulta mayor, o si el activo opera sobre todo en mercados OTC o institucionales.",
            f"Criterio MCI: volumen/capitalización < {th.vol_cap_low:.0%}", ("vol_cap",)))

    cm = v("circ_max")
    if cm is not None and cm >= th.circ_max_high:
        out.append(Finding(
            "oferta_dilucion", "a_favor",
            f"El {cm:.1%} de la oferta máxima ya está en circulación.",
            "Hipótesis: el riesgo de dilución por emisión futura de tokens es menor.",
            "Si existe emisión continua (inflación) no reflejada en la oferta máxima, o si los tokens circulantes están muy concentrados.",
            f"Criterio MCI: circulante/oferta máxima ≥ {th.circ_max_high:.0%}", ("circ_max",)))
    elif cm is not None and cm < th.circ_max_low:
        out.append(Finding(
            "oferta_dilucion", "cautela",
            f"Solo el {cm:.1%} de la oferta máxima está en circulación.",
            "Hipótesis: podría haber presión vendedora por desbloqueos y emisiones futuras.",
            "Si el calendario de desbloqueos verificado muestra emisiones lentas o bloqueadas a largo plazo.",
            f"Criterio MCI: circulante/oferta máxima < {th.circ_max_low:.0%}", ("circ_max",)))

    fc = v("fdv_cap")
    if fc is not None and fc > th.fdv_cap_high:
        out.append(Finding(
            "oferta_dilucion", "cautela",
            f"La valoración totalmente diluida es {fc:.2f} veces la capitalización actual.",
            "Hipótesis: parte relevante de la oferta aún no circula y podría diluir a los tenedores actuales.",
            "Si el calendario de emisión real es mucho más largo que el horizonte de análisis, o si el FDV usa una oferta máxima que no se emitirá.",
            f"Criterio MCI: FDV/capitalización > {th.fdv_cap_high}x", ("fdv_cap",)))

    c = v("commits")
    if c is not None and c > 0:
        out.append(Finding(
            "desarrollo", "a_favor",
            f"CoinGecko reporta {c:,} commits en GitHub en las últimas 4 semanas.",
            "Hipótesis (señal débil): el proyecto mantiene actividad de desarrollo pública.",
            "Si los commits son cambios triviales, automáticos o de repositorios secundarios, o si el desarrollo real está en repositorios no rastreados.",
            "Criterio MCI: commits > 0", ("commits",)))
    elif c is not None:
        out.append(Finding(
            "desarrollo", "cautela",
            "CoinGecko no reporta commits en las últimas 4 semanas.",
            "Hipótesis: el desarrollo público podría estar detenido.",
            "Si el desarrollo ocurre en repositorios privados o no vinculados a CoinGecko.",
            "Criterio MCI: commits = 0", ("commits",)))


    cf, fees = v("cap_fees"), v("fees_30d")
    if cf is not None and cf <= th.cap_fees_low:
        out.append(Finding(
            "ingresos_fees", "a_favor",
            f"La capitalización equivale a {cf:,.1f} veces las comisiones anualizadas (dato de 30 días).",
            "Hipótesis: el mercado valora el activo de forma moderada frente a la actividad económica que genera.",
            "Si las comisiones son incentivadas, puntuales o de bajo margen, o si los ingresos no llegan a los tenedores del token.",
            f"Criterio MCI: capitalización/comisiones anualizadas ≤ {th.cap_fees_low:.0f}x. Compará con pares del sector.", ("cap_fees",)))
    elif cf is not None and cf > th.cap_fees_high:
        out.append(Finding(
            "ingresos_fees", "cautela",
            f"La capitalización equivale a {cf:,.0f} veces las comisiones anualizadas (dato de 30 días).",
            "Hipótesis: la valoración descuenta un crecimiento muy alto que las comisiones actuales no respaldan.",
            "Si las comisiones crecen con fuerza o el valor del activo no depende de ellas (p. ej. reserva de valor).",
            f"Criterio MCI: capitalización/comisiones anualizadas > {th.cap_fees_high:.0f}x", ("cap_fees",)))
    elif fees is not None and fees <= 0:
        out.append(Finding(
            "ingresos_fees", "cautela",
            "DefiLlama registra comisiones nulas en los últimos 30 días.",
            "Hipótesis: el uso económico del protocolo es mínimo o no está medido.",
            "Si el protocolo opera sin comisiones por diseño o DefiLlama aún no lo mide bien.",
            "Criterio MCI: comisiones 30 d ≤ 0", ("fees_30d",)))

    td = v("tvl_7d")
    if td is not None and td <= th.tvl_drop_7d:
        out.append(Finding(
            "adopcion_uso", "cautela",
            f"El TVL cayó {abs(td):.1f}% en 7 días.",
            "Hipótesis: hubo salida de capital del protocolo.",
            "Si la caída refleja solo el precio de los activos depositados y no retiros netos.",
            f"Criterio MCI: variación del TVL a 7 días ≤ {th.tvl_drop_7d:.0f}%", ("tvl_7d",)))

    au = ev["audits"].value if "audits" in ev else None
    if au is not None:
        if str(au).strip() in ("", "0", "None"):
            out.append(Finding(
                "seguridad", "cautela",
                "DefiLlama no lista auditorías para este protocolo.",
                "Hipótesis: el código podría no haber sido revisado por terceros.",
                "Si existen auditorías no catalogadas por DefiLlama (verificá en el sitio oficial).",
                "Criterio MCI: auditorías listadas = ninguna", ("audits",)))
        else:
            out.append(Finding(
                "seguridad", "a_favor",
                f"DefiLlama lista auditorías para este protocolo (nivel {au}).",
                "Hipótesis (señal débil): el código tuvo al menos una revisión externa.",
                "Si las auditorías son antiguas, de alcance limitado o hubo incidentes posteriores.",
                "Criterio MCI: auditorías listadas ≠ ninguna", ("audits",)))

    p7, p30 = v("p7"), v("p30")
    if p7 is not None and p30 is not None:
        if p7 > 0 and p30 > 0:
            txt = "Rendimiento positivo a 7 y 30 días."
        elif p7 < 0 and p30 < 0:
            txt = "Rendimiento negativo a 7 y 30 días."
        elif p7 > 0 > p30:
            txt = "Rebote de 7 días dentro de un mes negativo."
        else:
            txt = "Rendimiento mixto entre 7 y 30 días."
        out.append(Finding(
            "precio", "contexto", txt + " Es contexto de precio, no un fundamento.",
            "El movimiento de precio no demuestra que la tendencia continúe ni que exista un motivo fundamental.",
            "Cualquier giro posterior de precio; no aporta información sobre la calidad del proyecto.",
            "Criterio MCI: signo de variaciones a 7 y 30 días", ("p7", "p30")))

    ac = v("ath_change")
    if ac is not None and ac <= th.ath_deep:
        out.append(Finding(
            "precio", "contexto",
            f"El precio está {abs(ac):.1f}% por debajo de su máximo histórico.",
            "Puede reflejar recuperación potencial o deterioro estructural; el dato por sí solo no distingue entre ambos.",
            "Un análisis de fundamentos y de la causa de la caída.",
            f"Criterio MCI: distancia al máximo ≤ {th.ath_deep:.0f}%", ("ath_change",)))
    return out
