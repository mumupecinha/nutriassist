# NutriAssist: calibrar o limite de confiança
#
# Faz perguntas de teste ao banco SEM registrar pendências e mostra as distâncias.
# Há dois grupos:
#   - DENTRO: perguntas escritas de um jeito novo (não estão na planilha), com o ID certo
#   - FORA:   perguntas que não têm nada a ver com dieta, que o NutriAssist deveria recusar
# Usa o mesmo caminho do NutriAssist (busca + conferência da IA). Leva alguns minutos.
#
# Para rodar: python calibrar.py

from nutriassist import buscar, escolher

DENTRO = [
    ("fruta de noite engorda mesmo?", "EMA-006"),
    ("da pra emagrecer comendo um docinho de vez em quando", "EMA-076"),
    ("minha barriga nao baixa de jeito nenhum", "EMA-017"),
    ("whey tira a fome?", "FOM-078"),
    ("é normal sentir fome toda hora?", "FOM-081"),
    ("chego do trabalho e como tudo que vejo pela frente", "FOM-009"),
    ("quais comidas tem mais proteina", "HIP-002"),
    ("sou vegano, da pra ganhar musculo?", "HIP-034"),
    ("como sei se engordei ou ganhei massa", "HIP-061"),
    ("vinagre de maçã em capsula funciona pra emagrecer?", "MER-092"),
    ("sorvete proteico vale a pena comprar?", "MER-061"),
    ("chia e linhaça ajudam em alguma coisa?", "MER-070"),
    ("se eu parar a academia o musculo vira gordura?", "MIT-061"),
    ("tem algum alimento que queima gordura?", "MIT-082"),
    ("pao de forma ou pao frances, qual é melhor?", "MIT-051"),
    ("vou viajar, o que comer no aeroporto?", "RES-030"),
    ("vinho tinto faz bem pra saude?", "RES-082"),
    ("vou num brunch domingo, como faço?", "RES-020"),
    ("o shoyu do japones atrapalha a dieta?", "RES-067"),
    ("quantos litros de agua tenho que beber", "ROT-009"),
    ("como faço marmita pra semana toda", "ROT-002"),
    ("me da ideias de recheio de tapioca", "ROT-100"),
    ("tomei cafe da manha, quanto tempo espero pra treinar?", "TRE-021"),
    ("treino cedo e nao consigo comer nada antes", "TRE-006"),
    ("desde que comecei a dieta minha força caiu", "TRE-076"),
    ("posso trocar a carne do almoço por ovo?", "TRO-100"),
    ("nao entendi como usa a lista de substituicao", "TRO-004"),
    ("faltei no treino, preciso comer menos hoje?", "TRO-077"),
]

FORA = [
    "qual a capital da França?",
    "quem ganhou o jogo do corinthians ontem?",
    "como faço para trocar o pneu do carro?",
    "me indica um filme bom para ver hoje",
    "qual a previsão do tempo para amanhã?",
    "como instalo o python no windows?",
    "quanto custa uma passagem para o rio?",
    "me conta uma piada",
    "qual o melhor celular para comprar?",
    "como aprender inglês rápido?",
    "oi, tudo bem?",
    "meu cachorro pode comer chocolate?",
    "como declarar imposto de renda?",
    "qual a raiz quadrada de 144?",
    "que horas são?",
]

def testar(pergunta):
    """Mostra a distância da busca e o que a conferência da IA decidiu."""
    dist = buscar(pergunta)[0][0]
    id_, _ = escolher(pergunta)
    return dist, id_


print("\n=== DENTRO (deveria achar o ID certo) ===")
certas = erradas = recusadas = 0
for pergunta, id_certo in DENTRO:
    dist, id_ = testar(pergunta)
    if id_ == id_certo:
        certas += 1
        marca = "OK     "
    elif id_ is None:
        recusadas += 1
        marca = "RECUSOU"
    else:
        erradas += 1
        marca = "ERRO   "
    extra = "" if id_ == id_certo else f"   [esperado {id_certo}]"
    print(f"{marca} {dist:.3f}  {str(id_):8} {pergunta}{extra}")

print("\n=== FORA (deveria recusar) ===")
recusou_fora = 0
for pergunta in FORA:
    dist, id_ = testar(pergunta)
    if id_ is None:
        recusou_fora += 1
    marca = "OK     " if id_ is None else "RESPONDEU"
    print(f"{marca} {dist:.3f}  {str(id_):8} {pergunta}")

print("\n=== RESUMO ===")
print(f"DENTRO: {certas} certas, {erradas} erradas, {recusadas} recusadas (de {len(DENTRO)})")
print(f"FORA:   {recusou_fora} de {len(FORA)} recusadas corretamente")
print("Lembrete: errada é o pior caso (resposta errada com confiança). Recusada vira pendência para o nutricionista.")
