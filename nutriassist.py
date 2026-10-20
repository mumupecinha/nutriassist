# NutriAssist v0: assistente de dúvidas do nutricionista (versão de testes, dados fictícios)
#
# Não usa IA para escrever: a resposta sai da planilha, palavra por palavra.
# Como funciona uma pergunta:
#   1. Travas em Python: sinais de alerta vão direto para o nutricionista
#   2. Busca (embeddings bge-m3): acha as dúvidas mais parecidas da planilha
#   3. Conferência (IA qwen3): a IA só escolhe qual dúvida pergunta a mesma coisa, ou nenhuma
#   4. A resposta da dúvida escolhida é devolvida como está na planilha
#
# Antes de rodar: python indexar_duvidas.py
# Para rodar: python nutriassist.py   (para sair, digite "sair")

import csv
import unicodedata
from datetime import datetime
from pathlib import Path

from langchain_chroma import Chroma
from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field

from embeddings import criar_embeddings

PASTA = Path(__file__).parent
PLANILHA = PASTA / "dados" / "duvidas_exemplo.csv"
PASTA_BANCO = PASTA / "banco_vetorial"
ARQUIVO_PENDENCIAS = PASTA / "pendencias" / "pendencias_nutricionista.csv"

# Distância máxima para uma dúvida virar candidata (0 = idêntico).
# Calibrado com o calibrar.py: com bge-m3, as certas ficaram até ~0.31 e as fora
# do assunto, a partir de ~0.32 (exceto pegadinhas). É só um primeiro filtro largo:
# quem decide de verdade é a conferência da IA.
LIMITE_CONFIANCA = 0.35
MAX_CANDIDATAS = 5
MODELO_IA = "qwen3:8b"

MSG_ENCAMINHAR = ("Essa dúvida é importante e quem precisa responder é o nutricionista. "
                  "Já registrei aqui e ele vai falar com você.")
MSG_NAO_SEI = ("Ainda não tenho uma resposta segura para isso. Registrei a sua dúvida "
               "e o nutricionista vai te responder.")
MSG_CUIDADO_URGENTE = ("Sinto muito que você esteja passando por isso. Você não está sozinho. "
                       "Se estiver em risco agora, ligue para o CVV no 188 (24 horas, gratuito) "
                       "ou procure um pronto-socorro. Também avisei o nutricionista.")


# ---------------------------------------------------------------
# PARTE 1: travas de entrada (Python puro, sem IA)
# ---------------------------------------------------------------

def normalizar(texto):
    """Minúsculas e sem acentos, para comparar palavras com segurança."""
    texto = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in texto if not unicodedata.combining(c))


# Falas de risco à vida: resposta de cuidado imediato
SINAIS_URGENTES = ["suicid", "me matar", "tirar minha vida", "me machucar", "me cortar",
                   "nao quero mais viver", "acabar com tudo"]

# Sinais que sempre vão para o nutricionista, sem buscar resposta
SINAIS_ENCAMINHAR = [
    "tontura", "desmai", "vomit", "sangrando", "com sangue", "sangue nas fezes",
    "dor no peito", "falta de ar", "febre",
    "gravida", "gestante", "amament", "remedio", "medicamento", "ozempic", "mounjaro",
    "caneta", "insulina", "laxante", "diuretico", "purgar",
    "exame", "colesterol alto", "pressao alta", "diabet",
    # frases de uso, e não a palavra solta: "Whey é anabolizante?" é um mito e tem resposta
    "usar anabolizante", "tomar anabolizante", "usando anabolizante",
    "tomar bomba", "usar bomba", "usando bomba",
    "cancelar", "remarcar", "reembolso", "pagamento",
]
# Lição dos testes: palavras soltas como "sangue", "bomba" e "anabolizante" barravam
# perguntas inofensivas ("tipo sanguíneo", "fica bombada", "whey é anabolizante?").
# Toda mudança nesta lista precisa ser testada contra a planilha inteira.


def trava_de_entrada(pergunta):
    texto = normalizar(pergunta)
    for sinal in SINAIS_URGENTES:
        if sinal in texto:
            return "urgente", sinal
    for sinal in SINAIS_ENCAMINHAR:
        if sinal in texto:
            return "encaminhar", sinal
    return None, None


# ---------------------------------------------------------------
# PARTE 2: planilha e busca
# ---------------------------------------------------------------

def carregar_planilha():
    with open(PLANILHA, encoding="utf-8-sig") as f:
        return {linha["id"]: linha for linha in csv.DictReader(f, delimiter=";")}


DUVIDAS = carregar_planilha()
banco = Chroma(
    collection_name="duvidas_nutriassist",
    embedding_function=criar_embeddings(),
    persist_directory=str(PASTA_BANCO),
)


def buscar(pergunta, k=10):
    """Devolve as dúvidas mais parecidas: lista de (distância, id), da mais próxima para a menos."""
    melhores = {}
    for doc, distancia in banco.similarity_search_with_score(pergunta, k=k):
        id_ = doc.metadata["id"]
        if id_ not in melhores or distancia < melhores[id_]:
            melhores[id_] = distancia
    return sorted((d, i) for i, d in melhores.items())


