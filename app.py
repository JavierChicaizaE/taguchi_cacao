"""
app.py
======
Interfaz de usuario para el aplicativo independiente de Diseño Robusto de Taguchi.
Aplica el análisis de arreglos ortogonales, S/N, ANOVA y optimización univariante y multirespuesta.
"""

import io
import os
import logging
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio

st.set_page_config(
    page_title="Taguchi - Tostado de Cacao Nacional",
    layout="wide"
)

# Silenciar logs recurrentes de health check (/_stcore/health) en consola
logging.getLogger("streamlit").setLevel(logging.WARNING)

from taguchi_core import (
    full_factorial, orthogonal_array, orthogonal_array_L4, cross_arrays, signal_to_noise,
    response_table, pareto_anova, predict_optimal_sn, mrsn_index
)
from response_model import simulate_responses, FACTOR_RANGES

# Definición del target nominal-es-mejor (NB) para Pardeamiento
try:
    center_test = pd.DataFrame({"Temperatura": [0.0], "Tiempo": [0.0], "Humedad": [0.0]})
    center_out = simulate_responses(center_test, seed=42)
    PARDEAMIENTO_TARGET = float(center_out["Indice_pardeamiento"].iloc[0])
except Exception:
    PARDEAMIENTO_TARGET = 45.0

# ---------------------------------------------------------------------------
# SELECTOR DE TEMA EN EL SIDEBAR (Modo Claro vs Modo Oscuro)
# ---------------------------------------------------------------------------
st.sidebar.markdown('<div class="sidebar-header">Personalización</div>', unsafe_allow_html=True)
theme_mode = st.sidebar.radio(
    "Tema visual del aplicativo",
    ["Claro (Editorial)", "Oscuro (Técnico)"],
    label_visibility="visible"
)

# Definir variables de color de la paleta terrosa según el tema elegido
if theme_mode == "Claro (Editorial)":
    bg_app = "#FAF8F5"
    bg_sidebar = "#FFFFFF"
    bg_card = "#FFFFFF"
    border_color = "#EADED6"
    text_main = "#2E1B10"
    text_muted = "#6C5D53"
    accent_warm = "#B45309"
    accent_cool = "#475569"
    bg_howto = "#FDFBF7"
    border_howto = "#EADED6"
    text_howto = "#5C3D24"
    bg_metric = "#FFFFFF"
    text_metric_val = "#2E1B10"
    bg_button_secondary = "#FFFFFF"
    text_button_secondary = "#2E1B10"
    border_button_secondary = "#D1C7BD"
    
    # Plotly
    plot_paper_bg = "rgba(0,0,0,0)"
    plot_plot_bg = "#FFFFFF"
    plot_text_color = "#2E1B10"
    plot_grid_color = "#EADED6"
    plotly_colorway = ["#B45309", "#475569", "#78350F", "#1E293B"]
    TAGUCHI_SCALE = [[0, "#FAF8F5"], [0.5, "#B45309"], [1, "#2E1B10"]]
else:
    bg_app = "#160F0A"
    bg_sidebar = "#1F150F"
    bg_card = "#2A1E16"
    border_color = "#3D2B20"
    text_main = "#FAF8F5"
    text_muted = "#A89B90"
    accent_warm = "#F59E0B"
    accent_cool = "#94A3B8"
    bg_howto = "#201610"
    border_howto = "#3D2B20"
    text_howto = "#FAF8F5"
    bg_metric = "#2A1E16"
    text_metric_val = "#FAF8F5"
    bg_button_secondary = "#2A1E16"
    text_button_secondary = "#FAF8F5"
    border_button_secondary = "#3D2B20"
    
    # Plotly
    plot_paper_bg = "rgba(0,0,0,0)"
    plot_plot_bg = "#2A1E16"
    plot_text_color = "#FAF8F5"
    plot_grid_color = "#3D2B20"
    plotly_colorway = ["#F59E0B", "#94A3B8", "#D97706", "#475569"]
    TAGUCHI_SCALE = [[0, "#160F0A"], [0.5, "#F59E0B"], [1, "#FAF8F5"]]

