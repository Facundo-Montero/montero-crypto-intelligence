# MONTERO CRYPTO INTELLIGENCE (MCI) v1.0

Plataforma de investigación cripto basada en evidencia. No da señales de compra: muestra qué dicen los datos, qué falta y qué invalidaría una tesis.

## Pantallas
- **Mercado:** capitalización total, dominancia de BTC, mapa de calor, sentimiento y mayores movimientos.
- **Radar:** filtros, orden y tabla con mini-gráfico. Tocá una fila para abrir el dossier.
- **Activo:** conclusión calculada, gráfico de precio, cobertura de evidencia, números clave, TVL y comisiones, hipótesis con "qué las invalidaría", enlaces para verificar, descarga del resumen.
- **Comparar:** 2 a 4 activos lado a lado.
- **Guía:** cómo leer MCI, criterios y estado de las fuentes.

## Fuentes (todas gratuitas, sin clave obligatoria)
CoinGecko (mercado, historial, ficha) · DefiLlama (TVL, comisiones, ingresos, auditorías listadas) · alternative.me (miedo y codicia).
No incluye desbloqueos de tokens (dato de pago).

## Reglas
Sin trading, sin wallets. No es asesoramiento financiero. Si falta evidencia esencial la conclusión es NO CONCLUYENTE.

## Publicar
Streamlit Community Cloud · repo `Facundo-Montero/montero-crypto-intelligence` · rama `main` · archivo `app.py`.
Clave opcional de CoinGecko (plan Demo): **Settings → Secrets** → `COINGECKO_API_KEY = "tu_clave"`.

## Estructura
```
app.py                      # navegación y contexto
mci/sources/                # una fuente = un módulo
mci/analysis/               # classify, evidence, rules (umbrales), verdict, report
mci/views/                  # una pantalla = un módulo
mci/ui/                     # tema, componentes y gráficos
tests/                      # pytest (sin red: fuentes simuladas)
```

## Pruebas (opcional)
`pip install -r requirements-dev.txt` y luego `pytest`.
