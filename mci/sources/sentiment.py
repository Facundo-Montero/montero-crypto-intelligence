"""Índice de Miedo y Codicia (alternative.me). Es un indicador de sentimiento de mercado, no un fundamento."""
from datetime import datetime, timezone

from mci.sources.base import SourceError, get_json

URL = "https://api.alternative.me/fng/"
SOURCE_NAME = "alternative.me · Fear & Greed Index"
LABELS_ES = {"extreme fear": "Miedo extremo", "fear": "Miedo", "neutral": "Neutral",
             "greed": "Codicia", "extreme greed": "Codicia extrema"}


def fetch_fear_greed(limit=30):
    data = get_json(URL, {"limit": limit}, source="alternative.me")
    items = data.get("data") if isinstance(data, dict) else None
    out = []
    for it in items or []:
        try:
            out.append({"value": int(it["value"]), "label": str(it.get("value_classification", "")), "ts": int(it["timestamp"])})
        except (KeyError, TypeError, ValueError):
            continue
    if not out:
        raise SourceError("alternative.me no devolvió datos válidos.")
    return out, datetime.now(timezone.utc)
