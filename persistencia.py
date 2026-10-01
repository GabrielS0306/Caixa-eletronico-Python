import json
import math
from pathlib import Path

ARQUIVO_DADOS = Path(__file__).with_name("dados.json")

def validar_numero(valor):
    return (
        isinstance(valor, (int, float))
        and not isinstance(valor, bool)
        and math.isfinite(valor)
    )

def validar_dados(dados):
    if not isinstance(dados, dict):
        return False

    saldo = dados.get("saldo")
    transacoes = dados.get("transacoes")

    if not validar_numero(saldo) or saldo < 0:
        return False

    if not isinstance(transacoes, list):
        return False

    for item in transacoes:
        if not isinstance(item, dict):
            return False

        tipo = item.get("tipo")
        valor = item.get("valor")
        saldo_transacao = item.get("saldo")

        if tipo not in ("Depósito", "Saque"):
            return False

        if not validar_numero(valor) or valor <= 0:
            return False

        if not validar_numero(saldo_transacao) or saldo_transacao < 0:
            return False

    return True

def salvar_dados(saldo, transacoes):
    dados = {
        "saldo": saldo,
        "transacoes": transacoes
    }

    if not validar_dados(dados):
        print("Erro: os dados não são válidos para salvar.")
        return False

    try:
        with open(ARQUIVO_DADOS, "w", encoding="utf-8") as arquivo:
            json.dump(
                dados,
                arquivo,
                indent=4,
                ensure_ascii=False,
                allow_nan=False
            )

        return True

    except (OSError, TypeError, ValueError) as erro:
        print(f"Erro ao salvar os dados: {erro}")
        return False

def carregar_dados():
    if not ARQUIVO_DADOS.exists():
        return 0.0, []

    try:
        with open(ARQUIVO_DADOS, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)

        if not validar_dados(dados):
            raise ValueError("Estrutura ou valores inválidos.")

        return float(dados["saldo"]), dados["transacoes"]

    except (json.JSONDecodeError, OSError, ValueError) as erro:
        print(f"Não foi possível carregar os dados: {erro}")
        print("Iniciando com valores padrão.")
        return 0.0, []