import json
from pathlib import Path

from conta_bancaria import (
    ContaBancaria,
    TipoTransacao,
    Transacao,
    ValorInvalidoError,
    arredondar,
    para_decimal
)

ARQUIVO_DADOS = Path(__file__).with_name("dados.json")


def converter_valor(valor):
    # Valores são salvos como texto ("10.50"); números aceitos para ler o formato antigo
    if not isinstance(valor, (str, int, float)):
        raise ValorInvalidoError("Valor com tipo inválido.")

    return arredondar(para_decimal(valor))


def conta_para_dados(conta):
    return {
        "titular": conta.titular,
        "saldo": str(conta.saldo),
        "transacoes": [
            {
                "tipo": item.tipo.value,
                "valor": str(item.valor),
                "saldo": str(item.saldo)
            }
            for item in conta.transacoes
        ]
    }


def dados_para_conta(dados):
    if not isinstance(dados, dict):
        raise ValueError("Estrutura inválida.")

    titular = dados.get("titular", "")
    transacoes_dados = dados.get("transacoes")

    if not isinstance(titular, str) or not isinstance(transacoes_dados, list):
        raise ValueError("Estrutura inválida.")

    saldo = converter_valor(dados.get("saldo"))

    if saldo < 0:
        raise ValueError("Saldo negativo.")

    transacoes = []

    for item in transacoes_dados:
        if not isinstance(item, dict):
            raise ValueError("Transação inválida.")

        try:
            tipo = TipoTransacao(item.get("tipo"))
        except ValueError:
            raise ValueError(
                f"Tipo de transação inválido: {item.get('tipo')!r}"
            ) from None

        valor = converter_valor(item.get("valor"))
        saldo_transacao = converter_valor(item.get("saldo"))

        if valor <= 0 or saldo_transacao < 0:
            raise ValueError("Valores de transação inválidos.")

        transacoes.append(Transacao(tipo, valor, saldo_transacao))

    return ContaBancaria(titular, saldo, transacoes)


def salvar_conta(conta):
    try:
        with open(ARQUIVO_DADOS, "w", encoding="utf-8") as arquivo:
            json.dump(
                conta_para_dados(conta),
                arquivo,
                indent=4,
                ensure_ascii=False
            )

        return True

    except OSError as erro:
        print(f"Erro ao salvar os dados: {erro}")
        return False


def carregar_conta():
    if not ARQUIVO_DADOS.exists():
        return ContaBancaria()

    try:
        with open(ARQUIVO_DADOS, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)

        return dados_para_conta(dados)

    except (OSError, ValueError) as erro:
        print(f"Não foi possível carregar os dados: {erro}")
        print("Iniciando com valores padrão.")
        return ContaBancaria()
