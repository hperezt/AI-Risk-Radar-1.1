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

    # ======================
    # 🌐 Prompt multilingüe
    # ======================
    if lang == "es":
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
- Enumera todos los riesgos encontrados en este fragmento.
- Considera como riesgo lo que afecte TIEMPO, COSTO, EJECUCIÓN, SEGURIDAD o ACEPTACIÓN SOCIAL/REGULATORIA.
- Por cada riesgo incluye:
  - "risk": enunciado breve
  - "justification": explicación clara desde la perspectiva interdisciplinaria
  - "countermeasure": propuesta de mitigación
  - "page": número de página o sección si es posible inferirlo
  - "evidence": extracto textual breve que fundamenta el riesgo
- Ignora encabezados, pies de página, numeración o texto irrelevante como "DB InfraGO AG Seite X".
Solo usa contenido sustantivo.

Texto analizado:
{text[:16000]}

Contexto adicional:
{context}

Devuelve únicamente un JSON válido con exactamente dos listas:
{{
  "intuitive_risks": [...],
  "counterintuitive_risks": [...]
}}
"""
    elif lang == "en":
        prompt = f"""
Comment: This is an AI-assisted analysis exercise.
The goal is to evaluate how an LLM can collaborate with human experts to
identify relevant risks in railway projects in Germany.
Quality, clarity, and sound reasoning are more important than quantity.

You act as an interdisciplinary committee composed of:
- Engineers specialized in planning and execution of railway infrastructure projects in Europe.
- Lawyers specialized in infrastructure law and German regulations.
- Consultants and analysts with experience in risk assessment for railway projects.

Your task is to read a FRAGMENT of a technical document (not the entire document)
and detect planning risks that may cause delays, cost overruns,
contractual conflicts, or operational failures.

Instructions:
- Classify risks into two lists: "intuitive_risks" and "counterintuitive_risks".
- Each list can have 0 to N risks (do not invent or repeat generic risks, do not limit the number).
- Enumerate ALL risks found in this fragment.
- Consider risks that affect TIME, COST, EXECUTION, SAFETY or SOCIAL/REGULATORY ACCEPTANCE.
- For each risk include:
  - "risk": short statement
  - "justification": clear explanation
  - "countermeasure": mitigation proposal
  - "page": page or section number if possible
  - "evidence": short textual excerpt supporting the risk
- Ignore headers, footers, page numbers or irrelevant text such as "DB InfraGO AG Seite X".
Use only substantive content.

Analyzed text:
{text[:16000]}

Additional context:
{context}

Return ONLY a valid JSON with exactly two lists:
{{
  "intuitive_risks": [...],
  "counterintuitive_risks": [...]
}}
"""
    elif lang == "de":
        prompt = f"""
Kommentar: Dies ist eine von KI unterstützte Analyseübung.
Das Ziel ist zu bewerten, wie ein LLM mit menschlichen Experten zusammenarbeiten kann,
um relevante Risiken in Eisenbahninfrastrukturprojekten in Deutschland zu identifizieren.
Qualität, Klarheit und solide Begründung sind wichtiger als Quantität.

Sie agieren als ein interdisziplinäres Komitee bestehend aus:
- Ingenieuren für Planung und Bau von Eisenbahninfrastrukturprojekten in Europa.
- Juristen mit Spezialisierung im Infrastrukturrecht und deutschen Vorschriften.
- Beratern und Analysten mit Erfahrung in der Risikoanalyse von Bahnprojekten.

Ihre Aufgabe ist es, einen FRAGMENT eines technischen Dokuments zu lesen
und Planungsrisiken zu erkennen, die Verzögerungen, Kostensteigerungen,
vertragliche Konflikte oder operative Ausfälle verursachen können.

Anweisungen:
- Klassifizieren Sie die Risiken in zwei Listen: "intuitive_risks" und "counterintuitive_risks".
- Jede Liste kann von 0 bis N Risiken enthalten (erfinden oder wiederholen Sie keine generischen Risiken, begrenzen Sie die Anzahl nicht).
- Zählen Sie ALLE Risiken aus diesem Fragment auf.
- Betrachten Sie Risiken, die ZEIT, KOSTEN, AUSFÜHRUNG, SICHERHEIT oder SOZIALE/REGULATORISCHE AKZEPTANZ betreffen.
- Für jedes Risiko geben Sie an:
  - "risk": kurze Aussage
  - "justification": klare Erklärung
  - "countermeasure": Vorschlag zur Minderung
  - "page": Seiten- oder Abschnittsnummer falls möglich
  - "evidence": kurzer Textauszug zur Begründung
- Ignorieren Sie Kopfzeilen, Fußzeilen, Seitenzahlen oder irrelevanten Text wie "DB InfraGO AG Seite X".
Verwenden Sie nur wesentlichen Inhalt.

Analysierter Text:
{text[:16000]}

Zusätzlicher Kontext:
{context}

Geben Sie NUR ein gültiges JSON mit genau zwei Listen zurück:
{{
  "intuitive_risks": [...],
  "counterintuitive_risks": [...]
}}
"""
    else:
        prompt = f"Language not recognized. Defaulting to Spanish.\n\n{text[:16000]}"

    # ======================
    # 🚀 Llamada a la API
    # ======================
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

    # 🧹 Limpiar JSON si viene envuelto en ```json ... ```
    if raw_content.startswith("```"):
        raw_content = raw_content.strip("`")
        raw_content = raw_content.replace("json", "", 1).strip()

    try:
        return json.loads(raw_content)
    except Exception as e:
        raise RuntimeError(f"No se pudo parsear JSON: {e}\nRespuesta cruda: {raw_content}")
