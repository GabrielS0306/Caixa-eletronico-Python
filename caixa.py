import time

import cedulas
import historico
import relatorio
import persistencia

from cedulas import CedulasIndisponiveisError
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


def realizar_saque(conta, valor):
    try:
        # Calcula as cédulas antes de sacar para não debitar um valor que o caixa não consegue entregar
        notas = cedulas.calcular_cedulas(valor)
        conta.sacar(valor)

    except (CedulasIndisponiveisError, SaldoInsuficienteError) as erro:
        print(erro)
        return False

    print("Saque realizado com sucesso!")
    print("Retire suas cédulas:")

    for cedula, quantidade in notas.items():
        print(f"  {quantidade} x {formatar_moeda(cedula)}")

    return True


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
            valor = obter_valor(
                "Valor do saque (múltiplos de "
                f"{formatar_moeda(min(cedulas.CEDULAS))}): R$ "
            )

            if valor is not None and realizar_saque(conta, valor):
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
