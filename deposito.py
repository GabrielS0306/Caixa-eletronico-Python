def deposito(valor, saldo):
    if valor <= 0:
        print("Valor inválido! Digite um valor maior que zero.")

        return saldo

    saldo += valor

    print("Depósito realizado com sucesso!")

    return saldo