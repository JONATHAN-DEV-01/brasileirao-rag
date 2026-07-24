"""
extrator.py — Extrator FBref Brasileirão Série A
==================================================
Extrai tabelas estatísticas do FBref, trata os dados e persiste
em um banco de dados relacional (PostgreSQL ou MySQL) via SQLAlchemy.

Uso:
    python extrator.py [--ano 2025] [--modo completo|basico] [--sem-db]

Modos:
    basico    → Apenas a tabela de classificação (1 requisição)
    completo  → Classificação + todas as tabelas de estatísticas de equipe
                + varredura dos links individuais dos times (mais demorado)
"""

import argparse
import logging
import time
from io import StringIO
from typing import Optional

import pandas as pd
import requests
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from config import (
    DB_URL,
    FBREF_URL,
    HTTP_HEADERS,
    REQUEST_DELAY,
    TEMPORADA,
)

# ── Logger ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Camada de Requisição HTTP
# ─────────────────────────────────────────────────────────────────────────────

def _get_session() -> requests.Session:
    """Cria uma Session requests com headers realistas reutilizável."""
    session = requests.Session()
    session.headers.update(HTTP_HEADERS)
    return session


def _fetch_html(url: str, session: requests.Session, delay: int = REQUEST_DELAY) -> str:
    """
    Busca o HTML de uma URL com:
      - Headers de navegador para evitar bloqueio por User-Agent.
      - Pausa obrigatória ANTES da requisição para respeitar o rate limit do FBref.
      - Sanitização dos comentários HTML (<!-- -->) que encapsulam tabelas avançadas.

    Args:
        url     : URL a ser acessada.
        session : Session requests configurada com headers.
        delay   : Segundos de pausa antes da requisição.

    Returns:
        HTML da página com comentários removidos (pronto para pd.read_html).
    """
    log.info(f"Aguardando {delay}s antes de acessar: {url}")
    time.sleep(delay)

    response = session.get(url, timeout=30)
    response.raise_for_status()

    # ⚠️  FBref encapsula tabelas avançadas em comentários HTML.
    # Remover os delimitadores expõe essas tabelas para o parser.
    html_sanitizado = response.text.replace("<!--", "").replace("-->", "")
    return html_sanitizado


# ─────────────────────────────────────────────────────────────────────────────
# Tratamento de DataFrames
# ─────────────────────────────────────────────────────────────────────────────

def _flatten_multiindex(df: pd.DataFrame) -> pd.DataFrame:
    """
    Achata (flatten) colunas com MultiIndex geradas pelo pd.read_html quando
    a tabela HTML tem cabeçalhos em dois níveis (grupo + coluna).

    Exemplo:
        ('Unnamed: 0_level_0', 'Squad') → 'Squad'
        ('Performance', 'Gls')          → 'Performance_Gls'

    Args:
        df: DataFrame possivelmente com MultiIndex nas colunas.

    Returns:
        DataFrame com colunas simples (strings).
    """
    if isinstance(df.columns, pd.MultiIndex):
        colunas = []
        for nivel_superior, nivel_inferior in df.columns:
            # Ignora o nível superior se for gerado automaticamente pelo pandas
            if "Unnamed" in str(nivel_superior) or nivel_superior == nivel_inferior:
                colunas.append(str(nivel_inferior))
            else:
                colunas.append(f"{nivel_superior}_{nivel_inferior}")
        df.columns = colunas
    return df


def _limpar_dataframe(df: pd.DataFrame, temporada: str) -> pd.DataFrame:
    """
    Aplica limpeza geral a um DataFrame extraído do FBref:
      - Remove linhas de subtotal/cabeçalho repetido ('Squad' == 'Squad').
      - Remove a coluna de rk/notas se presente.
      - Adiciona a coluna 'temporada' para rastreabilidade.
      - Converte colunas numéricas para float onde possível.
      - Reseta o índice.

    Args:
        df        : DataFrame bruto do FBref.
        temporada : Ano da temporada (ex: '2025').

    Returns:
        DataFrame limpo e enriquecido com a coluna 'temporada'.
    """
    # Remove linhas de cabeçalho repetido que o FBref insere a cada 25 times
    if "Squad" in df.columns:
        df = df[df["Squad"] != "Squad"].copy()

    # Remove coluna de notas se existir
    for col_lixo in ["Notes", "Matches", "Rk"]:
        if col_lixo in df.columns:
            df.drop(columns=[col_lixo], inplace=True, errors="ignore")

    # Adiciona coluna de temporada para rastreabilidade no banco
    df["temporada"] = temporada

    # Tenta converter tudo que parece número para float
    for col in df.columns:
        if col not in ("Squad", "temporada", "Nation", "Pos", "Age", "Comp"):
            df[col] = pd.to_numeric(df[col], errors="ignore")

    df.reset_index(drop=True, inplace=True)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# Extratores por Tabela