# Inyección de CSS Terroso Premium con tipografías mixtas (Playfair Serif / Inter / JetBrains Mono)
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;0,900;1,400;1,700&family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif !important;
        background-color: {bg_app} !important;
        color: {text_main} !important;
    }}
    #MainMenu, footer, header {{ visibility: hidden; }}

    .block-container {{ padding-top: 2rem !important; padding-left: 2rem !important; padding-right: 2rem !important; max-width: 1300px !important; }}

    div[data-testid="stAppViewContainer"] {{
        background: {bg_app} !important;
    }}
    div[data-testid="stMain"] {{ background: transparent !important; }}

    /* Títulos editoriales */
    h1, h2, h3, h4, .hero-title {{
        font-family: 'Playfair Display', serif !important;
        font-weight: 700 !important;
        color: {text_main} !important;
        letter-spacing: -0.02em !important;
    }}

    /* Datos y tablas monoespaciadas */
    [data-testid="stMetricValue"], [data-testid="stDataFrame"], code, pre, td, th {{
        font-family: 'JetBrains Mono', monospace !important;
    }}

    /* SIDEBAR */
    section[data-testid="stSidebar"] {{
        background: {bg_sidebar} !important;
        border-right: 1px solid {border_color} !important;
    }}
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] div,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] label {{
        color: {text_main} !important;
    }}

    /* Cards */
    .sidebar-card {{
        background: {bg_card} !important;
        border: 1px solid {border_color} !important;
        border-radius: 8px !important;
        padding: 1rem !important;
        margin-bottom: 0.75rem !important;
    }}
    .sidebar-header {{
        font-size: 0.68rem !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
        color: {accent_warm} !important;
        margin-bottom: 0.5rem !important;
    }}
    .sidebar-desc {{
        font-size: 0.85rem !important;
        color: {text_main} !important;
        font-weight: 700 !important;
        margin-bottom: 0.6rem !important;
    }}
    .sidebar-meta {{ display: flex !important; flex-direction: column !important; gap: 0.35rem !important; }}
    .meta-item {{
        display: flex !important;
        justify-content: space-between !important;
        font-size: 0.75rem !important;
        border-bottom: 1px solid {border_color} !important;
        padding-bottom: 0.25rem !important;
    }}
    .meta-item:last-child {{ border-bottom: none !important; }}
    .meta-label {{ color: {text_muted} !important; }}
    .meta-val {{ color: {text_main} !important; font-weight: 600 !important; }}
    
    .sidebar-pill-container {{ display: flex !important; flex-direction: column !important; gap: 0.4rem !important; }}
    .sidebar-pill {{
        background: {bg_sidebar} !important;
        border: 1px solid {border_color} !important;
        border-radius: 6px !important;
        padding: 0.5rem 0.75rem !important;
        display: flex !important;
        flex-direction: column !important;
    }}
    .pill-title {{ font-size: 0.8rem !important; font-weight: 600 !important; color: {text_main} !important; }}
    .pill-subtitle {{ font-size: 0.72rem !important; color: {text_muted} !important; margin-top: 1px; }}

    /* HERO */
    .hero {{
        background: linear-gradient(135deg, #2E1B10 0%, #3E2212 40%, #5C3D24 75%, #8B5E34 100%);
        border-radius: 12px;
        padding: 0;
        margin-bottom: 1.75rem;
        display: grid;
        grid-template-columns: 1fr 1fr;
        min-height: 200px;
        position: relative;
        overflow: hidden;
        border: 1px solid {border_color};
        box-shadow: 0 4px 20px rgba(46,27,16,0.15);
    }}
    .hero::before {{
        content: "";
        position: absolute; inset: 0;
        background-image: radial-gradient(circle, rgba(255,255,255,0.06) 1px, transparent 1px);
        background-size: 20px 20px;
        pointer-events: none;
        z-index: 0;
    }}
    .hero-left {{
        padding: 2.5rem 2.5rem 2.5rem 3rem;
        z-index: 2;
        display: flex;
        flex-direction: column;
        justify-content: center;
        border-right: 1px solid rgba(255,255,255,0.1);
    }}
    .hero-tag {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(255,255,255,0.12);
        border: 1px solid rgba(255,255,255,0.18);
        border-radius: 4px;
        padding: 4px 12px;
        font-size: 0.68rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: #FAF8F5;
        margin-bottom: 14px;
        width: fit-content;
    }}
    .hero-title {{
        font-weight: 900;
        font-size: 2.1rem;
        line-height: 1.15;
        color: #FFFFFF !important;
        margin: 0 0 10px 0;
        letter-spacing: -0.03em;
    }}
    .hero-title span {{
        display: block;
        font-size: 1.15rem;
        font-weight: 600;
        color: #FAF8F5 !important;
        letter-spacing: -0.01em;
        margin-top: 6px;
    }}
    .hero-desc {{
        font-size: 0.9rem;
        color: #FAF8F5 !important;
        line-height: 1.65;
        margin: 0;
        max-width: 440px;
        font-weight: 400;
        opacity: 0.9;
    }}
    .hero-right {{
        padding: 2rem 2.5rem 2rem 2rem;
        z-index: 2;
        display: flex;
        flex-direction: column;
        justify-content: center;
        gap: 0.85rem;
    }}
    .hero-group-label {{
        font-size: 0.65rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.14em;
        color: rgba(255,255,255,0.6);
        margin-bottom: 2px;
    }}
    .hero-members-grid {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 8px;
    }}
    .hero-member-card {{
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 8px;
        padding: 8px 12px;
        transition: background 0.2s ease;
    }}
    .hero-member-card:hover {{
        background: rgba(255,255,255,0.15);
    }}
    .hero-member-name {{
        font-size: 0.82rem;
        font-weight: 600;
        color: #FFFFFF;
        line-height: 1.2;
    }}
    .hero-divider {{
        width: 100%;
        height: 1px;
        background: rgba(255,255,255,0.12);
        margin: 2px 0;
    }}

    /* TABS */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0; border-bottom: 2px solid {border_color} !important;
        background: transparent; padding-bottom: 0;
    }}
    .stTabs [data-baseweb="tab"] {{
        font-family: 'Inter', sans-serif; font-weight: 600; font-size: 0.88rem;
        color: {text_muted} !important; padding: 10px 20px;
        background: transparent; border: none;
        transition: all 0.2s ease;
    }}
    .stTabs [data-baseweb="tab"]:hover {{
        color: {text_main} !important;
        background: {bg_card};
    }}
    .stTabs [aria-selected="true"] {{
        color: {accent_warm} !important;
        background: transparent !important;
        border-bottom: 2px solid {accent_warm} !important;
        font-weight: 700 !important;
        margin-bottom: -2px;
    }}

    /* METRIC CARDS */
    div[data-testid="stMetric"] {{
        background: {bg_card} !important;
        border: 1px solid {border_color} !important;
        border-radius: 12px !important;
        padding: 1.25rem 1.5rem !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02) !important;
        border-left: 4px solid {accent_warm} !important;
        transition: all 0.2s ease !important;
    }}
    div[data-testid="stMetric"]:hover {{
        border-color: {accent_warm} !important;
        transform: translateY(-2px);
    }}
    div[data-testid="stMetricValue"] {{
        font-weight: 700 !important;
        font-size: 2.1rem !important;
        letter-spacing: -0.04em !important;
        color: {text_metric_val} !important;
    }}
    div[data-testid="stMetricLabel"] {{
        font-weight: 700 !important;
        font-size: 0.72rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
        color: {accent_cool} !important;
    }}

    /* BOTONES */
    button[data-testid^="baseButton-"] {{
        border-radius: 6px !important;
        font-weight: 600 !important;
        font-size: 0.84rem !important;
        padding: 0.5rem 1.25rem !important;
        transition: all 0.2s ease !important;
        cursor: pointer !important;
    }}
    button[data-testid="baseButton-primary"] {{
        background: {accent_warm} !important;
        border: 1px solid {accent_warm} !important;
        color: #FFFFFF !important;
        box-shadow: 0 2px 6px rgba(180,83,9,0.2) !important;
    }}
    button[data-testid="baseButton-primary"]:hover {{
        background: #92400E !important;
        border-color: #92400E !important;
        transform: translateY(-1px) !important;
    }}
    button[data-testid="baseButton-secondary"] {{
        background: {bg_button_secondary} !important;
        border: 1px solid {border_button_secondary} !important;
        color: {text_button_secondary} !important;
    }}
    button[data-testid="baseButton-secondary"]:hover {{
        border-color: {accent_warm} !important;
        color: {accent_warm} !important;
    }}
    button[data-testid="baseButton-download"] {{
        background: #F0FDF4 !important;
        border: 1px solid #86EFAC !important;
        color: #166534 !important;
    }}

    /* INPUTS */
    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] > div {{
        background: {bg_card} !important;
        border: 1.5px solid {border_color} !important;
        border-radius: 6px !important;
        color: {text_main} !important;
    }}
    div[data-baseweb="select"] *, div[data-baseweb="input"] input {{
        color: {text_main} !important;
    }}
    .stRadio label span,
    .stSlider label,
    .stSelectbox label,
    .stNumberInput label,
    .stMultiSelect label,
    .stFileUploader label {{
        color: {text_main} !important;
        font-weight: 600 !important;
    }}

    /* HOWTO BOX */
    .howto {{
        background: {bg_howto} !important;
        border-left: 4px solid {accent_warm};
        border-radius: 0 8px 8px 0;
        padding: 1.1rem 1.4rem;
        margin-bottom: 1.5rem;
        border-top: 1px solid {border_howto} !important;
        border-right: 1px solid {border_howto} !important;
        border-bottom: 1px solid {border_howto} !important;
    }}
    .howto-title {{ font-weight: 700; color: {text_howto}; font-size: 0.9rem; margin-bottom: 4px; }}
    .howto-body {{ color: {text_muted}; font-size: 0.86rem; line-height: 1.6; }}

    /* TEXTO GENERAL */
    div[data-testid="stMarkdownContainer"] p,
    div[data-testid="stMarkdownContainer"] li,
    div[data-testid="stMarkdownContainer"] strong,
    div[data-testid="stMarkdownContainer"] span {{
        color: {text_main} !important;
        line-height: 1.6;
    }}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# CONFIGURACIÓN DE PLANTILLA PLOTLY (Terrosa, libre de morado)
