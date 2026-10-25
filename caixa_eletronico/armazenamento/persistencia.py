import json
from datetime import datetime
from pathlib import Path

from caixa_eletronico.nucleo.conta_bancaria import (
    ContaBancaria,
    TipoTransacao,
    Transacao,
    ValorInvalidoError,
    arredondar,
    para_decimal
)
from caixa_eletronico.nucleo.seguranca import Senha

# Raiz do projeto: armazenamento/ -> caixa_eletronico/ -> raiz
ARQUIVO_DADOS = Path(__file__).resolve().parents[2] / "dados.json"


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


def conta_para_dados(conta):
    seguranca = None

    if conta.senha is not None:
        seguranca = {
            "salt": conta.senha.salt,
            "hash": conta.senha.hash_pin,
            "tentativas_falhas": conta.tentativas_falhas
        }

    return {
        "titular": conta.titular,
        "seguranca": seguranca,
        "saldo": str(conta.saldo),
        "transacoes": [
            {
                "tipo": item.tipo.value,
                "valor": str(item.valor),
                "saldo": str(item.saldo),
                "data": item.data.isoformat() if item.data else None
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
        data = converter_data(item.get("data"))

        if valor <= 0 or saldo_transacao < 0:
            raise ValueError("Valores de transação inválidos.")

        transacoes.append(Transacao(tipo, valor, saldo_transacao, data))

    senha, tentativas = converter_seguranca(dados.get("seguranca"))

    return ContaBancaria(titular, saldo, transacoes, senha, tentativas)


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