# ─────────────────────────────────────────────────────────────────────────────

# Mapeamento: id da tabela no HTML → nome da tabela no banco de dados
TABELAS_EQUIPE = {
    "results2025241_overall": "classificacao",
    "stats_squads_standard_for": "stats_geral_mandante",
    "stats_squads_standard_against": "stats_geral_visitante",
    "stats_squads_shooting_for": "stats_finalizacoes_favor",
    "stats_squads_shooting_against": "stats_finalizacoes_contra",
    "stats_squads_passing_for": "stats_passes_favor",
    "stats_squads_keeper_for": "stats_goleiros",
    "stats_squads_possession_for": "stats_posse",
    "stats_squads_misc_for": "stats_diversos",
}


def extrair_tabelas_principais(html: str, temporada: str) -> dict[str, pd.DataFrame]:
    """
    Extrai todas as tabelas mapeadas em TABELAS_EQUIPE de uma única página HTML.

    Args:
        html      : HTML sanitizado da página do FBref.
        temporada : Ano da temporada para enriquecer os dados.

    Returns:
        Dicionário {nome_tabela: DataFrame} com todos os dados extraídos.
    """
    soup = BeautifulSoup(html, "lxml")
    resultado: dict[str, pd.DataFrame] = {}

    for table_id, nome_tabela in TABELAS_EQUIPE.items():
        tag = soup.find("table", {"id": table_id})
        if tag is None:
            log.warning(f"Tabela '{table_id}' não encontrada no HTML. Pulando.")
            continue

        try:
            df = pd.read_html(StringIO(str(tag)))[0]
            df = _flatten_multiindex(df)
            df = _limpar_dataframe(df, temporada)
            resultado[nome_tabela] = df
            log.info(f"  ✓ {nome_tabela}: {len(df)} linhas extraídas.")
        except Exception as e:
            log.error(f"  ✗ Erro ao extrair '{table_id}': {e}")

    return resultado


def extrair_links_times(html: str, base_url: str = "https://fbref.com") -> list[dict]:
    """
    Percorre a tabela de classificação e extrai os links para as
    páginas individuais de cada time na temporada.

    Args:
        html     : HTML sanitizado da página principal do FBref.
        base_url : Domínio base para montar URLs absolutas.

    Returns:
        Lista de dicts [{nome: str, url: str}, ...].
    """
    soup = BeautifulSoup(html, "lxml")
    links = []

    # A tabela de classificação geral tem links para os times na coluna "Squad"
    tabela = soup.find("table", {"id": lambda x: x and "overall" in x})
    if not tabela:
        log.warning("Tabela de classificação não encontrada para varrer links dos times.")
        return links

    for linha in tabela.find_all("tr"):
        celula = linha.find("td", {"data-stat": "team"})
        if celula and celula.find("a"):
            href = celula.find("a")["href"]
            nome = celula.get_text(strip=True)
            links.append({"nome": nome, "url": f"{base_url}{href}"})

    log.info(f"Links extraídos: {len(links)} times encontrados.")
    return links


def extrair_stats_time(url: str, nome_time: str, session: requests.Session, temporada: str) -> dict[str, pd.DataFrame]:
    """
    Acessa a página individual de um time no FBref e extrai suas
    estatísticas detalhadas (escalações, gols, etc.).

    Args:
        url       : URL da página do time no FBref.
        nome_time : Nome do time (usado nos logs).
        session   : Session HTTP configurada.
        temporada : Ano da temporada.

    Returns:
        Dicionário com DataFrames extraídos da página do time.
    """
    log.info(f"Extraindo dados de: {nome_time}")
    html = _fetch_html(url, session)
    soup = BeautifulSoup(html, "lxml")
    resultado = {}

    # Tenta capturar a tabela de resultados do time na temporada
    for table in soup.find_all("table"):
        table_id = table.get("id", "")
        if not table_id:
            continue
        try:
            df = pd.read_html(StringIO(str(table)))[0]
            df = _flatten_multiindex(df)
            df["time"] = nome_time
            df = _limpar_dataframe(df, temporada)
            resultado[f"time_{table_id}"] = df
        except Exception:
            pass

    log.info(f"  ✓ {nome_time}: {len(resultado)} tabelas extraídas.")
    return resultado


# ─────────────────────────────────────────────────────────────────────────────
# Persistência no Banco de Dados
# ─────────────────────────────────────────────────────────────────────────────

