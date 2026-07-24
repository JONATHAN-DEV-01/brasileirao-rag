# ⚽ Extrator FBref — Brasileirão Série A

Script Python para extração automática de dados estatísticos do **Campeonato Brasileiro Série A** diretamente do site [FBref](https://fbref.com), com persistência em banco de dados relacional (PostgreSQL ou MySQL).

---

## 📁 Estrutura do Projeto

```
scripts/fbref_brasileirao/
├── extrator.py       ← Script principal de extração
├── config.py         ← Leitura de variáveis de ambiente
├── .env.example      ← Template das variáveis de ambiente
├── requirements.txt  ← Dependências Python
├── output/           ← CSVs gerados (criado automaticamente)
└── README.md         ← Este arquivo
```

---

## ☁️ Pré-requisito: Supabase (Banco de Dados em Nuvem)

Este script foi adaptado para salvar os dados diretamente no **Supabase**. Como o Supabase utiliza PostgreSQL por baixo dos panos, utilizamos a string de conexão nativa.

Para obter sua credencial:
1. Acesse seu projeto no [Supabase](https://supabase.com/).
2. Vá em **Project Settings** (engrenagem) > **Database**.
3. Na seção **Connection string**, escolha a aba **URI**.
4. Desmarque "Use connection pooling" (ou deixe marcado se preferir, a porta mudará de 5432 para 6543).
5. Copie a string que começa com `postgresql://...` e não se esqueça de substituir `[YOUR-PASSWORD]` pela sua senha real.

---

## ⚙️ Instalação

### 1. Entre na pasta do script

```bash
cd scripts/fbref_brasileirao
```

### 2. Crie um ambiente virtual (recomendado)

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

```bash
# Copie o template
cp .env.example .env
```

Edite o arquivo `.env` preenchendo a sua string do Supabase:

```env
SUPABASE_DB_URL=postgresql://postgres.xxx:sua_senha@aws-0-sa-east-1.pooler.supabase.com:6543/postgres
FBREF_URL=https://fbref.com/en/comps/24/2025/2025-Serie-A-Stats
REQUEST_DELAY=8
TEMPORADA=2025
```

---

## 🚀 Uso

### Modo Básico (apenas tabelas de estatísticas de equipe)

Extrai classificação, gols, xG, posse, chutes, passes e goleiros em **~1 requisição**:

```bash
python extrator.py --modo basico
```

### Modo Completo (+ páginas individuais de cada time)

Percorre as páginas dos 20 times e captura métricas granulares. **Mais demorado** (~20 requisições com pausas de 8s cada):

```bash
python extrator.py --modo completo
```

### Sem Banco (exportar apenas para CSV)

Ideal para validar os dados sem precisar de Docker configurado:

```bash
python extrator.py --modo basico --sem-db
```

Os arquivos serão salvos em `output/*.csv`.

### Extrair outra temporada

```bash
python extrator.py --ano 2024 --modo basico
```

---

## 📊 Tabelas Extraídas

| Tabela no Banco             | Conteúdo                              |
|-----------------------------|---------------------------------------|
| `classificacao_2025`        | Tabela de classificação geral         |
| `stats_geral_mandante_2025` | Gols, assistências, cartões (casa)    |
| `stats_geral_visitante_2025`| Gols, assistências, cartões (fora)    |
| `stats_finalizacoes_*_2025` | Chutes a gol, xG, xGA                 |
| `stats_passes_favor_2025`   | Passes completados, progressivos      |
| `stats_goleiros_2025`       | Defesas, PSxG, gols sofridos          |
| `stats_posse_2025`          | Posse, toques, conduções              |
| `stats_diversos_2025`       | Faltas, impedimentos, bolas ganhas    |

---

## ⚠️ Rate Limiting — Muito Importante

O FBref implementa proteção contra scraping agressivo. O script já inclui pausas automáticas configuráveis via `REQUEST_DELAY` (padrão: **8 segundos**).

**Não reduza esse valor abaixo de 6 segundos**, pois seu IP pode ser bloqueado temporariamente.

---

## 🔧 Troubleshooting

| Problema | Solução |
|---|---|
| `ModuleNotFoundError` | Ative o venv e rode `pip install -r requirements.txt` |
| `OperationalError` (DB) | Verifique se o Docker está rodando e a `DB_URL` está correta |
| Tabela não encontrada | O FBref muda IDs de tabelas entre temporadas. Inspecione o HTML e atualize `TABELAS_EQUIPE` em `extrator.py` |
| `403 Forbidden` | Aguarde alguns minutos e tente novamente. Aumente o `REQUEST_DELAY` |
| Dados incompletos | Use `--modo completo` para capturar as páginas individuais dos times |
