"""
Control de Última Milla · Prototipo de la solución de BI (Caso 7)
==================================================================
App en Streamlit que lee el modelo estrella generado por 02_etl.ipynb
y muestra:
  1. Tablero operativo con filtros
  2. Matriz zona × transportista
  3. Simulador de reasignación
  4. Modelo de datos

Ejecutar en local:   streamlit run app.py
"""
import sqlite3
from html import escape
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from scipy.optimize import linprog

st.set_page_config(page_title="Control de Última Milla", page_icon="🚚", layout="wide")

# ───────────────────────────── Diseño (colores, tipografía, tarjetas) ─────────────────────────────
# Paleta inspirada en los colores institucionales de la UCE: azul cobalto y rojo escarlata
TINTA, MUTED, LINEA, FONDO = "#13233A", "#5B6878", "#D3DAE4", "#F1F4F8"
AZUL, ROJO, GRIS, NARANJA = "#0B3D7A", "#C8102E", "#C5CEDA", "#5B8FD0"
AZUL_OSC = "#082C5A"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700&family=Barlow:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');
html, body, [class*="css"], .stApp, .stMarkdown, p, label, li {{ font-family: 'Barlow', 'Segoe UI', sans-serif; }}
.stApp {{ background: {FONDO}; color: {TINTA}; }}
header[data-testid="stHeader"] {{ background: transparent; }}
.block-container {{ padding-top: 1.6rem; max-width: 1280px; }}
h1, h2, h3 {{ font-family: 'Barlow Condensed', 'Arial Narrow', sans-serif !important; color: {TINTA}; letter-spacing: .01em; }}
/* Encabezado tipo etiqueta de envío */
.top {{ display:flex; flex-wrap:wrap; gap:12px 24px; justify-content:space-between; align-items:flex-end;
        background:linear-gradient(120deg, {AZUL_OSC} 0%, {AZUL} 60%, #14529C 100%); border-bottom:5px solid {ROJO};
        border-radius:12px; padding:20px 24px; margin-bottom:8px; }}
.top h1 {{ font-size:36px; font-weight:700; margin:0; padding:0; line-height:1.05; color:#FFFFFF !important; }}
.top p {{ margin:4px 0 0; color:#C9D8EE; font-size:15px; }}
.etiqueta {{ font-family:'IBM Plex Mono', monospace; font-size:12px; color:#C9D8EE; border:1px dashed rgba(255,255,255,.45);
             border-radius:6px; padding:6px 10px; display:grid; grid-template-columns:auto auto; gap:2px 14px; }}
.etiqueta b {{ color:#FFFFFF; font-weight:500; }}
/* Pestañas */
.stTabs [data-baseweb="tab-list"] {{ gap: 4px; border-bottom:1px solid {LINEA}; }}
.stTabs [data-baseweb="tab"] {{ font-family:'Barlow Condensed', sans-serif; font-size:19px; font-weight:600; color:{MUTED}; padding:8px 14px; }}
.stTabs [aria-selected="true"] {{ color:{AZUL} !important; }}
.stTabs [data-baseweb="tab-highlight"] {{ background:{ROJO}; height:3px; }}
.stTabs [data-baseweb="tab"] p {{ font-family:'Barlow Condensed', sans-serif; font-size:19px; font-weight:600; }}
/* Etiquetas de los filtros */
[data-testid="stWidgetLabel"] p {{ font-size:12px; text-transform:uppercase; letter-spacing:.06em; font-weight:600; color:{MUTED}; }}
/* Frase resumen */
.lead {{ font-size:17px; margin:6px 0 14px; color:{TINTA}; }}
.lead b {{ font-weight:600; }}
/* Tarjetas KPI */
.kpis {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(170px, 1fr)); gap:10px; margin-bottom:14px; }}
.kpi {{ background:#fff; border:1px solid {LINEA}; border-top:3px solid {AZUL}; border-radius:10px; padding:12px 14px; display:flex; flex-direction:column; gap:2px; }}
.kpi .k {{ font-size:11.5px; text-transform:uppercase; letter-spacing:.06em; color:{MUTED}; font-weight:600; }}
.kpi .v {{ font-family:'Barlow Condensed', sans-serif; white-space:nowrap; font-size:clamp(26px, 2.5vw, 34px); font-weight:600; line-height:1.05; font-variant-numeric:tabular-nums; color:{TINTA}; }}
.kpi .s {{ font-size:12.5px; color:{MUTED}; }}
.kpi.alerta {{ border-color:#EBA6B1; }} .kpi.alerta .v {{ color:{ROJO}; }}
.kpi.grande .v {{ font-size:54px; font-weight:700; }}
.sube {{ color:#2B8A51; font-weight:600; }} .baja {{ color:{ROJO}; font-weight:600; }}
/* Tarjetas de lectura */
.lectura {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(240px, 1fr)); gap:10px; margin-top:6px; }}
.lectura div {{ background:#fff; border:1px solid {LINEA}; border-radius:8px; padding:10px 12px; font-size:14px; }}
.lectura b {{ font-family:'Barlow Condensed', sans-serif; font-size:18px; display:block; margin-bottom:2px; }}
/* Contenedores con borde = tarjetas blancas */
[data-testid="stVerticalBlockBorderWrapper"], [class*="st-key-card_"] {{ background:#fff; border-color:{LINEA} !important; border-radius:10px; }}
[class*="st-key-card_"] h3, [data-testid="stVerticalBlockBorderWrapper"] h3 {{ font-size:22px !important; font-weight:600; padding:0 0 2px !important; margin:0 !important; }}
.interp {{ background:#EEF3FA; border-left:4px solid {AZUL}; border-radius:6px; padding:10px 14px; margin:2px 0 6px;
           font-size:14.5px; line-height:1.5; color:{TINTA}; }}
.interp .t {{ display:block; font-size:11.5px; text-transform:uppercase; letter-spacing:.06em; font-weight:700; color:{AZUL}; margin-bottom:2px; }}
.interp b {{ font-weight:600; }}
.interp.alerta {{ background:#FBEFF1; border-left-color:{ROJO}; }} .interp.alerta .t {{ color:{ROJO}; }}
.nota {{ font-size:13px; color:{MUTED}; margin:-4px 0 4px; }}
footer {{ visibility:hidden; }}
</style>
""", unsafe_allow_html=True)


def estilo(fig, titulo=None, alto=330):
    """Aplica a cada gráfico la misma tipografía y fondo del diseño."""
    fig.update_layout(
        title=dict(text=titulo, font=dict(family="Barlow Condensed, Arial Narrow, sans-serif", size=21, color=TINTA)) if titulo else None,
        font=dict(family="Barlow, Segoe UI, sans-serif", size=13, color=TINTA),
        paper_bgcolor="white", plot_bgcolor="white", height=alto,
        margin=dict(l=10, r=10, t=50 if titulo else 10, b=10),
        hoverlabel=dict(bgcolor="white", font=dict(family="Barlow, sans-serif", size=13)))
    fig.update_xaxes(gridcolor="#E6EBEC", zerolinecolor=LINEA)
    fig.update_yaxes(gridcolor="#E6EBEC", zerolinecolor=LINEA)
    return fig


_n_tarjeta = [0]


def tarjeta():
    """Contenedor con borde y fondo blanco (la clave permite darle estilo con CSS)."""
    _n_tarjeta[0] += 1
    return st.container(border=True, key=f"card_{_n_tarjeta[0]}")


def tarjetas(items, clase_extra=""):
    """items = [(etiqueta, valor, subtítulo, alerta)] → fila de tarjetas KPI en HTML."""
    html = "".join(
        f'<div class="kpi {"alerta" if al else ""} {clase_extra}"><span class="k">{escape(k)}</span>'
        f'<span class="v">{v}</span><span class="s">{s}</span></div>'
        for k, v, s, al in items)
    st.markdown(f'<div class="kpis">{html}</div>', unsafe_allow_html=True)


def interpretacion(texto: str, alerta: bool = False):
    """Recuadro de interpretación automática que va debajo de cada gráfico."""
    st.markdown(f'<div class="interp{" alerta" if alerta else ""}"><span class="t">Interpretación</span>{texto}</div>',
                unsafe_allow_html=True)


# ───────────────────────────── Constantes ─────────────────────────────
ZONAS = ["Norte", "Centro", "Sur", "Valles", "Rural"]
DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
         "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
BASE = Path(__file__).parent
# 1º se busca la base SQLite del ETL; si no está, las carpetas con los 5 CSV del modelo estrella
RUTAS_BD = [BASE / "modelo_estrella" / "courier_dw.sqlite", BASE / "bd" / "courier_dw.sqlite",
            BASE / "courier_dw.sqlite",
            BASE / "salida" / "powerbi", BASE / "salida", BASE / "modelo_estrella"]
TABLAS = ["dim_tiempo", "dim_zona", "dim_transportista", "dim_servicio", "fact_envios"]


def existe_modelo(ruta: Path) -> bool:
    if ruta.suffix == ".sqlite":
        return ruta.is_file()
    return ruta.is_dir() and all((ruta / f"{t}.csv").is_file() for t in TABLAS)


def num(v, d=1):
    """Formato numérico con coma decimal y punto de miles (es-EC)."""
    s = f"{v:,.{d}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def pct(v, d=1):
    return f"{num(v * 100, d)} %"


# ───────────────────────────── Datos ─────────────────────────────
@st.cache_data
def cargar_datos(ruta: str) -> pd.DataFrame:
    """Une la tabla de hechos con sus dimensiones (consulta sobre el modelo estrella)."""
    if ruta.endswith(".sqlite"):
        con = sqlite3.connect(ruta)
    else:
        # Carpeta de CSV (salida/powerbi): se arma el modelo estrella en una base en memoria
        con = sqlite3.connect(":memory:")
        for t in TABLAS:
            pd.read_csv(Path(ruta) / f"{t}.csv", encoding="utf-8-sig").to_sql(t, con, index=False)
    df = pd.read_sql("""
        SELECT f.id_envio,
               d.fecha, d.num_mes, d.mes, d.semana_iso, d.num_dia_semana, d.dia_semana,
               z.zona, t.codigo_transportista AS transportista, s.tipo_servicio AS servicio,
               f.intentos_entrega, f.costo_envio, f.dias_transito, f.dias_retraso,
               f.dias_atraso, f.flag_entregado, f.flag_devuelto, f.flag_a_tiempo,
               f.sobrecosto_intentos, f.sobrecosto_devolucion
        FROM fact_envios f
        JOIN dim_tiempo d        ON d.id_tiempo = f.id_tiempo_recepcion
        JOIN dim_zona z          ON z.id_zona = f.id_zona
        JOIN dim_transportista t ON t.id_transportista = f.id_transportista
        JOIN dim_servicio s      ON s.id_servicio = f.id_servicio
    """, con)
    con.close()
    return df


ruta_bd = next((r for r in RUTAS_BD if existe_modelo(r)), None)
if ruta_bd is None:
    st.error("No se encontró el modelo estrella. Ejecuta primero **02_etl.ipynb** y sube junto a "
             "este archivo la carpeta `modelo_estrella/` (con `courier_dw.sqlite`) o la carpeta "
             "`salida/powerbi/` (con los 5 CSV).")
    st.stop()

df = cargar_datos(str(ruta_bd))
TRS = sorted(df["transportista"].unique())
SVS = sorted(df["servicio"].unique())
MESES_DATA = sorted(df["num_mes"].unique())


def resumen(d: pd.DataFrame) -> dict:
    """Indicadores clave de un conjunto de envíos."""
    ent = d["flag_entregado"].sum()
    return {
        "envios": len(d), "entregados": ent, "devueltos": d["flag_devuelto"].sum(),
        "otd": d["flag_a_tiempo"].sum() / ent if ent else 0,
        "retraso_neto": d["dias_retraso"].mean(),
        "retraso_tardios": d.loc[d["dias_retraso"] > 0, "dias_retraso"].mean(),
        "transito": d["dias_transito"].mean(),
        "devolucion": d["flag_devuelto"].mean() if len(d) else 0,
        "costo_prom": d["costo_envio"].mean(), "costo_total": d["costo_envio"].sum(),
        "intentos_extra": (d["intentos_entrega"] - 1).sum(),
        "sob_int": d["sobrecosto_intentos"].sum(), "sob_dev": d["sobrecosto_devolucion"].sum(),
    }


def otd_por(d: pd.DataFrame, col: str) -> pd.DataFrame:
    g = d.groupby(col).agg(envios=("id_envio", "size"), a_tiempo=("flag_a_tiempo", "sum"),
                           entregados=("flag_entregado", "sum"),
                           retraso=("dias_retraso", "mean"), atraso=("dias_atraso", "mean"),
                           devolucion=("flag_devuelto", "mean")).reset_index()
    g["otd"] = g["a_tiempo"] / g["entregados"]
    return g


# ───────────────────────────── Encabezado ─────────────────────────────
st.markdown(f"""
<div class="top">
  <div><h1>Control de Última Milla</h1>
  <p>Nivel de servicio, puntualidad y costo por zona y transportista · Solución de BI en Python</p></div>
  <div class="etiqueta">
    <span>CORTE</span><b>{MESES[MESES_DATA[0]-1][:3].upper()} – {MESES[MESES_DATA[-1]-1][:3].upper()} 2026</b>
    <span>ENVÍOS</span><b>{num(len(df), 0)}</b>
    <span>FUENTE</span><b>{escape(ruta_bd.relative_to(BASE).as_posix())}</b>
  </div>
</div>""", unsafe_allow_html=True)

# ───────────────────────────── Filtros (fila superior) ─────────────────────────────
FILTROS_INI = {"f_zona": "Todas", "f_tr": "Todos", "f_sv": "Todos",
               "f_desde": MESES_DATA[0], "f_hasta": MESES_DATA[-1]}
for clave, valor in FILTROS_INI.items():
    st.session_state.setdefault(clave, valor)


def quitar_filtros():
    for clave, valor in FILTROS_INI.items():
        st.session_state[clave] = valor


fc = st.columns([1.2, 1.2, 1.1, 1, 1, 0.9])
fc[0].selectbox("Zona", ["Todas"] + ZONAS, key="f_zona")
fc[1].selectbox("Transportista", ["Todos"] + TRS, key="f_tr")
fc[2].selectbox("Servicio", ["Todos"] + SVS, key="f_sv")
fc[3].selectbox("Desde", MESES_DATA, key="f_desde", format_func=lambda m: MESES[m - 1])
fc[4].selectbox("Hasta", MESES_DATA, key="f_hasta", format_func=lambda m: MESES[m - 1])
fc[5].markdown("<div style='height:1.75rem'></div>", unsafe_allow_html=True)
fc[5].button("Quitar filtros", on_click=quitar_filtros)

F_ZONA, F_TR, F_SV = st.session_state.f_zona, st.session_state.f_tr, st.session_state.f_sv
M_INI, M_FIN = sorted([st.session_state.f_desde, st.session_state.f_hasta])


def filtrar(d: pd.DataFrame, sin=()) -> pd.DataFrame:
    m = d["num_mes"].between(M_INI, M_FIN)
    if F_ZONA != "Todas" and "zona" not in sin:
        m &= d["zona"] == F_ZONA
    if F_TR != "Todos" and "tr" not in sin:
        m &= d["transportista"] == F_TR
    if F_SV != "Todos":
        m &= d["servicio"] == F_SV
    return d[m]


dff = filtrar(df)
OTD_SEMESTRE = resumen(df)["otd"]


def pp(a, b):
    """Diferencia en puntos porcentuales entre dos proporciones."""
    return num(abs(a - b) * 100)


def de_cada_100(p):
    """0,194 → '19 de cada 100'."""
    return f"{round(p * 100)} de cada 100"


def proporcion(p):
    """0,169 → '1 de cada 6'; útil para hablar en lenguaje cotidiano."""
    if 0 < p < 0.5:
        return f"1 de cada {round(1 / p)}"
    return f"{round(p * 100)} %"


def veces(r):
    if r >= 1.8:
        return "casi el doble de atraso"
    if r >= 1.5:
        return "más de una vez y media el atraso"
    return "bastante más atraso"


def texto_ranking(g: pd.DataFrame, col: str, articulo: str, sustantivo: str):
    """Interpretación del OTD por zona o por transportista (g ordenado de peor a mejor)."""
    if len(g) == 1:
        r = g.iloc[0]
        lado = "por encima" if r["otd"] >= OTD_SEMESTRE else "por debajo"
        return (f"Aquí solo estás viendo <b>{r[col]}</b>. Su puntualidad es de <b>{pct(r['otd'])}</b>, unos "
                f"{round(abs(r['otd'] - OTD_SEMESTRE) * 100)} puntos {lado} del promedio del semestre ({pct(OTD_SEMESTRE)})."), r["otd"] < 0.5
    peor, segundo, mejor = g.iloc[0], g.iloc[1], g.iloc[-1]
    if sustantivo == "zona":
        t = (f"<b>{peor[col]}</b> es la zona que más falla: solo llegan a tiempo <b>{de_cada_100(peor['otd'])}</b> envíos, "
             f"mientras que en {mejor[col]} lo hacen {round(mejor['otd'] * 100)}. ")
    else:
        t = (f"<b>{peor[col]}</b> es el transportista con más problemas: entrega a tiempo <b>{de_cada_100(peor['otd'])}</b> "
             f"envíos, cuando {mejor[col]} llega a {round(mejor['otd'] * 100)}. ")
    if segundo["otd"] - peor["otd"] >= 0.10:
        if sustantivo == "zona":
            t += (f"Está muy por detrás del resto (la siguiente, {segundo[col]}, ya llega a {pct(segundo['otd'], 0)}), "
                  "así que es por donde conviene empezar.")
        else:
            t += (f"Queda lejos de los demás ({segundo[col]}, el siguiente, ya está en {pct(segundo['otd'], 0)}), "
                  "por lo que es el primero que habría que revisar.")
    else:
        t += "Los últimos puestos están muy parejos, así que no hay un solo responsable."
    return t, peor["otd"] < 0.5


def texto_dias(gd: pd.DataFrame):
    peor = gd.loc[gd["atraso"].idxmax()]
    resto = gd[gd["dia_semana"] != peor["dia_semana"]]
    if resto.empty:
        return f"Con este filtro solo hay envíos recibidos el {peor['dia_semana'].lower()}.", False
    ratio = peor["atraso"] / resto["atraso"].mean() if resto["atraso"].mean() else 1
    if ratio >= 1.3:
        t = (f"Los envíos que llegan a bodega el <b>{peor['dia_semana'].lower()}</b> son los que más se retrasan: "
             f"acumulan {veces(ratio)} que los de otros días. ")
        if peor["dia_semana"] == "Lunes":
            t += ("Todo indica que lo que se recibe el fin de semana se junta y la operación no alcanza a despacharlo "
                  "a tiempo; reforzar el equipo los lunes ayudaría.")
        else:
            t += "Vale la pena revisar qué pasa con la capacidad de la operación ese día."
        return t, True
    return ("El atraso es parecido todos los días de la semana; ninguno se dispara por encima de los demás, "
            "así que el problema no depende del día de recepción."), False


def texto_costos(gi: pd.DataFrame, k: dict):
    c1 = gi.loc[gi["intentos_entrega"] == 1, "costo"]
    if len(gi) < 2 or c1.empty:
        return "Con este filtro no hay suficientes casos con varios intentos para comparar costos.", False
    ultimo = gi.iloc[-1]
    por_intento = (ultimo["costo"] - c1.iloc[0]) / (ultimo["intentos_entrega"] - 1)
    reintentos = gi.loc[gi["intentos_entrega"] > 1, "envios"].sum() / gi["envios"].sum()
    sob = k["sob_int"] + k["sob_dev"]
    t = (f"Cada vez que un paquete no se entrega a la primera, el envío sale unos <b>USD {num(por_intento, 2)}</b> más caro. "
         f"{proporcion(reintentos).capitalize()} envíos tuvo que volver a intentarse y, sumando las devoluciones, "
         f"eso significó <b>USD {num(sob, 0)}</b> de gasto extra: alrededor del {round(sob / k['costo_total'] * 100)} % "
         "de todo lo que costó la operación.")
    return t, sob / k["costo_total"] > 0.08


def texto_tendencia(dff: pd.DataFrame):
    w = dff.groupby("semana_iso").agg(a=("flag_a_tiempo", "sum"), e=("flag_entregado", "sum"), n=("id_envio", "size"))
    w = w[w["n"] >= 0.5 * w["n"].median()]                      # se excluyen semanas incompletas
    if len(w) < 4:
        return "Hay muy pocas semanas en el período elegido para ver una tendencia.", False
    w["otd"] = w["a"] / w["e"]
    q = max(2, len(w) // 4)
    ini, fin = w["otd"].iloc[:q].mean(), w["otd"].iloc[-q:].mean()
    if abs(fin - ini) < 0.02:
        t = (f"La puntualidad casi no ha cambiado en estas semanas: se ha movido entre {pct(w['otd'].min(), 0)} y "
             f"{pct(w['otd'].max(), 0)}, sin una mejora clara. ")
    elif fin > ini:
        t = f"La puntualidad va mejorando: pasó de alrededor de {pct(ini, 0)} al inicio a {pct(fin, 0)} en las últimas semanas. "
    else:
        t = f"La puntualidad se ha ido deteriorando: bajó de alrededor de {pct(ini, 0)} al inicio a {pct(fin, 0)} en las últimas semanas. "
    sv = dff.groupby("servicio").agg(a=("flag_a_tiempo", "sum"), e=("flag_entregado", "sum"))
    if len(sv) == 2:
        sv["otd"] = sv["a"] / sv["e"]
        if sv["otd"].max() - sv["otd"].min() < 0.02:
            t += "Estándar y Express van prácticamente juntos, así que el tipo de servicio no es lo que causa los retrasos."
        else:
            t += f"{sv['otd'].idxmax()} rinde mejor que {sv['otd'].idxmin()} en este período."
    return t, fin < ini - 0.02


tab1, tab2, tab3, tab4 = st.tabs(["Tablero operativo", "Matriz zona × transportista",
                                  "Simulador de reasignación", "Modelo de datos"])

# ═════════════════════════════ 1 · TABLERO ═════════════════════════════
with tab1:
    if dff.empty:
        st.warning("No hay envíos con estos filtros.")
    else:
        k = resumen(dff)
        gz = otd_por(dff, "zona").sort_values("otd")
        gt = otd_por(dff, "transportista").sort_values("otd")
        gd = otd_por(dff, "dia_semana").set_index("dia_semana")
        gd = gd.reindex([x for x in DIAS if x in gd.index]).reset_index()
        peor_dia = gd.loc[gd["atraso"].idxmax(), "dia_semana"]
        sob = k["sob_int"] + k["sob_dev"]
        st.markdown(
            f'<p class="lead">OTD de <b>{pct(k["otd"])}</b> en {num(k["envios"], 0)} envíos. Peor zona: '
            f'<b>{gz.iloc[0]["zona"]} ({pct(gz.iloc[0]["otd"])})</b>; peor transportista: '
            f'<b>{gt.iloc[0]["transportista"]} ({pct(gt.iloc[0]["otd"])})</b>; el <b>{peor_dia.lower()}</b> '
            f'concentra el mayor atraso. Los intentos fallidos y las devoluciones cuestan <b>USD {num(sob, 0)}</b>.</p>',
            unsafe_allow_html=True)

        tarjetas([
            ("Envíos", num(k["envios"], 0), f'{num(k["entregados"], 0)} entregados · {num(k["devueltos"], 0)} devueltos', False),
            ("Entregas a tiempo (OTD)", pct(k["otd"]), f'{num(k["entregados"] - k["otd"] * k["entregados"], 0)} entregas tardías', k["otd"] < 0.7),
            ("Retraso de tardíos", f'{num(k["retraso_tardios"], 2)} d', f'Neto {num(k["retraso_neto"], 2)} d · tránsito {num(k["transito"], 2)} d', False),
            ("Tasa de devolución", pct(k["devolucion"], 2), f'{num(k["intentos_extra"], 0)} intentos adicionales', False),
            ("Costo por envío (USD)", f'$ {num(k["costo_prom"], 2)}', f'Total USD {num(k["costo_total"], 0)}', False),
            ("Sobrecosto (USD)", f"$ {num(sob, 0)}", f'{pct(sob / k["costo_total"])} del costo · intentos USD {num(k["sob_int"], 0)}', False),
        ])

        def barras_h(g, col, titulo, nota, articulo, sustantivo):
            peor = g["otd"].min()
            fig = go.Figure(go.Bar(
                x=g["otd"], y=g[col], orientation="h",
                marker=dict(color=[ROJO if v == peor else AZUL for v in g["otd"]], cornerradius=4),
                text=[pct(v) for v in g["otd"]], textposition="outside",
                customdata=np.stack([g["envios"], g["retraso"]], axis=1),
                hovertemplate="<b>%{y}</b><br>OTD %{x:.1%}<br>Envíos %{customdata[0]:,}<br>Retraso neto %{customdata[1]:.2f} días<extra></extra>"))
            fig.update_layout(xaxis=dict(range=[0, 1.12], tickformat=".0%"),
                              yaxis=dict(categoryorder="array", categoryarray=list(g[col])[::-1]))
            with tarjeta():
                st.markdown(f"### {titulo}")
                st.markdown(f'<p class="nota">{nota}</p>', unsafe_allow_html=True)
                st.plotly_chart(estilo(fig, alto=300), config={"displayModeBar": False})
                interpretacion(*texto_ranking(g, col, articulo, sustantivo))

        a, b = st.columns(2)
        with a:
            barras_h(gz, "zona", "OTD por zona", "En rojo, la peor zona.", "la", "zona")
        with b:
            barras_h(gt, "transportista", "OTD por transportista", "En rojo, el peor transportista.", "el", "transportista")

        a, b = st.columns(2)
        with a, tarjeta():
            st.markdown("### Atraso por día de recepción")
            st.markdown('<p class="nota">Días de atraso por envío entregado; los adelantos cuentan 0.</p>', unsafe_allow_html=True)
            fig = go.Figure(go.Bar(
                x=gd["dia_semana"], y=gd["atraso"],
                marker=dict(color=[ROJO if d == peor_dia else AZUL for d in gd["dia_semana"]], cornerradius=4),
                text=[num(v, 2) for v in gd["atraso"]], textposition="outside",
                customdata=gd["otd"], hovertemplate="<b>%{x}</b><br>Atraso %{y:.2f} días<br>OTD %{customdata:.1%}<extra></extra>"))
            fig.update_layout(yaxis=dict(range=[0, gd["atraso"].max() * 1.25]))
            st.plotly_chart(estilo(fig, alto=300), config={"displayModeBar": False})
            interpretacion(*texto_dias(gd))
        with b, tarjeta():
            st.markdown("### Costo promedio según intentos")
            st.markdown('<p class="nota">USD por envío; debajo, número de envíos.</p>', unsafe_allow_html=True)
            gi = dff.groupby("intentos_entrega").agg(costo=("costo_envio", "mean"), envios=("id_envio", "size")).reset_index()
            fig = go.Figure(go.Bar(
                x=[f"{i} intento{'s' if i > 1 else ''}<br>{num(n, 0)} env." for i, n in zip(gi["intentos_entrega"], gi["envios"])],
                y=gi["costo"], marker=dict(color=AZUL, cornerradius=4),
                text=[f"$ {num(v, 2)}" for v in gi["costo"]], textposition="outside",
                hovertemplate="%{x}<br>Costo promedio USD %{y:.2f}<extra></extra>"))
            fig.update_layout(yaxis=dict(range=[0, gi["costo"].max() * 1.25]))
            st.plotly_chart(estilo(fig, alto=300), config={"displayModeBar": False})
            interpretacion(*texto_costos(gi, k))

        with tarjeta():
            st.markdown("### Tendencia semanal del OTD")
            st.markdown('<p class="nota">Por semana de recepción y tipo de servicio. Las semanas 1 y 27 están incompletas.</p>', unsafe_allow_html=True)
            gs = dff.groupby(["semana_iso", "servicio"]).agg(a=("flag_a_tiempo", "sum"), e=("flag_entregado", "sum")).reset_index()
            gs["otd"] = gs["a"] / gs["e"]
            fig = px.line(gs, x="semana_iso", y="otd", color="servicio", markers=True,
                          color_discrete_sequence=[AZUL, NARANJA],
                          labels={"semana_iso": "Semana del año", "otd": "OTD", "servicio": "Servicio"})
            fig.update_traces(line_width=2.4)
            fig.update_layout(yaxis_tickformat=".0%", legend=dict(orientation="h", y=1.1, x=0))
            st.plotly_chart(estilo(fig, alto=320), config={"displayModeBar": False})
            interpretacion(*texto_tendencia(dff))

# ═════════════════════════════ 2 · MATRIZ ═════════════════════════════
with tab2:
    st.markdown('<p class="lead">La matriz cruza cada zona con cada transportista. <b>Una columna roja</b> señala '
                'un transportista con bajo desempeño en todas partes; <b>una fila roja</b>, una zona con un '
                'problema estructural.</p>', unsafe_allow_html=True)
    dm = filtrar(df, sin=("zona", "tr"))
    with tarjeta():
        modo = st.radio("Mostrar", ["OTD %", "Participación de envíos %"], horizontal=True)
        if dm.empty:
            st.warning("No hay envíos con estos filtros.")
        else:
            g = dm.groupby(["zona", "transportista"]).agg(a=("flag_a_tiempo", "sum"), e=("flag_entregado", "sum"),
                                                          n=("id_envio", "size")).reset_index()
            orden = otd_por(dm, "zona").sort_values("otd")["zona"].tolist()
            if modo == "OTD %":
                m = (g.pivot(index="zona", columns="transportista", values="a")
                     / g.pivot(index="zona", columns="transportista", values="e")).loc[orden] * 100
                escala = [[0, "#E9A08F"], [0.3, "#F2C7B6"], [0.5, "#F6E3B4"], [0.7, "#E2EABF"], [0.8, "#CDE6CD"], [1, "#9CD3AE"]]
                fig = px.imshow(m, text_auto=".1f", color_continuous_scale=escala, zmin=0, zmax=100,
                                aspect="auto", labels=dict(color="OTD %", x="Transportista", y="Zona"))
                st.markdown("### OTD por zona y transportista (%)")
            else:
                n = g.pivot(index="zona", columns="transportista", values="n").loc[orden]
                m = n.div(n.sum(axis=1), axis=0) * 100
                fig = px.imshow(m, text_auto=".1f", color_continuous_scale=[[0, "#F1F4F8"], [1, AZUL]], zmin=0, zmax=25,
                                aspect="auto", labels=dict(color="% de la zona", x="Transportista", y="Zona"))
                st.markdown("### Participación de cada transportista en la zona (%)")
            fig.update_traces(textfont=dict(size=16, family="Barlow, sans-serif", color=TINTA), xgap=3, ygap=3)
            fig.update_xaxes(side="top", showgrid=False)
            fig.update_yaxes(showgrid=False)
            st.plotly_chart(estilo(fig, alto=400), config={"displayModeBar": False})
            tot_tr = otd_por(dm, "transportista").sort_values("otd")
            m_otd = (g.pivot(index="zona", columns="transportista", values="a")
                     / g.pivot(index="zona", columns="transportista", values="e")).loc[orden] * 100
            peor_tr, peor_z = tot_tr.iloc[0]["transportista"], orden[0]
            if modo == "OTD %":
                mejor = m_otd.stack().idxmax()
                veces_peor = int((m_otd.idxmin(axis=1) == peor_tr).sum())
                if veces_peor >= 0.6 * len(orden):
                    t = (f"La columna de <b>{peor_tr}</b> se ve roja en casi todas las zonas: el problema es del transportista, "
                         "no de las rutas que le tocan. ")
                else:
                    t = f"<b>{peor_tr}</b> es el que peor rinde en general, aunque su desempeño cambia bastante según la zona. "
                fila = m_otd.loc[peor_z]
                if fila.max() < 50:
                    t += (f"En <b>{peor_z}</b>, en cambio, fallan todos (ninguno pasa del {round(fila.max())} %), lo que apunta a "
                          "un problema de la zona misma, probablemente una promesa de entrega que no se ajusta a la distancia. ")
                else:
                    t += (f"En <b>{peor_z}</b>, la zona más baja, {fila.idxmax()} sí logra {round(fila.max())} %: "
                          "convendría darle más rutas ahí. ")
                t += f"La mejor pareja es {mejor[1]} en {mejor[0]}, con {round(m_otd.stack().max())} %."
                interpretacion(t, alerta=bool((m_otd < 50).any().any()))
            else:
                part = m
                mejor_en_z = m_otd.loc[peor_z].idxmax()
                if part.max().max() - part.min().min() < 5:
                    t = (f"Hoy cada transportista recibe más o menos la misma parte de cada zona (entre "
                         f"{round(part.min().min())} y {round(part.max().max())} %), sin importar qué tan bien trabaje. ")
                else:
                    t = "El reparto ya no es parejo: algunos transportistas concentran más envíos que otros en ciertas zonas. "
                t += (f"Por eso {peor_tr} atiende {peor_z} casi en la misma medida que {mejor_en_z}, que es quien mejor "
                      "funciona ahí. Esa es la asignación que conviene corregir.")
                interpretacion(t)


# ═════════════════════════════ 3 · SIMULADOR ═════════════════════════════
@st.cache_data
def datos_simulador(d: pd.DataFrame):
    d = d.assign(o0=(d["flag_entregado"] == 1) & (d["dias_retraso"] <= 0),
                 o1=(d["flag_entregado"] == 1) & (d["dias_retraso"] <= 1),
                 o2=(d["flag_entregado"] == 1) & (d["dias_retraso"] <= 2))
    g = d.groupby(["zona", "transportista"]).agg(n=("id_envio", "size"), e=("flag_entregado", "sum"),
                                                 o0=("o0", "sum"), o1=("o1", "sum"), o2=("o2", "sum"))
    actual = g["n"].unstack().loc[ZONAS]
    otd = {k: (g[f"o{k}"] / g["e"]).unstack().loc[ZONAS] for k in (0, 1, 2)}
    return actual, otd


actual, OTD = datos_simulador(df)
demanda, volumen = actual.sum(axis=1), actual.sum(axis=0)


def propuesta_reglas() -> pd.DataFrame:
    """Las 3 reglas de 04_reasignacion.ipynb."""
    otd = OTD[0]
    p = pd.DataFrame(0.0, index=ZONAS, columns=TRS)
    for z in ["Rural", "Valles"]:
        mejores = otd.loc[z].drop("TR07").sort_values(ascending=False).index[:4]
        p.loc[z, mejores] = demanda[z] / 4
    v07 = volumen["TR07"] * 0.5
    p.loc["Norte", "TR07"] = p.loc["Centro", "TR07"] = v07 / 2
    otros = [t for t in TRS if t != "TR07"]
    libre = (volumen.mean() + (volumen["TR07"] - v07) / 7) - p[otros].sum(axis=0)
    for z in ["Norte", "Centro", "Sur"]:
        p.loc[z, otros] = (demanda[z] - p.loc[z].sum()) * libre / libre.sum()
    return p


def propuesta_optima() -> pd.DataFrame:
    """Programación lineal: maximiza entregas a tiempo con restricciones operativas."""
    otd = OTD[0]
    Z, T = otd.shape
    cap = volumen * 1.12
    cap["TR07"] = volumen["TR07"] * 0.5
    lim = [(0, 0) if (t == "TR07" and z in ("Rural", "Valles")) else (0, 0.35 * demanda[z])
           for z in ZONAS for t in TRS]
    r = linprog(-otd.values.ravel(), A_ub=np.kron(np.ones(Z), np.eye(T)), b_ub=cap.values,
                A_eq=np.kron(np.eye(Z), np.ones(T)), b_eq=demanda.values, bounds=lim, method="highs")
    return pd.DataFrame(r.x.reshape(Z, T), index=ZONAS, columns=TRS)


def a_porcentaje(asig: pd.DataFrame) -> pd.DataFrame:
    return (asig.div(asig.sum(axis=1), axis=0) * 100).round(1)


ESCENARIOS = {
    "Asignación actual": lambda: a_porcentaje(actual),
    "Propuesta por reglas": lambda: a_porcentaje(propuesta_reglas()),
    "Óptimo matemático": lambda: a_porcentaje(propuesta_optima()),
}


def evaluar(shares: pd.DataFrame, extra_rural: int):
    w = shares.clip(lower=0).fillna(0)
    w = w.div(w.sum(axis=1).replace(0, np.nan), axis=0)
    otd_z = pd.Series({z: (w.loc[z] * OTD[extra_rural if z == "Rural" else 0].loc[z]).sum() for z in ZONAS})
    carga = (w.mul(demanda, axis=0)).sum(axis=0)
    glob = (otd_z * demanda).sum() / demanda.sum()
    return otd_z, glob, carga


with tab3:
    if "shares" not in st.session_state:
        st.session_state.shares = ESCENARIOS["Propuesta por reglas"]()
        st.session_state.escenario = "Propuesta por reglas"
        st.session_state.version = 0

    izq, der = st.columns([2.2, 1])
    with izq:
        st.markdown('<p class="lead">Reparte los envíos de cada zona entre los transportistas y mira cómo cambia la '
                    'puntualidad esperada. Se aplica el OTD histórico de cada combinación zona × transportista '
                    'al nuevo reparto (semestre completo, sin filtros).</p>', unsafe_allow_html=True)
        cols = st.columns(len(ESCENARIOS))
        for i, nombre in enumerate(ESCENARIOS):
            if cols[i].button(nombre, type="primary" if st.session_state.escenario == nombre else "secondary"):
                st.session_state.shares = ESCENARIOS[nombre]()
                st.session_state.escenario = nombre
                st.session_state.version += 1
                st.rerun()
        prom = st.radio("Promesa Estándar para la zona Rural", [3, 4, 5], horizontal=True,
                        format_func=lambda d: f"{d} días" + (" (actual)" if d == 3 else ""))

    with tarjeta():
        st.markdown("### Reparto de envíos por zona (%)")
        st.markdown('<p class="nota">Cada fila es una zona y debe sumar 100 %. Si no suma 100, se reparte en '
                    'proporción. Pon 0 para sacar a un transportista de una zona.</p>', unsafe_allow_html=True)
        editado = st.data_editor(
            st.session_state.shares, key=f"editor_{st.session_state.version}",
            column_config={t: st.column_config.NumberColumn(t, min_value=0.0, max_value=100.0, step=0.5, format="%.1f")
                           for t in TRS})
        sumas = editado.sum(axis=1)
        if (sumas.sub(100).abs() > 0.6).any():
            st.caption("⚠️ Algunas filas no suman 100 %; se reparten en proporción: "
                       + ", ".join(f"{z} {num(s)} %" for z, s in sumas.items() if abs(s - 100) > 0.6))
    if not editado.equals(st.session_state.shares):
        st.session_state.escenario = "Personalizado"

    base_z, base_g, _ = evaluar(a_porcentaje(actual), 0)
    sim_z, sim_g, carga = evaluar(editado, prom - 3)
    dif = (sim_g - base_g) * 100
    with der:
        st.markdown(f"""<div class="kpi grande" style="margin-top:6px">
          <span class="k">OTD esperado</span><span class="v">{pct(sim_g)}</span>
          <span class="s"><span class="{'sube' if dif >= 0 else 'baja'}">{'+' if dif >= 0 else '−'}{num(abs(dif))} pp</span>
          frente al actual ({pct(base_g)})</span>
          <span class="s">Escenario: {escape(st.session_state.escenario)} · promesa Rural de {prom} días</span>
        </div>""", unsafe_allow_html=True)

    a, b = st.columns(2)
    with a, tarjeta():
        st.markdown("### OTD esperado por zona")
        st.markdown('<p class="nota">Gris: asignación actual · azul: escenario simulado.</p>', unsafe_allow_html=True)
        comp = pd.DataFrame({"Zona": ZONAS * 2, "Escenario": ["Actual"] * 5 + ["Simulado"] * 5,
                             "OTD": list(base_z[ZONAS]) + list(sim_z[ZONAS])})
        fig = px.bar(comp, x="OTD", y="Zona", color="Escenario", barmode="group", orientation="h",
                     color_discrete_map={"Actual": GRIS, "Simulado": AZUL}, text_auto=".1%")
        fig.update_layout(xaxis=dict(tickformat=".0%", range=[0, 1.1]), showlegend=False,
                          yaxis=dict(categoryorder="array", categoryarray=ZONAS[::-1], title=None))
        st.plotly_chart(estilo(fig, alto=360), config={"displayModeBar": False})
        cambio_z = (sim_z - base_z)[ZONAS]
        if cambio_z.abs().max() < 0.001:
            interpretacion("Este reparto es igual al actual, así que la puntualidad no cambia. Prueba la propuesta por "
                           "reglas o el óptimo, o mueve los porcentajes, para ver qué pasaría al reasignar las rutas.")
        else:
            verbo = "subiría" if dif >= 0 else "bajaría"
            t = (f"Con este reparto, la puntualidad general {verbo} de {pct(base_g)} a <b>{pct(sim_g)}</b>. "
                 f"Donde más se nota es en <b>{cambio_z.idxmax()}</b> (+{num(cambio_z.max() * 100)} puntos)")
            if cambio_z.min() < -0.002:
                t += (f", mientras que {cambio_z.idxmin()} pierde un poco ({num(abs(cambio_z.min()) * 100)} puntos) "
                      "porque recibe parte del volumen que se mueve")
            t += ". "
            if sim_z["Rural"] < 0.3:
                t += ("Rural, sin embargo, sigue muy baja: con la misma promesa de 3 días ningún reparto la salva, "
                      "por eso vale la pena probar 5 días.")
            elif prom > 3:
                t += f"Al darle {prom} días de promesa, Rural sube a {pct(sim_z['Rural'])}."
            interpretacion(t, alerta=dif < 0)
    with b, tarjeta():
        st.markdown("### Carga por transportista")
        st.markdown('<p class="nota">Envíos del semestre; línea negra = volumen actual. Rojo: más de +12 %.</p>', unsafe_allow_html=True)
        cg = pd.DataFrame({"Transportista": TRS, "Simulado": carga[TRS].values, "Actual": volumen[TRS].values})
        cg["Cambio"] = cg["Simulado"] / cg["Actual"] - 1
        fig = go.Figure()
        fig.add_bar(y=cg["Transportista"], x=cg["Simulado"], orientation="h", name="Simulado",
                    marker=dict(color=[ROJO if c > 0.125 else AZUL for c in cg["Cambio"]], cornerradius=4),
                    text=[f"{num(s, 0)} ({'+' if c >= 0 else '−'}{num(abs(c) * 100, 0)} %)" for s, c in zip(cg["Simulado"], cg["Cambio"])],
                    textposition="outside")
        fig.add_scatter(y=cg["Transportista"], x=cg["Actual"], mode="markers", name="Volumen actual",
                        marker=dict(symbol="line-ns-open", size=22, color=TINTA, line_width=3))
        fig.update_layout(xaxis=dict(range=[0, cg[["Simulado", "Actual"]].max().max() * 1.4]), showlegend=False,
                          yaxis=dict(categoryorder="array", categoryarray=TRS[::-1]))
        st.plotly_chart(estilo(fig, alto=360), config={"displayModeBar": False})
        sobre = cg[cg["Cambio"] > 0.125]
        reducidos = cg[cg["Cambio"] < -0.25]
        if sobre.empty:
            t = ("Ningún transportista quedaría con una carga excesiva (todos crecen menos de un 12 %), "
                 "así que el cambio es viable. ")
        else:
            nombres = ", ".join(sobre["Transportista"])
            t = (f"Ojo: {nombres} tendría{'n' if len(sobre) > 1 else ''} que asumir más de un 12 % de carga extra, "
                 "y con ese volumen podrían empezar a retrasarse. ")
        if not reducidos.empty:
            nombres = " y ".join(reducidos["Transportista"])
            t += f"{nombres} recibiría{'n' if len(reducidos) > 1 else ''} menos envíos que hoy, y ese volumen pasa a quienes rinden mejor."
        interpretacion(t, alerta=not sobre.empty)
    st.markdown('<p class="nota">Supuesto: cada transportista mantiene su desempeño por zona al cambiar su volumen.</p>',
                unsafe_allow_html=True)

# ═════════════════════════════ 4 · MODELO ═════════════════════════════
with tab4:
    st.markdown('<p class="lead">Toda la app se alimenta de un único <b>modelo estrella</b> generado por el ETL. '
                'Grano: un envío por fila. <code>dim_tiempo</code> es una dimensión de rol (recepción, promesa y entrega).</p>',
                unsafe_allow_html=True)
    with tarjeta():
        st.markdown("### Esquema estrella")
        st.graphviz_chart("""
        digraph {
          rankdir=LR; bgcolor="white"; node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=11, color="#C5CEDA"];
          edge [color="#5A6A6F", fontname="Helvetica", fontsize=10];
          dim_tiempo [label="dim_tiempo\\n187 días\\nfecha, mes, semana,\\ndía de la semana", fillcolor="#F5F7F6"];
          dim_zona [label="dim_zona\\n5 zonas", fillcolor="#F5F7F6"];
          fact [label="fact_envios\\n41 952 envíos\\ntránsito, retraso, marca a tiempo,\\ncosto, intentos, sobrecosto", fillcolor="#DCE6F4", color="#0B3D7A", penwidth=2];
          dim_tr [label="dim_transportista\\n8 transportistas", fillcolor="#F5F7F6"];
          dim_sv [label="dim_servicio\\nEstándar / Express", fillcolor="#F5F7F6"];
          dim_tiempo -> fact [label="1:N", dir=none]; dim_zona -> fact [label="1:N", dir=none];
          fact -> dim_tr [label="N:1", dir=none]; fact -> dim_sv [label="N:1", dir=none];
        }""")
    a, b = st.columns(2)
    with a, tarjeta():
        st.markdown("### Definición de los indicadores")
        st.table(pd.DataFrame({
            "Indicador": ["OTD", "Retraso neto", "Retraso de tardíos", "Atraso por envío", "Tasa de devolución", "Sobrecosto"],
            "Cálculo": ["Σ flag_a_tiempo ÷ Σ flag_entregado", "promedio(entrega − promesa)",
                        "promedio(entrega − promesa) si > 0", "promedio(máx(retraso, 0))",
                        "Σ flag_devuelto ÷ envíos", "intentos extra × ≈USD 1,50 + devoluciones × ≈USD 2,00"],
        }).set_index("Indicador"))
    with b, tarjeta():
        st.markdown("### Flujo de la solución")
        st.markdown("1. `01_exploratorio.ipynb` · calidad de datos  \n"
                    "2. `02_etl.ipynb` · modelo estrella  \n"
                    "3. `03_kpis.ipynb` · indicadores y hallazgos en SQL  \n"
                    "4. `04_reasignacion.ipynb` · simulación y programación lineal  \n"
                    "5. `app.py` · esta app en Streamlit")