# ---------------------------------------------------------------
# PARTE 3: conferência com IA
# ---------------------------------------------------------------
# Por que IA aqui? O calibrar.py mostrou que a busca sozinha erra perguntas parecidas
# ("antes" x "depois" do treino, "café" bebida x café da manhã) com distância baixa.
# A IA NÃO escreve a resposta: ela só aponta o número da candidata certa, ou 0.

class Escolha(BaseModel):
    numero: int = Field(description="Número da dúvida que pergunta a mesma coisa. 0 se nenhuma.")


ia = ChatOllama(model=MODELO_IA, temperature=0, reasoning=False).with_structured_output(Escolha)

INSTRUCAO = """Você confere um assistente de dúvidas de dieta.
Abaixo há a mensagem de um paciente e uma lista numerada de dúvidas já respondidas.
Escolha o número da dúvida que pergunta A MESMA COISA que o paciente, de forma que
a resposta dela sirva para ele. Atenção a detalhes: antes x depois, durante x faltar,
café (bebida) x café da manhã, pessoa x animal.
Se nenhuma servir, ou se a mensagem não for sobre a alimentação do próprio paciente, responda 0.

Mensagem do paciente: {pergunta}

Dúvidas:
{lista}"""


def conferir_com_ia(pergunta, candidatas):
    """candidatas: lista de IDs. Devolve o ID escolhido pela IA, ou None."""
    lista = "\n".join(f"{n}. {DUVIDAS[i]['pergunta']} (ou: {DUVIDAS[i]['variacao_1']})"
                      for n, i in enumerate(candidatas, 1))
    escolha = ia.invoke(INSTRUCAO.format(pergunta=pergunta, lista=lista))
    if 1 <= escolha.numero <= len(candidatas):
        return candidatas[escolha.numero - 1]
    return None


def escolher(pergunta):
    """Busca + conferência. Devolve (id escolhido ou None, detalhes)."""
    resultados = buscar(pergunta)
    detalhes = [f"{i} (distância {d:.3f}): {DUVIDAS[i]['pergunta']}" for d, i in resultados[:3]]
    candidatas = [i for d, i in resultados if d <= LIMITE_CONFIANCA][:MAX_CANDIDATAS]
    if not candidatas:
        return None, ["Busca: nenhuma dúvida parecida o bastante"] + detalhes
    id_ = conferir_com_ia(pergunta, candidatas)
    if id_ is None:
        return None, [f"Conferência da IA: nenhuma das {len(candidatas)} candidatas serve"] + detalhes
    return id_, [f"Conferência da IA: escolheu {id_} entre {len(candidatas)} candidatas"] + detalhes


# ---------------------------------------------------------------
# PARTE 4: registro de pendências para o nutricionista
# ---------------------------------------------------------------

def registrar_pendencia(pergunta, motivo):
    ARQUIVO_PENDENCIAS.parent.mkdir(exist_ok=True)
    novo = not ARQUIVO_PENDENCIAS.exists()
    with open(ARQUIVO_PENDENCIAS, "a", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        if novo:
            w.writerow(["data_hora", "pergunta", "motivo", "status"])
        w.writerow([datetime.now().strftime("%d/%m/%Y %H:%M"), pergunta, motivo, "aberta"])


# ---------------------------------------------------------------
# PARTE 5: o fluxo completo de uma pergunta
# ---------------------------------------------------------------

def responder(pergunta):
    """Devolve (resposta, detalhes). Os detalhes mostram o que o sistema fez."""
    tipo, sinal = trava_de_entrada(pergunta)
    if tipo == "urgente":
        registrar_pendencia(pergunta, f"URGENTE: sinal '{sinal}'")
        return MSG_CUIDADO_URGENTE, [f"Trava de entrada: sinal urgente '{sinal}'"]
    if tipo == "encaminhar":
        registrar_pendencia(pergunta, f"sinal de alerta '{sinal}'")
        return MSG_ENCAMINHAR, [f"Trava de entrada: sinal '{sinal}'"]

    id_, detalhes = escolher(pergunta)
    if id_ is None:
        registrar_pendencia(pergunta, "sem resposta confiável")
        return MSG_NAO_SEI, detalhes

    item = DUVIDAS[id_]
    if "ENCAMINHAR" in item["fonte"]:
        registrar_pendencia(pergunta, f"resposta {item['id']} prevê encaminhamento")
    detalhes.insert(0, f"Resposta de {item['id']} | fonte: {item['fonte']} | status: {item['status']}")
    return item["resposta"], detalhes


if __name__ == "__main__":
    if not PASTA_BANCO.exists():
        print("Banco não encontrado. Rode antes: python indexar_duvidas.py")
        raise SystemExit
    print("NutriAssist v0 (testes, respostas em rascunho). Digite 'sair' para encerrar.\n")
    while True:
        pergunta = input("Você: ").strip()
        if pergunta.lower() in ("sair", "exit", "quit"):
            break
        if not pergunta:
            continue
        resposta, detalhes = responder(pergunta)
        for linha in detalhes:
            print(f"  [{linha}]")
        print(f"\nNutriAssist: {resposta}\n")
