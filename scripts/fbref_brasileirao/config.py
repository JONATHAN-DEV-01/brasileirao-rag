"""
config.py — Configurações centralizadas do Extrator FBref
==========================================================
Lê variáveis do arquivo .env e expõe constantes para o extrator.
"""

import os
from dotenv import load_dotenv

# Carrega .env do mesmo diretório deste arquivo
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

# ── Banco de Dados (Supabase) ───────────────────────────────────────────────
_raw_url = os.getenv("SUPABASE_DB_URL", "")
# SQLAlchemy requer o driver explícito no postgres (postgresql+psycopg2://)
if _raw_url.startswith("postgresql://"):
    DB_URL = _raw_url.replace("postgresql://", "postgresql+psycopg2://", 1)
else:
    DB_URL = _raw_url

# ── FBref ───────────────────────────────────────────────────────────────────
FBREF_URL: str = os.getenv(
    "FBREF_URL",
    "https://fbref.com/en/comps/24/2025/2025-Serie-A-Stats",
)

# Pausa obrigatória entre requisições (segundos).
# FBref bloqueia IPs que fazem requisições em rajada. Mínimo: 6s.
REQUEST_DELAY: int = int(os.getenv("REQUEST_DELAY", "8"))

# Temporada (usado como sufixo nos nomes das tabelas do banco)
TEMPORADA: str = os.getenv("TEMPORADA", "2025")

# ── Headers HTTP realistas ──────────────────────────────────────────────────
# Simula um navegador Firefox para evitar bloqueios por User-Agent suspeito.
HTTP_HEADERS: dict = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) "
        "Gecko/20100101 Firefox/124.0"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/avif,image/webp,*/*;q=0.8"
    ),
    "Referer": "https://fbref.com/",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}
