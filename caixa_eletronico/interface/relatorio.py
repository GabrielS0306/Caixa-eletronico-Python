from decimal import Decimal

from caixa_eletronico.nucleo.conta_bancaria import TipoTransacao
from caixa_eletronico.formatacao import formatar_moeda


def gerar_relatorio(transacoes, saldo_atual):
    resumo = {
        "saldo_atual": saldo_atual,
        "total_depositado": Decimal("0.00"),
        "total_sacado": Decimal("0.00"),
        "quantidade_depositos": 0,
        "quantidade_saques": 0,
        "total_transacoes": len(transacoes)
    }

    for item in transacoes:
        if item.tipo is TipoTransacao.DEPOSITO:
            resumo["total_depositado"] += item.valor
            resumo["quantidade_depositos"] += 1
        else:
            resumo["total_sacado"] += item.valor
            resumo["quantidade_saques"] += 1

    return resumo


def mostrar_relatorio(transacoes, saldo_atual):
    resumo = gerar_relatorio(transacoes, saldo_atual)

    print("\n===== RELATÓRIO DA CONTA =====")
    print(f"Saldo atual: {formatar_moeda(resumo['saldo_atual'])}")
    print(f"Total depositado: {formatar_moeda(resumo['total_depositado'])}")
    print(f"Total sacado: {formatar_moeda(resumo['total_sacado'])}")
    print(f"Quantidade de depósitos: {resumo['quantidade_depositos']}")
    print(f"Quantidade de saques: {resumo['quantidade_saques']}")
    print(f"Total de transações: {resumo['total_transacoes']}")
    print("==============================")
