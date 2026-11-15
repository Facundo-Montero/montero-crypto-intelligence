"""Dimensiones de evidencia y veredicto calculado. El veredicto mide CALIDAD DE EVIDENCIA, no atractivo."""
from mci.analysis.classify import NON_GROWTH
from mci.models import Dimension, Verdict

# clave, etiqueta, ¿esencial?, texto si la fuente aún no está integrada
DIMENSIONS = [
    ("liquidez", "Liquidez y actividad de mercado", False, "CoinGecko no informó volumen o capitalización."),
    ("oferta_dilucion", "Oferta y dilución (cuantitativo)", True, "CoinGecko no informó oferta máxima ni FDV."),
    ("desarrollo", "Actividad de desarrollo", False, "CoinGecko no reportó actividad en GitHub."),
    ("adopcion_uso", "Adopción y uso real (usuarios, TVL, retención)", True, "Fuente todavía no integrada en MCI (etapa 3)."),
    ("ingresos_fees", "Ingresos y comisiones del protocolo", True, "Fuente todavía no integrada en MCI (etapa 3)."),
    ("seguridad", "Seguridad y auditorías", True, "Fuente todavía no integrada en MCI (etapa 4)."),
    ("tokenomics_unlocks", "Calendario de desbloqueos y distribución de holders", True, "Fuente todavía no integrada en MCI (etapa 4)."),
    ("gobernanza_competencia", "Gobernanza, competencia y riesgo regulatorio", False, "Fuente todavía no integrada en MCI (etapa 5)."),
]

# Qué evidencias alimentan cada dimensión con las fuentes ya integradas (CoinGecko).
_PARTIAL_IF_ANY = {
    "liquidez": ("vol_cap",),
    "oferta_dilucion": ("circ_max", "fdv_cap"),
    "desarrollo": ("commits",),
}
_PARTIAL_TEXT = {
    "liquidez": "Solo volumen reportado agregado; falta profundidad real de mercado.",
    "oferta_dilucion": "Solo oferta y FDV; falta calendario de emisión y desbloqueos.",
    "desarrollo": "Solo conteo de commits; no evalúa calidad ni alcance.",
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
        return Verdict("fuera_de_alcance", "FUERA DE ALCANCE — no aplica tesis de crecimiento",
                       (f"El activo se clasificó como «{classification}». Su valor depende de un activo subyacente "
                        "o de un respaldo, no de fundamentos propios de un protocolo.",), covered, total)
    missing = tuple(d.label for d in dimensions if d.essential and d.status == "sin_datos")
    partial = tuple(d.label for d in dimensions if d.essential and d.status == "parcial")
    if missing:
        return Verdict("no_concluyente", "NO CONCLUYENTE", tuple(f"Falta evidencia esencial: {m}." for m in missing),
                       covered, total)
    if partial:
        return Verdict("parcial", "EVIDENCIA PARCIAL — solo tesis preliminar",
                       tuple(f"Evidencia esencial solo parcial: {p}." for p in partial), covered, total)
    return Verdict("suficiente", "EVIDENCIA SUFICIENTE PARA UNA TESIS FUNDAMENTADA (no es una recomendación)",
                   ("Todas las dimensiones esenciales tienen cobertura. Contrastá igualmente las fuentes.",), covered, total)
