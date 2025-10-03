import logging
import traceback
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse

# 📄 Parsers existentes para PDF, DOCX y TXT
from app.parsers import (
    extract_text_from_pdf,
    extract_text_from_docx,
    extract_text_from_txt,
)

# 🧠 Función que manda texto al modelo (ya existente)
from app.risk_engine import generate_risks

# 🧩 NUEVO: función modular de chunking
from app.utils.chunking import split_into_chunks  
logging.basicConfig(
    level=logging.INFO,  # Cambia a DEBUG si quieres más detalle
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("uvicorn.error")
app = FastAPI(debug=True)

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/")
def root():
    return {"message": "AI Risk Radar API is running"}

@app.post("/analyze")
async def analyze_document(
    file: UploadFile = File(...),
    context: str = Form(""),
    lang: str = Form("es"),
    longdoc: bool = Form(False),  # 🆕 Nuevo flag para activar modo long doc
):
    try:
        filename = (file.filename or "").lower()
        file_bytes = await file.read()

        # -----------------------------------------
        # 1) EXTRACCIÓN DE TEXTO (ya lo tienes)
        # -----------------------------------------
        if filename.endswith(".pdf"):
            text_per_page = extract_text_from_pdf(file_bytes)
            joined_text = "\n---\n".join(
                [f"[Página {p['page']}]\n{p['text']}" for p in text_per_page]
            )
        elif filename.endswith(".docx"):
            joined_text = extract_text_from_docx(file_bytes)
        elif filename.endswith(".txt"):
            joined_text = extract_text_from_txt(file_bytes)
        else:
            return JSONResponse(
                content={
                    "error_code": "unsupported_format",
                    "message": "Formato no soportado (usa .txt, .pdf o .docx)",
                },
                status_code=400,
            )

        if not joined_text or len(joined_text) < 100:
            return JSONResponse(
                content={
                    "error_code": "empty_or_too_short",
                    "message": "El archivo se leyó vacío o muy corto. Revisa el parser o prueba otro archivo.",
                },
                status_code=422,
            )

        # -----------------------------------------
        # 2) ANÁLISIS DE RIESGOS
        # -----------------------------------------

        if longdoc:
            # 🆕 MODO LONG DOC: dividir en chunks de 3000 tokens
            chunks = split_into_chunks(joined_text, max_tokens=3000)

            results = []
            for i, chunk in enumerate(chunks):
                result = generate_risks(chunk, context=context, lang=lang)
                result["_debug"] = {
                    "filename": filename,
                    "chunk_id": i + 1,
                    "chunk_chars": len(chunk),
                }
                results.append(result)

            final_result = {"chunks": results}

        else:
            # 🔁 MODO NORMAL (igual que antes)
            result = generate_risks(joined_text, context=context, lang=lang)
            result["_debug"] = {
                "filename": filename,
                "chars": len(joined_text),
            }
            final_result = result

        # -----------------------------------------
        # 3) RESPUESTA FINAL
        # -----------------------------------------
        return JSONResponse(content=final_result)

    except Exception as e:
        logger.error(f"Error en /analyze: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            content={
                "error_code": "internal_error",
                "message": str(e),
            },
            status_code=500,
        )
