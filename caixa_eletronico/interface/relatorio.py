from decimal import Decimal

from caixa_eletronico.nucleo.conta_bancaria import TipoTransacao
from caixa_eletronico.formatacao import formatar_moeda

# Chaves do resumo (total, quantidade) usadas para cada tipo de transação
CHAVES_POR_TIPO = {
    TipoTransacao.DEPOSITO: ("total_depositado", "quantidade_depositos"),
    TipoTransacao.SAQUE: ("total_sacado", "quantidade_saques"),
    TipoTransacao.TRANSFERENCIA_ENVIADA: (
        "total_enviado", "quantidade_enviadas"
    ),
    TipoTransacao.TRANSFERENCIA_RECEBIDA: (
        "total_recebido", "quantidade_recebidas"
    )
}


def gerar_relatorio(transacoes, saldo_atual):
    resumo = {
        "saldo_atual": saldo_atual,
        "total_transacoes": len(transacoes)
    }

    for chave_total, chave_quantidade in CHAVES_POR_TIPO.values():
        resumo[chave_total] = Decimal("0.00")
        resumo[chave_quantidade] = 0

    for item in transacoes:
        chave_total, chave_quantidade = CHAVES_POR_TIPO[item.tipo]

        resumo[chave_total] += item.valor
        resumo[chave_quantidade] += 1

    return resumo


def mostrar_totais(resumo, sufixo=""):
    print(
        f"Total depositado{sufixo}: "
        f"{formatar_moeda(resumo['total_depositado'])}"
    )
    print(f"Total sacado{sufixo}: {formatar_moeda(resumo['total_sacado'])}")
    print(
        f"Total enviado em transferências{sufixo}: "
        f"{formatar_moeda(resumo['total_enviado'])}"
    )
    print(
        f"Total recebido em transferências{sufixo}: "
        f"{formatar_moeda(resumo['total_recebido'])}"
    )


def mostrar_relatorio(transacoes, saldo_atual):
    resumo = gerar_relatorio(transacoes, saldo_atual)

    print("\n===== RELATÓRIO DA CONTA =====")
    print(f"Saldo atual: {formatar_moeda(resumo['saldo_atual'])}")
    mostrar_totais(resumo)
    print(f"Quantidade de depósitos: {resumo['quantidade_depositos']}")
    print(f"Quantidade de saques: {resumo['quantidade_saques']}")
    print(
        "Quantidade de transferências enviadas: "
        f"{resumo['quantidade_enviadas']}"
    )
    print(
        "Quantidade de transferências recebidas: "
        f"{resumo['quantidade_recebidas']}"
    )
    print(f"Total de transações: {resumo['total_transacoes']}")
    print("==============================")
