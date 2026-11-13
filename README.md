# MONTERO CRYPTO INTELLIGENCE (MCI)

Dashboard web de investigación cripto construido con Streamlit. Su objetivo es ayudar a investigar activos con datos visibles, limitaciones explícitas y una separación clara entre hechos, estimaciones e hipótesis.

## Funcionalidades de esta primera versión

- Explorador de mercado con filtros por clasificación y búsqueda.
- Datos de precio, capitalización, volumen y variaciones de 24 h / 7 d.
- Dossier individual con métricas de oferta y FDV cuando están disponibles.
- Exclusión predeterminada de stablecoins y activos wrapped/sintéticos del radar de crecimiento.
- Avisos explícitos cuando la evidencia fundamental no alcanza para una conclusión.
- Interfaz oscura adaptable a escritorio y móvil.

## Fuente y límites

Los datos de mercado se consultan desde la API pública de CoinGecko y se almacenan en caché durante cinco minutos. La disponibilidad, cobertura y límites dependen del proveedor. Esta versión todavía no verifica directamente TVL, fees, ingresos, actividad de usuarios, auditorías ni calendarios de desbloqueo; por eso no emite señales de compra.

## Publicar gratis en Streamlit Community Cloud

1. Entrá en https://share.streamlit.io/ e iniciá sesión con GitHub.
2. Elegí **Create app**.
3. Seleccioná el repositorio `Facundo-Montero/montero-crypto-intelligence`.
4. Branch: `main`.
5. Main file path: `app.py`.
6. Elegí **Deploy**.

Streamlit instalará las dependencias desde `requirements.txt`. No hacen falta claves API para esta versión.

## Desarrollo local (opcional)

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Metodología y advertencias

- El orden por capitalización no representa potencial de rentabilidad.
- Volumen, liquidez y momentum no equivalen a fundamentos.
- La clasificación del activo es heurística y puede contener errores.
- La ausencia de un dato no significa que el riesgo no exista.
- MCI no conecta wallets, no ejecuta operaciones y no garantiza rendimientos.
- La plataforma es informativa y no constituye asesoramiento financiero.

**Regla central:** si faltan datos esenciales para sostener una tesis, la conclusión debe ser **NO CONCLUYENTE**, no una recomendación de compra.
