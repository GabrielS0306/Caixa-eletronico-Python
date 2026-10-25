import unittest

from caixa_eletronico.nucleo.seguranca import (
    PinInvalidoError,
    Senha,
    validar_formato_pin
)

class TestFormatoPin(unittest.TestCase):
    def test_pins_validos(self):
        for pin in ("1234", "00000", "987654"):
            with self.subTest(pin=pin):
                validar_formato_pin(pin)

    def test_pins_invalidos(self):
        for pin in ("", "123", "1234567", "abcd", "12 34", "12.4", "１２３４"):
            with self.subTest(pin=pin):
                with self.assertRaises(PinInvalidoError):
                    validar_formato_pin(pin)

class TestSenha(unittest.TestCase):
    def test_confere_pin_correto(self):
        senha = Senha.criar("1234")

        self.assertTrue(senha.confere("1234"))
        self.assertFalse(senha.confere("4321"))

    def test_pin_nao_fica_salvo(self):
        senha = Senha.criar("1234")

        self.assertNotIn("1234", senha.salt + senha.hash_pin)

    def test_salt_diferente_gera_hash_diferente(self):
        primeira = Senha.criar("1234")
        segunda = Senha.criar("1234")

        self.assertNotEqual(primeira.salt, segunda.salt)
        self.assertNotEqual(primeira.hash_pin, segunda.hash_pin)

    def test_criar_com_pin_invalido(self):
        with self.assertRaises(PinInvalidoError):
            Senha.criar("12")

if __name__ == "__main__":
    unittest.main()
