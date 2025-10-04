# ================================================
# 🌐 AI Risk Radar – Streamlit App (Optimized)
# ================================================

import os
import re
import random
import json
import streamlit as st
import requests
import pandas as pd
import gspread
from google.oauth2 import service_account
from translations import translations as t

# ⚙️ Configuración de página (debe ir al principio)
st.set_page_config(page_title="AI Risk Radar", layout="centered")

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
# 🔄 Función para renderizar riesgos
# ==========================
def render_risks(df, title, icon, lang_code, mode="expand"):
    """Renderiza riesgos en dos modos: expanders narrativos o tabla analítica"""

    if df.empty:
        return

    st.subheader(f"{icon} {title}")

    if mode == "expand":
        # Vista detallada con expanders
        for _, row in df.iterrows():
            with st.expander(f"{icon} {row.get('risk', 'Riesgo sin título')}"):
                if row.get("page") or row.get("evidence"):
                    st.markdown("**📄 Fuente del riesgo:**")
                if row.get("page"):
                    st.markdown(f"• **Página:** {row['page']}")
                if row.get("evidence"):
                    snippet = row["evidence"][:500]
                    st.markdown(f"• **Fragmento del texto:**\n\n> {snippet}{'...' if len(row['evidence']) > 500 else ''}")
                st.markdown(f"**{t['columns']['justification'][lang_code]}**")
                st.write(row.get("justification", ""))
                st.markdown(f"**{t['columns']['countermeasure'][lang_code]}**")
                st.write(row.get("countermeasure", ""))

    else:
        # Vista tipo tabla amigable, ancho completo y texto con salto de línea
    def render_risks(df, title, icon, lang_code, mode="expand"):
    """Renderiza riesgos en dos modos: expanders narrativos o tabla analítica"""

    if df.empty:
        return

    st.subheader(f"{icon} {title}")

    if mode == "expand":
        # Vista detallada con expanders
        for _, row in df.iterrows():
            with st.expander(f"{icon} {row.get('risk', 'Riesgo sin título')}"):
                if row.get("page") or row.get("evidence"):
                    st.markdown("**📄 Fuente del riesgo:**")
                if row.get("page"):
                    st.markdown(f"• **Página:** {row['page']}")
                if row.get("evidence"):
                    snippet = row["evidence"][:500]
                    st.markdown(f"• **Fragmento del texto:**\n\n> {snippet}{'...' if len(row['evidence']) > 500 else ''}")
                st.markdown(f"**{t['columns']['justification'][lang_code]}**")
                st.write(row.get("justification", ""))
                st.markdown(f"**{t['columns']['countermeasure'][lang_code]}**")
                st.write(row.get("countermeasure", ""))

    else:
        # Vista tipo tabla global con wrapping y ancho máximo
        df_table = df.rename(columns={
            "risk": "🟠 Riesgo",
            "justification": "📖 Justificación",
            "countermeasure": "🛠️ Contramedida",
            "evidence": "📄 Evidencia",
            "page": "📑 Página"
        })

        # Forzar wrapping en celdas largas
        styled = df_table.style.set_table_styles({
            col: [{"selector": "td", "props": "white-space: normal; word-wrap: break-word;"}]
            for col in df_table.columns if col in ["📖 Justificación", "🛠️ Contramedida", "📄 Evidencia"]
        })

        st.dataframe(styled, use_container_width=True, height=400)

        # Botón CSV único por tabla
        csv_data = df_table.to_csv(index=False).encode("utf-8")
        st.download_button(
            label=f"⬇️ Descargar {title} (CSV)",
            data=csv_data,
            file_name=f"{title.lower().replace(' ', '_')}.csv",
            mime="text/csv",
            key=f"csv_{title}_{lang_code}"
        )



# ==========================
# 🚀 Aplicación principal
# ==========================
if st.session_state["authorized"]:
    st.title(t["app_title"][lang_code])
    st.markdown(t["file_instruction"][lang_code])

    uploaded_file = st.file_uploader(t["file_label"][lang_code], type=["txt", "pdf", "docx"])
    context = st.text_input(t["context_label"][lang_code], placeholder=t["context_placeholder"][lang_code])

    # 🔀 Toggle de vista expandida/tabla
    view_mode = st.radio(
        "👁️ Selecciona vista:",
        options=["expand", "table"],
        format_func=lambda x: "Vista expandida" if x == "expand" else "Vista en tabla",
        horizontal=True
    )

    # 🆕 Checkbox para activar modo longdoc
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

                    # 👉 Modo normal → listas de riesgos directas
                    if "intuitive_risks" in result or "counterintuitive_risks" in result:
                        df1 = pd.DataFrame(result.get("intuitive_risks", []))
                        render_risks(df1, t["intuitive_risks"][lang_code], "🔸", lang_code, mode=view_mode)
                        if not df1.empty:
                            csv1 = df1.to_csv(index=False).encode("utf-8")
                            st.download_button(
                                label="⬇️ Descargar riesgos intuitivos (CSV)",
                                data=csv1,
                                file_name="riesgos_intuitivos.csv",
                                mime="text/csv",
                                key="csv_intuitivos_normal"
                            )

                        df2 = pd.DataFrame(result.get("counterintuitive_risks", []))
                        render_risks(df2, t["counterintuitive_risks"][lang_code], "🔹", lang_code, mode=view_mode)
                        if not df2.empty:
                            csv2 = df2.to_csv(index=False).encode("utf-8")
                            st.download_button(
                                label="⬇️ Descargar riesgos contraintuitivos (CSV)",
                                data=csv2,
                                file_name="riesgos_contraintuitivos.csv",
                                mime="text/csv",
                                key="csv_contra_normal"
                            )

                        dbg = result.get("_debug")
                        if dbg:
                            st.caption(f"DEBUG · chars={dbg.get('chars')} · file={dbg.get('filename')}")

                    # 👉 Modo longdoc → procesar todos los chunks en una sola tabla global
                    elif "chunks" in result:
                        all_intuitive = []
                        all_counter = []

                        for chunk in result["chunks"]:
                            all_intuitive.extend(chunk.get("intuitive_risks", []))
                            all_counter.extend(chunk.get("counterintuitive_risks", []))

                        df1 = pd.DataFrame(all_intuitive)
                        df2 = pd.DataFrame(all_counter)

                        render_risks(df1, t["intuitive_risks"][lang_code], "🔸", lang_code, mode=view_mode)
                        render_risks(df2, t["counterintuitive_risks"][lang_code], "🔹", lang_code, mode=view_mode)

                        if not df1.empty:
                            csv1 = df1.to_csv(index=False).encode("utf-8")
                            st.download_button(
                                label="⬇️ Descargar riesgos intuitivos (CSV)",
                                data=csv1,
                                file_name="riesgos_intuitivos.csv",
                                mime="text/csv",
                                key="csv_intuitivos_longdoc"
                            )

                        if not df2.empty:
                            csv2 = df2.to_csv(index=False).encode("utf-8")
                            st.download_button(
                                label="⬇️ Descargar riesgos contraintuitivos (CSV)",
                                data=csv2,
                                file_name="riesgos_contraintuitivos.csv",
                                mime="text/csv",
                                key="csv_contra_longdoc"
                            )

                        if result.get("source") == "modo simulado (mock)":
                            st.info(t["mock_notice"][lang_code])

                except requests.exceptions.RequestException as e:
                    st.error(t["error"]["network"][lang_code] + f": {e}")
                except Exception as e:
                    st.error(f"{t['error']['default'][lang_code]}: {e}")
