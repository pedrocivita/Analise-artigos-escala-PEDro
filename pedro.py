"""PEDro scoring helpers for the Streamlit app.

The Gemini call uses the supported generateContent REST method. This project
does not depend on the retired google-generativeai package. The API key is
passed only in the x-goog-api-key header, never in the URL or the JSON body.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
SAMPLE_DIR = ROOT / "samples"
SAMPLE_PDF_PATH = SAMPLE_DIR / "mccaskey2018_sensorimotor_rct.pdf"
SAMPLE_RESULT_PATH = SAMPLE_DIR / "mccaskey2018_pedro.json"

# Stable Flash model for new projects (Google model list, October 2026).
# gemini-1.5-flash-latest was shut down with Gemini 1.5 on 29 September 2025.
GEMINI_MODEL = "gemini-3.8-flash"
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)
REQUEST_TIMEOUT_SECONDS = 120


@dataclass(frozen=True)
class AnalysisResult:
    text: str | None
    error: str | None


def gemini_headers(api_key: str) -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key,
    }


def build_prompt(article_text: str) -> str:
    return f"""
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
    {article_text}
    """


def gemini_payload(article_text: str) -> dict:
    return {
        "contents": [{"parts": [{"text": build_prompt(article_text)}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 8192,
            "thinkingConfig": {"thinkingLevel": "low"},
        },
    }


def candidate_text(result: dict) -> str | None:
    candidates = result.get("candidates") or []
    if not candidates:
        return None
    content = candidates[0].get("content") or {}
    parts = content.get("parts") or []
    chunks: list[str] = []
    for part in parts:
        if part.get("thought"):
            continue
        text = part.get("text")
        if isinstance(text, str) and text.strip():
            chunks.append(text)
    if not chunks:
        return None
    return "\n".join(chunks)


def analyze_article(article_text: str, api_key: str) -> AnalysisResult:
    """Call Gemini. Returned errors are safe to show: they omit the key and the body."""
    if not api_key:
        return AnalysisResult(
            text=None,
            error=(
                "Chave de API do Google AI Studio não fornecida. "
                "Informe a chave na barra lateral ou configure GEMINI_API_KEY nos segredos do app."
            ),
        )

    try:
        response = requests.post(
            GEMINI_URL,
            headers=gemini_headers(api_key),
            json=gemini_payload(article_text),
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except requests.HTTPError as exc:
        status = None
        error_response = getattr(exc, "response", None)
        if error_response is not None:
            status = getattr(error_response, "status_code", None)
        if status is None:
            message = "Erro HTTP ao contatar a API do Gemini."
        else:
            message = f"Erro HTTP ao contatar a API do Gemini (status {status})."
        return AnalysisResult(text=None, error=message)
    except requests.RequestException:
        return AnalysisResult(
            text=None,
            error="Não foi possível contatar a API do Gemini.",
        )

    try:
        payload = response.json()
    except ValueError:
        return AnalysisResult(
            text=None,
            error="A API do Gemini devolveu uma resposta inválida.",
        )

    if not isinstance(payload, dict):
        return AnalysisResult(
            text=None,
            error="A API do Gemini devolveu uma resposta inválida.",
        )

    text = candidate_text(payload)
    if not text:
        return AnalysisResult(
            text=None,
            error="A API do Gemini não devolveu texto de análise.",
        )
    return AnalysisResult(text=text, error=None)


def load_sample_result() -> dict:
    with SAMPLE_RESULT_PATH.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Sample PEDro file must be a JSON object.")
    return data


def scored_total(sample: dict) -> int:
    total = 0
    for item in sample["criteria"]:
        if item.get("scored") and item.get("answer") == "Sim":
            total += 1
    return total


def reliability_label(score: int) -> str:
    if score <= 3:
        return "Baixa"
    if score <= 6:
        return "Moderada"
    return "Alta"


def render_sample_markdown(sample: dict | None = None) -> str:
    data = sample if sample is not None else load_sample_result()
    criteria = data["criteria"]
    if len(criteria) != 11:
        raise ValueError("The sample result must contain 11 PEDro criteria.")
    score = scored_total(data)
    lines = ["## Análise pela Escala PEDro", ""]
    for item in criteria:
        number = item["number"]
        name = item["name"]
        answer = item["answer"]
        justification = item["justification"]
        lines.append(f"**{number}. {name}:** {answer} - *{justification}*")
        lines.append("")
    lines.extend(
        [
            "---",
            "",
            f"### Pontuação Final PEDro: {score}/10",
            "",
            f"### Nível de Confiabilidade: {reliability_label(score)}",
            "",
            "**Resumo da Análise:**",
            data["summary"],
            "",
        ]
    )
    return "\n".join(lines)
