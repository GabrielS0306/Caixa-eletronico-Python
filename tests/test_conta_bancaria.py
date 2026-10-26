import unittest

from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

from caixa_eletronico.nucleo.conta_bancaria import (
    ContaBancaria,
    SaldoInsuficienteError,
    TipoTransacao,
    TransferenciaInvalidaError,
    ValorInvalidoError
)
from caixa_eletronico.nucleo.seguranca import ContaBloqueadaError

class TestDeposito(unittest.TestCase):
    def setUp(self):
        self.conta = ContaBancaria(saldo=50)

    def test_deposito_valido(self):
        resultado = self.conta.depositar(100)

        self.assertEqual(resultado, Decimal("150.00"))
        self.assertEqual(self.conta.saldo, Decimal("150.00"))

    def test_deposito_zero(self):
        with self.assertRaises(ValorInvalidoError):
            self.conta.depositar(0)

        self.assertEqual(self.conta.saldo, Decimal("50.00"))

    def test_deposito_negativo(self):
        with self.assertRaises(ValorInvalidoError):
            self.conta.depositar(-20)

        self.assertEqual(self.conta.saldo, Decimal("50.00"))

    def test_deposito_registra_transacao(self):
        self.conta.depositar("25.50")

        transacao = self.conta.transacoes[0]

        self.assertEqual(transacao.tipo, TipoTransacao.DEPOSITO)
        self.assertEqual(transacao.valor, Decimal("25.50"))
        self.assertEqual(transacao.saldo, Decimal("75.50"))

class TestSaque(unittest.TestCase):
    def setUp(self):
        self.conta = ContaBancaria(saldo=100)

    def test_saque_valido(self):
        resultado = self.conta.sacar(30)

        self.assertEqual(resultado, Decimal("70.00"))

    def test_saque_saldo_insuficiente(self):
        with self.assertRaises(SaldoInsuficienteError):
            self.conta.sacar(150)

        self.assertEqual(self.conta.saldo, Decimal("100.00"))
        self.assertEqual(self.conta.transacoes, ())

    def test_saque_zero(self):
        with self.assertRaises(ValorInvalidoError):
            self.conta.sacar(0)

    def test_saque_negativo(self):
        with self.assertRaises(ValorInvalidoError):
            self.conta.sacar(-20)

        self.assertEqual(self.conta.saldo, Decimal("100.00"))

    def test_saque_saldo_exato(self):
        resultado = self.conta.sacar(100)

        self.assertEqual(resultado, Decimal("0.00"))

    def test_saque_registra_transacao(self):
        self.conta.sacar(40)

        transacao = self.conta.transacoes[0]

        self.assertEqual(transacao.tipo, TipoTransacao.SAQUE)
        self.assertEqual(transacao.saldo, Decimal("60.00"))

class TestValidacao(unittest.TestCase):
    def setUp(self):
        self.conta = ContaBancaria()

    def test_sem_erro_de_arredondamento(self):
        self.conta.depositar(0.1)
        self.conta.depositar(0.2)

        self.assertEqual(self.conta.saldo, Decimal("0.30"))

    def test_mais_de_duas_casas_decimais(self):
        with self.assertRaises(ValorInvalidoError):
            self.conta.depositar("10.555")

    def test_valores_nao_finitos(self):
        for valor in ("nan", "inf", float("inf"), float("nan")):
            with self.subTest(valor=valor):
                with self.assertRaises(ValorInvalidoError):
                    self.conta.depositar(valor)

    def test_texto_invalido(self):
        with self.assertRaises(ValorInvalidoError):
            self.conta.depositar("abc")

    def test_booleano(self):
        with self.assertRaises(ValorInvalidoError):
            self.conta.depositar(True)

    def test_saldo_inicial_negativo(self):
        with self.assertRaises(ValorInvalidoError):
            ContaBancaria(saldo=-10)

    def test_transacoes_nao_podem_ser_alteradas_por_fora(self):
        self.assertIsInstance(self.conta.transacoes, tuple)

