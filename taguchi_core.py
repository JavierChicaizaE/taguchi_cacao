"""
taguchi_core.py
===============
Motor estadístico independiente para el Diseño Robusto de Parámetros de Taguchi.
Proporciona funciones para generar arreglos, calcular razones señal/ruido,
tablas de respuestas, análisis de varianza (ANOVA) y optimización multirespuesta.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Union, Optional

def full_factorial(levels_per_factor: Dict[str, List[Union[int, float]]]) -> pd.DataFrame:
    """
    Genera un diseño factorial completo a partir de un diccionario de niveles por factor.
    Ejemplo:
        levels = {"A": [120, 140, 160], "B": [10, 20, 30]}
    """
    import itertools
    keys = list(levels_per_factor.keys())
    values = list(levels_per_factor.values())
    grid = list(itertools.product(*values))
    return pd.DataFrame(grid, columns=keys)

def orthogonal_array_L4() -> pd.DataFrame:
    """
    Genera una matriz externa ortogonal L4(2^2) para factores de ruido N1 y N2.
    Nivel -1 significa bajo, Nivel 1 significa alto.
    """
    data = [
        [-1, -1],
        [-1,  1],
        [ 1, -1],
        [ 1,  1]
    ]
    return pd.DataFrame(data, columns=["N1", "N2"])

def cross_arrays(inner: pd.DataFrame, outer: pd.DataFrame) -> pd.DataFrame:
    """
    Cruza una matriz interna (control) con una externa (ruido) para generar
    el diseño experimental cruzado completo de Taguchi.
    """
    inner_df = inner.copy()
    outer_df = outer.copy()
    inner_df["_key"] = 1
    outer_df["_key"] = 1
    crossed = pd.merge(inner_df, outer_df, on="_key").drop(columns=["_key"])
    return crossed.reset_index(drop=True)

def signal_to_noise(values: Union[np.ndarray, List[float], pd.Series], kind: str, target: Optional[float] = None) -> float:
    """
    Calcula la razón señal/ruido (S/N) en decibelios (dB) para un vector de valores.
    Tipos:
      - "LB" (Larger-is-better / Mayor-es-mejor):
          S/N = -10 * log10( (1/n) * sum(1 / y^2) )
      - "SB" (Smaller-is-better / Menor-es-mejor):
          S/N = -10 * log10( (1/n) * sum(y^2) )
      - "NB" (Nominal-is-best / Nominal-es-mejor):
          Si se provee 'target' (objetivo):
              S/N = -10 * log10( (1/n) * sum((y - target)^2) )
          Si no se provee 'target' (estándar Taguchi):
              S/N = 10 * log10( mean^2 / var )
    """
    y = np.array(values, dtype=float)
    n = len(y)
    if n == 0:
        return 0.0

    kind = kind.upper()
    if kind == "LB":
        # Evitar división por cero
        y_safe = np.where(y == 0, 1e-12, y)
        mean_inv_sq = np.mean(1.0 / (y_safe ** 2))
        return -10.0 * np.log10(mean_inv_sq) if mean_inv_sq > 0 else 0.0

    elif kind == "SB":
        mean_sq = np.mean(y ** 2)
        return -10.0 * np.log10(mean_sq) if mean_sq > 0 else 0.0

    elif kind == "NB":
        if target is not None:
            mse = np.mean((y - target) ** 2)
            return -10.0 * np.log10(mse) if mse > 0 else 50.0 # tope superior si error es cero
        else:
            mean = np.mean(y)
            var = np.var(y, ddof=1)
            if var < 1e-12:
                var = 1e-12
            return 10.0 * np.log10((mean ** 2) / var) if mean != 0 else -50.0

    else:
        raise ValueError(f"Tipo de razón S/N '{kind}' no válido. Use 'LB', 'SB' o 'NB'.")

def response_table(df: pd.DataFrame, factor_cols: List[str], target_col: str) -> pd.DataFrame:
    """
    Calcula los promedios de la columna objetivo (S/N o Media) por cada nivel de cada factor.
    Retorna un DataFrame indexado por los factores de control con las columnas:
      - Nivel 1, Nivel 2, Nivel 3 (o los niveles únicos que tenga el factor en orden ascendente)
      - Delta (Max - Min)
      - Ranking (en orden descendente de Delta)
    """
    records = []
    
    # Determinar el número máximo de niveles entre todos los factores para estructurar las columnas
    max_levels = max(len(df[f].unique()) for f in factor_cols)
    level_headers = [f"Nivel {i+1}" for i in range(max_levels)]
    
    for factor in factor_cols:
        unique_levels = sorted(df[factor].unique())
        means = {}
        for i, val in enumerate(unique_levels):
            mean_val = df[df[factor] == val][target_col].mean()
            means[f"Nivel {i+1}"] = mean_val
        
        # Si un factor tiene menos niveles que el máximo, llenar con NaN
        for i in range(len(unique_levels), max_levels):
            means[f"Nivel {i+1}"] = np.nan
            
        vals = [means[h] for h in level_headers if not np.isnan(means[h])]
        delta = max(vals) - min(vals) if len(vals) > 1 else 0.0
        
        row = {"Factor": factor}
        row.update(means)
        row["Delta"] = delta
        records.append(row)
        
    res_df = pd.DataFrame(records).set_index("Factor")
    
    # Calcular ranking de Delta
    res_df["Ranking"] = res_df["Delta"].rank(ascending=False, method="min").astype(int)
    return res_df

def pareto_anova(df: pd.DataFrame, factor_cols: List[str], target_col: str) -> pd.DataFrame:
    """
    Realiza el Análisis de Varianza (ANOVA) de contribución porcentual de los factores de control
    sobre la respuesta especificada (usualmente la razón S/N).
    Retorna un DataFrame con las columnas: Suma de Cuadrados (SC), grados de libertad (gl),
    Cuadrado Medio (CM), F y Contribución (%).
    """
    grand_mean = df[target_col].mean()
    n_total = len(df)
    ss_total = np.sum((df[target_col] - grand_mean) ** 2)
    df_total = n_total - 1
    
    records = []
    ss_factors_sum = 0.0
    df_factors_sum = 0
    
    for factor in factor_cols:
        unique_levels = df[factor].unique()
        ss_factor = 0.0
        for lvl in unique_levels:
            sub_df = df[df[factor] == lvl][target_col]
            n_lvl = len(sub_df)
            mean_lvl = sub_df.mean()
            ss_factor += n_lvl * ((mean_lvl - grand_mean) ** 2)
            
        gl_factor = len(unique_levels) - 1
        ms_factor = ss_factor / gl_factor if gl_factor > 0 else 0.0
        
        ss_factors_sum += ss_factor
        df_factors_sum += gl_factor
        
        records.append({
            "Source": factor,
            "SC": ss_factor,
            "gl": gl_factor,
            "CM": ms_factor,
            "F": 0.0, # Se calculará luego de obtener el error
            "Contribución (%)": 0.0
        })
        
    # Calcular error residual
    ss_error = max(0.0, ss_total - ss_factors_sum)
    gl_error = max(0, df_total - df_factors_sum)
    ms_error = ss_error / gl_error if gl_error > 0 else 0.0
    
    # Completar F y contribuciones
    for rec in records:
        if ms_error > 0:
            rec["F"] = rec["CM"] / ms_error
        else:
            rec["F"] = np.nan
        rec["Contribución (%)"] = (rec["SC"] / ss_total * 100.0) if ss_total > 0 else 0.0
        
    # Fila de Error
    records.append({
        "Source": "Error Residual",
        "SC": ss_error,
        "gl": gl_error,
        "CM": ms_error,
        "F": np.nan,
        "Contribución (%)": (ss_error / ss_total * 100.0) if ss_total > 0 else 0.0
    })
    
    # Fila Total
    records.append({
        "Source": "Total",
        "SC": ss_total,
        "gl": df_total,
        "CM": np.nan,
        "F": np.nan,
        "Contribución (%)": 100.0
    })
    
    return pd.DataFrame(records).set_index("Source")

def predict_optimal_sn(resp_table: pd.DataFrame, optimal_levels: Dict[str, str], grand_mean: float) -> float:
    """
    Predice el S/N óptimo bajo la hipótesis aditiva de Taguchi.
    optimal_levels: Dict que mapea factor a nivel seleccionado (ej. {"Temperatura": "Nivel 2"})
    """
    sn_pred = grand_mean
    for factor, opt_lvl in optimal_levels.items():
        if factor in resp_table.index:
            mean_opt = resp_table.loc[factor, opt_lvl]
            sn_pred += (mean_opt - grand_mean)
    return sn_pred

def mrsn_index(sn_matrix: pd.DataFrame, weights: Dict[str, float]) -> pd.Series:
    """
    Calcula el Índice de Razón Señal/Ruido Multi-respuesta (MRSN) para optimización simultánea.
    sn_matrix: DataFrame donde cada columna es el vector de S/N de una respuesta (9 filas para L9).
    weights: Diccionario con los pesos de ponderación para cada respuesta.
    """
    normalized_matrix = pd.DataFrame(index=sn_matrix.index)
    total_weight = sum(weights.values())
    
    for col in sn_matrix.columns:
        if col in weights:
            col_min = sn_matrix[col].min()
            col_max = sn_matrix[col].max()
            diff = col_max - col_min
            if diff < 1e-12:
                normalized_matrix[col] = 1.0 # Si no hay variación, normalizar a 1
            else:
                normalized_matrix[col] = (sn_matrix[col] - col_min) / diff
                
    mrsn = pd.Series(0.0, index=sn_matrix.index)
    for col in normalized_matrix.columns:
        if col in weights:
            mrsn += normalized_matrix[col] * (weights[col] / total_weight)
            
    return mrsn
