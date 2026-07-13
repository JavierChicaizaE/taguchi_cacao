"""
response_model.py
=================
Modelo físico de simulación de respuestas de cacao para el módulo de Taguchi.
Independiente de rsm_core para eliminar dependencias innecesarias del proyecto RSM.
"""

import numpy as np
import pandas as pd

FACTOR_RANGES = {
    "Temperatura": (120, 160),   # °C
    "Tiempo": (10, 30),          # min
    "Humedad": (5, 8),           # % base húmeda
}

def simulate_responses(df_coded: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    """
    Recibe un dataframe con columnas Temperatura, Tiempo, Humedad EN UNIDADES
    CODIFICADAS [-1, 1] y devuelve las 4 respuestas simuladas.
    """
    rng = np.random.default_rng(seed)
    T = df_coded["Temperatura"].values
    t = df_coded["Tiempo"].values
    H = df_coded["Humedad"].values
    n = len(df_coded)

    # --- Polifenoles totales (mg GAE/g) ---
    polifenoles = (
        24.0
        - 3.2 * T
        - 2.1 * t
        - 0.6 * T ** 2
        - 0.4 * t ** 2
        - 0.5 * T * t
        + 0.5 * H
        + rng.normal(0, 0.5, n)
    )
    polifenoles = np.clip(polifenoles, 5, None)

    # --- Actividad antioxidante DPPH (% inhibición) ---
    dpph = (
        68.0
        - 5.5 * T
        - 3.0 * t
        - 1.0 * T ** 2
        - 0.5 * t ** 2
        - 0.8 * T * t
        + 0.8 * H
        + rng.normal(0, 1.0, n)
    )
    dpph = np.clip(dpph, 10, 95)

    # --- Índice de pardeamiento (color, adimensional 0-100) ---
    pardeamiento = (
        45.0
        + 8.5 * T
        + 6.0 * t
        + 1.2 * T ** 2
        + 0.8 * t ** 2
        + 1.5 * T * t
        - 1.0 * H
        + rng.normal(0, 1.2, n)
    )
    pardeamiento = np.clip(pardeamiento, 10, 100)

    # --- Puntaje sensorial (escala 1-9) con óptimo intermedio ---
    sensorial = (
        7.6
        - 1.4 * (T + 0.2) ** 2
        - 1.1 * (t + 0.4) ** 2
        - 0.3 * T * t
        + 0.15 * H
        + rng.normal(0, 0.2, n)
    )
    sensorial = np.clip(sensorial, 1, 9)

    out = df_coded.copy()
    out["Polifenoles_mgGAE_g"] = np.round(polifenoles, 2)
    out["DPPH_pct_inhibicion"] = np.round(dpph, 2)
    out["Indice_pardeamiento"] = np.round(pardeamiento, 2)
    out["Puntaje_sensorial"] = np.round(sensorial, 2)
    return out
