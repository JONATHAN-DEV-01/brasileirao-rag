"""
styles.py — CSS customizado do Brasileirão RAG
===============================================
Paleta de cores, tipografia, bolhas de chat, sidebar e loading screen.
Isolado aqui para que ajustes visuais não toquem em lógica de negócio.
"""

CUSTOM_CSS = """
<style>
/* ── Importação de fonte moderna ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Reset e fontes globais ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* ── Cabeçalho principal da aplicação ── */
.main-header {
    background: linear-gradient(135deg, #8b55d8 0%, #0d3145 60%, #0a2538 100%);
    border-radius: 16px;
    padding: 28px 32px;
    margin-bottom: 24px;
    border: 1px solid rgba(139, 85, 216, 0.35);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
    text-align: center;
}

.main-header h1 {
    color: #f0f0f0;
    font-size: 2rem;
    font-weight: 800;
    margin: 0 0 6px 0;
    letter-spacing: -0.5px;
}

.main-header .subtitle {
    color: #f8ae39;
    font-size: 0.95rem;
    font-weight: 500;
    margin: 0;
    opacity: 0.9;
}

/* ── Badge de provedor de LLM ── */
.provider-badge {
    display: inline-block;
    background: rgba(248, 174, 57, 0.18);
    color: #f8ae39;
    border: 1px solid rgba(248, 174, 57, 0.45);
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.5px;
    margin-top: 10px;
    text-transform: uppercase;
}

/* ── Bolhas de chat — Usuário ── */
.chat-message-user {
    display: flex;
    justify-content: flex-end;
    margin-bottom: 14px;
}

.chat-message-user .bubble {
    background: linear-gradient(135deg, #8b55d8, #6b3fb5);
    color: #ffffff;
    border-radius: 18px 18px 4px 18px;
    padding: 12px 18px;
    max-width: 75%;
    font-size: 0.93rem;
    line-height: 1.55;
    box-shadow: 0 4px 12px rgba(139, 85, 216, 0.3);
}

/* ── Bolhas de chat — Assistente ── */
.chat-message-assistant {
    display: flex;
    justify-content: flex-start;
    margin-bottom: 14px;
}

.chat-message-assistant .bubble {
    background: rgba(255, 255, 255, 0.06);
    color: #f0f0f0;
    border: 1px solid rgba(139, 85, 216, 0.25);
    border-radius: 18px 18px 18px 4px;
    padding: 12px 18px;
    max-width: 80%;
    font-size: 0.93rem;
    line-height: 1.6;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

/* ── Avatar dos participantes ── */
.avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.1rem;
    flex-shrink: 0;
    margin: 0 10px;
    align-self: flex-end;
}

.avatar-user      { background: linear-gradient(135deg, #8b55d8, #6b3fb5); }
.avatar-assistant { background: linear-gradient(135deg, #f8ae39, #e0952a); }

/* ── Card de fonte/citação ── */
.source-card {
    background: rgba(248, 174, 57, 0.08);
    border: 1px solid rgba(248, 174, 57, 0.3);
    border-radius: 10px;
    padding: 10px 14px;
    margin-top: 6px;
    font-size: 0.82rem;
    color: #f0f0f0;
}

.source-card .source-title {
    color: #f8ae39;
    font-weight: 700;
    font-size: 0.85rem;
    margin-bottom: 4px;
}

/* ── Sidebar customizada ── */
[data-testid="stSidebar"] {
    background-color: #0a2538 !important;
    border-right: 1px solid rgba(139, 85, 216, 0.2);
}

[data-testid="stSidebar"] .stMarkdown {
    color: #f0f0f0;
}

/* ── Caixa de input de mensagem ── */
[data-testid="stChatInput"] textarea {
    background-color: rgba(255, 255, 255, 0.06) !important;
    color: #f0f0f0 !important;
    border: 1px solid rgba(139, 85, 216, 0.4) !important;
    border-radius: 12px !important;
    font-family: 'Inter', sans-serif !important;
}

/* ── Botões ── */
[data-testid="baseButton-secondary"] {
    background: transparent !important;
    border: 1px solid rgba(139, 85, 216, 0.5) !important;
    color: #8b55d8 !important;
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
    transition: all 0.2s ease !important;
}

[data-testid="baseButton-secondary"]:hover {
    background: rgba(139, 85, 216, 0.15) !important;
    border-color: #8b55d8 !important;
}

/* ── Spinner de carregamento ── */
[data-testid="stSpinner"] {
    color: #8b55d8 !important;
}

/* ── Divisória ── */
hr {
    border-color: rgba(139, 85, 216, 0.2) !important;
}

/* ── Expander das fontes ── */
[data-testid="stExpander"] {
    background: rgba(255, 255, 255, 0.03) !important;
    border: 1px solid rgba(248, 174, 57, 0.25) !important;
    border-radius: 10px !important;
}

[data-testid="stExpander"] summary {
    color: #f8ae39 !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
}

/* ── Alerta / Info ── */
[data-testid="stAlert"] {
    border-radius: 10px !important;
}

/* ── Loading screen (st.status) ── */
[data-testid="stStatus"] {
    background: rgba(139, 85, 216, 0.08) !important;
    border: 1px solid rgba(139, 85, 216, 0.35) !important;
    border-radius: 14px !important;
    padding: 4px 0 !important;
}

[data-testid="stStatus"] > div > div > p {
    color: #f0f0f0 !important;
    font-size: 0.9rem !important;
}

[data-testid="stStatusWidget"] {
    color: #f8ae39 !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
}

/* ── Scrollbar customizada ── */
::-webkit-scrollbar       { width: 6px; }
::-webkit-scrollbar-track { background: #0a2538; }
::-webkit-scrollbar-thumb { background: #8b55d8; border-radius: 3px; }
</style>
"""
