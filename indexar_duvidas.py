# NutriAssist, passo 1: preparar o banco de busca
#
# Lê a planilha de dúvidas (dados/duvidas_exemplo.csv) e guarda cada jeito de perguntar
# (a dúvida principal + as 4 variações) no banco vetorial, todos apontando para o mesmo ID.
# Assim, perguntas diferentes que querem dizer a mesma coisa levam à mesma resposta.
#
# Rode de novo sempre que a planilha mudar.
# Para rodar: python indexar_duvidas.py

import csv
import shutil
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document

from embeddings import criar_embeddings

PASTA = Path(__file__).parent
PLANILHA = PASTA / "dados" / "duvidas_exemplo.csv"
PASTA_BANCO = PASTA / "banco_vetorial"
LOTE = 50  # quantos textos mandar por vez (lotes grandes derrubaram o Ollama no Windows)


def carregar_documentos():
    documentos = []
    with open(PLANILHA, encoding="utf-8-sig") as f:
        for linha in csv.DictReader(f, delimiter=";"):
            jeitos = [linha["pergunta"]] + [linha[f"variacao_{i}"] for i in range(1, 5)]
            for texto in jeitos:
                if texto.strip():
                    documentos.append(
                        Document(
                            page_content=texto.strip(),
                            metadata={"id": linha["id"], "tema": linha["tema"]},
                        )
                    )
    return documentos


if __name__ == "__main__":
    documentos = carregar_documentos()
    print(f"{len(documentos)} jeitos de perguntar encontrados na planilha.")

    # Recria o banco do zero para não duplicar (só mexe na pasta banco_vetorial)
    if PASTA_BANCO.exists():
        shutil.rmtree(PASTA_BANCO)

    banco = Chroma(
        collection_name="duvidas_nutriassist",
        embedding_function=criar_embeddings(),
        persist_directory=str(PASTA_BANCO),
        # "cosine" faz a distância ir de 0 (idêntico) a 2 (oposto): fica mais fácil ler
        collection_metadata={"hnsw:space": "cosine"},
    )

    for inicio in range(0, len(documentos), LOTE):
        banco.add_documents(documentos[inicio:inicio + LOTE])
        print(f"  {min(inicio + LOTE, len(documentos))} de {len(documentos)} indexados...")

    print("Pronto! Banco salvo em banco_vetorial.")
