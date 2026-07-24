"""
================================================================================
app.py — Brasileirão RAG  |  Ponto de entrada da aplicação
================================================================================
Descrição : Sistema RAG (Retrieval-Augmented Generation) que responde perguntas
            sobre o Campeonato Brasileiro utilizando LangChain, ChromaDB,
            HuggingFace Embeddings e LLM via Groq ou Google Gemini.

Estrutura do projeto:
  config.py          → Configurações centralizadas (chaves, modelos, planilhas)
  styles.py          → CSS customizado (paleta de cores, componentes visuais)
  data/loader.py     → Carregamento e transformação das planilhas Excel
  rag/vectorstore.py → ChromaDB com detecção automática de atualizações
  rag/llm.py         → Inicialização do LLM (Groq / Google Gemini)
  rag/pipeline.py    → Prompt de sistema e chain RAG (LCEL)
  ui/sidebar.py      → Painel lateral (seletor de modelo, sugestões, controles)
  ui/chat.py         → Interface de chat, loading screen e orquestração

CONFIGURAÇÃO INICIAL:
  1. Copie .env.example → .env e preencha suas chaves de API.
  2. Coloque os arquivos .xlsx na mesma pasta que este app.py.
  3. Instale as dependências: pip install -r requirements.txt
  4. Execute: python -m streamlit run app.py
================================================================================
"""

from ui.chat import main

if __name__ == "__main__":
    main()
