"""
ui/chat.py — Interface de chat e orquestração principal
========================================================
Renderiza as mensagens, o loading screen de inicialização,
o input de perguntas e coordena o fluxo de resposta do RAG.
"""

import streamlit as st
from langchain_core.documents import Document

from config import LLM_PROVIDER
from styles import CUSTOM_CSS
from rag.vectorstore import obter_vectorstore
from rag.llm import obter_llm
from rag.pipeline import criar_chain_rag
from ui.sidebar import renderizar_sidebar


def configurar_pagina() -> None:
    """Configura as opções globais da página Streamlit."""
    st.set_page_config(
        page_title="Brasileirão",
        page_icon="⚽",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def inicializar_estado() -> None:
    """Inicializa as variáveis de estado da sessão Streamlit."""
    if "mensagens" not in st.session_state:
        st.session_state["mensagens"] = []


def renderizar_mensagem(
    role: str,
    content: str,
    fontes: list[Document] | None = None,
) -> None:
    """
    Renderiza uma mensagem de chat com estilo customizado.

    Args:
        role    : 'user' ou 'assistant'.
        content : Texto da mensagem.
        fontes  : Lista de Documents com as fontes (apenas para o assistente).
    """
    if role == "user":
        st.markdown(f"""
        <div class='chat-message-user'>
            <div class='bubble'>{content}</div>
            <div class='avatar avatar-user'>🧑</div>
        </div>
        """, unsafe_allow_html=True)

    else:
        conteudo_html = content.replace("\n", "<br>")
        st.markdown(f"""
        <div class='chat-message-assistant'>
            <div class='avatar avatar-assistant'>⚽</div>
            <div class='bubble'>{conteudo_html}</div>
        </div>
        """, unsafe_allow_html=True)

        if fontes:
            with st.expander("📂 Ver fontes utilizadas"):
                for i, doc in enumerate(fontes, 1):
                    campeonato = doc.metadata.get("Campeonato", "")
                    time       = doc.metadata.get("Time", "")
                    secao      = doc.metadata.get("Sessao", "")
                    
                    titulo = " | ".join(filter(None, [campeonato, time, secao])) or "Trecho do Documento"
                    trecho = doc.page_content[:300] + ("..." if len(doc.page_content) > 300 else "")
                    
                    st.markdown(f"""
                    <div class='source-card'>
                        <div class='source-title'>
                            📋 Fonte {i} — {titulo}
                        </div>
                        <div style='color:#cbd5e0; font-size:0.8rem; margin-top:4px;'>
                            {trecho}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)


def _obter_pipeline():
    """
    Obtém (ou inicializa) o pipeline RAG de forma lazy.
    - Nada é carregado no boot do app, apenas quando o usuário enviar a 1ª pergunta.
    - Nas perguntas subsequentes, tudo é lido do cache do Streamlit (instantâneo).

    Returns:
        Tupla (chain, retriever) prontos para uso.
    """
    # Verifica se já foi inicializado nessa sessão
    ja_inicializado = st.session_state.get("sistema_pronto", False)

    if not ja_inicializado:
        with st.status(
            "⚙️ Inicializando o Assistente Brasileirão...",
            expanded=True,
        ) as status_init:

            st.write("📥 Carregando modelo de embeddings e base de conhecimento...")
            vectorstore = obter_vectorstore()
            st.write("✅ Base de conhecimento pronta!")

            st.write("🤖 Conectando ao modelo de linguagem...")
            llm = obter_llm(st.session_state.get("llm_provider", LLM_PROVIDER))
            st.write("✅ Modelo de IA conectado!")

            st.write("🔗 Montando pipeline de busca e geração...")
            chain, retriever = criar_chain_rag(vectorstore, llm)
            st.write("✅ Pipeline pronto!")

            status_init.update(
                label="✅ Assistente Brasileirão pronto! Pode perguntar.",
                state="complete",
                expanded=False,
            )

        st.session_state["sistema_pronto"]  = True
        st.session_state["_llm_provider"]   = st.session_state.get("llm_provider", LLM_PROVIDER)
        return chain, retriever

    # Nas chamadas seguintes, LLM e chain são recriados leve (sem recarregar embeddings/Chroma)
    vectorstore = obter_vectorstore()
    llm         = obter_llm(st.session_state.get("llm_provider", LLM_PROVIDER))
    chain, retriever = criar_chain_rag(vectorstore, llm)

    if st.session_state.get("_llm_provider") != st.session_state.get("llm_provider", LLM_PROVIDER):
        st.session_state["_llm_provider"] = st.session_state.get("llm_provider", LLM_PROVIDER)

    return chain, retriever


def main() -> None:
    """Função principal — orquestra toda a aplicação Streamlit."""

    configurar_pagina()
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    inicializar_estado()
    renderizar_sidebar()

    # ── Cabeçalho principal ────────────────────────────────────────────────
    provider_atual = st.session_state.get("llm_provider", LLM_PROVIDER)
    provedor_label = (
        "Groq · LLaMA 3.1 Instant"
        if provider_atual == "groq"
        else "Google · Gemini Flash Latest"
    )
    st.markdown(f"""
    <div class='main-header'>
        <h1>⚽ Assistente Brasileirão</h1>
        <p class='subtitle'>
            Tire suas dúvidas sobre o Campeonato Brasileiro com inteligência artificial
        </p>
        <span class='provider-badge'>🤖 {provedor_label}</span>
    </div>
    """, unsafe_allow_html=True)

    # ── Histórico de mensagens ─────────────────────────────────────────────
    for msg in st.session_state["mensagens"]:
        renderizar_mensagem(
            role    = msg["role"],
            content = msg["content"],
            fontes  = msg.get("fontes"),
        )

    # ── Captura de pergunta rápida da sidebar ──────────────────────────────
    pergunta_rapida = st.session_state.pop("pergunta_rapida", None)

    # ── Input de chat (sempre visível, mesmo antes do sistema inicializar) ──
    prompt_usuario = st.chat_input(
        "🎙️ Faça sua pergunta sobre o Brasileirão...",
        key="chat_input",
    )
    pergunta_final = prompt_usuario or pergunta_rapida

    # ── Processamento da pergunta (lazy: sistema inicia aqui na 1ª vez) ────
    if pergunta_final:
        st.session_state["mensagens"].append({
            "role"   : "user",
            "content": pergunta_final,
        })
        renderizar_mensagem("user", pergunta_final)

        try:
            # Pipeline inicializa aqui na 1ª pergunta (lazy loading)
            chain, retriever = _obter_pipeline()
        except FileNotFoundError as e:
            st.error(str(e))
            st.markdown("""
            ### 📁 Como resolver:
            1. Coloque os arquivos **`.md`** na mesma pasta que o `app.py`.
            2. Reinicie o aplicativo com `python -m streamlit run app.py`.
            """)
            st.stop()
        except RuntimeError as e:
            st.error(str(e))
            st.markdown("""
            ### 🔑 Como resolver:
            1. Copie `.env.example` para `.env`.
            2. Preencha sua chave de API no arquivo `.env`.
            3. Reinicie com `python -m streamlit run app.py`.
            """)
            st.stop()
        except Exception as e:
            st.exception(e)
            st.stop()

        with st.spinner("🔍 Analisando os dados do Brasileirão..."):
            try:
                fontes   = retriever.invoke(pergunta_final)
                resposta = chain.invoke(pergunta_final)
            except Exception as e:
                resposta = f"⚠️ Erro ao gerar a resposta: {str(e)}"
                fontes   = []

        st.session_state["mensagens"].append({
            "role"   : "assistant",
            "content": resposta,
            "fontes" : fontes,
        })
        renderizar_mensagem("assistant", resposta, fontes)

        if pergunta_rapida:
            st.rerun()

