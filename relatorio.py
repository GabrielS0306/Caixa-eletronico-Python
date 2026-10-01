def mostrar_relatorio(transacoes, saldo_atual):
    total_depositado = sum(
        item["valor"]
        for item in transacoes
        if item["tipo"] == "Depósito"
    )

    total_sacado = sum(
        item["valor"]
        for item in transacoes
        if item["tipo"] == "Saque"
    )

    quantidade_depositos = sum(
        1 for item in transacoes
        if item["tipo"] == "Depósito"
    )

    quantidade_saques = sum(
        1 for item in transacoes
        if item["tipo"] == "Saque"
    )

    total_transacoes = len(transacoes)

    print("\n===== RELATÓRIO DA CONTA =====")
    print(f"Saldo atual: R$ {saldo_atual:.2f}")
    print(f"Total depositado: R$ {total_depositado:.2f}")
    print(f"Total sacado: R$ {total_sacado:.2f}")
    print(f"Quantidade de depósitos: {quantidade_depositos}")
    print(f"Quantidade de saques: {quantidade_saques}")
    print(f"Total de transações: {total_transacoes}")
    print("==============================")