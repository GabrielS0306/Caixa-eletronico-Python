# Conversão entre as contas e o formato do antigo dados.json. Usado apenas
# para importar os dados de versões anteriores para o SQLite.
from datetime import datetime

from caixa_eletronico.nucleo.banco import NUMERO_INICIAL, Banco
from caixa_eletronico.nucleo.conta_bancaria import (
    ContaBancaria,
    TipoTransacao,
    Transacao,
    ValorInvalidoError,
    arredondar,
    para_decimal
)
from caixa_eletronico.nucleo.seguranca import Senha


def converter_valor(valor):
    # Valores são salvos como texto ("10.50"); números aceitos para ler o formato antigo
    if not isinstance(valor, (str, int, float)):
        raise ValorInvalidoError("Valor com tipo inválido.")

    return arredondar(para_decimal(valor))


def converter_data(data):
    # Transações do formato antigo não têm data
    if data is None:
        return None

    if not isinstance(data, str):
        raise ValueError("Data com tipo inválido.")

    try:
        return datetime.fromisoformat(data)
    except ValueError:
        raise ValueError(f"Data inválida: {data!r}") from None


def converter_seguranca(dados):
    # Contas salvas antes do PIN existir não têm a seção de segurança
    if dados is None:
        return None, 0

    if not isinstance(dados, dict):
        raise ValueError("Dados de segurança inválidos.")

    salt = dados.get("salt")
    hash_pin = dados.get("hash")
    tentativas = dados.get("tentativas_falhas", 0)

    if not (isinstance(salt, str) and salt and isinstance(hash_pin, str) and hash_pin):
        raise ValueError("Dados de segurança inválidos.")

    try:
        bytes.fromhex(salt)
        bytes.fromhex(hash_pin)
    except ValueError:
        raise ValueError("Dados de segurança inválidos.") from None

    if (
        not isinstance(tentativas, int)
        or isinstance(tentativas, bool)
        or tentativas < 0
    ):
        raise ValueError("Número de tentativas inválido.")

    return Senha(salt, hash_pin), tentativas


def converter_contraparte(contraparte):
    if contraparte is None:
        return None

    if not (isinstance(contraparte, str) and contraparte.isdigit()):
        raise ValueError(f"Conta de transferência inválida: {contraparte!r}")

    return contraparte


def conta_para_dados(conta):
    seguranca = None

    if conta.senha is not None:
        seguranca = {
            "salt": conta.senha.salt,
            "hash": conta.senha.hash_pin,
            "tentativas_falhas": conta.tentativas_falhas
        }

    return {
        "numero": conta.numero,
        "titular": conta.titular,
        "seguranca": seguranca,
        "saldo": str(conta.saldo),
        "transacoes": [
            {
                "tipo": item.tipo.value,
                "valor": str(item.valor),
                "saldo": str(item.saldo),
                "data": item.data.isoformat() if item.data else None,
                "contraparte": item.contraparte
            }
            for item in conta.transacoes
        ]
    }


def dados_para_conta(dados):
    if not isinstance(dados, dict):
        raise ValueError("Estrutura inválida.")

    numero = dados.get("numero", "")
    titular = dados.get("titular", "")
    transacoes_dados = dados.get("transacoes")

    if (
        not isinstance(numero, str)
        or not isinstance(titular, str)
        or not isinstance(transacoes_dados, list)
    ):
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
        data = converter_data(item.get("data"))
        contraparte = converter_contraparte(item.get("contraparte"))

        if valor <= 0 or saldo_transacao < 0:
            raise ValueError("Valores de transação inválidos.")

        transacoes.append(
            Transacao(tipo, valor, saldo_transacao, data, contraparte)
        )

    senha, tentativas = converter_seguranca(dados.get("seguranca"))

    return ContaBancaria(
        titular, saldo, transacoes, senha, tentativas, numero
    )


def formato_antigo(dados):
    # Antes de existirem várias contas, o arquivo guardava uma conta só
    return isinstance(dados, dict) and "contas" not in dados


def banco_para_dados(banco):
    return {"contas": [conta_para_dados(conta) for conta in banco.contas]}


def dados_para_banco(dados):
    if formato_antigo(dados):
        conta = dados_para_conta(dados)
        conta.numero = str(NUMERO_INICIAL)

        return Banco([conta])

    if not isinstance(dados, dict) or not isinstance(dados["contas"], list):
        raise ValueError("Estrutura inválida.")

    return Banco([dados_para_conta(item) for item in dados["contas"]])
