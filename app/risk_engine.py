# app/risk_engine.py

import os
import json
import openai
from dotenv import load_dotenv

# ------------------------------------------------
# Cargar variables de entorno (.env en local, Render en producción)
# ------------------------------------------------
load_dotenv()

# Configuración de modelo y API
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")   # Modelo por defecto si no está definido
API_KEY = os.getenv("OPENAI_API_KEY")                 # Clave de OpenAI
USE_MOCK = False                                      # Modo simulado para pruebas offline

if not API_KEY:
    raise RuntimeError("OPENAI_API_KEY no está definida. Añádela en .env o en Render > Environment")

# Configurar API Key (cliente viejo <=0.28.0)
openai.api_key = API_KEY


def generate_risks(text: str, context: str = "", lang: str = "es") -> dict:
    """
    Genera riesgos a partir de un fragmento de documento usando GPT.
    Devuelve un JSON con dos listas: intuitive_risks y counterintuitive_risks.
    """

    if USE_MOCK:
        # 🔄 Modo simulado para pruebas locales
        return {
            "intuitive_risks": [
                {
                    "risk": "Retraso por clima",
                    "justification": "Condiciones adversas",
                    "countermeasure": "Plan de contingencia",
                    "page": 1,
                    "evidence": "Clima en zona de obra",
                }
            ],
            "counterintuitive_risks": [
                {
                    "risk": "Exceso de presupuesto por ahorro mal planificado",
                    "justification": "Decisiones apresuradas",
                    "countermeasure": "Revisión independiente",
                    "page": 2,
                    "evidence": "Reportes financieros",
                }
            ],
        }

    # 🧠 Prompt interdisciplinario optimizado para long doc
    prompt = f"""
Comentario: Este es un ejercicio de análisis asistido por inteligencia artificial. 
El objetivo es evaluar cómo un modelo LLM puede colaborar con expertos humanos para 
identificar riesgos relevantes en proyectos ferroviarios en Alemania. 
La calidad, claridad y solidez del razonamiento es más importante que la cantidad de resultados.

Actúas como un comité interdisciplinario compuesto por:
- Ingenieros especializados en planificación y ejecución de proyectos de infraestructura ferroviaria en Europa.
- Abogados expertos en derecho de infraestructura y normativa aplicable en Alemania.
- Consultores y analistas con experiencia en evaluación de riesgos en el sector ferroviario alemán.

Piensa como si estos perfiles discutieran en conjunto cada riesgo y llegaran a un consenso argumentado.

Tu tarea es leer un FRAGMENTO de un documento técnico (no todo el documento completo) 
y detectar riesgos de planificación que puedan generar retrasos, sobrecostos, 
conflictos contractuales o fallas operativas relevantes.

Instrucciones:
- Clasifica los riesgos en dos listas: "intuitive_risks" y "counterintuitive_risks".
- Cada lista puede tener de 0 hasta N riesgos (no inventes ni repitas riesgos genéricos).
- Considera como riesgo lo que afecte TIEMPO, COSTO, EJECUCIÓN, SEGURIDAD o ACEPTACIÓN SOCIAL/REGULATORIA.
- Por cada riesgo incluye:
  - "risk": enunciado breve
  - "justification": explicación clara desde la perspectiva interdisciplinaria
  - "countermeasure": propuesta de mitigación
  - "page": número de página o sección si es posible inferirlo
  - "evidence": extracto textual breve que fundamenta el riesgo

Texto analizado:
{text[:16000]}

Contexto adicional (si existe):
{context}

Devuelve únicamente un JSON válido con exactamente dos listas:
{{
  "intuitive_risks": [...],
  "counterintuitive_risks": [...]
}}
"""

    response = openai.ChatCompletion.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": (
                    "Eres un comité interdisciplinario de expertos (ingeniería civil y ferroviaria, "
                    "abogados en normativa alemana, compras y logística) que analiza riesgos en proyectos de infraestructura."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=2000,
    )

    try:
        data = json.loads(response["choices"][0]["message"]["content"])
    except Exception as e:
        raise RuntimeError(f"No se pudo parsear JSON: {e}")

    return data

