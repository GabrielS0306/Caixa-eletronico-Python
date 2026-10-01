import json
from pathlib import Path

ARQUIVO_DADOS = Path(__file__).with_name("dados.json")

def salvar_dados(saldo, transacoes):
    dados = {
        "saldo": saldo,
        "transacoes": transacoes
    }

    with open(ARQUIVO_DADOS, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, indent=4, ensure_ascii=False)

def carregar_dados():
    if not ARQUIVO_DADOS.exists():
        return 0.0, []

    try:
        with open(ARQUIVO_DADOS, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)

        saldo = float(dados["saldo"])
        transacoes = dados["transacoes"]

        if not isinstance(transacoes, list):
            raise ValueError("Histórico inválido.")

        return saldo, transacoes

    except (json.JSONDecodeError, KeyError, TypeError, ValueError, OSError):
        print("Não foi possível carregar os dados. Iniciando com valores padrão.")

        return 0.0, []