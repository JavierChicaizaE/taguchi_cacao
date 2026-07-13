# Taguchi · Tostado de Cacao Nacional 🍫

Aplicativo interactivo e independiente para la implementación del **Diseño Robusto de Parámetros de Taguchi** aplicado al tostado de cacao Nacional (Ecuador), desarrollado en Python + Streamlit.

Permite cruzar una matriz interna de factores de control $L_9$ (Temperatura, Tiempo) con una matriz externa de factores de ruido $L_4$ (Humedad Ambiental y Humedad del Lote de Grano), evaluar la Razón Señal/Ruido ($S/N$) por corrida, generar gráficos de efectos, ejecutar el análisis de varianza (Pareto ANOVA), optimizar de forma univariante y multirespuesta (Índice MRSN), y exportar los reportes en Excel.

> ⚠️ **Nota de transparencia:** Este proyecto utiliza conjuntos de datos **sintéticos**, calculados a partir de un modelo físico aproximado del comportamiento térmico del grano de cacao Fino de Aroma (ver `response_model.py` y `generate_data.py`). No sustituye datos de laboratorio.

---

## Estructura del Repositorio

```
taguchi_cacao/
├── app.py                      # Interfaz de usuario (Streamlit)
├── taguchi_core.py             # Motor estadístico (cálculos de S/N, ANOVA, MRSN)
├── response_model.py           # Modelo físico base del grano de cacao
├── generate_data.py            # Generador del dataset sintético (L9 x L4)
├── requirements.txt            # Dependencias del proyecto
├── .streamlit/
│   └── config.toml             # Configuración del tema base de Streamlit
├── data/
│   └── cacao_taguchi_sintetico.csv  # Dataset generado (36 corridas)
└── README.md                   # Documentación y declaración de uso de IA
```

---

## Instalación y Ejecución Local

```bash
# 1. Clonar el repositorio
git clone <URL_DE_TU_REPO>
cd taguchi_cacao

# 2. Crear entorno virtual (recomendado)
python3 -m venv .venv
source .venv/bin/activate        # En Windows: .venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Generar dataset de Taguchi
python generate_data.py

# 5. Ejecutar la aplicación
streamlit run app.py
```

La app se abrirá automáticamente en tu navegador en `http://localhost:8501`.

---

## Despliegue en Streamlit Community Cloud

1. Sube este proyecto a tu repositorio de GitHub (público).
2. Accede a [share.streamlit.io](https://share.streamlit.io) con tu cuenta de GitHub.
3. Haz clic en **"New app"** $\rightarrow$ selecciona tu repositorio, la rama (`main`) y el archivo principal (`app.py`).
4. Haz clic en **"Deploy"**. En 2-3 minutos el aplicativo estará en vivo y listo para compartir.

---

## Factores y Respuestas de Calidad

### Factores de Control (Matriz Interna L9)
- **Temperatura de Tostado (A)**: 120°C, 140°C, 160°C
- **Tiempo de Tostado (B)**: 10 min, 20 min, 30 min

### Factores de Ruido (Matriz Externa L4)
- **Humedad Ambiental (N1)**: Baja (50% HR), Alta (80% HR)
- **Humedad del Grano (N2)**: Baja (5%), Alta (8%)

### Respuestas y Razones S/N:
1.  **Polifenoles totales (mg GAE/g)** — Mayor es mejor (LB)
2.  **Actividad antioxidante DPPH (%)** — Mayor es mejor (LB)
3.  **Índice de pardeamiento (color)** — Nominal es mejor (NB, target = valor central 45.0)
4.  **Puntaje sensorial (1-9)** — Mayor es mejor (LB, peso = 1.5 en optimización multirespuesta)

---

## Declaración de Uso de IA

| Tarea | Uso de IA | Alcance y Verificación |
|---|---|---|
| **Estilización Editorial** | Generación de variables CSS para el tema terroso (cacao) con tipografía serif. | Inspección de legibilidad del texto e integración del modo claro/oscuro. |
| **Separación de Proyecto** | Extracción del simulador físico a `response_model.py` y eliminación de dependencias de RSM. | Pruebas de ejecución de importaciones cruzadas en el motor Taguchi. |
| **Navegación Agrupada** | Programación del sistema jerárquico de selección en la barra lateral. | Validación de reactividad en Streamlit al cambiar de pestañas temáticas. |
