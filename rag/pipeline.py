"""
rag/pipeline.py — Prompt e Chain RAG
=====================================
Define o prompt de sistema do analista esportivo e constrói o pipeline
LCEL (LangChain Expression Language) de recuperação e geração.
"""

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough


# ── Prompt do analista esportivo ───────────────────────────────────────────────
SYSTEM_PROMPT = """Você é um analista esportivo especialista no Campeonato Brasileiro de Futebol (Série A).
Sua missão é responder perguntas dos torcedores com precisão, clareza e entusiasmo.

VOCÊ TEM ACESSO A DADOS DE DUAS TEMPORADAS:
- Brasileirão Série A 2025: temporada ENCERRADA (dados completos — 38 rodadas, 380 jogos).
- Brasileirão Série A 2026: temporada EM ANDAMENTO (dados parciais — até a rodada 19).

REGRAS FUNDAMENTAIS:
1. Baseie suas respostas EXCLUSIVAMENTE nas informações do CONTEXTO fornecido abaixo.
2. SEMPRE indique de qual temporada (2025 ou 2026) o dado foi retirado.
3. Para dados da temporada 2026, lembre ao torcedor que a temporada ainda está em andamento
   e os dados podem estar desatualizados.
4. Se a informação solicitada NÃO estiver no contexto, diga claramente:
   "Não encontrei essa informação nos dados disponíveis sobre o Brasileirão."
5. NUNCA invente dados, estatísticas, nomes de jogadores ou resultados.
6. Quando apresentar números ou estatísticas, seja preciso e cite os dados exatamente como estão.
7. Responda sempre em Português do Brasil.
8. Use uma linguagem apaixonada pelo futebol, mas mantenha a precisão factual.
9. Quando relevante, organize a resposta em formato estruturado (listas, tabelas em texto).

CONTEXTO RECUPERADO:
{context}

PERGUNTA DO TORCEDOR:
{question}

RESPOSTA DO ANALISTA:"""

PROMPT_TEMPLATE = ChatPromptTemplate.from_template(SYSTEM_PROMPT)


def formatar_contexto(docs: list[Document]) -> str:
    """
    Formata a lista de documentos recuperados em um único bloco de texto
    para inserção no prompt.

    Args:
        docs: Lista de Documents retornados pelo retriever.

    Returns:
        String com todos os trechos concatenados e numerados.
    """
    trechos = []
    for i, doc in enumerate(docs, 1):
        campeonato = doc.metadata.get("Campeonato", "")
        time       = doc.metadata.get("Time", "")
        secao      = doc.metadata.get("Sessao", "")
        
        titulo = " | ".join(filter(None, [campeonato, time, secao])) or "Documento"
        
        trechos.append(
            f"[Trecho {i} | {titulo}]\n{doc.page_content}"
        )
    return "\n\n---\n\n".join(trechos)


def criar_chain_rag(vectorstore: Chroma, llm):
    """
    Constrói o pipeline RAG utilizando LCEL (LangChain Expression Language).

    Fluxo:
      Pergunta → Retriever (busca semântica) → Prompt → LLM → Resposta

    Args:
        vectorstore : Instância do Chroma com os documentos indexados.
        llm         : Instância do LLM configurado.

    Returns:
        Tupla (chain, retriever).
    """
    retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 12, "fetch_k": 30},
    )

    chain = (
        {
            "context" : retriever | formatar_contexto,
            "question": RunnablePassthrough(),
        }
        | PROMPT_TEMPLATE
        | llm
        | StrOutputParser()
    )

    return chain, retriever
