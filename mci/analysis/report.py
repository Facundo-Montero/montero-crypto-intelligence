"""Exportación del dossier: resumen en Markdown y evidencias en CSV."""
import csv
import io

from mci.formatting import fmt_dt

_STATUS = {"cubierta": "cubierta", "parcial": "parcial", "sin_datos": "sin datos"}
_POL = {"a_favor": "Indicios a favor (hipótesis)", "cautela": "Riesgos y cautelas", "contexto": "Contexto"}


def evidence_csv(ev):
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Dato", "Valor", "Tipo", "Fuente", "Consultado (UTC)", "Nota", "Enlace"])
    for e in ev.values():
        w.writerow([e.label, e.display, e.kind, e.source, fmt_dt(e.fetched_at), e.note, e.url])
    return buf.getvalue()


def dossier_markdown(name, symbol, classification, verdict, dims, findings, ev):
    L = [f"# Dossier MCI — {name} ({symbol.upper()})", "",
         f"**Conclusión: {verdict.label}** — {' '.join(verdict.reasons)}",
         f"Cobertura de evidencia: {verdict.covered}/{verdict.total}. No es una probabilidad de rentabilidad ni una recomendación.",
         f"Clasificación heurística: {classification}", "", "## Cobertura por dimensión"]
    L += [f"- {d.label}: {_STATUS[d.status]} — {d.detail}" for d in dims]
    for pol in ("a_favor", "cautela", "contexto"):
        items = [f for f in findings if f.polarity == pol]
        if items:
            L += ["", f"## {_POL[pol]}"]
            for f in items:
                L += [f"- **{f.observation}** {f.implication} _Se invalidaría si: {f.invalidation}_ ({f.rule})"]
    L += ["", "## Evidencias y fuentes", "| Dato | Valor | Tipo | Fuente | Consultado |", "|---|---|---|---|---|"]
    L += [f"| {e.label} | {e.display} | {e.kind} | {e.source} | {fmt_dt(e.fetched_at)} |" for e in ev.values()]
    L += ["", "_MCI es una herramienta de investigación. No es asesoramiento financiero._"]
    return "\n".join(L)
