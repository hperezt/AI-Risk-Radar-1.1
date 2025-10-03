# app/risk_engine.py

import os
import json
from dotenv import load_dotenv
from openai import OpenAI

# Cargar .env
load_dotenv()

# Inicializar cliente con la clave
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise RuntimeError("OPENAI_API_KEY no está definida en .env ni en el entorno.")

client = OpenAI(api_key=API_KEY)

MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
USE_MOCK = False


def generate_risks(text: str, context: str = "", lang: str = "es") -> dict:
    """
    Genera riesgos a partir de un fragmento de documento usando GPT.
    Devuelve un JSON con dos listas: intuitive_risks y counterintuitive_risks.
    """

    if USE_MOCK:
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

    # Prompt interdisciplinario
    prompt = f"""
Comentario: Este es un ejercicio de análisis asistido por inteligencia artificial. 
El objetivo es evaluar cómo un modelo LLM puede colaborar con expertos humanos para 
identificar riesgos relevantes en proyectos ferroviarios en Alemania. 
La calidad, claridad y solidez del razonamiento es más importante que la cantidad de resultados.

Actúas como un comité interdisciplinario compuesto por:
- Ingenieros especializados en planificación y ejecución de proyectos de infraestructura ferroviaria en Europa.
- Abogados expertos en derecho de infraestructura y normativa aplicable en Alemania.
- Consultores y analistas con experiencia en evaluación de riesgos en el sector ferroviario alemán.

Tu tarea es leer un FRAGMENTO de un documento técnico (no todo el documento completo) 
y detectar riesgos de planificación que puedan generar retrasos, sobrecostos, 
conflictos contractuales o fallas operativas relevantes.

Instrucciones:
- Clasifica los riesgos en dos listas: "intuitive_risks" y "counterintuitive_risks".
- Cada lista puede tener de 0 hasta N riesgos (no inventes ni repitas riesgos genéricos, no limites el número de riesgos).
- Enumera todos los riesgos encontrados en este fragmento. No hay un límite máximo. Si encuentras 1000, devuélvelos todos. No resumas, no agrupes.
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

    # Llamada a la API moderna
    response = client.chat.completions.create(
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
        max_tokens=6000,
    )

    raw_content = response.choices[0].message.content.strip()

    # 🧹 Eliminar backticks o etiquetas de código que rompen el JSON
    if raw_content.startswith("```"):
        raw_content = raw_content.strip("`")
        raw_content = raw_content.replace("json", "", 1).strip()

    try:
        return json.loads(raw_content)
    except Exception as e:
        raise RuntimeError(f"No se pudo parsear JSON: {e}\nRespuesta cruda: {raw_content}")
