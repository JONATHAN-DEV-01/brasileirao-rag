"""
config.py — Configurações centralizadas do Brasileirão RAG
===========================================================
Único ponto de configuração: chaves de API, modelos, caminhos e planilhas.
Para adicionar uma nova temporada, basta incluir uma entrada em EXCEL_FILES.
"""

import os
from dotenv import load_dotenv

# Carrega automaticamente o arquivo .env da pasta raiz do projeto.
# As chaves NÃO estão hardcoded — configure no arquivo .env.
load_dotenv()

# ── Chaves de API ──────────────────────────────────────────────────────────────
GROQ_API_KEY   = os.getenv("GROQ_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Provedor padrão quando nenhum foi selecionado na sessão
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()

# ── Modelos de LLM ─────────────────────────────────────────────────────────────
GROQ_MODEL   = "llama-3.1-8b-instant"   # llama3-8b-8192 foi descontinuado
GOOGLE_MODEL = "gemini-flash-latest"

# ── Embeddings e Vector Store ──────────────────────────────────────────────────
# intfloat/multilingual-e5-small: ~118M params (vs ~560M do large).
# Muito mais leve em RAM/disco, mantendo qualidade de retrieval próxima
# quando o chunking semântico já é bem feito (como o nosso via MarkdownHeader).
EMBEDDING_MODEL = "intfloat/multilingual-e5-small"
CHROMA_DIR      = "./chroma_brasileirao"

# ── Arquivos de Dados (Markdown) ───────────────────────────────────────────────
MARKDOWN_FILES: list[dict] = [
    {
        "arquivo": "rag_brasileirao_2025_enriquecido.md",
        "temporada": "2025",
    },
    {
        "arquivo": "rag_brasileirao_2026_enriquecido.md",
        "temporada": "2026",
    },
]
