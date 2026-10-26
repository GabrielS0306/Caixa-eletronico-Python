from caixa_eletronico.formatacao import formatar_data, formatar_moeda
from caixa_eletronico.nucleo.conta_bancaria import TipoTransacao


def mostrar_historico(transacoes, titulo="HISTÓRICO"):
    if not transacoes:
        print("Nenhuma transação registrada.")
        return

    print(f"\n=== {titulo} ===")

    for item in transacoes:
        print(f"Data: {formatar_data(item.data)}")
        print(f"Tipo: {item.tipo.value}")

        if item.contraparte:
            if item.tipo is TipoTransacao.TRANSFERENCIA_ENVIADA:
                print(f"Para a conta: {item.contraparte}")
            else:
                print(f"Da conta: {item.contraparte}")

        print(f"Valor: {formatar_moeda(item.valor)}")
        print(f"Saldo após operação: {formatar_moeda(item.saldo)}")
        print("--------------------")
