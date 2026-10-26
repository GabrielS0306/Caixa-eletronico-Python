import json
import os
import sqlite3

from contextlib import closing, suppress
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from caixa_eletronico.armazenamento import formato_json
from caixa_eletronico.nucleo.banco import Banco
from caixa_eletronico.nucleo.conta_bancaria import (
    ContaBancaria,
    TipoTransacao,
    Transacao
)

# Raiz do projeto: armazenamento/ -> caixa_eletronico/ -> raiz
RAIZ_PROJETO = Path(__file__).resolve().parents[2]
ARQUIVO_BANCO = RAIZ_PROJETO / "banco.db"
# Arquivo das versões anteriores, importado na primeira execução
ARQUIVO_JSON = RAIZ_PROJETO / "dados.json"

TIPOS = ", ".join(f"'{tipo.value}'" for tipo in TipoTransacao)

# STRICT faz o SQLite recusar valores do tipo errado (ex.: texto em INTEGER).
# Valores em dinheiro são guardados em centavos para não depender de float.
ESQUEMA = f"""
CREATE TABLE IF NOT EXISTS contas (
    numero TEXT PRIMARY KEY,
    titular TEXT NOT NULL,
    saldo_centavos INTEGER NOT NULL CHECK (saldo_centavos >= 0),
    pin_salt TEXT,
    pin_hash TEXT,
    tentativas_falhas INTEGER NOT NULL DEFAULT 0
        CHECK (tentativas_falhas >= 0)
) STRICT;

CREATE TABLE IF NOT EXISTS transacoes (
    id INTEGER PRIMARY KEY,
    numero_conta TEXT NOT NULL REFERENCES contas (numero),
    tipo TEXT NOT NULL CHECK (tipo IN ({TIPOS})),
    valor_centavos INTEGER NOT NULL CHECK (valor_centavos > 0),
    saldo_centavos INTEGER NOT NULL CHECK (saldo_centavos >= 0),
    data TEXT,
    contraparte TEXT
) STRICT;

CREATE INDEX IF NOT EXISTS idx_transacoes_conta
    ON transacoes (numero_conta, id);
"""

SALVAR_CONTA = """
INSERT INTO contas (
    numero, titular, saldo_centavos, pin_salt, pin_hash, tentativas_falhas
)
VALUES (?, ?, ?, ?, ?, ?)
ON CONFLICT (numero) DO UPDATE SET
    titular = excluded.titular,
    saldo_centavos = excluded.saldo_centavos,
    pin_salt = excluded.pin_salt,
    pin_hash = excluded.pin_hash,
    tentativas_falhas = excluded.tentativas_falhas
"""

SALVAR_TRANSACAO = """
INSERT INTO transacoes (
    numero_conta, tipo, valor_centavos, saldo_centavos, data, contraparte
)
VALUES (?, ?, ?, ?, ?, ?)
"""


class ArmazenamentoIndisponivelError(Exception):
    """Os dados existem, mas não puderam ser lidos (arquivo em uso, sem permissão...)."""


def para_centavos(valor):
    return int(valor * 100)


def de_centavos(centavos):
    # scaleb(-2) divide por 100 mantendo exatamente 2 casas: 1050 -> 10.50
    return Decimal(centavos).scaleb(-2)


def conectar(caminho):
    conexao = sqlite3.connect(caminho)

    try:
        conexao.execute("PRAGMA foreign_keys = ON")
        conexao.executescript(ESQUEMA)

    except BaseException:
        # No Windows, um arquivo aberto não pode ser renomeado depois
        conexao.close()
        raise

    return conexao


def ler_banco(conexao):
    contas = []

    linhas_contas = conexao.execute(
        """
        SELECT numero, titular, saldo_centavos,
               pin_salt, pin_hash, tentativas_falhas
        FROM contas
        ORDER BY CAST(numero AS INTEGER)
        """
    ).fetchall()

    for numero, titular, saldo, salt, hash_pin, tentativas in linhas_contas:
        transacoes = [
            Transacao(
                TipoTransacao(tipo),
                de_centavos(valor),
                de_centavos(saldo_transacao),
                formato_json.converter_data(data),
                formato_json.converter_contraparte(contraparte)
            )
            for tipo, valor, saldo_transacao, data, contraparte
            in conexao.execute(
                """
                SELECT tipo, valor_centavos, saldo_centavos, data, contraparte
                FROM transacoes
                WHERE numero_conta = ?
                ORDER BY id
                """,
                (numero,)
            )
        ]

        senha = None

        # Reaproveita a validação do salt, do hash e das tentativas
        if salt is not None or hash_pin is not None:
            senha, tentativas = formato_json.converter_seguranca({
                "salt": salt,
                "hash": hash_pin,
                "tentativas_falhas": tentativas
            })

        contas.append(
            ContaBancaria(
                titular, de_centavos(saldo), transacoes,
                senha, tentativas, numero
            )
        )

    return Banco(contas)


