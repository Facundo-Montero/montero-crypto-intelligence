"""Utilidades HTTP compartidas por todas las fuentes."""
import requests


class SourceError(Exception):
    """Error legible al consultar una fuente externa."""


def get_json(url, params=None, headers=None, source="la fuente", timeout=25):
    try:
        r = requests.get(url, params=params or {}, headers=headers or {}, timeout=timeout)
    except requests.RequestException as exc:
        raise SourceError(f"No se pudo conectar con {source} ({exc.__class__.__name__}).") from exc
    if r.status_code == 429:
        raise SourceError(f"{source} limitó temporalmente las consultas. Esperá un minuto y reintentá.")
    if r.status_code >= 400:
        raise SourceError(f"{source} respondió con error HTTP {r.status_code}.")
    try:
        return r.json()
    except ValueError as exc:
        raise SourceError(f"{source} devolvió una respuesta que no es JSON válido.") from exc
