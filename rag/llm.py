"""
rag/llm.py — Inicialização do modelo de linguagem
==================================================
Instancia o LLM correto (Groq ou Google Gemini) com base no provedor
selecionado na sessão do Streamlit ou configurado no .env.
"""

import streamlit as st
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI

from config import (
    GROQ_API_KEY,
    GOOGLE_API_KEY,
    GROQ_MODEL,
    GOOGLE_MODEL,
    LLM_PROVIDER,
)


def obter_llm(provedor: str | None = None):
    """
    Instancia o LLM com base no provedor solicitado.
    Prioridade: argumento > session_state > variável de ambiente LLM_PROVIDER.

    Args:
        provedor : Identificador do provedor ('groq' ou 'google').
                   Se None, lê de st.session_state['llm_provider'] ou LLM_PROVIDER.

    Returns:
        Instância do LLM configurado.

    Raises:
        EnvironmentError : Se a chave de API necessária não estiver configurada.
        ValueError       : Se o provedor configurado for inválido.
    """
    provider = provedor or st.session_state.get("llm_provider", LLM_PROVIDER)

    if provider == "groq":
        if not GROQ_API_KEY:
            raise RuntimeError(
                "🔑 GROQ_API_KEY não encontrada!\n"
                "Configure a variável no arquivo .env conforme o .env.example."
            )
        return ChatGroq(
            model=GROQ_MODEL,
            api_key=GROQ_API_KEY,
            temperature=0.2,
            max_tokens=1024,
        )

    elif provider == "google":
        if not GOOGLE_API_KEY:
            raise RuntimeError(
                "🔑 GOOGLE_API_KEY não encontrada!\n"
                "Configure a variável no arquivo .env conforme o .env.example."
            )
        return ChatGoogleGenerativeAI(
            model=GOOGLE_MODEL,
            google_api_key=GOOGLE_API_KEY,
            temperature=0.2,
            convert_system_message_to_human=True,
        )

    else:
        raise ValueError(
            f"Provedor '{provider}' inválido. "
            "Use 'groq' ou 'google' no arquivo .env."
        )