def gravar_banco(caminho, banco):
    with closing(conectar(caminho)) as conexao:
        # "with conexao" abre uma transação: grava tudo ou, se der erro, nada
        with conexao:
            ja_salvas = dict(conexao.execute(
                "SELECT numero_conta, COUNT(*) FROM transacoes "
                "GROUP BY numero_conta"
            ))

            for conta in banco.contas:
                senha = conta.senha

                conexao.execute(SALVAR_CONTA, (
                    conta.numero,
                    conta.titular,
                    para_centavos(conta.saldo),
                    senha.salt if senha else None,
                    senha.hash_pin if senha else None,
                    conta.tentativas_falhas
                ))

                # Transações nunca mudam depois de criadas: basta inserir as novas
                novas = conta.transacoes[ja_salvas.get(conta.numero, 0):]

                conexao.executemany(SALVAR_TRANSACAO, [
                    (
                        conta.numero,
                        item.tipo.value,
                        para_centavos(item.valor),
                        para_centavos(item.saldo),
                        item.data.isoformat() if item.data else None,
                        item.contraparte
                    )
                    for item in novas
                ])


def salvar_banco(banco):
    try:
        gravar_banco(ARQUIVO_BANCO, banco)
        return True

    except sqlite3.Error as erro:
        print(f"Erro ao salvar os dados: {erro}")
        return False


def guardar_corrompido(caminho, erro):
    # Renomeia em vez de apagar: o arquivo pode ser recuperado depois
    destino = caminho.with_name(
        f"{caminho.name}.corrompido-{datetime.now():%Y-%m-%d_%H-%M-%S}"
    )

    try:
        caminho.replace(destino)

    except OSError as erro_copia:
        # Sem a cópia, continuar poderia sobrescrever os dados
        raise ArmazenamentoIndisponivelError(
            f"{caminho.name} está corrompido ({erro}) e não foi possível "
            f"guardar uma cópia dele: {erro_copia}"
        ) from erro_copia

    print(f"Não foi possível carregar {caminho.name}: {erro}")
    print(
        f"O arquivo foi guardado como {destino.name} e o caixa "
        "começará sem contas."
    )


def importar_json():
    if not ARQUIVO_JSON.exists():
        return Banco()

    try:
        with open(ARQUIVO_JSON, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)

        banco = formato_json.dados_para_banco(dados)

    except OSError as erro:
        raise ArmazenamentoIndisponivelError(
            f"Não foi possível ler {ARQUIVO_JSON.name}: {erro}"
        ) from erro

    # JSON malformado, acentos inválidos ou dados fora do formato
    except ValueError as erro:
        guardar_corrompido(ARQUIVO_JSON, erro)
        return Banco()

    # Grava num arquivo à parte e só depois troca: se a importação falhar no
    # meio, não fica um banco.db incompleto que esconderia o dados.json
    temporario = ARQUIVO_BANCO.with_name(f"{ARQUIVO_BANCO.name}.importacao")

    try:
        temporario.unlink(missing_ok=True)
        gravar_banco(temporario, banco)
        os.replace(temporario, ARQUIVO_BANCO)

    except (OSError, sqlite3.Error) as erro:
        raise ArmazenamentoIndisponivelError(
            f"Não foi possível importar {ARQUIVO_JSON.name}: {erro}"
        ) from erro

    finally:
        with suppress(OSError):
            temporario.unlink(missing_ok=True)

    migrado = ARQUIVO_JSON.with_name(f"{ARQUIVO_JSON.name}.migrado")

    # Se a renomeação falhar, nada se perde: o banco.db já tem os dados
    with suppress(OSError):
        ARQUIVO_JSON.replace(migrado)

    print(
        f"Dados importados de {ARQUIVO_JSON.name} para {ARQUIVO_BANCO.name}. "
        f"O arquivo antigo foi guardado como {migrado.name}."
    )

    return banco


def carregar_banco():
    if not ARQUIVO_BANCO.exists():
        return importar_json()

    try:
        with closing(conectar(ARQUIVO_BANCO)) as conexao:
            return ler_banco(conexao)

    # Arquivo em uso, sem permissão de leitura etc.: os dados podem estar
    # íntegros, então não é seguro começar do zero
    except sqlite3.OperationalError as erro:
        raise ArmazenamentoIndisponivelError(
            f"Não foi possível abrir {ARQUIVO_BANCO.name}: {erro}"
        ) from erro

    # Arquivo que não é um banco SQLite ou com dados inválidos
    except (sqlite3.DatabaseError, ValueError) as erro:
        guardar_corrompido(ARQUIVO_BANCO, erro)
        return Banco()
