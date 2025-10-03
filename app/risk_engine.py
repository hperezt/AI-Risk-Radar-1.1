def generate_risks(text: str, context: str = "", lang: str = "es") -> dict:
    """
    Genera riesgos a partir del texto de un documento usando GPT.
    Devuelve un JSON con riesgos intuitivos y contraintuitivos.
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
                },
            ],
            "counterintuitive_risks": [
                {
                    "risk": "Exceso de presupuesto por ahorro mal planificado",
                    "justification": "Decisiones apresuradas",
                    "countermeasure": "Revisión independiente",
                    "page": 2,
                    "evidence": "Reportes financieros",
                },
            ],
        }

    # 🧠 Prompt optimizado para long doc con grupo interdisciplinario
    prompt = f"""
Idioma de salida: {lang}

Actúa como un grupo interdisciplinario compuesto por:
- Ingenieros civiles
- Ingenieros ferroviarios
- Abogados especialistas en derecho de infraestructura y transporte
- Expertos en compras y logística

Analiza el siguiente fragmento de un documento de infraestructura.
Identifica todos los riesgos relevantes que aparezcan en este texto, sin límite de cantidad.

Criterios:
- Considera como riesgo lo que afecte TIEMPO, COSTO, EJECUCIÓN, SEGURIDAD o ACEPTACIÓN SOCIAL/REGULATORIA.
- Clasifica en dos listas: "intuitive_risks" y "counterintuitive_risks".
- Cada lista puede tener de 0 hasta N elementos.
- No repitas riesgos genéricos. Analiza únicamente lo que esté en este fragmento.
- Por cada riesgo incluye:
  - "risk": enunciado breve
  - "justification": por qué es un riesgo en este contexto
  - "countermeasure": cómo mitigarlo
  - "page": número de página o sección si se puede inferir
  - "evidence": cita textual breve que lo respalde

Texto analizado:
{text[:16000]}

Contexto adicional (si existe):
{context}

Devuelve únicamente un JSON válido.
"""

    response = openai.ChatCompletion.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": (
                    "Eres un analista de riesgos experto en proyectos de infraestructura. "
                    "Trabajas junto con un equipo interdisciplinario (ingeniería civil, ingeniería ferroviaria, "
                    "abogados, compras y logística) para evaluar riesgos desde múltiples perspectivas."
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
