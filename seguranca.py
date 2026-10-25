import hashlib
import hmac
import secrets

from dataclasses import dataclass

MAX_TENTATIVAS = 3
ITERACOES = 200_000


class PinInvalidoError(ValueError):
    """PIN fora do formato de 4 a 6 dígitos."""


class ContaBloqueadaError(Exception):
    """Conta bloqueada por excesso de tentativas de PIN incorretas."""


def validar_formato_pin(pin):
    # isascii evita que dígitos de outros alfabetos (ex.: "１２３４") passem no isdigit
    if not (pin.isascii() and pin.isdigit() and 4 <= len(pin) <= 6):
        raise PinInvalidoError("O PIN deve ter de 4 a 6 dígitos numéricos.")


def gerar_hash(pin, salt):
    return hashlib.pbkdf2_hmac(
        "sha256", pin.encode("utf-8"), salt, ITERACOES
    ).hex()


@dataclass(frozen=True)
class Senha:
    salt: str
    hash_pin: str

    @classmethod
    def criar(cls, pin):
        validar_formato_pin(pin)
        salt = secrets.token_bytes(16)

        return cls(salt.hex(), gerar_hash(pin, salt))

    def confere(self, pin):
        # compare_digest leva o mesmo tempo para qualquer PIN errado
        calculado = gerar_hash(pin, bytes.fromhex(self.salt))

        return hmac.compare_digest(calculado, self.hash_pin)
