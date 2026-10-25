import unittest
from caixa_eletronico.interface import historico

from datetime import datetime
from decimal import Decimal
from io import StringIO
from contextlib import redirect_stdout
from unittest.mock import patch

from caixa_eletronico.nucleo.conta_bancaria import (
    ContaBancaria,
    TipoTransacao,
    Transacao
)

class TestHistorico(unittest.TestCase):
    def mostrar(self, transacoes):
        saida = StringIO()

        with redirect_stdout(saida):
            historico.mostrar_historico(transacoes)

        return saida.getvalue()

    def test_historico_com_transacoes(self):
        conta = ContaBancaria()
        conta.depositar(1200)
        conta.sacar("50.25")

        resultado = self.mostrar(conta.transacoes)

        self.assertIn("Tipo: Depósito", resultado)
        self.assertIn("Valor: R$ 1.200,00", resultado)
        self.assertIn("Tipo: Saque", resultado)
        self.assertIn("Valor: R$ 50,25", resultado)
        self.assertIn("Saldo após operação: R$ 1.149,75", resultado)

    def test_historico_mostra_data(self):
        conta = ContaBancaria()

        with patch(
            "caixa_eletronico.nucleo.conta_bancaria.agora",
            return_value=datetime(2026, 10, 25, 9, 5, 0)
        ):
            conta.depositar(10)

        resultado = self.mostrar(conta.transacoes)

        self.assertIn("Data: 25/10/2026 09:05:00", resultado)

    def test_transacao_antiga_sem_data(self):
        transacoes = (
            Transacao(TipoTransacao.DEPOSITO, Decimal("10.00"), Decimal("10.00")),
        )

        resultado = self.mostrar(transacoes)

        self.assertIn("Data: não registrada", resultado)

    def test_historico_vazio(self):
        resultado = self.mostrar(())

        self.assertIn("Nenhuma transação registrada.", resultado)

if __name__ == "__main__":
    unittest.main()
