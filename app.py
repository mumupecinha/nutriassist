# NutriAssist: interface visual (Streamlit)
#
# Antes de rodar:
#   pip install -r requirements.txt
#   python indexar_duvidas.py
# Para abrir: streamlit run app.py   (para fechar: Ctrl + C no PowerShell)
#
# O personagem: coloque a imagem dele em assets/personagem.png (PNG quadrado, fundo
# transparente de preferência). Enquanto não houver imagem, aparece um emoji no lugar.

import base64
import time
from pathlib import Path

import streamlit as st
from streamlit_option_menu import option_menu

import nutriassist

PASTA = Path(__file__).parent
IMG_PERSONAGEM = PASTA / "assets" / "personagem.png"        # rosto: avatar do chat
IMG_CORPO = PASTA / "assets" / "personagem_corpo.png"       # corpo inteiro: barra lateral
IMG_LOGO = PASTA / "assets" / "logo.png"                    # logo (opcional, PNG com fundo transparente)
AVATAR = str(IMG_PERSONAGEM) if IMG_PERSONAGEM.exists() else "🥑"
NOME = "NutriAssist"

# Cores da identidade (as mesmas do .streamlit/config.toml)
MARROM, CREME, BEGE, SALVIA = "#3B2A20", "#F5EFE6", "#EAE0D2", "#7E9471"


def imagem_html(caminho, largura):
    """Transforma uma imagem em texto (base64) para usar dentro de HTML."""
    if not caminho.exists():
        return ""
    dados = base64.b64encode(caminho.read_bytes()).decode()
    return f'<img src="data:image/png;base64,{dados}" width="{largura}">'


def digitar(texto):
    """Entrega o texto palavra por palavra, para parecer que está sendo digitado."""
    for palavra in texto.split(" "):
        yield palavra + " "
        time.sleep(0.03)


st.set_page_config(page_title=NOME, page_icon=AVATAR, layout="centered")

