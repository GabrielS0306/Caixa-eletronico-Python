from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from enum import Enum

CENTAVO = Decimal("0.01")


class ValorInvalidoError(ValueError):
    """Valor que não é um número finito, positivo e com até 2 casas decimais."""


class SaldoInsuficienteError(Exception):
    """Saque maior que o saldo disponível."""


class TipoTransacao(str, Enum):
    DEPOSITO = "Depósito"
    SAQUE = "Saque"


@dataclass(frozen=True)
class Transacao:
    tipo: TipoTransacao
    valor: Decimal
    saldo: Decimal
    # None em transações antigas, salvas antes de a data ser registrada
    data: datetime | None = None


def agora():
    return datetime.now().replace(microsecond=0)


def para_decimal(valor):
    # bool é subclasse de int, então True viraria 1 sem essa checagem
    if isinstance(valor, bool):
        raise ValorInvalidoError("Entrada inválida! Digite um número.")

    try:
        numero = Decimal(str(valor))
    except InvalidOperation:
        raise ValorInvalidoError("Entrada inválida! Digite um número.") from None

    if not numero.is_finite():
        raise ValorInvalidoError("Digite um número válido e finito.")

    return numero


def arredondar(numero):
    try:
        return numero.quantize(CENTAVO, rounding=ROUND_HALF_UP)
    except InvalidOperation:
        raise ValorInvalidoError("Valor muito grande.") from None


def validar_valor(valor):
    numero = para_decimal(valor)

    if numero <= 0:
        raise ValorInvalidoError("O valor deve ser maior que zero.")

    arredondado = arredondar(numero)

    if arredondado != numero:
        raise ValorInvalidoError("O valor deve ter no máximo 2 casas decimais.")

    return arredondado


class ContaBancaria:
    def __init__(self, titular="", saldo=0, transacoes=None):
        saldo = arredondar(para_decimal(saldo))

        if saldo < 0:
            raise ValorInvalidoError("O saldo não pode ser negativo.")

        self.titular = titular
        self._saldo = saldo
        self._transacoes = list(transacoes or [])

    @property
    def saldo(self):
        return self._saldo

    @property
    def transacoes(self):
        return tuple(self._transacoes)

    def depositar(self, valor):
        valor = validar_valor(valor)

        self._saldo += valor
        self._registrar(TipoTransacao.DEPOSITO, valor)

        return self._saldo

    def sacar(self, valor):
        valor = validar_valor(valor)

        if valor > self._saldo:
            raise SaldoInsuficienteError("Saldo insuficiente!")

        self._saldo -= valor
        self._registrar(TipoTransacao.SAQUE, valor)

        return self._saldo

    def _registrar(self, tipo, valor):
        self._transacoes.append(Transacao(tipo, valor, self._saldo, agora()))
