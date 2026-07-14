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
    page_title="Modelo robusto - Tostado de Cacao Nacional",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
# TEMA VISUAL (renderizado en topbar, no en sidebar)
# ---------------------------------------------------------------------------
THEME_OPTIONS = ["Claro profesional", "Oscuro técnico"]
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = THEME_OPTIONS[0]
theme_mode = st.session_state.theme_mode

# Paleta institucional para una interfaz tecnica y formal.
if theme_mode == "Claro profesional":
    bg_app = "#F5F4F0"
    bg_sidebar = "#243742"
    bg_card = "#FFFFFF"
    bg_panel = "#EAE9E2"
    border_color = "#D4D3C4"
    text_main = "#243742"
    text_muted = "#2F4858"
    sidebar_text = "#FFFFFF"
    sidebar_muted = "#C8B592"
    accent_warm = "#FF7700"
    accent_warm_hover = "#E06600"
    accent_cool = "#33658A"
    accent_gold = "#F0BA19"
    bg_howto = "#FFFFFF"
    border_howto = "#C8B592"
    text_howto = "#243742"
    bg_metric = "#FFFFFF"
    text_metric_val = "#243742"
    bg_button_secondary = "#FFFFFF"
    text_button_secondary = "#243742"
    border_button_secondary = "#D4D3C4"
    shadow_soft = "0 14px 34px rgba(36, 55, 66, 0.08)"

    plot_paper_bg = "rgba(0,0,0,0)"
    plot_plot_bg = "#FFFFFF"
    plot_text_color = "#243742"
    plot_grid_color = "#EAE9E2"
    plotly_colorway = ["#FF7700", "#33658A", "#69D1C5", "#2F4858", "#F0BA19"]
    TAGUCHI_SCALE = [[0, "#F5F4F0"], [0.5, "#FF7700"], [1, "#243742"]]
else:
    bg_app = "#1E2A33"
    bg_sidebar = "#18222A"
    bg_card = "#243742"
    bg_panel = "#2F4858"
    border_color = "#2F4858"
    text_main = "#EBF1F5"
    text_muted = "#C8B592"
    sidebar_text = "#EBF1F5"
    sidebar_muted = "#C8B592"
    accent_warm = "#FF7700"
    accent_warm_hover = "#FF9233"
    accent_cool = "#69D1C5"
    accent_gold = "#F0BA19"
    bg_howto = "#243742"
    border_howto = "#2F4858"
    text_howto = "#EBF1F5"
    bg_metric = "#243742"
    text_metric_val = "#EBF1F5"
    bg_button_secondary = "#243742"
    text_button_secondary = "#EBF1F5"
    border_button_secondary = "#2F4858"
    shadow_soft = "0 14px 34px rgba(0, 0, 0, 0.35)"

    plot_paper_bg = "rgba(0,0,0,0)"
    plot_plot_bg = "#243742"
    plot_text_color = "#EBF1F5"
    plot_grid_color = "#2F4858"
    plotly_colorway = ["#FF7700", "#69D1C5", "#F0BA19", "#33658A", "#C8B592"]
    TAGUCHI_SCALE = [[0, "#1E2A33"], [0.5, "#FF7700"], [1, "#EBF1F5"]]

