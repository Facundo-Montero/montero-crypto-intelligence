"""Dimensiones de evidencia y veredicto calculado. El veredicto mide CALIDAD DE EVIDENCIA, no atractivo."""
from mci.analysis.classify import NON_GROWTH
from mci.models import Dimension, Verdict

# clave, etiqueta corta, ¿esencial?, texto si no hay dato
DIMENSIONS = [
    ("liquidez", "Liquidez", False, "CoinGecko no informó volumen o capitalización."),
    ("oferta_dilucion", "Oferta y dilución", True, "CoinGecko no informó oferta máxima ni FDV."),
    ("desarrollo", "Desarrollo", False, "CoinGecko no reportó actividad en GitHub."),
    ("adopcion_uso", "Adopción y uso", True, "DefiLlama no tiene TVL para este activo."),
    ("ingresos_fees", "Ingresos", True, "DefiLlama no tiene comisiones ni ingresos para este activo."),
    ("seguridad", "Seguridad", True, "Sin datos de auditorías para este activo."),
    ("gobernanza_competencia", "Gobernanza y competencia", False, "Todavía no hay fuente integrada en MCI."),
]

_PARTIAL_IF_ANY = {
    "liquidez": ("vol_cap",),
    "oferta_dilucion": ("circ_max", "fdv_cap"),
    "desarrollo": ("commits",),
    "adopcion_uso": ("tvl",),
    "ingresos_fees": ("fees_30d", "rev_30d"),
    "seguridad": ("audits", "audit_links"),
}
_PARTIAL_TEXT = {
    "liquidez": "Solo volumen agregado reportado; falta profundidad real de mercado.",
    "oferta_dilucion": "Hay oferta y FDV; falta el calendario de desbloqueos (fuente de pago).",
    "desarrollo": "Solo conteo de commits; no mide calidad.",
    "adopcion_uso": "Hay TVL; faltan usuarios activos y retención.",
    "ingresos_fees": "Hay comisiones agregadas; no se verifica si son orgánicas.",
    "seguridad": "Hay auditorías listadas; no se revisó su alcance ni vigencia.",
}


def assess_dimensions(ev, extra_status=None):
    """extra_status: {clave: ('cubierta'|'parcial', detalle)} para fuentes futuras o pruebas."""
    extra_status = extra_status or {}
    out = []
    for key, label, essential, missing_text in DIMENSIONS:
        if key in extra_status:
            status, detail = extra_status[key]
        elif any(k in ev for k in _PARTIAL_IF_ANY.get(key, ())):
            status, detail = "parcial", _PARTIAL_TEXT[key]
        else:
            status, detail = "sin_datos", missing_text
        out.append(Dimension(key, label, essential, status, detail))
    return out


def build_verdict(classification, dimensions):
    total = len(dimensions)
    covered = sum(1 for d in dimensions if d.status != "sin_datos")
    if classification in NON_GROWTH:
        return Verdict("fuera_de_alcance", "FUERA DE ALCANCE",
                       (f"Clasificado como «{classification}»: su valor depende de un respaldo o activo subyacente, "
                        "no de fundamentos propios.",), covered, total)
    missing = tuple(d.label for d in dimensions if d.essential and d.status == "sin_datos")
    partial = tuple(d.label for d in dimensions if d.essential and d.status == "parcial")
    if missing:
        return Verdict("no_concluyente", "NO CONCLUYENTE",
                       (f"Falta evidencia esencial: {', '.join(missing)}.",), covered, total)
    if partial:
        return Verdict("parcial", "EVIDENCIA PARCIAL",
                       (f"Solo tesis preliminar. Evidencia esencial parcial: {', '.join(partial)}.",), covered, total)
    return Verdict("suficiente", "EVIDENCIA SUFICIENTE",
                   ("Todas las dimensiones esenciales tienen cobertura. Sigue sin ser una recomendación.",), covered, total)