# ---------------------------------------------------------------------------
pio_default_template = go.layout.Template(
    layout=go.Layout(
        font=dict(family="JetBrains Mono, monospace", color=plot_text_color, size=11),
        title=dict(font=dict(family="Playfair Display, serif", size=14, color=plot_text_color, weight=700)),
        colorway=plotly_colorway,
        paper_bgcolor=plot_paper_bg,
        plot_bgcolor=plot_plot_bg,
        xaxis=dict(
            gridcolor=plot_grid_color, zerolinecolor=plot_grid_color,
            tickfont=dict(color=plot_text_color, size=10),
            title_font=dict(color=plot_text_color, size=11)
        ),
        yaxis=dict(
            gridcolor=plot_grid_color, zerolinecolor=plot_grid_color,
            tickfont=dict(color=plot_text_color, size=10),
            title_font=dict(color=plot_text_color, size=11)
        ),
        legend=dict(
            bgcolor=bg_card,
            bordercolor=border_color,
            borderwidth=1,
            font=dict(color=plot_text_color, size=10)
        ),
    )
)
pio.templates["taguchi_theme"] = pio_default_template
pio.templates.default = "taguchi_theme"

# Meta información de respuestas y sus metas por defecto en S/N
RESPONSE_META = {
    "Polifenoles_mgGAE_g": {"label": "Polifenoles totales (mg GAE/g)", "sn_type": "LB", "weight": 1.0},
    "DPPH_pct_inhibicion": {"label": "Actividad antioxidante DPPH (% inhibición)", "sn_type": "LB", "weight": 1.0},
    "Indice_pardeamiento": {"label": "Índice de pardeamiento (color)", "sn_type": "NB", "weight": 1.0, "target": PARDEAMIENTO_TARGET},
    "Puntaje_sensorial": {"label": "Puntaje sensorial (1-9)", "sn_type": "LB", "weight": 1.5},
}

