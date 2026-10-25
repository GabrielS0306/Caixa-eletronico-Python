import unittest
import relatorio

from decimal import Decimal
from io import StringIO
from contextlib import redirect_stdout

from conta_bancaria import ContaBancaria

class TestRelatorio(unittest.TestCase):
    def test_gerar_relatorio(self):
        conta = ContaBancaria()
        conta.depositar(200)
        conta.depositar(50)
        conta.sacar(80)

        resumo = relatorio.gerar_relatorio(conta.transacoes, conta.saldo)

        self.assertEqual(resumo["saldo_atual"], Decimal("170.00"))
        self.assertEqual(resumo["total_depositado"], Decimal("250.00"))
        self.assertEqual(resumo["total_sacado"], Decimal("80.00"))
        self.assertEqual(resumo["quantidade_depositos"], 2)
        self.assertEqual(resumo["quantidade_saques"], 1)
        self.assertEqual(resumo["total_transacoes"], 3)

    def test_relatorio_sem_transacoes(self):
        resumo = relatorio.gerar_relatorio((), Decimal("0.00"))

        self.assertEqual(resumo["total_depositado"], Decimal("0.00"))
        self.assertEqual(resumo["total_sacado"], Decimal("0.00"))
        self.assertEqual(resumo["total_transacoes"], 0)

    def test_mostrar_relatorio(self):
        conta = ContaBancaria()
        conta.depositar(1500)
        conta.sacar(80)

        saida = StringIO()

        with redirect_stdout(saida):
            relatorio.mostrar_relatorio(conta.transacoes, conta.saldo)

        resultado = saida.getvalue()

        self.assertIn("Saldo atual: R$ 1.420,00", resultado)
        self.assertIn("Total depositado: R$ 1.500,00", resultado)
        self.assertIn("Total sacado: R$ 80,00", resultado)
        self.assertIn("Quantidade de depósitos: 1", resultado)
        self.assertIn("Quantidade de saques: 1", resultado)
        self.assertIn("Total de transações: 2", resultado)

if __name__ == "__main__":
    unittest.main()
