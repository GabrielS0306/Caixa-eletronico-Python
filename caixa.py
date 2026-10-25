import time

import historico
import relatorio
import persistencia

from conta_bancaria import (
    SaldoInsuficienteError,
    ValorInvalidoError,
    validar_valor
)
from formatacao import formatar_moeda


def obter_valor(mensagem):
    entrada = input(mensagem).strip().replace(",", ".")

    try:
        return validar_valor(entrada)

    except ValorInvalidoError as erro:
        print(erro)
        return None


def main():
    conta = persistencia.carregar_conta()

    while True:
        print("\n===== CAIXA ELETRÔNICO =====")
        print("1 - Depósito")
        print("2 - Saque")
        print("3 - Consultar saldo")
        print("4 - Histórico de transações")
        print("5 - Relatório da conta")
        print("0 - Sair")

        opcao = input("Escolha uma opção: ").strip()

        if opcao == "1":
            valor = obter_valor("Valor do depósito: R$ ")

            if valor is not None:
                conta.depositar(valor)
                print("Depósito realizado com sucesso!")
                persistencia.salvar_conta(conta)

        elif opcao == "2":
            valor = obter_valor("Valor do saque: R$ ")

            if valor is not None:
                try:
                    conta.sacar(valor)

                except SaldoInsuficienteError as erro:
                    print(erro)

                else:
                    print("Saque realizado com sucesso!")
                    persistencia.salvar_conta(conta)

        elif opcao == "3":
            print(f"Saldo disponível: {formatar_moeda(conta.saldo)}")

        elif opcao == "4":
            historico.mostrar_historico(conta.transacoes)

        elif opcao == "5":
            relatorio.mostrar_relatorio(conta.transacoes, conta.saldo)

        elif opcao == "0":
            print("Saindo do caixa eletrônico...")
            time.sleep(1)
            print("Obrigado por utilizar o caixa eletrônico!")
            break

        else:
            print("Opção inválida! Tente novamente.")


if __name__ == "__main__":
    main()
