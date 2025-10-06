# ================================================
# 🌐 AI Risk Radar – Streamlit App (Optimized v2)
# ================================================

import os
import re
import random
import json
import io
import streamlit as st
import requests
import pandas as pd
import gspread
from google.oauth2 import service_account
from translations import translations as t

# ⚙️ Configuración de página
st.set_page_config(page_title="AI Risk Radar", layout="wide")

# ==========================
# 🌐 Config idioma
# ==========================
LANGUAGES = {"Español": "es", "English": "en", "Deutsch": "de"}
lang = st.sidebar.selectbox("🌐 Idioma / Language / Sprache", list(LANGUAGES.keys()))
lang_code = LANGUAGES[lang]

# ==========================
# 🔗 Configuración de API
# ==========================
BASE_URL = os.environ.get("API_URL", "http://localhost:10000")
API_URL = f"{BASE_URL}/analyze"

# ==========================
# 📂 Configuración de Google Sheets
# ==========================
SHEET_ID = os.environ.get("SHEET_ID")
GCP_CREDS = os.environ.get("GCP_CREDS")

if GCP_CREDS and SHEET_ID:
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        data = json.loads(GCP_CREDS)
        data["private_key"] = data["private_key"].replace("\\n", "\n")
        creds = service_account.Credentials.from_service_account_info(data, scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SHEET_ID).sheet1
    except Exception as e:
        st.error(f"⚠️ Error al conectar con Google Sheets: {e}")
        sheet = None
else:
    sheet = None

# ==========================
# 🔐 Control de acceso
# ==========================
if "authorized" not in st.session_state:
    st.session_state["authorized"] = False

if "captcha_num1" not in st.session_state:
    st.session_state["captcha_num1"] = random.randint(1, 9)
    st.session_state["captcha_num2"] = random.randint(1, 9)

if not st.session_state["authorized"]:
    st.header("🔐 Acceso a la Demo")
    email = st.text_input("📧 Ingresa tu email")
    reason = st.text_area("📝 ¿Por qué quieres probar AI Risk Radar?")
    captcha_answer = st.number_input(
        f"🔢 Resuelve: {st.session_state['captcha_num1']} + {st.session_state['captcha_num2']} = ?",
        min_value=0, step=1
    )

    if st.button("Enviar"):
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            st.error("❌ Ingresa un email válido.")
        elif captcha_answer != (st.session_state["captcha_num1"] + st.session_state["captcha_num2"]):
            st.error("❌ Captcha incorrecto.")
        elif not reason.strip():
            st.error("❌ Por favor indica una razón de uso.")
        else:
            try:
                if sheet:
                    sheet.append_row([email, reason])
                st.session_state["authorized"] = True
                st.success("✅ Acceso concedido. Ahora puedes usar la demo.")
                st.rerun()
            except Exception as e:
                st.error(f"⚠️ Error al guardar en Google Sheets: {e}")

# ==========================
# 🔄 Función para renderizar tabla combinada
# ==========================
def render_combined_table(df1: pd.DataFrame, df2: pd.DataFrame, title: str, lang_code: str):
    df1 = (df1 or pd.DataFrame()).copy()
    df2 = (df2 or pd.DataFrame()).copy()

    if not df1.empty:
        df1["__type"] = "🔸 Intuitivo"
    if not df2.empty:
        df2["__type"] = "🔹 Contraintuitivo"

    combined = pd.concat([df1, df2], ignore_index=True)
    if combined.empty:
        st.info("No hay datos para mostrar.")
        return

    rename_map = {
        "__type": "🔎 Tipo",
        "risk": "🟠 Riesgo",
        "justification": "📖 Justificación",
        "countermeasure": "🛠️ Contramedida",
        "page": "📑 Página",
        "evidence": "📄 Evidencia",
    }
    combined.rename(columns={k: v for k, v in rename_map.items() if k in combined.columns}, inplace=True)
    ordered = [c for c in ["🔎 Tipo", "🟠 Riesgo", "📖 Justificación", "🛠️ Contramedida", "📑 Página", "📄 Evidencia"] if c in combined.columns]
    combined = combined[ordered]

    st.subheader(title)
    st.markdown("""
    <style>
      table.wraptable { table-layout: fixed; width: 100%; border-collapse: collapse; }
      table.wraptable th, table.wraptable td {
        white-space: normal !important; word-wrap: break-word !important; overflow-wrap: anywhere !important;
        text-align: left; vertical-align: top; padding: 0.5rem;
      }
      table.wraptable thead th { position: sticky; top: 0; background-color: #111; color: #fff; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(combined.to_html(classes="wraptable", index=False, escape=False), unsafe_allow_html=True)

    # 🔽 Descargar como Excel
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        combined.to_excel(writer, index=False, sheet_name="Riesgos")

    st.download_button(
        label=f"⬇️ Descargar {title} (Excel)",
        data=buffer.getvalue(),
        file_name=f"{title.lower().replace(' ', '_')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key=f"xlsx_{title}_{lang_code}"
    )

# ==========================
# 🚀 Aplicación principal
# ==========================
if st.session_state["authorized"]:
    st.title(t["app_title"][lang_code])
    st.markdown(t["file_instruction"][lang_code])

    uploaded_file = st.file_uploader(t["file_label"][lang_code], type=["txt", "pdf", "docx"])
    context = st.text_input(t["context_label"][lang_code], placeholder=t["context_placeholder"][lang_code])

    longdoc_mode = st.checkbox("📖 Procesar como documento largo (chunked)", value=False)

    if st.button(t["analyze_button"][lang_code]):
        if not uploaded_file:
            st.warning(t["no_file_warning"][lang_code])
        else:
            with st.spinner(t["analyzing"][lang_code]):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                data = {"context": context, "lang": lang_code, "longdoc": longdoc_mode}

                try:
                    r = requests.post(API_URL, files=files, data=data, timeout=120)
                    r.raise_for_status()
                    result = r.json()
                    st.success(t["analysis_done"][lang_code])

                    if "intuitive_risks" in result or "counterintuitive_risks" in result:
                        df1 = pd.DataFrame(result.get("intuitive_risks", []))
                        df2 = pd.DataFrame(result.get("counterintuitive_risks", []))
                        render_combined_table(df1, df2, "Riesgos combinados", lang_code)

                    elif "chunks" in result:
                        all_intuitive, all_counter = [], []
                        for chunk in result["chunks"]:
                            all_intuitive.extend(chunk.get("intuitive_risks", []))
                            all_counter.extend(chunk.get("counterintuitive_risks", []))
                        df1 = pd.DataFrame(all_intuitive)
                        df2 = pd.DataFrame(all_counter)
                        render_combined_table(df1, df2, "Riesgos combinados", lang_code)

                    if result.get("source") == "modo simulado (mock)":
                        st.info(t["mock_notice"][lang_code])

                except requests.exceptions.RequestException as e:
                    st.error(t["error"]["network"][lang_code] + f": {e}")
                except Exception as e:
                    st.error(f"{t['error']['default'][lang_code]}: {e}")
