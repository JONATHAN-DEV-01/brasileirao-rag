"""
================================================================================
data/loader.py
================================================================================
Módulo responsável por carregar os arquivos Markdown otimizados para RAG
e particioná-los em chunks semânticos usando cabeçalhos.
"""
import os
from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter
from config import MARKDOWN_FILES

def carregar_documentos_markdown(caminho_arquivo: str, temporada: str) -> list[Document]:
    """
    Lê um arquivo Markdown e transforma cada seção em um Document do LangChain,
    utilizando quebras por cabeçalhos (MarkdownHeaderTextSplitter).
    """
    if not os.path.exists(caminho_arquivo):
        raise FileNotFoundError(
            f"Arquivo '{caminho_arquivo}' não encontrado.\n"
            f"Coloque o arquivo Markdown na mesma pasta que o app.py."
        )

    with open(caminho_arquivo, "r", encoding="utf-8") as f:
        content = f.read()

    headers_to_split_on = [
        ("#", "Campeonato"),
        ("##", "Time"),
        ("###", "Sessao"),
    ]
    
    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=False
    )
    
    md_header_splits = markdown_splitter.split_text(content)
    
    documentos = []
    for doc in md_header_splits:
        doc.metadata["temporada"] = temporada
        doc.metadata["fonte"] = caminho_arquivo
        documentos.append(doc)
        
    return documentos


def carregar_todos_arquivos() -> list[Document]:
    """
    Itera sobre todos os arquivos Markdown configurados em config.py
    e retorna uma lista unificada de todos os Documents.
    """
    todos: list[Document] = []

    for cfg in MARKDOWN_FILES:
        arquivo   = cfg["arquivo"]
        temporada = cfg["temporada"]

        if not os.path.exists(arquivo):
            continue

        docs = carregar_documentos_markdown(
            caminho_arquivo=arquivo,
            temporada=temporada,
        )
        todos.extend(docs)

    return todos
