def sacar(valor, saldo):
    if valor <= 0:
        print("Valor inválido! Digite um valor maior que zero.")

    elif valor > saldo:
        print("Saldo insuficiente!")

    else:
        saldo -= valor

        print("Saque realizado com sucesso!")

    return saldo