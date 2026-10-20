# Configuração dos embeddings, compartilhada pela indexação e pelo agente.
#
# Fica num arquivo só porque a indexação e a busca PRECISAM usar exatamente
# o mesmo modelo e o mesmo jeito de preparar o texto. Se um mudar e o outro não,
# a busca deixa de funcionar sem dar erro nenhum (só traz resultados ruins).
#
# O nomic-embed-text foi treinado para receber prefixos:
#   - "search_document: " antes dos textos guardados no banco
#   - "search_query: "    antes das perguntas
# Sem eles, a qualidade da busca cai bastante.

from langchain_ollama import OllamaEmbeddings

MODELO_EMBEDDINGS = "nomic-embed-text"


class EmbeddingsComPrefixo(OllamaEmbeddings):
    """Igual ao OllamaEmbeddings, mas acrescenta os prefixos que o nomic espera."""

    def embed_documents(self, texts):
        return super().embed_documents([f"search_document: {t}" for t in texts])

    def embed_query(self, text):
        return super().embed_query(f"search_query: {text}")


def criar_embeddings():
    return OllamaEmbeddings(model="bge-m3")
