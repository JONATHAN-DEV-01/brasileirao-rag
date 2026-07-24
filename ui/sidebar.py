"""
ui/sidebar.py — Painel lateral do Brasileirão RAG
==================================================
Renderiza o seletor de modelo de IA, a lista de planilhas em uso,
as sugestões de perguntas e o botão de limpar conversa.
"""

import os

import streamlit as st

from config import MARKDOWN_FILES, LLM_PROVIDER


def renderizar_sidebar() -> None:
    """Renderiza o painel lateral com informações e controles."""
    with st.sidebar:
        # ── Identidade visual ──────────────────────────────────────────────
        st.markdown("""
        <div style='text-align:center; padding: 12px 0 20px 0;'>
            <div style='font-size:3rem;'>⚽</div>
            <h2 style='color:#f8ae39; margin:8px 0 4px 0; font-size:1.1rem;'>
                Brasileirão
            </h2>
            <p style='color:#a0aec0; font-size:0.8rem; margin:0;'>
                Assistente Brasileirão
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        # ── Seletor de modelo de IA ────────────────────────────────────────
        st.markdown("### ⚙️ Configuração")

        opcoes_modelo = {
            "🚀 Groq — LLaMA 3.1 Instant": "groq",
            "🌐 Google Gemini 1.5 Flash"  : "google",
        }

        provedor_atual = st.session_state.get("llm_provider", LLM_PROVIDER)
        idx_inicial = (
            list(opcoes_modelo.values()).index(provedor_atual)
            if provedor_atual in opcoes_modelo.values()
            else 0
        )

        modelo_selecionado = st.selectbox(
            "Modelo de IA",
            options=list(opcoes_modelo.keys()),
            index=idx_inicial,
            key="selectbox_modelo",
        )
        provedor_escolhido = opcoes_modelo[modelo_selecionado]

        if st.session_state.get("llm_provider") != provedor_escolhido:
            st.session_state["llm_provider"] = provedor_escolhido

        # ── Fontes de Conhecimento (Markdown) ──────────────────────────────
        st.markdown("""
        <p style='color:#a0aec0; font-size:0.75rem; margin: 10px 0 6px 0;
                  text-transform:uppercase; letter-spacing:0.5px; font-weight:600;'>
            📂 Base de Conhecimento (MD)
        </p>
        """, unsafe_allow_html=True)

        arquivos_presentes = [cfg for cfg in MARKDOWN_FILES if os.path.exists(cfg["arquivo"])]
        for cfg in arquivos_presentes:
            st.markdown(f"""
            <div class='source-card' style='margin:0 0 6px 0; padding:7px 12px;'>
                <div class='source-title' style='font-size:0.78rem;'>
                    📄 {cfg['arquivo']}
                </div>
                <div style='color:#a0aec0; font-size:0.70rem; margin-top:2px;'>
                    Temporada {cfg['temporada']}
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.divider()

        # ── Sugestões de perguntas ─────────────────────────────────────────
        st.markdown("### 💡 Sugestões de perguntas")

        perguntas_exemplo = [
            "Qual time lidera o Brasileirão 2026?",
            "Quem é o artilheiro do Brasileirão?",
            "Quantos gols o Flamengo fez em 2025?",
            "Qual foi o resultado Botafogo x Cruzeiro em 2026?",
            "Quais times estão na zona de rebaixamento?",
        ]

        for pergunta in perguntas_exemplo:
            if st.button(pergunta, use_container_width=True, key=f"btn_{hash(pergunta)}"):
                st.session_state["pergunta_rapida"] = pergunta

        st.divider()

        # ── Limpar histórico ───────────────────────────────────────────────
        if st.button("🗑️ Limpar conversa", use_container_width=True):
            st.session_state["mensagens"] = []
            st.session_state.pop("pergunta_rapida", None)
            st.rerun()

        st.divider()

        st.markdown("""
        <p style='color:#6b7280; font-size:0.72rem; text-align:center; margin:0;'>
            Powered by LangChain + ChromaDB
        </p>
        """, unsafe_allow_html=True)
