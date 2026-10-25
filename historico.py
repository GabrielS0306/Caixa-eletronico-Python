from formatacao import formatar_moeda


def mostrar_historico(transacoes):
    if not transacoes:
        print("Nenhuma transação registrada.")
        return

    print("\n=== HISTÓRICO ===")

    for item in transacoes:
        print(f"Tipo: {item.tipo.value}")
        print(f"Valor: {formatar_moeda(item.valor)}")
        print(f"Saldo após operação: {formatar_moeda(item.saldo)}")
        print("--------------------")
