import os
import sys
import time

from datetime import datetime
from getpass import getpass

from caixa_eletronico.nucleo import cedulas
from caixa_eletronico.nucleo import extrato
from caixa_eletronico.interface import historico
from caixa_eletronico.interface import relatorio
from caixa_eletronico.armazenamento import exportacao
from caixa_eletronico.armazenamento import persistencia

from caixa_eletronico.nucleo.banco import ContaNaoEncontradaError
from caixa_eletronico.nucleo.cedulas import CedulasIndisponiveisError
from caixa_eletronico.nucleo.conta_bancaria import (
    SaldoInsuficienteError,
    TransferenciaInvalidaError,
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


def terminal_esconde_pin():
    # No Windows, o terminal integrado do VS Code envia as teclas como
    # sequências de escape; o getpass nunca recebe o Enter e fica travado.
    return not (
        sys.platform == "win32"
        and os.environ.get("TERM_PROGRAM") == "vscode"
    )


def ler_pin(mensagem):
    if terminal_esconde_pin():
        return getpass(mensagem)

    return input(mensagem).strip()


def ler_novo_pin():
    while True:
        pin = ler_pin("Novo PIN (4 a 6 dígitos): ")

        try:
            validar_formato_pin(pin)

        except PinInvalidoError as erro:
            print(erro)
            continue

        if ler_pin("Confirme o PIN: ") != pin:
            print("Os PINs não conferem. Tente novamente.")
            continue

        return pin


def cadastrar_pin(conta):
    conta.definir_pin(ler_novo_pin())
    print("PIN cadastrado com sucesso!")


def tentar_pin(banco, conta, mensagem="Digite seu PIN: "):
    acertou = conta.autenticar(ler_pin(mensagem))

    # Salva a cada tentativa para o bloqueio valer mesmo se o programa for fechado
    persistencia.salvar_banco(banco)

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


def autenticar(banco, conta):
    if conta.bloqueada:
        print(MENSAGEM_BLOQUEIO)
        return False

    while not conta.bloqueada:
        if tentar_pin(banco, conta):
            return True

    return False


def obter_titular():
    while True:
        titular = input("Nome do titular: ").strip()

        if titular:
            return titular

        print("Informe o nome do titular.")


def abrir_conta(banco):
    titular = obter_titular()
    conta = banco.abrir_conta(titular, ler_novo_pin())

    persistencia.salvar_banco(banco)

    print(f"Conta aberta com sucesso! O número da sua conta é {conta.numero}.")
    print("Anote esse número: ele será pedido para acessar a conta.")

    return conta


def acessar_conta(banco):
    numero = input("Número da conta: ")

    try:
        conta = banco.buscar(numero)

    except ContaNaoEncontradaError as erro:
        print(erro)
        return None

    # Conta convertida do formato antigo, de antes de existir PIN ou titular
    if not conta.possui_pin:
        print("Esta conta ainda não tem PIN. Crie um para protegê-la.")

        if not conta.titular:
            conta.titular = obter_titular()

        cadastrar_pin(conta)
        persistencia.salvar_banco(banco)
        return conta

    if not autenticar(banco, conta):
        return None

    if not conta.titular:
        print("Esta conta ainda não tem o nome do titular cadastrado.")
        conta.titular = obter_titular()
        persistencia.salvar_banco(banco)

    return conta


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


def realizar_transferencia(banco, conta):
    numero = input("Número da conta de destino: ")

    try:
        destino = banco.buscar(numero)

    except ContaNaoEncontradaError as erro:
        print(erro)
        return False

    if destino is conta:
        print("Não é possível transferir para a própria conta.")
        return False

    valor = obter_valor("Valor da transferência: R$ ")

    if valor is None:
        return False

    print(
        f"Transferir {formatar_moeda(valor)} para a conta "
        f"{destino.numero} ({destino.titular or 'sem nome'})?"
    )

    if input("Confirma? (s/n): ").strip().lower() != "s":
        print("Transferência cancelada.")
        return False

    try:
        conta.transferir(destino, valor)

    except (SaldoInsuficienteError, TransferenciaInvalidaError) as erro:
        print(erro)
        return False

    print("Transferência realizada com sucesso!")
    return True


def obter_data(mensagem):
    while True:
        texto = input(mensagem).strip()

        if not texto:
            return None

        try:
            return datetime.strptime(texto, "%d/%m/%Y").date()

        except ValueError:
            print("Data inválida! Use o formato dd/mm/aaaa.")


def emitir_extrato(conta):
    print("\nDeixe em branco para não limitar o período.")
    inicio = obter_data("Data inicial (dd/mm/aaaa): ")
    fim = obter_data("Data final (dd/mm/aaaa): ")

    try:
        transacoes = extrato.filtrar_por_periodo(
            conta.transacoes, inicio, fim
        )

    except extrato.PeriodoInvalidoError as erro:
        print(erro)
        return

    if not transacoes:
        print("Nenhuma transação no período informado.")
        return

    historico.mostrar_historico(transacoes, titulo="EXTRATO")

    resumo = relatorio.gerar_relatorio(transacoes, conta.saldo)
    relatorio.mostrar_totais(resumo, sufixo=" no período")

    resposta = input("Exportar para CSV? (s/n): ").strip().lower()

    if resposta != "s":
        return

    try:
        caminho = exportacao.exportar_csv(transacoes, conta.numero)

    except OSError as erro:
        print(f"Erro ao exportar o extrato: {erro}")

    else:
        print(f"Extrato salvo em: {caminho}")


def menu_conta(banco, conta):
    while True:
        print(f"\n===== CONTA {conta.numero} - {conta.titular} =====")
        print("1 - Depósito")
        print("2 - Saque")
        print("3 - Transferência")
        print("4 - Consultar saldo")
        print("5 - Histórico de transações")
        print("6 - Extrato por período")
        print("7 - Relatório da conta")
        print("8 - Alterar PIN")
        print("0 - Sair da conta")

        opcao = input("Escolha uma opção: ").strip()

        if opcao == "1":
            valor = obter_valor("Valor do depósito: R$ ")

            if valor is not None:
                conta.depositar(valor)
                print("Depósito realizado com sucesso!")
                persistencia.salvar_banco(banco)

        elif opcao == "2":
            valor = obter_valor(
                "Valor do saque (múltiplos de "
                f"{formatar_moeda(min(cedulas.CEDULAS))}): R$ "
            )

            if valor is not None and realizar_saque(conta, valor):
                persistencia.salvar_banco(banco)

        elif opcao == "3":
            if realizar_transferencia(banco, conta):
                persistencia.salvar_banco(banco)

        elif opcao == "4":
            print(f"Saldo disponível: {formatar_moeda(conta.saldo)}")

        elif opcao == "5":
            historico.mostrar_historico(conta.transacoes)

        elif opcao == "6":
            emitir_extrato(conta)

        elif opcao == "7":
            relatorio.mostrar_relatorio(conta.transacoes, conta.saldo)

        elif opcao == "8":
            if tentar_pin(banco, conta, "PIN atual: "):
                cadastrar_pin(conta)
                persistencia.salvar_banco(banco)

            elif conta.bloqueada:
                return

        elif opcao == "0":
            print("Sessão encerrada.")
            return

        else:
            print("Opção inválida! Tente novamente.")


def main():
    try:
        banco = persistencia.carregar_banco()

    except persistencia.ArmazenamentoIndisponivelError as erro:
        print(f"Erro: {erro}")
        print("O caixa não pode ser iniciado sem acesso aos dados.")
        return

    if not terminal_esconde_pin():
        print(
            "Aviso: neste terminal o PIN ficará visível ao digitar. "
            "Para escondê-lo, execute fora do VS Code."
        )

    while True:
        print("\n===== CAIXA ELETRÔNICO =====")
        print("1 - Acessar conta")
        print("2 - Abrir nova conta")
        print("0 - Sair")

        opcao = input("Escolha uma opção: ").strip()

        if opcao == "1":
            conta = acessar_conta(banco)

            if conta is not None:
                menu_conta(banco, conta)

        elif opcao == "2":
            menu_conta(banco, abrir_conta(banco))

        elif opcao == "0":
            print("Saindo do caixa eletrônico...")
            time.sleep(1)
            print("Obrigado por utilizar o caixa eletrônico!")
            break

        else:
            print("Opção inválida! Tente novamente.")
