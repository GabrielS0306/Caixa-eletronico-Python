import unittest

from decimal import Decimal
from io import StringIO
from contextlib import redirect_stdout
from unittest.mock import patch

import caixa

from formatacao import formatar_moeda

class TestObterValor(unittest.TestCase):
    def obter(self, entrada):
        with patch("builtins.input", return_value=entrada):
            with redirect_stdout(StringIO()):
                return caixa.obter_valor("Valor: ")

    def test_aceita_virgula(self):
        self.assertEqual(self.obter("10,50"), Decimal("10.50"))

    def test_aceita_ponto(self):
        self.assertEqual(self.obter(" 99.9 "), Decimal("99.90"))

    def test_rejeita_entradas_invalidas(self):
        for entrada in ("", "abc", "0", "-5", "nan", "inf", "1,234"):
            with self.subTest(entrada=entrada):
                self.assertIsNone(self.obter(entrada))

class TestFormatarMoeda(unittest.TestCase):
    def test_formato_brasileiro(self):
        self.assertEqual(formatar_moeda(Decimal("1234567.8")), "R$ 1.234.567,80")

    def test_valor_pequeno(self):
        self.assertEqual(formatar_moeda(Decimal("0.5")), "R$ 0,50")

if __name__ == "__main__":
    unittest.main()
