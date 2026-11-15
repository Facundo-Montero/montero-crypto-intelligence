"""Modelos de datos de MCI: separan hechos, estimaciones e hipótesis y guardan su procedencia."""
from dataclasses import dataclass
from datetime import datetime

HECHO = "hecho"            # dato reportado por una fuente identificada
ESTIMACION = "estimación"  # cálculo de MCI sobre hechos (fórmula visible)
HIPOTESIS = "hipótesis"    # interpretación posible; no se presenta como hecho


@dataclass(frozen=True)
class Evidence:
    key: str
    label: str
    value: object          # valor crudo (None = sin dato)
    display: str           # valor formateado para mostrar
    kind: str              # HECHO | ESTIMACION
    source: str
    url: str
    fetched_at: datetime   # momento real de la consulta
    note: str = ""


@dataclass(frozen=True)
class Finding:
    dimension: str
    polarity: str          # "a_favor" | "cautela" | "contexto"
    observation: str       # hecho o estimación que se observa
    implication: str       # hipótesis que se desprende (no es un hecho)
    invalidation: str      # qué la invalidaría
    rule: str              # criterio/umbral de MCI usado (visible y editable)
    basis: tuple = ()      # claves de Evidence en las que se apoya


@dataclass(frozen=True)
class Dimension:
    key: str
    label: str
    essential: bool        # ¿es imprescindible para sostener una tesis?
    status: str            # "cubierta" | "parcial" | "sin_datos"
    detail: str


@dataclass(frozen=True)
class Verdict:
    level: str             # "no_concluyente" | "parcial" | "suficiente" | "fuera_de_alcance"
    label: str
    reasons: tuple
    covered: int           # dimensiones con algún dato
    total: int
