# Aula 03 — Prompt engineering
# Dados compartilhados pelos scripts 00 e 01.
#
# Por que um módulo em vez de repetir em cada arquivo: este é o conjunto de
# teste da aula, e conjunto de teste é ATIVO (aula 02, nota 04, §7). Ele fica
# num lugar só para que os experimentos comparem exatamente a mesma coisa —
# se cada script tivesse a sua cópia, uma edição em um deles invalidaria a
# comparação com os outros sem ninguém perceber.

# As 5 categorias possíveis. Vira `enum` no schema (aula 02, nota 02, §7.2).
CATEGORIAS = ["entrega_atrasada", "endereco_errado", "produto_avariado",
              "duvida", "elogio"]

# Conjunto de TESTE — 10 mensagens com gabarito.
# Metade tem armadilha: número que não é pedido, número por extenso, número
# com pontuação, dois pedidos, e elogio junto com reclamação.
TESTE = [
    ("Meu pedido 48219 era pra chegar terça e até hoje nada. Já são 5 dias!",
     "entrega_atrasada"),

    ("bom dia, o entregador deixou na rua de tras, numero 45. o meu é 145",
     "endereco_errado"),

    ("A caixa do pedido 77310 chegou toda amassada e a tampa trincou",
     "produto_avariado"),

    ("vocês entregam no sábado?",
     "duvida"),

    ("Só pra dizer que o rapaz da entrega foi super educado, obrigada!",
     "elogio"),

    ("Pedido 90021 cancelado e recomprado como 90455, o 90455 não chegou",
     "entrega_atrasada"),

    ("PEDIDO 12 MIL 340 ENTREGUE NO CEP ERRADO, EU MORO NO 04567890",
     "endereco_errado"),

    ("Recebi o pedido n 55.102 com a tela rachada. Quero trocar.",
     "produto_avariado"),

    ("o produto veio certo, sem arranhão nenhum, mas veio 3 dias depois",
     "entrega_atrasada"),

    ("qual o prazo para devolução?",
     "duvida"),
]

# Exemplos para o few-shot — NÃO são do conjunto de teste.
#
# Repare em três decisões, todas justificadas pelo Min et al. (nota 01, §6.2):
#   1. cobrem as 5 categorias (o espaço de rótulos importa mais que a
#      quantidade de exemplos);
#   2. são mensagens com cara de mensagem real, com erro de digitação —
#      a distribuição da entrada importa;
#   3. o formato é rigorosamente idêntico em todos.
EXEMPLOS = [
    ("comprei semana passada e ate agora nao chegou nada", "entrega_atrasada"),
    ("entregaram na casa do vizinho de novo",              "endereco_errado"),
    ("o vidro veio quebrado dentro da caixa",              "produto_avariado"),
    ("vcs tem loja fisica em campinas?",                   "duvida"),
    ("chegou antes do prazo, muito obrigado!",             "elogio"),
]

