"""
rag/vectorstore.py — Gerenciamento do ChromaDB
===============================================
Cria ou carrega o Vector Store com detecção automática de mudanças nos
arquivos Markdown via fingerprint (tamanho + data de modificação).

Otimizações implementadas:
  - Embeddings carregados UMA única vez e cacheados com @st.cache_resource.
  - Vectorstore separado em função própria e também cacheado.
  - Lazy loading: nenhum componente é inicializado até a primeira chamada.
"""

import os
import shutil

import streamlit as st
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from config import CHROMA_DIR, MARKDOWN_FILES, EMBEDDING_MODEL
from data.loader import carregar_todos_arquivos


# Arquivo interno que armazena o fingerprint da última indexação
_FINGERPRINT_FILE = os.path.join(CHROMA_DIR, ".sources_fingerprint")


def _calcular_fingerprint() -> str:
    """
    Gera uma string única baseada no tamanho e data de modificação
    de cada arquivo Markdown. Se qualquer arquivo for alterado, o fingerprint muda.
    """
    partes = []
    for cfg in MARKDOWN_FILES:
        arq = cfg["arquivo"]
        if os.path.exists(arq):
            stat_info = os.stat(arq)
            partes.append(f"{arq}:{stat_info.st_size}:{stat_info.st_mtime:.0f}")
    return "|".join(sorted(partes))


@st.cache_resource(show_spinner=False)
def _obter_embeddings() -> HuggingFaceEmbeddings:
    """
    Carrega o modelo de embeddings UMA ÚNICA VEZ em toda a sessão do app.
    O @st.cache_resource garante que mesmo com reruns do Streamlit (que
    acontecem a cada clique/interação do usuário), o modelo NÃO é recarregado.

    Trocar de multilingual-e5-large (~560M params) para
    intfloat/multilingual-e5-small (~118M params) reduz o uso de RAM e
    o tempo de cold-start sem impacto perceptível na qualidade de retrieval,
    pois com um bom chunking semântico (MarkdownHeaderTextSplitter) a diferença
    é marginal.
    """
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


@st.cache_resource(show_spinner=False)
def obter_vectorstore() -> Chroma:
    """
    Inicializa (ou carrega do disco) o Vector Store ChromaDB.
    Também é cacheado com @st.cache_resource para não reindexar a
    cada rerun do Streamlit.

    Comportamento inteligente por ambiente:
      - Local       : persiste o índice no disco (CHROMA_DIR). Rereboots são rápidos.
      - Streamlit Cloud : disco efêmero → usa Chroma in-memory. O índice é
                      recriado 1x na inicialização e mantido vivo no cache.

    Returns:
        Instância do Chroma carregada e pronta para consultas.
    """
    embeddings = _obter_embeddings()

    # Detecta se está no Streamlit Cloud (não tem disco persistente)
    is_cloud = os.environ.get("STREAMLIT_SHARING_MODE") or not os.access(".", os.W_OK)

    # ── Modo LOCAL: persiste no disco ──────────────────────────────────────
    if not is_cloud:
        fingerprint_atual = _calcular_fingerprint()
        fingerprint_salvo = ""

        if os.path.exists(_FINGERPRINT_FILE):
            with open(_FINGERPRINT_FILE, "r", encoding="utf-8") as f:
                fingerprint_salvo = f.read().strip()

        indice_existe = (
            os.path.exists(CHROMA_DIR)
            and any(f for f in os.listdir(CHROMA_DIR) if not f.startswith("."))
            if os.path.exists(CHROMA_DIR)
            else False
        )
        indice_atualizado = fingerprint_atual == fingerprint_salvo

        if indice_existe and indice_atualizado:
            return Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)

        if indice_existe and not indice_atualizado:
            st.info("🔄 Bases de Conhecimento (MD) atualizadas — recriando índice...")
            shutil.rmtree(CHROMA_DIR, ignore_errors=True)
        elif not indice_existe:
            st.info("📊 Primeira execução: indexando dados (Markdown)...")

        documentos = carregar_todos_arquivos()
        if not documentos:
            raise ValueError("Nenhum documento foi gerado. Verifique os arquivos .md.")

        vectorstore = Chroma.from_documents(
            documents=documentos,
            embedding=embeddings,
            persist_directory=CHROMA_DIR,
        )

        os.makedirs(CHROMA_DIR, exist_ok=True)
        with open(_FINGERPRINT_FILE, "w", encoding="utf-8") as f:
            f.write(fingerprint_atual)

        return vectorstore

    # ── Modo CLOUD: in-memory (sem disco persistente) ──────────────────────
    st.info("☁️ Modo Cloud: indexando dados em memória...")
    documentos = carregar_todos_arquivos()
    if not documentos:
        raise ValueError("Nenhum documento foi gerado. Verifique os arquivos .md.")

    return Chroma.from_documents(
        documents=documentos,
        embedding=embeddings,
    )

