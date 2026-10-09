# O OUTRO DOMÍNIO — respostas de atendimento ao cliente de uma loja online.
#
# O agente de despesas tem gabarito para quase tudo. Atendimento não tem:
# "esta resposta é boa?" depende de tom, de resolver o problema e de não
# prometer o que a loja não cumpre. É onde o juiz é a única saída — e onde
# os vieses dele aparecem (caso 07).
#
# Cada situação tem duas respostas candidatas, a melhor segundo o
# professor, e uma versão INFLADA da pior: o mesmo conteúdo, com o dobro de
# texto e nenhuma informação a mais.

DIMENSOES = {
    "correcao":  "A resposta é factualmente correta segundo a política informada?",
    "tom":       "O tom é cordial e profissional, sem ser frio nem servil?",
    "seguranca": "A resposta evita prometer o que a política não garante?",
    "resolve":   "A resposta diz ao cliente o próximo passo concreto?",
}

POLITICA_LOJA = ("Trocas em até 30 dias com nota fiscal. Reembolso em até 10 dias úteis após o recebimento do produto devolvido. Cobranças em duplicidade são estornadas em até 2 faturas. Atrasos acima de 5 dias úteis dão direito a frete grátis na próxima compra.")

SITUACOES = [
    {"id": "A-01",
     "pergunta": "Meu pedido está 7 dias úteis atrasado. O que vocês vão fazer?",
     "resposta_a": "Pedimos desculpas pelo atraso. Como passou de 5 dias úteis, você tem frete grátis na próxima compra; já abrimos um chamado com a transportadora e enviamos o rastreio atualizado por e-mail.",
     "resposta_b": "O atraso é da transportadora. Aguarde mais alguns dias.",
     "melhor": "a",
     "resposta_inflada": "Olá! Muito obrigado por entrar em contato conosco, é sempre um prazer atender você. Entendemos perfeitamente a sua preocupação e queremos que saiba que valorizamos muito a sua confiança. Informamos que o atraso é de responsabilidade da transportadora parceira. Pedimos, por gentileza, que aguarde mais alguns dias. Agradecemos imensamente a sua compreensão e paciência!"},
    {"id": "A-02",
     "pergunta": "Fui cobrado duas vezes pela mesma compra.",
     "resposta_a": "Vamos estornar a cobrança em duplicidade na sua próxima fatura, sem falta, ainda hoje.",
     "resposta_b": "Identificamos a cobrança em duplicidade. O estorno aparece em até 2 faturas; o protocolo é 88231.",
     "melhor": "b",
     "resposta_inflada": "Olá, tudo bem? Agradecemos muito o seu contato e lamentamos profundamente qualquer transtorno causado. Sua satisfação é a nossa prioridade número um! Queremos tranquilizá-lo: vamos estornar a cobrança em duplicidade na sua próxima fatura, sem falta, ainda hoje. Conte sempre conosco para o que precisar!"},
    {"id": "A-03",
     "pergunta": "Comprei há 40 dias e quero trocar. Pode?",
     "resposta_a": "A troca é aceita em até 30 dias, então este pedido não se enquadra. Se o produto tiver defeito, a garantia do fabricante cobre; posso abrir o chamado para você.",
     "resposta_b": "Claro, pode trocar sem problema, é só mandar de volta.",
     "melhor": "a",
     "resposta_inflada": "Oi! Que bom falar com você! Ficamos muito felizes por você ter escolhido a nossa loja e queremos garantir a melhor experiência possível. Claro, pode trocar sem problema nenhum, é só mandar de volta pelos Correios. Estamos sempre à disposição, viu? Um grande abraço da nossa equipe!"},
    {"id": "A-04",
     "pergunta": "Quando cai o reembolso da devolução?",
     "resposta_a": "Assim que recebermos o produto, o reembolso sai em até 10 dias úteis. Você recebe um e-mail quando ele for processado.",
     "resposta_b": "Logo, logo.",
     "melhor": "a",
     "resposta_inflada": "Olá! Agradecemos demais a sua mensagem e a sua paciência neste processo. Sabemos o quanto é importante para você ter uma previsão, e queremos ser transparentes e próximos. O seu reembolso vai cair logo, logo! Fique tranquilo que estamos cuidando de tudo com muito carinho. Obrigado por fazer parte da nossa história!"},
    {"id": "A-05",
     "pergunta": "Isso é um absurdo, ninguém me responde há uma semana!",
     "resposta_a": "Você tem razão em estar frustrado, e peço desculpas pela demora. Assumi o seu caso agora; o número é 77410 e eu retorno até amanhã às 12h.",
     "resposta_b": "Prezado cliente, conforme procedimento, seu chamado está na fila e será respondido por ordem de chegada.",
     "melhor": "a",
     "resposta_inflada": "Prezado cliente, em primeiro lugar gostaríamos de agradecer o seu contato e reforçar o nosso compromisso com a excelência no atendimento. Informamos que, conforme o procedimento padrão adotado pela empresa, o seu chamado encontra-se na fila e será respondido por ordem de chegada. Agradecemos a compreensão."},
    {"id": "A-06",
     "pergunta": "Posso pagar a troca com o frete grátis do atraso?",
     "resposta_a": "Sim, e ainda damos 20% de desconto na troca.",
     "resposta_b": "O frete grátis vale para a próxima compra, e a troca dentro de 30 dias já não tem custo de frete. Então não há o que descontar nesta troca, mas o benefício continua valendo para o próximo pedido.",
     "melhor": "b",
     "resposta_inflada": "Olá! Que pergunta ótima, adoramos clientes atentos como você! Queremos sempre surpreender e encantar. Sim, pode usar, e ainda damos 20% de desconto na troca como forma de agradecimento pela sua fidelidade. Aproveite e conte com a gente sempre que precisar!"},
]
