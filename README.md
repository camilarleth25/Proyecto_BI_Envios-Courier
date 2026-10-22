<p align="center"><img src="logos/logo_uce_ultima_milla.png" alt="Universidad Central del Ecuador · Control de Última Milla" width="720"></p>

# Inteligencia de Negocios · Logística de Última Milla de una Empresa Courier

**Caso 7 · Indicadores de nivel de servicio en logística de última milla**
Componente: Inteligencia de Negocios · Subcomponente: Analítica de Operaciones

Solución de BI que transforma los registros de envíos de una empresa de courier en un **modelo dimensional (esquema estrella)** y en una **app interactiva** con indicadores de nivel de servicio, puntualidad y desempeño por zona y transportista.

## 🔗 Prototipo en línea

**[Abrir el prototipo](https://TU-USUARIO.github.io/control-ultima-milla/)** · tablero operativo con filtros, matriz zona × transportista, simulador de reasignación y modelo de datos. Debajo de cada gráfico hay un recuadro **"¿Qué nos dice este gráfico?"** con una interpretación en lenguaje sencillo que se vuelve a escribir sola cada vez que cambias un filtro o un escenario.

El prototipo es un solo archivo (`index.html`): no necesita instalar nada, se abre en cualquier navegador, incluso sin internet.

## Resultados principales

| Indicador | Resultado |
|---|---|
| Entregas a tiempo (OTD) | 74,5 % |
| Zona con peor puntualidad | Rural (19,4 %) |
| Transportista con peor puntualidad | TR07 (45,2 %) |
| Día con mayor retraso | Lunes (62,8 % de OTD) |
| Sobrecosto por intentos y devoluciones | USD 15 089 (9,3 % del costo) |
| OTD esperado con la reasignación propuesta | 77,1 % (óptimo matemático: 79,2 %) |

## Contenido del repositorio

| Archivo o carpeta | Qué contiene |
|---|---|
| `index.html` | **Prototipo final** (tablero, matriz, simulador y modelo, con interpretaciones automáticas) |
| `logos/` | Logo del prototipo (SVG animado, SVG estático y PNG), versión sobre verde, ícono, sello de la UCE en blanco y logo combinado |
| `app.py` | Versión opcional del prototipo en Streamlit (lee el modelo estrella) |
| `requirements.txt` | Librerías que necesita la app |
| `.streamlit/config.toml` | Tema de colores de la app |
| `01_exploratorio.ipynb` | Análisis exploratorio y calidad de datos |
| `02_etl.ipynb` | ETL: dimensiones, tabla de hechos, medidas y carga |
| `03_kpis.ipynb` | Indicadores clave y hallazgos con SQL |
| `04_reasignacion.ipynb` | Recomendación de reasignación (reglas y programación lineal) |
| `datos/envios_courier.csv` | Datos de origen: 41 952 envíos, enero a junio de 2026 |
| `bd/courier_dw.sqlite` | Modelo estrella en SQLite (generado por `02_etl`) |
| `salida/powerbi/` | Las 5 tablas del modelo estrella en CSV para Power BI |

## Modelo estrella

- **Hechos:** `fact_envios` (un envío por fila): días de tránsito, retraso frente a la promesa, marca de entrega a tiempo, costo, intentos y sobrecosto.
- **Dimensiones:** `dim_tiempo` (con día de la semana; dimensión de rol), `dim_zona`, `dim_transportista`, `dim_servicio`.

## Cómo abrirlo en tu computadora

- **Prototipo:** doble clic en `index.html`.
- **Versión Streamlit (opcional):**

```bash
pip install -r requirements.txt jupyterlab
streamlit run app.py
```

Para reconstruir el modelo desde los datos de origen, ejecuta los notebooks en orden: `01` → `02` → `03` → `04`.

## Herramientas

Python (pandas, SQLite, SciPy, Plotly, Streamlit) · Jupyter · SQL · Power BI

---
Autor: [Nombre del estudiante] · Universidad Central del Ecuador · 2026