# CSS visual: sistema profesional, sidebar fijo y componentes Streamlit refinados.
st.markdown(f"""
<style>
    :root {{
        --app-bg: {bg_app};
        --sidebar-bg: {bg_sidebar};
        --card-bg: {bg_card};
        --panel-bg: {bg_panel};
        --border: {border_color};
        --text: {text_main};
        --muted: {text_muted};
        --sidebar-text: {sidebar_text};
        --sidebar-muted: {sidebar_muted};
        --accent: {accent_warm};
        --accent-hover: {accent_warm_hover};
        --accent-cool: {accent_cool};
        --accent-gold: {accent_gold};
        --shadow-soft: {shadow_soft};
        --sidebar-width: 340px;
    }}

    html, body, [class*="css"] {{
        font-family: "Segoe UI", Inter, Arial, sans-serif !important;
        background-color: var(--app-bg) !important;
        color: var(--text) !important;
    }}
    #MainMenu, footer, header {{ visibility: hidden; }}

    div[data-testid="stAppViewContainer"] {{ background: var(--app-bg) !important; }}
    div[data-testid="stMain"] {{ background: transparent !important; }}
    .block-container {{
        max-width: 1360px !important;
        padding: 1.1rem 2rem 3rem !important;
    }}

    @media (min-width: 900px) {{
        section[data-testid="stSidebar"] {{
            position: relative !important;
            width: var(--sidebar-width) !important;
            min-width: var(--sidebar-width) !important;
            max-width: var(--sidebar-width) !important;
            height: 100vh !important;
            overflow-y: auto !important;
            z-index: 2 !important;
            transform: translateX(0) !important;
            visibility: visible !important;
        }}
        section[data-testid="stSidebar"] > div:first-child {{
            width: var(--sidebar-width) !important;
            min-width: var(--sidebar-width) !important;
        }}
        div[data-testid="stMain"] {{
            width: calc(100vw - var(--sidebar-width)) !important;
        }}
    }}

    [data-testid="collapsedControl"], [data-testid="stSidebarCollapseButton"] {{
        display: none !important;
    }}

    .topbar {{
        background: var(--card-bg) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        padding: 0.95rem 1.08rem !important;
        margin: 0 0 1rem !important;
        box-shadow: var(--shadow-soft) !important;
        min-height: 5.1rem !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
    }}
    .topbar-title {{
        color: var(--text) !important;
        font-size: 0.78rem !important;
        font-weight: 820 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
        margin-bottom: 0.22rem !important;
    }}
    .topbar-subtitle {{
        color: var(--muted) !important;
        font-size: 0.9rem !important;
        line-height: 1.35 !important;
    }}
    .theme-shell {{
        background: var(--card-bg) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        padding: 0.78rem 0.9rem 0.72rem !important;
        margin: 0 0 0.45rem !important;
        box-shadow: var(--shadow-soft) !important;
        min-height: 2.65rem !important;
    }}
    .theme-label {{
        color: var(--muted) !important;
        font-size: 0.68rem !important;
        font-weight: 820 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.07em !important;
        margin-bottom: 0.1rem !important;
    }}
    .theme-value {{
        color: var(--text) !important;
        font-size: 0.86rem !important;
        font-weight: 740 !important;
        line-height: 1.2 !important;
    }}
    .st-key-theme_light button,
    .st-key-theme_dark button {{
        min-height: 2.45rem !important;
        border-radius: 999px !important;
        padding: 0.38rem 0.8rem !important;
        font-size: 0.88rem !important;
        font-weight: 760 !important;
        white-space: nowrap !important;
        box-shadow: none !important;
    }}
    .st-key-theme_light p,
    .st-key-theme_dark p {{
        font-size: 0.88rem !important;
        font-weight: 760 !important;
        line-height: 1 !important;
        margin: 0 !important;
    }}

    h1, h2, h3, h4 {{
        font-family: "Segoe UI", Inter, Arial, sans-serif !important;
        color: var(--text) !important;
        font-weight: 760 !important;
        letter-spacing: 0 !important;
    }}
    h2, h3 {{ margin-top: 1.2rem !important; }}
    p, li, label, span, div[data-testid="stMarkdownContainer"] {{ color: var(--text) !important; }}
    div[data-testid="stMarkdownContainer"] p,
    div[data-testid="stMarkdownContainer"] li {{ line-height: 1.62 !important; }}
    code, pre, td, th, [data-testid="stMetricValue"] {{
        font-family: "Cascadia Mono", "Consolas", monospace !important;
    }}

    section[data-testid="stSidebar"] {{
        background: var(--sidebar-bg) !important;
        border-right: 1px solid rgba(148,163,184,0.22) !important;
        box-shadow: 8px 0 22px rgba(15,23,42,0.10) !important;
    }}
    section[data-testid="stSidebar"] > div {{
        padding: 1.05rem 0.9rem 1.25rem !important;
    }}
    section[data-testid="stSidebar"] * {{ color: var(--sidebar-text) !important; }}
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p {{ color: var(--sidebar-text) !important; font-weight: 600 !important; }}
    section[data-testid="stSidebar"] div[role="radiogroup"] label {{
        background: rgba(255,255,255,0.045) !important;
        border: 1px solid rgba(148,163,184,0.22) !important;
        border-radius: 7px !important;
        padding: 0.45rem 0.55rem !important;
        margin-bottom: 0.35rem !important;
    }}

    .sidebar-card {{
        background: rgba(255,255,255,0.045) !important;
        border: 1px solid rgba(148,163,184,0.20) !important;
        border-radius: 8px !important;
        padding: 0.92rem !important;
        margin: 0 0 0.85rem !important;
        box-shadow: none !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease, background 0.2s ease !important;
    }}
    .sidebar-card:hover {{
        background: rgba(255,255,255,0.07) !important;
        transform: translateY(-2px);
    }}
    .spec-card {{
        border-left: 4px solid var(--accent-cool) !important;
    }}
    .control-card {{
        border-left: 4px solid var(--accent) !important;
    }}
    .noise-card {{
        border-left: 4px solid var(--accent-gold) !important;
    }}
    .sidebar-header {{
        color: var(--accent-gold) !important;
        font-size: 0.69rem !important;
        font-weight: 800 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
        margin: 0 0 0.55rem !important;
    }}
    .sidebar-desc {{
        color: var(--sidebar-text) !important;
        font-size: 0.92rem !important;
        line-height: 1.35 !important;
        font-weight: 750 !important;
        margin-bottom: 0.8rem !important;
    }}
    .sidebar-meta {{ display: grid !important; gap: 0.42rem !important; }}
    .meta-item {{
        display: grid !important;
        grid-template-columns: 1fr auto !important;
        gap: 0.55rem !important;
        align-items: center !important;
        padding-top: 0.42rem !important;
        border-top: 1px solid rgba(255,255,255,0.10) !important;
    }}
    .meta-label, .pill-subtitle {{ color: var(--sidebar-muted) !important; font-size: 0.73rem !important; }}
    .meta-val {{ color: var(--sidebar-text) !important; font-size: 0.73rem !important; font-weight: 760 !important; text-align: right !important; }}
    .sidebar-pill-container {{ display: grid !important; gap: 0.46rem !important; }}
    .sidebar-pill {{
        background: rgba(15,23,42,0.30) !important;
        border: 1px solid rgba(148,163,184,0.20) !important;
        border-radius: 7px !important;
        padding: 0.62rem 0.72rem !important;
        display: grid !important;
        gap: 0.12rem !important;
    }}
    .pill-title {{ color: var(--sidebar-text) !important; font-size: 0.8rem !important; font-weight: 760 !important; }}

    .hero {{
        background: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: 8px;
        margin-bottom: 1.35rem;
        display: grid;
        grid-template-columns: minmax(0, 1.16fr) minmax(330px, 0.84fr);
        min-height: 286px;
        overflow: hidden;
        box-shadow: var(--shadow-soft);
        position: relative;
    }}
    .hero-left {{
        padding: 2rem 2.2rem 1.8rem;
        display: flex;
        flex-direction: column;
        justify-content: center;
        border-left: 5px solid var(--accent);
        border-right: 1px solid var(--border);
    }}
    .hero-right {{
        padding: 1.45rem;
        background: var(--panel-bg);
        display: grid;
        grid-template-rows: auto auto auto;
        gap: 0.95rem;
    }}
    .hero-title {{
        color: var(--text) !important;
        font-size: clamp(1.9rem, 2.7vw, 2.72rem);
        line-height: 1.05;
        font-weight: 820 !important;
        margin: 0 0 0.7rem 0;
        letter-spacing: 0 !important;
    }}
    .hero-title span {{
        display: block;
        color: var(--muted) !important;
        font-size: 1.02rem;
        line-height: 1.35;
        font-weight: 650;
        margin-top: 0.52rem;
    }}
    .hero-desc {{
        max-width: 780px;
        color: var(--muted) !important;
        font-size: 0.96rem;
        line-height: 1.58;
        margin: 0 0 1rem 0;
    }}
    .hero-kpis {{
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.62rem;
    }}
    .hero-kpi {{
        background: var(--panel-bg);
        border: 1px solid var(--border);
        border-radius: 8px;
        color: var(--text) !important;
        font-size: 0.8rem;
        font-weight: 760;
        padding: 0.66rem 0.72rem;
    }}
    .hero-kpi strong {{
        display: block;
        color: var(--accent) !important;
        font-size: 0.68rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 0.12rem;
    }}
    .hero-method {{
        display: grid;
        grid-template-columns: 1fr auto 1fr;
        align-items: center;
        gap: 0.65rem;
    }}
    .method-box {{
        background: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 0.75rem;
        min-height: 4.8rem;
    }}
    .method-label {{
        color: var(--muted) !important;
        font-size: 0.66rem;
        font-weight: 820;
        text-transform: uppercase;
        letter-spacing: 0.07em;
        margin-bottom: 0.28rem;
    }}
    .method-main {{
        color: var(--text) !important;
        font-size: 1.18rem;
        font-weight: 840;
        line-height: 1;
    }}
    .method-sub {{
        color: var(--muted) !important;
        font-size: 0.75rem;
        margin-top: 0.22rem;
    }}
    .method-arrow {{
        color: var(--accent) !important;
        font-size: 1.3rem;
        font-weight: 840;
    }}
    .hero-panel-title {{
        color: var(--text) !important;
        font-size: 0.95rem;
        font-weight: 820;
        margin: 0;
    }}
    .hero-panel-copy {{
        color: var(--muted) !important;
        font-size: 0.82rem;
        line-height: 1.45;
        margin: 0;
    }}
    .hero-group-label {{
        color: var(--accent-cool) !important;
        font-size: 0.7rem;
        font-weight: 820;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }}
    .hero-divider {{ height: 1px; background: var(--border); }}
    .hero-members-grid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 0.5rem; }}
    .hero-member-card {{
        background: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 0.62rem;
        display: grid;
        grid-template-columns: auto;
        align-items: center;
        justify-items: center;
        text-align: center;
        gap: 0.4rem;
    }}
    .hero-member-avatar {{
        width: 2rem;
        height: 2rem;
        border-radius: 999px;
        display: grid;
        place-items: center;
        background: rgba(37,99,235,0.12);
        border: 1px solid rgba(37,99,235,0.25);
        color: var(--accent) !important;
        font-size: 0.74rem;
        font-weight: 840;
    }}
    .hero-member-name {{ color: var(--text) !important; font-size: 0.75rem; font-weight: 780; line-height: 1.22; }}
    .hero-member-role {{
        color: var(--muted) !important;
        font-size: 0.62rem;
        font-weight: 780;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}

    div[data-testid="stMetric"] {{
        background: var(--card-bg) !important;
        border: 1px solid var(--border) !important;
        border-left: 4px solid var(--accent) !important;
        border-radius: 8px !important;
        padding: 1rem 1.12rem !important;
        box-shadow: var(--shadow-soft) !important;
    }}
    div[data-testid="stMetricValue"] {{ color: {text_metric_val} !important; font-size: 1.68rem !important; font-weight: 800 !important; letter-spacing: 0 !important; }}
    div[data-testid="stMetricLabel"] {{ color: var(--accent-cool) !important; font-size: 0.72rem !important; font-weight: 800 !important; text-transform: uppercase !important; letter-spacing: 0.06em !important; }}

    button[data-testid^="baseButton-"] {{
        border-radius: 7px !important;
        font-weight: 720 !important;
        font-size: 0.84rem !important;
        min-height: 2.35rem !important;
        transition: border-color 0.16s ease, background 0.16s ease, transform 0.16s ease !important;
    }}
    button[data-testid="baseButton-primary"] {{
        background: var(--accent) !important;
        border: 1px solid var(--accent) !important;
        color: #FFFFFF !important;
        box-shadow: 0 8px 18px rgba(37,99,235,0.20) !important;
    }}
    button[data-testid="baseButton-primary"]:hover {{ background: var(--accent-hover) !important; border-color: var(--accent-hover) !important; transform: translateY(-1px); }}
    button[data-testid="baseButton-secondary"] {{
        background: {bg_button_secondary} !important;
        border: 1px solid {border_button_secondary} !important;
        color: {text_button_secondary} !important;
    }}
    button[data-testid="baseButton-secondary"]:hover {{ border-color: var(--accent) !important; color: var(--accent) !important; }}
    button[data-testid="baseButton-download"] {{
        background: var(--accent-cool) !important;
        border: 1px solid var(--accent-cool) !important;
        color: #FFFFFF !important;
    }}

    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] > div,
    textarea {{
        background: var(--card-bg) !important;
        border: 1px solid var(--border) !important;
        border-radius: 7px !important;
        color: var(--text) !important;
    }}
    div[data-baseweb="select"] *, div[data-baseweb="input"] input, textarea {{ color: var(--text) !important; }}
    .stRadio label span, .stSelectbox label, .stNumberInput label, .stMultiSelect label, .stFileUploader label {{
        color: var(--text) !important;
        font-weight: 700 !important;
    }}
    div[data-baseweb="popover"], div[data-baseweb="menu"], ul[role="listbox"], ul[role="listbox"] li {{
        background: var(--card-bg) !important;
        color: var(--text) !important;
    }}
    ul[role="listbox"] li:hover, ul[role="listbox"] li[aria-selected="true"] {{ background: var(--accent) !important; color: #FFFFFF !important; }}

    div[data-testid="stDataFrame"], div[data-testid="stTable"] {{
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        overflow: hidden !important;
        box-shadow: var(--shadow-soft) !important;
    }}
    table, tr, td, th {{ background-color: var(--card-bg) !important; color: var(--text) !important; border-color: var(--border) !important; }}
    thead th {{ background-color: var(--panel-bg) !important; color: var(--text) !important; font-weight: 800 !important; }}

    .howto {{
        background: {bg_howto} !important;
        border: 1px solid {border_howto} !important;
        border-left: 4px solid var(--accent) !important;
        border-radius: 8px !important;
        padding: 1rem 1.18rem !important;
        margin-bottom: 1.2rem !important;
        box-shadow: var(--shadow-soft) !important;
    }}
    .howto-title {{ color: {text_howto} !important; font-weight: 800 !important; font-size: 0.9rem !important; margin-bottom: 0.22rem !important; }}
    .howto-body {{ color: var(--muted) !important; font-size: 0.88rem !important; line-height: 1.58 !important; }}

    .stAlert {{ border-radius: 8px !important; border: 1px solid var(--border) !important; }}
    hr {{ border-color: var(--border) !important; }}
    .js-plotly-plot {{ border-radius: 8px !important; overflow: hidden !important; }}

    @media (max-width: 900px) {{
        .block-container {{ padding: 1rem !important; }}
        .hero {{ grid-template-columns: 1fr; }}
        .hero-left {{ border-right: 0; border-bottom: 1px solid rgba(255,255,255,0.12); padding: 1.45rem; }}
        .hero-right {{ padding: 1.25rem 1.45rem; }}
        .hero-members-grid {{ grid-template-columns: 1fr; }}
    }}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# TOPBAR — selector visual fuera del sidebar
# ---------------------------------------------------------------------------
topbar_left, topbar_right = st.columns([0.70, 0.30], vertical_alignment="top")
with topbar_left:
    st.markdown(
        """
        <div class="topbar">
            <div class="topbar-title">Modelo robusto - Tostado de Cacao Nacional</div>
            <div class="topbar-subtitle">Análisis robusto de parámetros, estabilidad del proceso y optimización multirespuesta.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with topbar_right:
    st.markdown(
        """
        <div class="theme-shell">
            <div class="theme-label">Tema visual</div>
            <div class="theme-value">Modo de interfaz</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    light_col, dark_col = st.columns(2)
    light_type = "primary" if st.session_state.theme_mode == "Claro profesional" else "secondary"
    dark_type = "primary" if st.session_state.theme_mode == "Oscuro técnico" else "secondary"
    if light_col.button("☀  Claro", key="theme_light", type=light_type, use_container_width=True):
        st.session_state.theme_mode = "Claro profesional"
        st.rerun()
    if dark_col.button("◐  Oscuro", key="theme_dark", type=dark_type, use_container_width=True):
        st.session_state.theme_mode = "Oscuro técnico"
        st.rerun()

# ---------------------------------------------------------------------------
# CONFIGURACIÓN DE PLANTILLA PLOTLY (formal, técnica)
# ---------------------------------------------------------------------------
pio_default_template = go.layout.Template(
    layout=go.Layout(
        font=dict(family="Cascadia Mono, Consolas, monospace", color=plot_text_color, size=11),
        title=dict(font=dict(family="Segoe UI, Arial, sans-serif", size=14, color=plot_text_color, weight=700)),
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
    <div class="sidebar-card spec-card">
        <div class="sidebar-header">Ficha Técnica de Proceso</div>
        <div class="sidebar-desc">Tostado de Cacao Nacional (Ecuador)</div>
        <div class="sidebar-meta">
            <div class="meta-item"><span class="meta-label">Materia Prima</span><span class="meta-val">Cacao Fino de Aroma</span></div>
            <div class="meta-item"><span class="meta-label">Operación</span><span class="meta-val">Tostado térmico</span></div>
            <div class="meta-item"><span class="meta-label">Objetivo</span><span class="meta-val">Invariabilidad + Calidad</span></div>
        </div>
    </div>
    
    <div class="sidebar-card control-card">
        <div class="sidebar-header">Factores de Control (Matriz Interna)</div>
        <div class="sidebar-pill-container">
            <div class="sidebar-pill">
                <span class="pill-title">Temperatura de Control (<i>A</i>)</span>
                <span class="pill-subtitle">Rango: 120°C &ndash; 160°C</span>
            </div>
            <div class="sidebar-pill">
                <span class="pill-title">Tiempo de Control (<i>B</i>)</span>
                <span class="pill-subtitle">Rango: 10 &ndash; 30 min</span>
            </div>
        </div>
    </div>
    
    <div class="sidebar-card noise-card">
        <div class="sidebar-header">Factores de Ruido (Matriz Externa)</div>
        <div class="sidebar-pill-container">
            <div class="sidebar-pill">
                <span class="pill-title">Humedad Ambiental (<i>N</i><sub>1</sub>)</span>
                <span class="pill-subtitle">Extremos: 50% HR / 80% HR</span>
            </div>
            <div class="sidebar-pill">
                <span class="pill-title">Humedad del Grano (<i>N</i><sub>2</sub>)</span>
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
    <div class="hero-left">
        <p class="hero-title">
            Modelo robusto - Tostado de Cacao Nacional
            <span>Análisis experimental de temperatura, tiempo y humedad para evaluar calidad del proceso.</span>
        </p>
        <p class="hero-desc">El estudio cruza condiciones de control con escenarios de humedad para comparar respuestas fisicoquímicas y sensoriales del tostado.</p>
        <div class="hero-kpis">
            <span class="hero-kpi"><strong>Control</strong>Temperatura · Tiempo</span>
            <span class="hero-kpi"><strong>Ruido</strong>Humedad ambiente · grano</span>
            <span class="hero-kpi"><strong>Salida</strong>S/N · ANOVA · MRSN</span>
        </div>
    </div>
    <div class="hero-right">
        <div class="hero-method">
            <div class="method-box">
                <div class="method-label">Matriz interna</div>
                <div class="method-main">3 × 3</div>
                <div class="method-sub">niveles de control</div>
            </div>
            <div class="method-arrow">×</div>
            <div class="method-box">
                <div class="method-label">Matriz externa</div>
                <div class="method-main">2 × 2</div>
                <div class="method-sub">escenarios de ruido</div>
            </div>
        </div>
        <div class="hero-divider"></div>
        <div class="hero-members-grid">
            <div class="hero-member-card">
                <div class="hero-member-avatar">CE</div>
                <div>
                    <div class="hero-member-name">Chicaiza Eduardo</div>
                </div>
            </div>
            <div class="hero-member-card">
                <div class="hero-member-avatar">GD</div>
                <div>
                    <div class="hero-member-name">Guamanarca Didier</div>
                </div>
            </div>
            <div class="hero-member-card">
                <div class="hero-member-avatar">TK</div>
                <div>
                    <div class="hero-member-name">Tamay Katherine</div>
                </div>
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
# NAVEGACIÓN METODOLÓGICA (CONTENIDO PRINCIPAL)
# ---------------------------------------------------------------------------
ALL_STEPS = [
    "01. Datos y Arreglo Cruzado",
    "02. Cálculo de Razones S/N",
    "03. Tabla de Respuesta y Efectos",
    "04. Pareto ANOVA",
    "05. Optimización Robusta",
    "06. Exportar Reporte"
]

if "active_step" not in st.session_state:
    st.session_state.active_step = ALL_STEPS[0]

# Determinar el índice actual para resaltar la fase
step_index = ALL_STEPS.index(st.session_state.active_step)

active_border_1 = accent_warm if step_index in [0, 1] else border_color
active_border_2 = accent_warm if step_index in [2, 3] else border_color
active_border_3 = accent_warm if step_index in [4, 5] else border_color

active_text_1 = text_main if step_index in [0, 1] else text_muted
active_text_2 = text_main if step_index in [2, 3] else text_muted
active_text_3 = text_main if step_index in [4, 5] else text_muted

phase_html = f"""
<div style="display: flex; justify-content: space-between; margin-bottom: 15px; font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; font-family: 'Inter', sans-serif;">
    <div style="width: 32%; text-align: center; border-bottom: 3px solid {active_border_1}; padding-bottom: 8px; color: {active_text_1};">Fase I: Preparación y Datos</div>
    <div style="width: 32%; text-align: center; border-bottom: 3px solid {active_border_2}; padding-bottom: 8px; color: {active_text_2};">Fase II: Análisis y Contribución</div>
    <div style="width: 32%; text-align: center; border-bottom: 3px solid {active_border_3}; padding-bottom: 8px; color: {active_text_3};">Fase III: Optimización y Reporte</div>
</div>
"""
st.markdown(phase_html, unsafe_allow_html=True)

cols = st.columns(6)
step_labels = [
    "1. Datos y Arreglo",
    "2. Razones S/N",
    "3. Efectos y Tablas",
    "4. Pareto ANOVA",
    "5. Optimización",
    "6. Reporte"
]

for idx, label in enumerate(step_labels):
    step_val = ALL_STEPS[idx]
    is_active = (st.session_state.active_step == step_val)
    btn_type = "primary" if is_active else "secondary"
    if cols[idx].button(label, key=f"btn_step_{idx}", type=btn_type, use_container_width=True):
        st.session_state.active_step = step_val
        st.rerun()

step = st.session_state.active_step

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
        ["L4(2^3)", "L8(2^7)", "L9(3^4)", "L18(2^1x3^7)"],
        format_func=lambda x: {
            "L4(2^3)": "L₄ (2³)",
            "L8(2^7)": "L₈ (2⁷)",
            "L9(3^4)": "L₉ (3⁴)",
            "L18(2^1x3^7)": "L₁₈ (2¹ × 3⁷)"
        }.get(x, x)
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
        ca.plotly_chart(fig_sn, use_container_width=True, theme=None)
        cb.plotly_chart(fig_mean, use_container_width=True, theme=None)

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
            marker_color=["#2563EB", "#0F766E", "#7C3AED"][:len(contribs)]
        ))
        fig_bar.update_layout(
            title=f"Contribución Porcentual de los Factores sobre S/N ({response_pick})",
            xaxis_title="Fuente de Variación",
            yaxis_title="Contribución (%)",
            yaxis=dict(range=[0, 100]),
            height=400
        )
        
        st.plotly_chart(fig_bar, use_container_width=True, theme=None)

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
        
        colors = ["rgba(100, 116, 139, 0.38)"] * len(df_sn)
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
        st.plotly_chart(fig_runs, use_container_width=True, theme=None)
        
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
        st.plotly_chart(fig_scatter, use_container_width=True, theme=None)
        
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

# ---------------------------------------------------------------------------
# BOTONES DE NAVEGACIÓN SECUENCIAL (ANTERIOR / SIGUIENTE)
# ---------------------------------------------------------------------------
st.markdown("<br><br>", unsafe_allow_html=True)
st.divider()
col_prev, col_spacer, col_next = st.columns([0.25, 0.5, 0.25])

if step_index > 0:
    if col_prev.button("← Paso Anterior", key="btn_prev_step", use_container_width=True):
        st.session_state.active_step = ALL_STEPS[step_index - 1]
        st.rerun()

if step_index < len(ALL_STEPS) - 1:
    if col_next.button("Siguiente Paso →", key="btn_next_step", type="primary", use_container_width=True):
        st.session_state.active_step = ALL_STEPS[step_index + 1]
        st.rerun()

