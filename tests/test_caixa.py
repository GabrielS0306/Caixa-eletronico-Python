import unittest

from decimal import Decimal
from io import StringIO
from contextlib import redirect_stdout
from unittest.mock import patch

import caixa

from conta_bancaria import ContaBancaria
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

class TestRealizarSaque(unittest.TestCase):
    def sacar(self, conta, valor):
        saida = StringIO()

        with redirect_stdout(saida):
            sucesso = caixa.realizar_saque(conta, Decimal(valor))

        return sucesso, saida.getvalue()

    def test_saque_mostra_cedulas(self):
        conta = ContaBancaria(saldo=500)

        sucesso, resultado = self.sacar(conta, "270")

        self.assertTrue(sucesso)
        self.assertEqual(conta.saldo, Decimal("230.00"))
        self.assertIn("1 x R$ 200,00", resultado)
        self.assertIn("1 x R$ 50,00", resultado)
        self.assertIn("1 x R$ 20,00", resultado)

    def test_valor_indisponivel_nao_debita(self):
        conta = ContaBancaria(saldo=500)

        sucesso, resultado = self.sacar(conta, "25")

        self.assertFalse(sucesso)
        self.assertEqual(conta.saldo, Decimal("500.00"))
        self.assertEqual(conta.transacoes, ())
        self.assertIn("Valor indisponível", resultado)

    def test_saldo_insuficiente(self):
        conta = ContaBancaria(saldo=50)

        sucesso, resultado = self.sacar(conta, "100")

        self.assertFalse(sucesso)
        self.assertEqual(conta.saldo, Decimal("50.00"))
        self.assertIn("Saldo insuficiente!", resultado)

class TestFormatarMoeda(unittest.TestCase):
    def test_formato_brasileiro(self):
        self.assertEqual(formatar_moeda(Decimal("1234567.8")), "R$ 1.234.567,80")

    def test_valor_pequeno(self):
        self.assertEqual(formatar_moeda(Decimal("0.5")), "R$ 0,50")

if __name__ == "__main__":
    unittest.main()
