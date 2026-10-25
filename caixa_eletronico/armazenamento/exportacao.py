import csv

from datetime import datetime
from pathlib import Path

from caixa_eletronico.formatacao import formatar_data

# Raiz do projeto: armazenamento/ -> caixa_eletronico/ -> raiz
PASTA_EXTRATOS = Path(__file__).resolve().parents[2] / "extratos"


def formatar_numero(valor):
    # Vírgula decimal e sem separador de milhar: o Excel em português lê como número
    return f"{valor:.2f}".replace(".", ",")


def exportar_csv(transacoes, momento=None):
    momento = momento or datetime.now()

    PASTA_EXTRATOS.mkdir(parents=True, exist_ok=True)
    caminho = PASTA_EXTRATOS / f"extrato_{momento:%Y-%m-%d_%H-%M-%S}.csv"

    # utf-8-sig grava o BOM, que faz o Excel reconhecer os acentos;
    # ";" é o separador que o Excel em português espera
    with open(caminho, "w", encoding="utf-8-sig", newline="") as arquivo:
        escritor = csv.writer(arquivo, delimiter=";")
        escritor.writerow(["Data", "Tipo", "Valor", "Saldo após operação"])

        for item in transacoes:
            escritor.writerow([
                formatar_data(item.data) if item.data else "",
                item.tipo.value,
                formatar_numero(item.valor),
                formatar_numero(item.saldo)
            ])

    return caminho