# ---------------------------------------------------------------------------
# SIDEBAR — Ficha de caso Taguchi
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div class="sidebar-card">
        <div class="sidebar-header">Caso de Estudio: Taguchi</div>
        <div class="sidebar-desc">Tostado de Cacao Nacional (Ecuador)</div>
        <div class="sidebar-meta">
            <div class="meta-item"><span class="meta-label">Materia Prima</span><span class="meta-val">Cacao Fino de Aroma</span></div>
            <div class="meta-item"><span class="meta-label">Operación</span><span class="meta-val">Tostado térmico</span></div>
            <div class="meta-item"><span class="meta-label">Objetivo</span><span class="meta-val">Invariabilidad + Calidad</span></div>
        </div>
    </div>
    
    <div class="sidebar-card">
        <div class="sidebar-header">Factores de Control</div>
        <div class="sidebar-pill-container">
            <div class="sidebar-pill">
                <span class="pill-title">Temperatura de Control (A)</span>
                <span class="pill-subtitle">Rango: 120°C &ndash; 160°C</span>
            </div>
            <div class="sidebar-pill">
                <span class="pill-title">Tiempo de Control (B)</span>
                <span class="pill-subtitle">Rango: 10 &ndash; 30 min</span>
            </div>
        </div>
    </div>
    
    <div class="sidebar-card">
        <div class="sidebar-header">Factores de Ruido</div>
        <div class="sidebar-pill-container">
            <div class="sidebar-pill">
                <span class="pill-title">Humedad Ambiental (N1)</span>
                <span class="pill-subtitle">Extremos: 50% HR / 80% HR</span>
            </div>
            <div class="sidebar-pill">
                <span class="pill-title">Humedad del Grano (N2)</span>
                <span class="pill-subtitle">Extremos: 5% / 8% (mismo RSM)</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# ESTADO DE LA SESIÓN DE TAGUCHI
# ---------------------------------------------------------------------------
if "taguchi_df" not in st.session_state:
    st.session_state.taguchi_df = None
if "computed_sn" not in st.session_state:
    st.session_state.computed_sn = None

