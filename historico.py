def registrar_transacao(historico, tipo, valor, saldo):
    transacao = {
        "tipo": tipo,
        "valor": valor,
        "saldo": saldo
    }

    historico.append(transacao)


def mostrar_historico(historico):
    if not historico:
        print("Nenhuma transação registrada.")
        return

    print("\n=== HISTÓRICO ===")

    for item in historico:
        print(f"Tipo: {item['tipo']}")
        print(f"Valor: R$ {item['valor']:.2f}")
        print(f"Saldo após operação: R$ {item['saldo']:.2f}")
        print("--------------------")