class TestDataTransacao(unittest.TestCase):
    def test_transacao_registra_data_e_hora(self):
        momento = datetime(2026, 10, 25, 14, 30, 5)
        conta = ContaBancaria()

        with patch(
            "caixa_eletronico.nucleo.conta_bancaria.agora",
            return_value=momento
        ):
            conta.depositar(100)
            conta.sacar(40)

        self.assertEqual(conta.transacoes[0].data, momento)
        self.assertEqual(conta.transacoes[1].data, momento)

    def test_data_sem_microssegundos(self):
        conta = ContaBancaria()
        conta.depositar(10)

        self.assertEqual(conta.transacoes[0].data.microsecond, 0)

class TestPin(unittest.TestCase):
    def setUp(self):
        self.conta = ContaBancaria()
        self.conta.definir_pin("1234")

    def test_conta_nova_sem_pin(self):
        self.assertFalse(ContaBancaria().possui_pin)

    def test_pin_correto(self):
        self.assertTrue(self.conta.possui_pin)
        self.assertTrue(self.conta.autenticar("1234"))

    def test_pin_incorreto_reduz_tentativas(self):
        self.assertFalse(self.conta.autenticar("0000"))
        self.assertEqual(self.conta.tentativas_restantes, 2)

    def test_acerto_zera_tentativas(self):
        self.conta.autenticar("0000")
        self.conta.autenticar("1234")

        self.assertEqual(self.conta.tentativas_falhas, 0)

    def test_tres_erros_bloqueiam_a_conta(self):
        for _ in range(3):
            self.conta.autenticar("0000")

        self.assertTrue(self.conta.bloqueada)

        with self.assertRaises(ContaBloqueadaError):
            self.conta.autenticar("1234")

    def test_autenticar_sem_pin(self):
        with self.assertRaises(ValueError):
            ContaBancaria().autenticar("1234")

class TestTransferencia(unittest.TestCase):
    def setUp(self):
        self.origem = ContaBancaria("Ana", saldo=100, numero="1001")
        self.destino = ContaBancaria("Bruno", saldo=10, numero="1002")

    def nada_mudou(self):
        self.assertEqual(self.origem.saldo, Decimal("100.00"))
        self.assertEqual(self.destino.saldo, Decimal("10.00"))
        self.assertEqual(self.origem.transacoes, ())
        self.assertEqual(self.destino.transacoes, ())

    def test_transferencia_valida(self):
        momento = datetime(2026, 10, 25, 16, 0, 0)

        with patch(
            "caixa_eletronico.nucleo.conta_bancaria.agora",
            return_value=momento
        ):
            resultado = self.origem.transferir(self.destino, "30.25")

        self.assertEqual(resultado, Decimal("69.75"))
        self.assertEqual(self.destino.saldo, Decimal("40.25"))

        enviada = self.origem.transacoes[0]
        recebida = self.destino.transacoes[0]

        self.assertEqual(enviada.tipo, TipoTransacao.TRANSFERENCIA_ENVIADA)
        self.assertEqual(enviada.contraparte, "1002")
        self.assertEqual(enviada.saldo, Decimal("69.75"))
        self.assertEqual(recebida.tipo, TipoTransacao.TRANSFERENCIA_RECEBIDA)
        self.assertEqual(recebida.contraparte, "1001")
        self.assertEqual(recebida.saldo, Decimal("40.25"))
        self.assertEqual(enviada.data, momento)
        self.assertEqual(recebida.data, momento)

    def test_transferir_todo_o_saldo(self):
        self.origem.transferir(self.destino, 100)

        self.assertEqual(self.origem.saldo, Decimal("0.00"))

    def test_saldo_insuficiente_nao_altera_nenhuma_conta(self):
        with self.assertRaises(SaldoInsuficienteError):
            self.origem.transferir(self.destino, "100.01")

        self.nada_mudou()

    def test_valor_invalido_nao_altera_nenhuma_conta(self):
        for valor in (0, -5, "abc", "1.001"):
            with self.subTest(valor=valor):
                with self.assertRaises(ValorInvalidoError):
                    self.origem.transferir(self.destino, valor)

        self.nada_mudou()

    def test_para_a_propria_conta(self):
        with self.assertRaises(TransferenciaInvalidaError):
            self.origem.transferir(self.origem, 10)

        self.nada_mudou()

if __name__ == "__main__":
    unittest.main()
