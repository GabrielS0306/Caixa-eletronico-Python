import time

from getpass import getpass

from caixa_eletronico.nucleo import cedulas
from caixa_eletronico.interface import historico
from caixa_eletronico.interface import relatorio
from caixa_eletronico.armazenamento import persistencia

from caixa_eletronico.nucleo.cedulas import CedulasIndisponiveisError
from caixa_eletronico.nucleo.conta_bancaria import (
    SaldoInsuficienteError,
    ValorInvalidoError,
    validar_valor
)
from caixa_eletronico.formatacao import formatar_moeda
from caixa_eletronico.nucleo.seguranca import (
    MAX_TENTATIVAS,
    PinInvalidoError,
    validar_formato_pin
)

MENSAGEM_BLOQUEIO = (
    f"Conta bloqueada após {MAX_TENTATIVAS} tentativas incorretas. "
    "Procure sua agência."
)


def cadastrar_pin(conta):
    while True:
        pin = getpass("Novo PIN (4 a 6 dígitos): ")

        try:
            validar_formato_pin(pin)

        except PinInvalidoError as erro:
            print(erro)
            continue

        if getpass("Confirme o PIN: ") != pin:
            print("Os PINs não conferem. Tente novamente.")
            continue

        conta.definir_pin(pin)
        print("PIN cadastrado com sucesso!")
        return


def tentar_pin(conta, mensagem="Digite seu PIN: "):
    acertou = conta.autenticar(getpass(mensagem))

    # Salva a cada tentativa para o bloqueio valer mesmo se o programa for fechado
    persistencia.salvar_conta(conta)

    if acertou:
        return True

    if conta.bloqueada:
        print(MENSAGEM_BLOQUEIO)
    else:
        print(
            "PIN incorreto! Tentativas restantes: "
            f"{conta.tentativas_restantes}"
        )

    return False


def autenticar(conta):
    if conta.bloqueada:
        print(MENSAGEM_BLOQUEIO)
        return False

    while not conta.bloqueada:
        if tentar_pin(conta):
            return True

    return False


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

    if not conta.possui_pin:
        print("Nenhum PIN cadastrado. Crie um PIN para proteger sua conta.")
        cadastrar_pin(conta)
        persistencia.salvar_conta(conta)

    elif not autenticar(conta):
        return

    while True:
        print("\n===== CAIXA ELETRÔNICO =====")
        print("1 - Depósito")
        print("2 - Saque")
        print("3 - Consultar saldo")
        print("4 - Histórico de transações")
        print("5 - Relatório da conta")
        print("6 - Alterar PIN")
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

        elif opcao == "6":
            if tentar_pin(conta, "PIN atual: "):
                cadastrar_pin(conta)
                persistencia.salvar_conta(conta)

            elif conta.bloqueada:
                break

        elif opcao == "0":
            print("Saindo do caixa eletrônico...")
            time.sleep(1)
            print("Obrigado por utilizar o caixa eletrônico!")
            break

        else:
            print("Opção inválida! Tente novamente.")
