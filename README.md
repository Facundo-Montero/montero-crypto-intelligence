# MONTERO CRYPTO INTELLIGENCE (MCI)

Plataforma de investigación cripto basada en evidencia, hecha con Streamlit. No emite señales de compra: explica qué dicen los datos, qué falta y qué invalidaría una tesis.

## Qué hace la versión 0.3
- **Radar** con moneda (USD/ARS/EUR), volumen mínimo y exclusión de stablecoins y wrapped/derivados.
- **Dossier por activo** con evidencia rotulada como *hecho*, *estimación* o *hipótesis*, cada una con fuente, enlace y fecha de consulta.
- **Veredicto calculado**: mide la calidad de la evidencia, no el atractivo. Si falta evidencia esencial, el resultado es **NO CONCLUYENTE**.
- Cada indicio trae el criterio usado y **qué lo invalidaría**.
- El precio y el momentum se muestran como contexto, nunca como fundamento.

## Reglas
Sin trading automático, sin wallets, sin claves privadas. No es asesoramiento financiero.

## Publicar en Streamlit Community Cloud
Repositorio `Facundo-Montero/montero-crypto-intelligence`, rama `main`, archivo principal `app.py`. Streamlit Cloud redespliega solo cuando hacés push.

Clave opcional de CoinGecko (plan Demo gratuito): en la app, **Settings → Secrets**:
```toml
COINGECKO_API_KEY = "tu_clave"
```

## Estructura
```
app.py                     # interfaz
mci/models.py              # Evidence, Finding, Dimension, Verdict
mci/sources/coingecko.py   # una fuente = un módulo
mci/analysis/              # classify, evidence, rules (umbrales), verdict
tests/                     # pytest
```

## Pruebas (opcional)
```bash
pip install -r requirements-dev.txt
pytest
```

## Próximas etapas
3. Fundamentos con DefiLlama (TVL, fees, ingresos). 4. Tokenomics, desbloqueos y seguridad. 5. Comparables por sector. 6. Historial de tesis.
