from caixa_eletronico.nucleo.conta_bancaria import ContaBancaria

NUMERO_INICIAL = 1001


class ContaNaoEncontradaError(LookupError):
    """Número de conta que não existe no banco."""


class Banco:
    def __init__(self, contas=None):
        self._contas = {}

        for conta in contas or []:
            if not (isinstance(conta.numero, str) and conta.numero.isdigit()):
                raise ValueError(f"Número de conta inválido: {conta.numero!r}")

            if conta.numero in self._contas:
                raise ValueError(f"Número de conta repetido: {conta.numero}")

            self._contas[conta.numero] = conta

    @property
    def contas(self):
        return tuple(self._contas.values())

    def proximo_numero(self):
        maior = max(
            (int(numero) for numero in self._contas),
            default=NUMERO_INICIAL - 1
        )

        return str(maior + 1)

    def abrir_conta(self, titular, pin):
        titular = titular.strip()

        if not titular:
            raise ValueError("Informe o nome do titular.")

        conta = ContaBancaria(titular, numero=self.proximo_numero())
        # Define o PIN antes de adicionar: se ele for inválido, nada muda
        conta.definir_pin(pin)

        self._contas[conta.numero] = conta
        return conta

    def buscar(self, numero):
        numero = numero.strip()

        try:
            return self._contas[numero]
        except KeyError:
            raise ContaNaoEncontradaError(
                f"Conta {numero} não encontrada."
            ) from None