# ---------------------------------------------------------------
# PARTE 1: estilo (CSS). Fontes do Google Fonts, cantos arredondados, cartões
# ---------------------------------------------------------------
st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=Nunito:wght@400;600;700&family=Silkscreen&display=swap');
    /* Silkscreen é uma fonte "pixelada": usada só em detalhes, combinando com o personagem */
    .pixel {{ font-family: 'Silkscreen', monospace; letter-spacing: 1px; }}
    [data-testid="stChatMessageAvatarCustom"] img, [data-testid="stChatMessage"] img {{ image-rendering: pixelated; border-radius: 10px; }}
    html, body, [class*="css"], p, li, label, input, textarea {{ font-family: 'Nunito', sans-serif; }}
    h1, h2, h3 {{ font-family: 'Fraunces', serif !important; color: {MARROM}; letter-spacing: -0.5px; }}

    /* Faixa de boas-vindas */
    .hero {{
        background: {MARROM}; color: {CREME}; border-radius: 22px;
        padding: 22px 26px; margin-bottom: 18px;
    }}
    .hero h1 {{ color: {CREME} !important; margin: 0; font-size: 2.1rem; }}
    .hero p {{ margin: 6px 0 0; opacity: .9; }}
    .hero-topo {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }}
    .selo {{ background: {SALVIA}; color: white; border-radius: 6px; padding: 3px 8px; font-size: .7rem; }}

    /* Cartões */
    .cartao {{
        background: white; border-radius: 18px; padding: 16px 18px;
        box-shadow: 0 2px 10px rgba(59,42,32,.08); margin-bottom: 12px;
    }}
    .etiqueta {{
        display: inline-block; background: {SALVIA}; color: white; border-radius: 6px;
        padding: 2px 8px; font-size: .7rem; margin-right: 6px;
        font-family: 'Silkscreen', monospace; letter-spacing: 1px;
    }}
    .aviso {{
        background: {BEGE}; border-left: 5px solid {SALVIA}; border-radius: 12px;
        padding: 10px 14px; font-size: .9rem; margin-bottom: 14px;
    }}

    /* Botões e bolhas do chat */
    .stButton > button {{ border-radius: 999px; border: 1.5px solid {SALVIA}; font-weight: 600; }}
    [data-testid="stChatMessage"] {{ background: white; border-radius: 18px; padding: 10px 14px; }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------
# PARTE 2: menu lateral
# ---------------------------------------------------------------
with st.sidebar:
    if IMG_CORPO.exists():
        st.image(str(IMG_CORPO), width=120)
    st.markdown(f'<div class="pixel" style="font-size:1.3rem">{NOME}</div>', unsafe_allow_html=True)
    st.caption("O assistente do nutricionista")
    pagina = option_menu(
        menu_title=None,
        options=["Conversar", "Dúvidas por tema", "Sobre"],
        icons=["chat-heart", "journal-text", "info-circle"],
        default_index=0,
        styles={
            "container": {"background-color": BEGE, "padding": "6px", "border-radius": "16px"},
            "nav-link": {"font-size": "15px", "border-radius": "12px", "--hover-color": CREME},
            "nav-link-selected": {"background-color": SALVIA},
        },
    )
    if st.button("Limpar conversa"):
        st.session_state.pop("conversa", None)
        st.rerun()


def faixa(titulo, subtitulo):
    st.markdown(
        f'<div class="hero"><div class="hero-topo">{imagem_html(IMG_LOGO, 92)}'
        f'<span class="selo pixel">BETA</span></div>'
        f'<h1>{titulo}</h1><p>{subtitulo}</p></div>',
        unsafe_allow_html=True,
    )


AVISO = ('<div class="aviso"><b>Versão de testes.</b> As respostas ainda são rascunhos em revisão '
         'pelo nutricionista e o NutriAssist não substitui a consulta.</div>')


# ---------------------------------------------------------------
# PARTE 3: página Conversar
# ---------------------------------------------------------------
def pagina_conversar():
    faixa(f"Oi! Eu sou o {NOME} 👋", "Me pergunta qualquer dúvida do dia a dia da sua dieta.")
    st.markdown(AVISO, unsafe_allow_html=True)

    if "conversa" not in st.session_state:
        st.session_state.conversa = []

    # Sugestões para quem não sabe por onde começar
    if not st.session_state.conversa:
        st.markdown("**Que tal começar por uma destas?**")
        sugestoes = ["Vou num japonês. O que escolher?", "Posso comer fruta à noite?",
                     "O que comer antes do treino?", "Exagerei no fim de semana. E agora?"]
        colunas = st.columns(2)
        for n, texto in enumerate(sugestoes):
            if colunas[n % 2].button(texto, key=f"sug{n}", width="stretch"):
                st.session_state.pergunta_pendente = texto
                st.rerun()

    for msg in st.session_state.conversa:
        avatar = AVATAR if msg["papel"] == "assistant" else None
        with st.chat_message(msg["papel"], avatar=avatar):
            st.markdown(msg["texto"])
            if msg.get("detalhes"):
                with st.expander("O que eu fiz para responder"):
                    for linha in msg["detalhes"]:
                        st.caption(linha)

    pergunta = st.chat_input("Escreva a sua dúvida...") or st.session_state.pop("pergunta_pendente", None)
    if pergunta:
        st.session_state.conversa.append({"papel": "user", "texto": pergunta})
        # Mostra a pergunta na hora, sem esperar a resposta
        with st.chat_message("user"):
            st.markdown(pergunta)
        # Enquanto busca e confere, mostra "digitando"; depois escreve a resposta aos poucos
        with st.chat_message("assistant", avatar=AVATAR):
            with st.spinner(f"{NOME} está digitando..."):
                resposta, detalhes = nutriassist.responder(pergunta)
            st.write_stream(digitar(resposta))
        st.session_state.conversa.append({"papel": "assistant", "texto": resposta, "detalhes": detalhes})
        st.rerun()


# ---------------------------------------------------------------
# PARTE 4: página Dúvidas por tema (navegar sem perguntar)
# ---------------------------------------------------------------
def pagina_duvidas():
    faixa("Dúvidas por tema", "Navegue pelas perguntas mais comuns.")
    st.markdown(AVISO, unsafe_allow_html=True)
    duvidas = list(nutriassist.DUVIDAS.values())
    temas = sorted({d["tema"] for d in duvidas})
    col1, col2 = st.columns([1, 1])
    tema = col1.selectbox("Tema", temas)
    filtro = col2.text_input("Buscar uma palavra", placeholder="ex.: whey, japonês, doce")

    lista = [d for d in duvidas if d["tema"] == tema
             and (not filtro or nutriassist.normalizar(filtro) in nutriassist.normalizar(d["pergunta"] + " " + d["resposta"]))]
    st.caption(f"{len(lista)} dúvidas")
    for d in lista:
        with st.expander(d["pergunta"]):
            st.markdown(
                f'<span class="etiqueta">{d["objetivo"]}</span>'
                f'<span class="etiqueta" style="background:{MARROM}">{d["status"]}</span>',
                unsafe_allow_html=True,
            )
            st.write(d["resposta"])
            st.caption(f"Fonte: {d['fonte']}  |  {d['id']}")


# ---------------------------------------------------------------
# PARTE 5: página Sobre
# ---------------------------------------------------------------
def pagina_sobre():
    faixa(f"Sobre o {NOME}", "Como eu funciono, em poucas palavras.")
    st.markdown(
        f"""
        <div class="cartao"><b>Respostas do nutricionista.</b> Eu não invento: procuro a sua dúvida numa base
        de respostas escritas e revisadas pelo nutricionista, com fontes como o Guia Alimentar e diretrizes científicas.</div>
        <div class="cartao"><b>Quando não sei, aviso.</b> Se a dúvida envolve sintomas, remédios ou mudanças no
        seu plano, ou se eu não tiver uma resposta segura, eu passo para o nutricionista.</div>
        <div class="cartao"><b>Seu plano é dele.</b> Eu ajudo você a aplicar o plano no dia a dia, mas não mudo
        quantidades nem faço dieta nova.</div>
        """,
        unsafe_allow_html=True,
    )


if not nutriassist.PASTA_BANCO.exists():
    st.error("Banco não encontrado. Rode antes no PowerShell: python indexar_duvidas.py")
elif pagina == "Conversar":
    pagina_conversar()
elif pagina == "Dúvidas por tema":
    pagina_duvidas()
else:
    pagina_sobre()