def howto(title: str, body: str):
    st.markdown(
        f'<div class="howto"><div class="howto-title">{title}</div>'
        f'<div class="howto-body">{body}</div></div>',
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# HERO
# ---------------------------------------------------------------------------
st.markdown("""
<div class="hero">
    <!-- Panel izquierdo -->
    <div class="hero-left">
        <div class="hero-tag">Taguchi &middot; Proyecto Académico</div>
        <p class="hero-title">
            Diseño Robusto de Parámetros
            <span>Optimización para insensibilidad al ruido ambiental e inicial</span>
        </p>
        <p class="hero-desc">Aplicación del arreglo factorial control &times; ruido para minimizar la variación del proceso de tostado frente a la humedad no controlable.</p>
    </div>
    <!-- Panel derecho -->
    <div class="hero-right">
        <div class="hero-group-label">Integrantes</div>
        <div class="hero-divider"></div>
        <div class="hero-members-grid">
            <div class="hero-member-card">
                <div class="hero-member-name">Chicaiza Eduardo</div>
            </div>
            <div class="hero-member-card">
                <div class="hero-member-name">Guamanarca Didier</div>
            </div>
            <div class="hero-member-card" style="grid-column: 1 / -1;">
                <div class="hero-member-name">Tamay Katherine</div>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Inicializar dataset por defecto si existe
if st.session_state.taguchi_df is None:
    default_csv = "data/cacao_taguchi_sintetico.csv"
    if os.path.exists(default_csv):
        st.session_state.taguchi_df = pd.read_csv(default_csv)

# ---------------------------------------------------------------------------
# NAVEGACIÓN TEMÁTICA AGRUPADA EN EL SIDEBAR
# ---------------------------------------------------------------------------
st.sidebar.markdown('<div class="sidebar-header">Navegación Metodológica</div>', unsafe_allow_html=True)
fase = st.sidebar.selectbox(
    "Fase de Análisis",
    [
        "1. Preparación y Datos",
        "2. Análisis y Contribución",
        "3. Optimización y Reporte"
    ]
)

if fase == "1. Preparación y Datos":
    step = st.sidebar.radio(
        "Paso activo",
        [
            "01. Datos y Arreglo Cruzado",
            "02. Cálculo de Razones S/N"
        ]
    )
elif fase == "2. Análisis y Contribución":
    step = st.sidebar.radio(
        "Paso activo",
        [
            "03. Tabla de Respuesta y Efectos",
            "04. Pareto ANOVA"
        ]
    )
else:
    step = st.sidebar.radio(
        "Paso activo",
        [
            "05. Optimización Robusta",
            "06. Exportar Reporte"
        ]
    )

# ---------------------------------------------------------------------------
# RENDERIZADO DE LOS PASOS DE NAVEGACIÓN
# ---------------------------------------------------------------------------
control_cols = ["Temperatura_real", "Tiempo_real"]
noise_cols = ["N1_real", "N2_real"]

# ===========================================================================
# PASO 1: DATOS Y ARREGLO
# ===========================================================================
if step == "01. Datos y Arreglo Cruzado":
    st.subheader("Configuración de Arreglos y Cruce Experimental")
    howto(
        "¿Qué hace este paso?",
        "Muestra el diseño experimental de Taguchi, el cual cruza una matriz interna "
        "(las combinaciones 3x3 de los factores de control Temperatura y Tiempo) con una matriz externa "
        "(las combinaciones 2x2 de los ruidos de Humedad Ambiental N1 y Humedad de Grano N2). "
        "Esto genera un total de 36 corridas experimentales. Puedes cargar el dataset o regenerar el modelo físico."
    )

    modo = st.radio(
        "Fuente de datos para Taguchi",
        ["Usar dataset sintético del proyecto (Cacao Nacional)", "Cargar archivo CSV personalizado"],
        horizontal=True
    )

    if modo == "Usar dataset sintético del proyecto (Cacao Nacional)":
        if st.button("Cargar / Regenerar Dataset de Taguchi", type="primary"):
            try:
                import subprocess
                subprocess.run(["python", "generate_data.py"], check=True)
                st.session_state.taguchi_df = pd.read_csv("data/cacao_taguchi_sintetico.csv")
                st.success("Dataset de Taguchi cargado y calibrado con éxito.")
            except Exception as e:
                st.error(f"Error al generar el dataset sintético: {e}")
                # Fallback
                from generate_data import crossed_df
                st.session_state.taguchi_df = crossed_df.copy()
                st.success("Dataset generado en memoria con éxito.")
    else:
        up = st.file_uploader("Sube tu archivo CSV con el diseño cruzado de Taguchi", type=["csv"])
        if up is not None:
            st.session_state.taguchi_df = pd.read_csv(up)
            st.success("CSV personalizado cargado correctamente.")

    st.subheader("Generador de Arreglos Ortogonales de Referencia")
    ref_kind = st.selectbox(
        "Seleccionar un arreglo ortogonal para previsualizar:",
        ["L4(2^3)", "L8(2^7)", "L9(3^4)", "L18(2^1x3^7)"]
    )
    if st.button("Generar Arreglo de Referencia"):
        ref_df = orthogonal_array(ref_kind)
        st.dataframe(ref_df, use_container_width=True)

    st.divider()

    if st.session_state.taguchi_df is not None:
        st.subheader("Matriz Cruzada Completa (36 combinaciones control x ruido)")
        st.dataframe(st.session_state.taguchi_df, use_container_width=True, height=350)
        csv_bytes = st.session_state.taguchi_df.to_csv(index=False).encode("utf-8")
        st.download_button("Descargar Matriz Cruzada (CSV)", csv_bytes, "matriz_taguchi.csv", "text/csv")
    else:
        st.info("Carga o genera el dataset para visualizar la matriz cruzada.")

# ===========================================================================
# PASO 2: RAZONES S/N
# ===========================================================================
elif step == "02. Cálculo de Razones S/N":
    st.subheader("Cálculo de Razones Señal/Ruido (S/N)")
    howto(
        "¿Qué hace este paso?",
        "Para cada una de las 9 condiciones de control de la matriz interna, calcula la razón S/N y el promedio "
        "utilizando las 4 repeticiones de la matriz externa de ruido. Aquí puedes seleccionar qué respuestas analizar "
        "y ver sus fórmulas de cálculo correspondientes (LB, SB o NB)."
    )

    if st.session_state.taguchi_df is None:
        st.warning("Primero debes cargar o generar datos en la pestaña anterior.")
    else:
        df = st.session_state.taguchi_df
        
        response_pick = st.selectbox(
            "Seleccionar respuesta a modelar en S/N:",
            list(RESPONSE_META.keys()),
            format_func=lambda x: f"{RESPONSE_META[x]['label']} [{RESPONSE_META[x]['sn_type']}]"
        )
        
        meta = RESPONSE_META[response_pick]
        sn_type = meta["sn_type"]
        
        # Mostrar la fórmula matemática asociada
        if sn_type == "LB":
            st.latex(r"S/N_{LB} = -10 \log_{10} \left( \frac{1}{n} \sum_{i=1}^{n} \frac{1}{y_i^2} \right)")
        elif sn_type == "SB":
            st.latex(r"S/N_{SB} = -10 \log_{10} \left( \frac{1}{n} \sum_{i=1}^{n} y_i^2 \right)")
        else:
            st.latex(r"S/N_{NB} = 10 \log_{10} \left( \frac{\bar{y}^2}{s^2} \right)")

        # Calcular S/N y medias para las 9 corridas
        grouped = df.groupby(["Run_Control", "Temperatura_real", "Tiempo_real"])
        
        sn_records = []
        for (run_ctrl, temp, tiempo), group in grouped:
            rec = {
                "Run_Control": run_ctrl,
                "Temperatura_real": temp,
                "Tiempo_real": tiempo
            }
            for resp, r_meta in RESPONSE_META.items():
                y_v = group[resp].values
                target_val = r_meta.get("target") if r_meta["sn_type"] == "NB" else None
                rec[f"SN_{resp}"] = signal_to_noise(y_v, r_meta["sn_type"], target=target_val)
                rec[f"Mean_{resp}"] = float(np.mean(y_v))
            sn_records.append(rec)
            
        df_sn = pd.DataFrame(sn_records)
        st.session_state.computed_sn = df_sn
        
        st.subheader("Resultados de S/N y Medias para las 9 Corridas de Control")
        cols_to_show = ["Run_Control", "Temperatura_real", "Tiempo_real", f"SN_{response_pick}", f"Mean_{response_pick}"]
        st.dataframe(
            df_sn[cols_to_show].rename(columns={
                f"SN_{response_pick}": "Razón S/N (dB)",
                f"Mean_{response_pick}": "Promedio observado"
            }),
            use_container_width=True
        )

# ===========================================================================
# PASO 3: TABLA DE RESPUESTA Y EFECTOS
# ===========================================================================
elif step == "03. Tabla de Respuesta y Efectos":
    st.subheader("Tabla de Respuesta de Factores y Gráficos de Efectos")
    howto(
        "¿Qué hace este paso?",
        "Analiza el efecto promedio de cada factor de control por nivel. Calcula la diferencia "
        "entre el nivel más alto y el más bajo (Delta) y asigna un Ranking de impacto. "
        "Se generan los gráficos de efectos principales sobre el promedio de la respuesta y sobre la razón S/N."
    )

    if st.session_state.computed_sn is None:
        st.warning("Primero calcula las razones S/N en la pestaña anterior.")
    else:
        df_sn = st.session_state.computed_sn
        response_pick = st.selectbox(
            "Seleccionar respuesta a analizar:",
            list(RESPONSE_META.keys()),
            key="effects_resp"
        )
        
        tab_sn = response_table(df_sn, ["Temperatura_real", "Tiempo_real"], f"SN_{response_pick}")
        tab_mean = response_table(df_sn, ["Temperatura_real", "Tiempo_real"], f"Mean_{response_pick}")
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**Tabla de Respuesta de Razón S/N (dB) — {response_pick}**")
            st.dataframe(tab_sn.round(4), use_container_width=True)
        with c2:
            st.markdown(f"**Tabla de Respuesta del Promedio — {response_pick}**")
            st.dataframe(tab_mean.round(4), use_container_width=True)
            
        st.subheader("Gráficos de Efectos Principales")
        factors = ["Temperatura_real", "Tiempo_real"]
        
        # S/N Plot
        fig_sn = go.Figure()
        for f in factors:
            unique_levels = sorted(df_sn[f].unique())
            means_f = [df_sn[df_sn[f] == lvl][f"SN_{response_pick}"].mean() for lvl in unique_levels]
            fig_sn.add_trace(go.Scatter(
                x=[str(x) for x in unique_levels],
                y=means_f,
                mode="lines+markers",
                name=f.replace("_real", ""),
                line=dict(width=3),
                marker=dict(size=10)
            ))
        fig_sn.update_layout(
            title=f"Efectos Principales en S/N (dB) para {response_pick}",
            xaxis_title="Nivel de Factor",
            yaxis_title="Promedio Razón S/N (dB)",
            height=400
        )
        
        # Mean Plot
        fig_mean = go.Figure()
        for f in factors:
            unique_levels = sorted(df_sn[f].unique())
            means_f = [df_sn[df_sn[f] == lvl][f"Mean_{response_pick}"].mean() for lvl in unique_levels]
            fig_mean.add_trace(go.Scatter(
                x=[str(x) for x in unique_levels],
                y=means_f,
                mode="lines+markers",
                name=f.replace("_real", ""),
                line=dict(width=3),
                marker=dict(size=10)
            ))
        fig_mean.update_layout(
            title=f"Efectos Principales en el Promedio para {response_pick}",
            xaxis_title="Nivel de Factor",
            yaxis_title="Promedio de Respuesta",
            height=400
        )
        
        ca, cb = st.columns(2)
        ca.plotly_chart(fig_sn, use_container_width=True)
        cb.plotly_chart(fig_mean, use_container_width=True)

# ===========================================================================
# PASO 4: ANOVA
# ===========================================================================
elif step == "04. Pareto ANOVA":
    st.subheader("Análisis de Varianza (ANOVA) de Contribución Porcentual")
    howto(
        "¿Qué hace este paso?",
        "Cuantifica estadísticamente el impacto de cada factor de control sobre la razón S/N. "
        "Se desglosa la Suma de Cuadrados (SC) de cada factor y del error residual, mostrando "
        "el porcentaje de contribución directa de la Temperatura y el Tiempo sobre la estabilidad del tostado."
    )

    if st.session_state.computed_sn is None:
        st.warning("Primero debes calcular el S/N.")
    else:
        df_sn = st.session_state.computed_sn
        response_pick = st.selectbox(
            "Seleccionar respuesta para el ANOVA:",
            list(RESPONSE_META.keys()),
            key="anova_resp"
        )
        
        anova_df = pareto_anova(df_sn, ["Temperatura_real", "Tiempo_real"], f"SN_{response_pick}")
        
        st.subheader("Tabla ANOVA de Contribución")
        st.dataframe(anova_df.round(4), use_container_width=True)
        
        factors_only = anova_df.index[:-1]
        contribs = anova_df.loc[factors_only, "Contribución (%)"]
        
        fig_bar = go.Figure(go.Bar(
            x=list(factors_only),
            y=contribs,
            text=[f"{v:.2f}%" for v in contribs],
            textposition="auto",
            marker_color=["#B45309", "#475569", "#78350F"][:len(contribs)]
        ))
        fig_bar.update_layout(
            title=f"Contribución Porcentual de los Factores sobre S/N ({response_pick})",
            xaxis_title="Fuente de Variación",
            yaxis_title="Contribución (%)",
            yaxis=dict(range=[0, 100]),
            height=400
        )
        
        st.plotly_chart(fig_bar, use_container_width=True)

# ===========================================================================
# PASO 5: OPTIMIZACIÓN
# ===========================================================================
elif step == "05. Optimización Robusta":
    st.subheader("Optimización Robusta y Análisis Multirespuesta (MRSN)")
    howto(
        "¿Qué hace este paso?",
        "Determina los niveles operativos de Temperatura y Tiempo óptimos. Permite "
        "hacer una predicción del S/N robusto y encontrar la mejor combinación univariante "
        "o la condición óptima simultánea usando el Índice de Deseabilidad S/N Multirespuesta (MRSN)."
    )

    if st.session_state.computed_sn is None:
        st.warning("Primero debes calcular el S/N.")
    else:
        df_sn = st.session_state.computed_sn
        
        response_pick = st.selectbox(
            "Optimización univariante para la respuesta:",
            list(RESPONSE_META.keys()),
            key="opt_resp"
        )
        
        tab_sn = response_table(df_sn, ["Temperatura_real", "Tiempo_real"], f"SN_{response_pick}")
        grand_mean = df_sn[f"SN_{response_pick}"].mean()
        
        opt_levels = {}
        for factor in tab_sn.index:
            cols = [c for c in tab_sn.columns if c.startswith("Nivel")]
            opt_lvl = tab_sn.loc[factor, cols].idxmax()
            opt_levels[factor] = opt_lvl
            
        st.markdown("### Configuración Óptima Univariante Seleccionada")
        c1, c2, c3 = st.columns(3)
        for i, (factor, opt_l) in enumerate(opt_levels.items()):
            unique_vals = sorted(df_sn[factor].unique())
            lvl_index = int(opt_l.replace("Nivel ", "")) - 1
            real_val = unique_vals[lvl_index]
            unit = "°C" if "Temperatura" in factor else "min"
            if i == 0:
                c1.metric(f"Óptimo {factor.replace('_real','')}", f"{opt_l} ({real_val} {unit})")
            else:
                c2.metric(f"Óptimo {factor.replace('_real','')}", f"{opt_l} ({real_val} {unit})")
                
        pred_sn = predict_optimal_sn(tab_sn, opt_levels, grand_mean)
        c3.metric("Razón S/N Predicha", f"{pred_sn:.3f} dB")
        
        # Gráfica de S/N por Corrida Interna
        fig_runs = go.Figure()
        best_run_idx = df_sn[f"SN_{response_pick}"].idxmax()
        best_run = df_sn.loc[best_run_idx, "Run_Control"]
        
        colors = ["rgba(108, 93, 83, 0.4)"] * len(df_sn)
        colors[best_run_idx] = accent_warm
        
        fig_runs.add_trace(go.Bar(
            x=[f"Corrida {r}" for r in df_sn["Run_Control"]],
            y=df_sn[f"SN_{response_pick}"],
            marker_color=colors,
            text=[f"{v:.2f} dB" for v in df_sn[f"SN_{response_pick}"]],
            textposition="auto"
        ))
        fig_runs.update_layout(
            title=f"Razón S/N por Corrida de Control (El color cálido destaca la mejor condición observada: Corrida #{best_run})",
            xaxis_title="Corridas de Control",
            yaxis_title="Razón S/N (dB)",
            height=400
        )
        st.plotly_chart(fig_runs, use_container_width=True)
        
        st.divider()
        
        # Scatter Plot Media vs S/N
        st.markdown("### Análisis de Ventana Operativa Robusta (Media vs S/N)")
        
        fig_scatter = px.scatter(
            df_sn,
            x=f"Mean_{response_pick}",
            y=f"SN_{response_pick}",
            text="Run_Control",
            color="Temperatura_real",
            color_continuous_scale=TAGUCHI_SCALE,
            size=np.ones(len(df_sn)) * 10
        )
        fig_scatter.update_traces(textposition="top center")
        fig_scatter.update_layout(
            title=f"Análisis Robustez: Promedio vs Razón S/N para {response_pick}",
            xaxis_title="Promedio de Respuesta",
            yaxis_title="Razón S/N (dB)",
            height=400
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        st.divider()
        
        # Bloque Multirespuesta (MRSN)
        st.markdown("### Optimización Multirespuesta (Índice MRSN)")
        
        col_w1, col_w2, col_w3, col_w4 = st.columns(4)
        w_pol = col_w1.number_input("Peso Polifenoles", 0.1, 5.0, 1.0, step=0.1)
        w_dpph = col_w2.number_input("Peso DPPH", 0.1, 5.0, 1.0, step=0.1)
        w_pard = col_w3.number_input("Peso Pardeamiento", 0.1, 5.0, 1.0, step=0.1)
        w_sens = col_w4.number_input("Peso Sensorial", 0.1, 5.0, 1.5, step=0.1)
        
        weights = {
            "Polifenoles_mgGAE_g": w_pol,
            "DPPH_pct_inhibicion": w_dpph,
            "Indice_pardeamiento": w_pard,
            "Puntaje_sensorial": w_sens
        }
        
        sn_matrix = df_sn[[f"SN_{k}" for k in weights.keys()]].rename(columns=lambda c: c.replace("SN_", ""))
        df_sn["MRSN"] = mrsn_index(sn_matrix, weights)
        
        mrsn_table = df_sn[["Run_Control", "Temperatura_real", "Tiempo_real", "MRSN"]].sort_values(by="MRSN", ascending=False)
        
        col_t1, col_t2 = st.columns([0.6, 0.4])
        with col_t1:
            st.markdown("**Corridas ordenadas por Índice MRSN (Mejor primero)**")
            st.dataframe(mrsn_table.round(4), use_container_width=True)
        with col_t2:
            st.markdown("**Condición Multirespuesta Óptima Recomendada**")
            best_mrsn = mrsn_table.iloc[0]
            st.info(
                f"La mejor condición operativa simultánea se obtiene en la Corrida #{int(best_mrsn['Run_Control'])} \n"
                f"- Temperatura: {best_mrsn['Temperatura_real']} °C \n"
                f"- Tiempo: {best_mrsn['Tiempo_real']} min \n"
                f"- Índice MRSN: {best_mrsn['MRSN']:.4f}"
            )

# ===========================================================================
# PASO 6: EXPORTACIÓN
# ===========================================================================
else:
    st.subheader("Generar y Exportar Reporte Consolidado")
    howto(
        "¿Qué hace este paso?",
        "Genera un archivo Excel (.xlsx) que reúne de forma estructurada todas las "
        "tablas experimentales, los cálculos de S/N, las tablas de respuesta de factores y el ANOVA de contribución."
    )

    if st.session_state.computed_sn is None:
        st.warning("Primero debes calcular el S/N.")
    else:
        df_sn = st.session_state.computed_sn
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            if st.session_state.taguchi_df is not None:
                st.session_state.taguchi_df.to_excel(writer, sheet_name="Matriz_Cruzada", index=False)
            df_sn.to_excel(writer, sheet_name="SN_y_Medias", index=False)
            
            for resp in RESPONSE_META.keys():
                tab_sn = response_table(df_sn, ["Temperatura_real", "Tiempo_real"], f"SN_{resp}")
                tab_sn.to_excel(writer, sheet_name=f"Efectos_SN_{resp[:10]}")
                
            for resp in RESPONSE_META.keys():
                anova_df = pareto_anova(df_sn, ["Temperatura_real", "Tiempo_real"], f"SN_{resp}")
                anova_df.to_excel(writer, sheet_name=f"ANOVA_SN_{resp[:10]}")
                
        excel_data = buffer.getvalue()
        
        st.download_button(
            label="Descargar Reporte Completo (Excel)",
            data=excel_data,
            file_name="reporte_taguchi_tostado_cacao.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        st.success("Reporte estructurado listo para descargar.")
