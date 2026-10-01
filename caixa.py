import deposito
import saque
import saldo
import time

def obter_valor(mensagem):
    try:
        valor = float(input(mensagem))
        return valor

    except ValueError:
        print("Entrada inválida! Digite um número.")
        return None


saldo_atual = 0.0

while True:
    print("\n===== CAIXA ELETRÔNICO =====")
    print("1 - Depósito")
    print("2 - Saque")
    print("3 - Consultar saldo")
    print("0 - Sair")

    opcao = input("Escolha uma opção: ")

    if opcao == "1":
        valor = obter_valor("Valor do depósito: R$ ")

        if valor is not None:
            saldo_atual = deposito.deposito(valor, saldo_atual)

    elif opcao == "2":
        valor = obter_valor("Valor do saque: R$ ")

        if valor is not None:
            saldo_atual = saque.saque(valor, saldo_atual)

    elif opcao == "3":
        saldo.saldo_total(saldo_atual)

    elif opcao == "0":
        print("Saindo do caixa eletrônico...")
        time.sleep(1)
        print("Obrigado por utilizar o caixa eletrônico!")
        break

    else:
        print("Opção inválida! Tente novamente.")