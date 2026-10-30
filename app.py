from __future__ import annotations

from io import BytesIO

import PyPDF2
import streamlit as st

import pedro

st.set_page_config(
    page_title="Analisador de Artigos com Escala PEDro",
    page_icon="🔬",
    layout="wide",
)


def extract_text_from_pdf(pdf_file):
    """Extrai texto de um arquivo PDF carregado."""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text
        return text[:28000]
    except Exception as exc:
        st.error(f"Erro ao ler o arquivo PDF: {exc}")
        return None


def sidebar_api_key() -> str:
    """Password field value. Streamlit stores it only in st.session_state."""
    raw = st.session_state.get("gemini_api_key", "")
    if isinstance(raw, str):
        return raw.strip()
    return ""


def secret_api_key() -> str:
    """Read st.secrets['GEMINI_API_KEY'] when a secrets file exists.

    Missing secrets are ignored. The value is not written to the session,
    the page, or the application log.
    """
    try:
        if not st.secrets.load_if_toml_exists():
            return ""
        if "GEMINI_API_KEY" not in st.secrets:
            return ""
        value = st.secrets["GEMINI_API_KEY"]
    except Exception:
        return ""
    if not isinstance(value, str):
        return ""
    return value.strip()


def resolve_api_key() -> str:
    typed = sidebar_api_key()
    if typed:
        return typed
    return secret_api_key()


st.title("🔬 Analisador de Artigos Científicos (PEDro)")
st.markdown(
    "Faça o upload de um artigo em PDF para analisá-lo com a **Escala PEDro** "
    "usando a IA do Google Gemini. Sem chave, dá para ver uma amostra já calculada."
)

st.sidebar.header("Configurações")
st.sidebar.markdown(
    """
Para analisar um PDF seu, use uma chave gratuita do Google AI Studio.
1. Acesse [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Clique em "Create API key"
3. Cole a chave abaixo. Ela fica só nesta sessão do navegador.

No Streamlit Cloud, a mesma chave pode estar em `GEMINI_API_KEY` nos segredos do app.
"""
)
st.sidebar.text_input(
    "🔑 Chave de API do Google AI Studio",
    type="password",
    key="gemini_api_key",
    help="A chave digitada fica apenas em st.session_state desta sessão.",
)

if sidebar_api_key():
    st.sidebar.caption("Chave desta sessão pronta para a análise.")
elif secret_api_key():
    st.sidebar.caption("Usando a chave GEMINI_API_KEY dos segredos do app.")
else:
    st.sidebar.caption("Nenhuma chave carregada. A amostra abre sem chave.")

uploaded_file = st.sidebar.file_uploader("📄 Escolha o arquivo PDF", type="pdf")
analyze_button = st.sidebar.button("Analisar Artigo", use_container_width=True)
sample_button = st.sidebar.button("Testar com uma amostra", use_container_width=True)
pdf_bytes = pedro.SAMPLE_PDF_PATH.read_bytes()
st.sidebar.download_button(
    label="Baixar PDF da amostra",
    data=pdf_bytes,
    file_name=pedro.SAMPLE_PDF_PATH.name,
    mime="application/pdf",
    use_container_width=True,
)

st.markdown("---")
if sample_button:
    st.info(
        "Resultado de exemplo já calculado, sem chamada à API e sem chave. "
        "Os 11 critérios PEDro estão abaixo."
    )
    st.markdown(pedro.render_sample_markdown())
    st.caption(
        "Amostra: McCaskey et al., 2018, PLoS ONE 13(3):e0193358 "
        "(https://doi.org/10.1371/journal.pone.0193358). "
        "Licença Creative Commons Attribution (CC BY 4.0). "
        "O PDF está no repositório em samples/mccaskey2018_sensorimotor_rct.pdf."
    )
elif analyze_button and uploaded_file and resolve_api_key():
    with st.spinner("Extraindo texto do PDF..."):
        pdf_stream = BytesIO(uploaded_file.getvalue())
        article_text = extract_text_from_pdf(pdf_stream)

    if article_text:
        st.success("Texto extraído com sucesso! ✅")
        with st.spinner(
            "A IA do Google está analisando o artigo... Isso pode levar um momento."
        ):
            outcome = pedro.analyze_article(article_text, resolve_api_key())

        if outcome.text:
            st.markdown("## Resultado da Análise")
            st.markdown(outcome.text, unsafe_allow_html=True)
        else:
            st.error(outcome.error or "A análise não pôde ser concluída.")
elif analyze_button:
    st.warning(
        "Para analisar um artigo seu, envie um PDF e informe a chave de API. "
        "A amostra não precisa de chave."
    )
else:
    st.info(
        "Aguardando o upload do arquivo e a chave de API para iniciar a análise. "
        "Use Testar com uma amostra para ver os 11 critérios sem chave."
    )