def salvar_no_banco(
    dados: dict[str, pd.DataFrame],
    temporada: str,
    db_url: str = DB_URL,
) -> None:
    """
    Persiste todos os DataFrames no banco de dados relacional usando SQLAlchemy.
    Cada chave do dicionário vira um nome de tabela (com sufixo da temporada).

    Args:
        dados     : Dicionário {nome_tabela: DataFrame} a ser salvo.
        temporada : Sufixo da temporada para os nomes das tabelas.
        db_url    : String de conexão SQLAlchemy.
    """
    log.info("Conectando ao banco de dados...")
    try:
        engine = create_engine(db_url)
        # Testa a conexão antes de começar
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        log.info("Conexão com banco de dados OK!")
    except SQLAlchemyError as e:
        log.error(f"Falha na conexão com o banco: {e}")
        raise

    for nome_tabela, df in dados.items():
        tabela_final = f"{nome_tabela}_{temporada}"
        try:
            df.to_sql(
                name=tabela_final,
                con=engine,
                if_exists="replace",
                index=False,
                method="multi",
                chunksize=500,
            )
            log.info(f"  ✓ Tabela '{tabela_final}' salva ({len(df)} linhas).")
        except SQLAlchemyError as e:
            log.error(f"  ✗ Erro ao salvar '{tabela_final}': {e}")

    engine.dispose()
    log.info("Conexão com banco encerrada.")


# ─────────────────────────────────────────────────────────────────────────────
# Exportação CSV (fallback sem banco)
# ─────────────────────────────────────────────────────────────────────────────

def salvar_em_csv(dados: dict[str, pd.DataFrame], temporada: str) -> None:
    """
    Exporta os DataFrames como arquivos CSV na pasta 'output/'.
    Útil para validar os dados sem precisar de banco configurado.

    Args:
        dados     : Dicionário {nome_tabela: DataFrame}.
        temporada : Sufixo da temporada para o nome dos arquivos.
    """
    import os
    pasta = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(pasta, exist_ok=True)

    for nome, df in dados.items():
        caminho = os.path.join(pasta, f"{nome}_{temporada}.csv")
        df.to_csv(caminho, index=False, encoding="utf-8-sig")
        log.info(f"  ✓ CSV salvo: {caminho}")


# ─────────────────────────────────────────────────────────────────────────────
# Orquestrador Principal
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    """Ponto de entrada principal do extrator."""

    parser = argparse.ArgumentParser(
        description="Extrator FBref — Brasileirão Série A"
    )
    parser.add_argument(
        "--ano",
        default=TEMPORADA,
        help=f"Temporada a extrair (padrão: {TEMPORADA})",
    )
    parser.add_argument(
        "--modo",
        choices=["basico", "completo"],
        default="basico",
        help="'basico' = apenas tabelas principais | 'completo' = + páginas dos times",
    )
    parser.add_argument(
        "--sem-db",
        action="store_true",
        help="Se informado, salva em CSV em vez de persistir no banco.",
    )
    args = parser.parse_args()

    temporada = args.ano
    url_base = FBREF_URL.replace(TEMPORADA, temporada) if temporada != TEMPORADA else FBREF_URL

    log.info("=" * 60)
    log.info(f"  Extrator FBref — Brasileirão Série A {temporada}")
    log.info(f"  Modo    : {args.modo}")
    log.info(f"  URL     : {url_base}")
    log.info(f"  Destino : {'CSV (./output/)' if args.sem_db else 'Banco de Dados'}")
    log.info("=" * 60)

    session = _get_session()
    todos_dados: dict[str, pd.DataFrame] = {}

    # ── Etapa 1: Tabelas principais da página de stats ─────────────────────
    log.info("── Etapa 1: Extraindo tabelas principais ──")
    html_principal = _fetch_html(url_base, session, delay=0)  # 1ª requisição: sem delay
    dados_principais = extrair_tabelas_principais(html_principal, temporada)
    todos_dados.update(dados_principais)

    # ── Etapa 2 (opcional): Páginas individuais dos times ─────────────────
    if args.modo == "completo":
        log.info("── Etapa 2: Varrendo páginas individuais dos times ──")
        links_times = extrair_links_times(html_principal)

        for info_time in links_times:
            try:
                dados_time = extrair_stats_time(
                    url=info_time["url"],
                    nome_time=info_time["nome"],
                    session=session,
                    temporada=temporada,
                )
                # Prefixa o nome do time para evitar colisões de chave
                nome_slug = info_time["nome"].lower().replace(" ", "_")
                for k, v in dados_time.items():
                    todos_dados[f"{nome_slug}_{k}"] = v

            except Exception as e:
                log.error(f"Falha ao processar {info_time['nome']}: {e}")
                continue  # Continua para o próximo time em caso de falha

    # ── Etapa 3: Persistência ──────────────────────────────────────────────
    log.info(f"── Etapa 3: Salvando {len(todos_dados)} tabelas ──")
    if args.sem_db:
        salvar_em_csv(todos_dados, temporada)
    else:
        try:
            salvar_no_banco(todos_dados, temporada)
        except Exception:
            log.warning("Falha no banco. Salvando em CSV como fallback...")
            salvar_em_csv(todos_dados, temporada)

    log.info("=" * 60)
    log.info("Extração concluída com sucesso!")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
