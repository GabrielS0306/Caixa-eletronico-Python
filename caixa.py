import deposito
import saque
import saldo
import time
import historico
import math 
import persistencia

saldo_atual, transacoes = persistencia.carregar_dados()

def obter_valor(mensagem):
    try:
        entrada = input(mensagem).strip()
        valor = float(entrada.replace(",", "."))

        if not math.isfinite(valor):
            print("Digite um número válido e finito.")
            return None

        if valor <= 0:
            print("O valor deve ser maior que zero.")
            return None

        return valor

    except ValueError:
        print("Entrada inválida! Digite um número.")
        return None

while True:
    print("\n===== CAIXA ELETRÔNICO =====")
    print("1 - Depósito")
    print("2 - Saque")
    print("3 - Consultar saldo")
    print("4 - Histórico de transações")
    print("0 - Sair")

    opcao = input("Escolha uma opção: ")

    if opcao == "1":
        valor = obter_valor("Valor do depósito: R$ ")

        if valor is not None:
            saldo_atual = deposito.depositar(valor, saldo_atual)

            if valor > 0:
                historico.registrar_transacao(
                    transacoes, "Depósito", valor, saldo_atual
                )

                persistencia.salvar_dados(saldo_atual, transacoes)

    elif opcao == "2":
        valor = obter_valor("Valor do saque: R$ ")

        if valor is not None:
            saldo_anterior = saldo_atual
            saldo_atual = saque.sacar(valor, saldo_atual)

            if 0 < valor <= saldo_anterior:
                historico.registrar_transacao(
                    transacoes, "Saque", valor, saldo_atual
                )

                persistencia.salvar_dados(saldo_atual, transacoes)

    elif opcao == "3":
        saldo.saldo_total(saldo_atual)

    elif opcao == "4":
        historico.mostrar_historico(transacoes)

    elif opcao == "0":
        print("Saindo do caixa eletrônico...")
        time.sleep(1)
        print("Obrigado por utilizar o caixa eletrônico!")
        break

    else:
        print("Opção inválida! Tente novamente.")