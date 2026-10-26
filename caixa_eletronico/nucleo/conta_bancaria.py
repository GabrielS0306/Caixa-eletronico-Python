from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from enum import Enum

from caixa_eletronico.nucleo.seguranca import (
    MAX_TENTATIVAS,
    ContaBloqueadaError,
    Senha
)

CENTAVO = Decimal("0.01")


class ValorInvalidoError(ValueError):
    """Valor que não é um número finito, positivo e com até 2 casas decimais."""


class SaldoInsuficienteError(Exception):
    """Saque ou transferência maior que o saldo disponível."""


class TransferenciaInvalidaError(ValueError):
    """Transferência para a própria conta."""


class TipoTransacao(str, Enum):
    DEPOSITO = "Depósito"
    SAQUE = "Saque"
    TRANSFERENCIA_ENVIADA = "Transferência enviada"
    TRANSFERENCIA_RECEBIDA = "Transferência recebida"


@dataclass(frozen=True)
class Transacao:
    tipo: TipoTransacao
    valor: Decimal
    saldo: Decimal
    # None em transações antigas, salvas antes de a data ser registrada
    data: datetime | None = None
    # Número da outra conta, apenas em transferências
    contraparte: str | None = None


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
    def __init__(
        self, titular="", saldo=0, transacoes=None,
        senha=None, tentativas_falhas=0, numero=""
    ):
        saldo = arredondar(para_decimal(saldo))

        if saldo < 0:
            raise ValorInvalidoError("O saldo não pode ser negativo.")

        self.numero = numero
        self.titular = titular
        self._saldo = saldo
        self._transacoes = list(transacoes or [])
        self._senha = senha
        self._tentativas_falhas = tentativas_falhas

    @property
    def saldo(self):
        return self._saldo

    @property
    def transacoes(self):
        return tuple(self._transacoes)

    @property
    def senha(self):
        return self._senha

    @property
    def possui_pin(self):
        return self._senha is not None

    @property
    def tentativas_falhas(self):
        return self._tentativas_falhas

    @property
    def tentativas_restantes(self):
        return max(MAX_TENTATIVAS - self._tentativas_falhas, 0)

    @property
    def bloqueada(self):
        return self._tentativas_falhas >= MAX_TENTATIVAS

    def definir_pin(self, pin):
        self._senha = Senha.criar(pin)
        self._tentativas_falhas = 0

    def autenticar(self, pin):
        if self._senha is None:
            raise ValueError("Nenhum PIN cadastrado.")

        if self.bloqueada:
            raise ContaBloqueadaError("Conta bloqueada.")

        if self._senha.confere(pin):
            self._tentativas_falhas = 0
            return True

        self._tentativas_falhas += 1
        return False

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

    def transferir(self, destino, valor):
        valor = validar_valor(valor)

        if destino is self or destino.numero == self.numero:
            raise TransferenciaInvalidaError(
                "Não é possível transferir para a própria conta."
            )

        if valor > self._saldo:
            raise SaldoInsuficienteError("Saldo insuficiente!")

        # Tudo foi validado antes: daqui em diante as duas contas mudam juntas
        momento = agora()

        self._saldo -= valor
        self._registrar(
            TipoTransacao.TRANSFERENCIA_ENVIADA, valor, momento, destino.numero
        )

        destino._saldo += valor
        destino._registrar(
            TipoTransacao.TRANSFERENCIA_RECEBIDA, valor, momento, self.numero
        )

        return self._saldo

    def _registrar(self, tipo, valor, momento=None, contraparte=None):
        self._transacoes.append(
            Transacao(
                tipo, valor, self._saldo, momento or agora(), contraparte
            )
        )
