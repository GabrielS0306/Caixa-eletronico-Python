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

class TestPin(unittest.TestCase):
    def setUp(self):
        # Evita gravar no dados.json real durante os testes
        patcher = patch("caixa.persistencia.salvar_conta")
        self.salvar = patcher.start()
        self.addCleanup(patcher.stop)

        self.conta = ContaBancaria()
        self.conta.definir_pin("1234")

    def executar(self, funcao, pins):
        saida = StringIO()

        with patch("caixa.getpass", side_effect=pins):
            with redirect_stdout(saida):
                resultado = funcao(self.conta)

        return resultado, saida.getvalue()

    def test_autenticar_na_primeira(self):
        sucesso, _ = self.executar(caixa.autenticar, ["1234"])

        self.assertTrue(sucesso)

    def test_autenticar_depois_de_errar(self):
        sucesso, resultado = self.executar(
            caixa.autenticar, ["0000", "1111", "1234"]
        )

        self.assertTrue(sucesso)
        self.assertIn("Tentativas restantes: 2", resultado)
        self.assertIn("Tentativas restantes: 1", resultado)
        self.assertEqual(self.conta.tentativas_falhas, 0)

    def test_tres_erros_bloqueiam(self):
        sucesso, resultado = self.executar(
            caixa.autenticar, ["0000", "1111", "2222"]
        )

        self.assertFalse(sucesso)
        self.assertTrue(self.conta.bloqueada)
        self.assertIn("Conta bloqueada", resultado)
        self.assertEqual(self.salvar.call_count, 3)

    def test_conta_ja_bloqueada_nao_pede_pin(self):
        for _ in range(3):
            self.conta.autenticar("0000")

        sucesso, resultado = self.executar(caixa.autenticar, [])

        self.assertFalse(sucesso)
        self.assertIn("Conta bloqueada", resultado)

    def test_cadastrar_pin(self):
        _, resultado = self.executar(
            caixa.cadastrar_pin,
            ["12", "5678", "5679", "5678", "5678"]
        )

        self.assertIn("O PIN deve ter de 4 a 6 dígitos", resultado)
        self.assertIn("Os PINs não conferem", resultado)
        self.assertTrue(self.conta.autenticar("5678"))

class TestFormatarMoeda(unittest.TestCase):
    def test_formato_brasileiro(self):
        self.assertEqual(formatar_moeda(Decimal("1234567.8")), "R$ 1.234.567,80")

    def test_valor_pequeno(self):
        self.assertEqual(formatar_moeda(Decimal("0.5")), "R$ 0,50")

if __name__ == "__main__":
    unittest.main()
