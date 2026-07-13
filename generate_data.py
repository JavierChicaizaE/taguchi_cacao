"""
generate_data.py
================
Genera el dataset sintético cruzado para el módulo de Diseño Robusto (Taguchi).
Cruza un factorial completo 3x3 (Factores de Control: Temperatura, Tiempo) con
una matriz L4(2^2) (Factores de Ruido: Humedad Ambiental N1, Humedad del Grano N2).

Reutiliza directamente el simulador de respuestas físico de data_generator.py
para garantizar la consistencia entre los dos lentes de análisis (RSM y Taguchi).
"""

import os
import numpy as np
import pandas as pd
from response_model import simulate_responses, FACTOR_RANGES

# Configuración del diseño interno (Control)
# Temperatura (120, 140, 160) y Tiempo (10, 20, 30)
control_grid = []
run_ctrl = 1
for T_val in [120, 140, 160]:
    for t_val in [10, 20, 30]:
        control_grid.append({
            "Run_Control": run_ctrl,
            "Temperatura_real": T_val,
            "Temperatura_cod": (T_val - 140.0) / 20.0,
            "Tiempo_real": t_val,
            "Tiempo_cod": (t_val - 20.0) / 10.0
        })
        run_ctrl += 1
df_control = pd.DataFrame(control_grid)

# Configuración del diseño externo (Ruido)
# N1 = Humedad Ambiental: 50% HR (bajo, -1) y 80% HR (alto, +1)
# N2 = Humedad Inicial del Grano: 5% (bajo, -1) y 8% (alto, +1)
noise_grid = [
    {"N1_real": 50, "N1_cod": -1.0, "N2_real": 5.0, "N2_cod": -1.0},
    {"N1_real": 50, "N1_cod": -1.0, "N2_real": 8.0, "N2_cod": 1.0},
    {"N1_real": 80, "N1_cod": 1.0, "N2_real": 5.0, "N2_cod": -1.0},
    {"N1_real": 80, "N1_cod": 1.0, "N2_real": 8.0, "N2_cod": 1.0}
]
df_noise = pd.DataFrame(noise_grid)

# Cruce completo (9 x 4 = 36 corridas)
df_control["_key"] = 1
df_noise["_key"] = 1
crossed_df = pd.merge(df_control, df_noise, on="_key").drop(columns=["_key"])

# Preparar DataFrame en el formato esperado por simulate_responses
# Columnas: Temperatura, Tiempo, Humedad (en unidades codificadas)
sim_input = pd.DataFrame({
    "Temperatura": crossed_df["Temperatura_cod"],
    "Tiempo": crossed_df["Tiempo_cod"],
    "Humedad": crossed_df["N2_cod"]
})

# Ejecutar simulación base usando data_generator.simulate_responses
# seed=42 para reproducibilidad
sim_output = simulate_responses(sim_input, seed=42)

# Copiar respuestas base
crossed_df["Polifenoles_mgGAE_g"] = sim_output["Polifenoles_mgGAE_g"]
crossed_df["DPPH_pct_inhibicion"] = sim_output["DPPH_pct_inhibicion"]
crossed_df["Indice_pardeamiento"] = sim_output["Indice_pardeamiento"]
crossed_df["Puntaje_sensorial"] = sim_output["Puntaje_sensorial"]

# Añadir término de sensibilidad al ruido (N1 - Humedad ambiental) dependiente de la temperatura.
# Esto representa la sensibilidad térmica de Maillard frente a la humedad en producción.
T_c = crossed_df["Temperatura_cod"].values
N1_c = crossed_df["N1_cod"].values

# Efectos de degradación de calidad a alta temperatura y alta humedad ambiental
extra_polifenoles = -0.5 * (T_c + 1.0) * (N1_c + 1.0)
extra_dpph = -1.0 * (T_c + 1.0) * (N1_c + 1.0)
extra_pardeamiento = 1.5 * (T_c + 1.0) * (N1_c + 1.0)
extra_sensorial = -0.3 * (T_c + 1.2) * (N1_c + 1.0)

# Aplicar los efectos y redondear
crossed_df["Polifenoles_mgGAE_g"] = np.round(crossed_df["Polifenoles_mgGAE_g"] + extra_polifenoles, 2)
crossed_df["DPPH_pct_inhibicion"] = np.round(crossed_df["DPPH_pct_inhibicion"] + extra_dpph, 2)
crossed_df["Indice_pardeamiento"] = np.round(crossed_df["Indice_pardeamiento"] + extra_pardeamiento, 2)
crossed_df["Puntaje_sensorial"] = np.round(crossed_df["Puntaje_sensorial"] + extra_sensorial, 2)

# Asegurar límites físicos lógicos
crossed_df["Polifenoles_mgGAE_g"] = np.clip(crossed_df["Polifenoles_mgGAE_g"], 5.0, None)
crossed_df["DPPH_pct_inhibicion"] = np.clip(crossed_df["DPPH_pct_inhibicion"], 10.0, 95.0)
crossed_df["Indice_pardeamiento"] = np.clip(crossed_df["Indice_pardeamiento"], 10.0, 100.0)
crossed_df["Puntaje_sensorial"] = np.clip(crossed_df["Puntaje_sensorial"], 1.0, 9.0)

# Guardar en data/
os.makedirs("data", exist_ok=True)
output_path = "data/cacao_taguchi_sintetico.csv"
crossed_df.to_csv(output_path, index=False)
print(f"Dataset de Taguchi generado con éxito en: {output_path} ({len(crossed_df)} filas).")
