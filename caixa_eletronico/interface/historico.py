from caixa_eletronico.formatacao import formatar_data, formatar_moeda


def mostrar_historico(transacoes, titulo="HISTÓRICO"):
    if not transacoes:
        print("Nenhuma transação registrada.")
        return

    print(f"\n=== {titulo} ===")

    for item in transacoes:
        print(f"Data: {formatar_data(item.data)}")
        print(f"Tipo: {item.tipo.value}")
        print(f"Valor: {formatar_moeda(item.valor)}")
        print(f"Saldo após operação: {formatar_moeda(item.saldo)}")
        print("--------------------")
