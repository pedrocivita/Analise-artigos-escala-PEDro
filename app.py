import streamlit as st
import PyPDF2
import requests
import json
from io import BytesIO

# --- Configuração da Página ---
st.set_page_config(
    page_title="Analisador de Artigos com Escala PEDro",
    page_icon="🔬",
    layout="wide"
)

# --- Funções Core ---

def extract_text_from_pdf(pdf_file):
    """Extrai texto de um arquivo PDF carregado."""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text
        # Limita o texto para evitar exceder limites da API
        return text[:28000]
    except Exception as e:
        st.error(f"Erro ao ler o arquivo PDF: {e}")
        return None

def analyze_with_gemini(text, api_key):
    """Envia o texto para a API do Gemini (Google AI) para análise."""
    if not api_key:
        st.error("Chave de API do Google AI Studio não fornecida. Por favor, insira sua chave.")
        return None

    # URL da API do Gemini. Usando um modelo flash que é rápido e eficiente.
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={api_key}"
    
    # O prompt detalhado instrui a IA sobre a tarefa.
    prompt = f"""
    **Tarefa:** Você é um pesquisador especialista em fisioterapia e dermatologia estética com profundo conhecimento em análise de ensaios clínicos. Sua missão é avaliar a qualidade metodológica do artigo científico fornecido usando a escala PEDro.

    **Escala PEDro (Critérios):**
    1.  **Critério de elegibilidade:** Os critérios de elegibilidade foram especificados? (Não pontua)
    2.  **Alocação aleatória:** Os sujeitos foram alocados aleatoriamente nos grupos?
    3.  **Alocação sigilosa:** A alocação foi sigilosa?
    4.  **Semelhança na linha de base:** Os grupos eram semelhantes no início do estudo em relação aos indicadores prognósticos mais importantes?
    5.  **Cegamento dos sujeitos:** Houve cegamento de todos os sujeitos?
    6.  **Cegamento dos terapeutas:** Houve cegamento de todos os terapeutas que administraram a terapia?
    7.  **Cegamento dos avaliadores:** Houve cegamento de todos os avaliadores que mediram pelo menos um desfecho chave?
    8.  **Acompanhamento adequado:** As medidas de pelo menos um desfecho chave foram obtidas de mais de 85% dos sujeitos inicialmente alocados nos grupos?
    9.  **Análise por intenção de tratar:** Todos os sujeitos para os quais os desfechos estavam disponíveis receberam tratamento ou condição de controle conforme alocado, ou, quando não, os dados para análise foram analisados por "intenção de tratar"?
    10. **Comparações entre grupos:** Os resultados das comparações estatísticas entre os grupos são relatados para pelo menos um desfecho chave?
    11. **Medidas de ponto e variabilidade:** O estudo fornece tanto medidas de ponto quanto medidas de variabilidade para pelo menos um desfecho chave?

    **Instruções de Análise:**
    1.  Leia e analise o texto completo do artigo abaixo.
    2.  Para cada critério de 2 a 11, responda com "Sim" (1 ponto) ou "Não" (0 pontos). Se a informação não estiver clara ou presente no texto, considere como "Não".
    3.  Para cada resposta, forneça uma breve justificativa baseada em trechos do artigo, se possível.
    4.  Some os pontos dos critérios 2 a 11 para obter a pontuação final da escala PEDro (de 0 a 10).
    5.  Com base na pontuação, classifique a confiabilidade do estudo:
        - **0-3: Baixa confiabilidade**
        - **4-6: Moderada confiabilidade**
        - **7-10: Alta confiabilidade**
    6.  Apresente um resumo final conciso sobre a validade do estudo e sua aplicabilidade clínica.

    **Formato da Resposta (use Markdown):**
    ```markdown
    ## Análise pela Escala PEDro

    **1. Critérios de elegibilidade:** [Sim/Não] - *Justificativa...*
    **2. Alocação aleatória:** [Sim/Não] - *Justificativa...*
    ...
    **11. Medidas de ponto e variabilidade:** [Sim/Não] - *Justificativa...*

    ---

    ### Pontuação Final PEDro: X/10

    ### Nível de Confiabilidade: [Alta/Moderada/Baixa]

    **Resumo da Análise:**
    *...*
    ```

    **Texto do Artigo para Análise:**
    ---
    {text}
    """
    
    # Corpo da requisição
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()  # Lança um erro para respostas HTTP ruins (4xx ou 5xx)
        
        result = response.json()
        # Extrai o conteúdo de texto da resposta da API
        return result['candidates'][0]['content']['parts'][0]['text']
        
    except requests.exceptions.HTTPError as http_err:
        st.error(f"Erro HTTP ao contatar a API do Gemini: {http_err}")
        st.error(f"Resposta da API: {response.text}")
        return None
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado: {e}")
        return None

# --- Interface do Usuário (Streamlit) ---

st.title("🔬 Analisador de Artigos Científicos (PEDro)")
st.markdown("Faça o upload de um artigo em PDF para analisá-lo com a **Escala PEDro** usando a IA do Google Gemini.")

# Coluna para inputs
st.sidebar.header("Configurações")
st.sidebar.markdown("""
Para usar o app, você precisa de uma chave de API gratuita do Google AI Studio.
1. Acesse [makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)
2. Clique em "Create API key"
3. Copie e cole a chave abaixo.
""")
api_key = st.sidebar.text_input("🔑 Chave de API do Google AI Studio", type="password")
uploaded_file = st.sidebar.file_uploader("📄 Escolha o arquivo PDF", type="pdf")
analyze_button = st.sidebar.button("Analisar Artigo", use_container_width=True)

# Área de exibição principal
st.markdown("---")
if analyze_button and uploaded_file and api_key:
    with st.spinner("Extraindo texto do PDF..."):
        pdf_bytes = BytesIO(uploaded_file.getvalue())
        article_text = extract_text_from_pdf(pdf_bytes)

    if article_text:
        st.success("Texto extraído com sucesso! ✅")
        with st.spinner("A IA do Google está analisando o artigo... Isso pode levar um momento."):
            analysis_result = analyze_with_gemini(article_text, api_key)
        
        if analysis_result:
            st.markdown("## Resultado da Análise")
            st.markdown(analysis_result, unsafe_allow_html=True)
        else:
            st.warning("A análise não pôde ser concluída. Verifique sua chave de API e o console para erros.")
elif analyze_button:
    st.warning("Por favor, faça o upload de um arquivo PDF e insira sua chave de API do Google AI Studio.")
else:
    st.info("Aguardando o upload do arquivo e a chave de API para iniciar a análise.")