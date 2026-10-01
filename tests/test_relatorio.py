import unittest
import relatorio

from io import StringIO
from contextlib import redirect_stdout

class TestRelatorio(unittest.TestCase):
    def test_relatorio_com_transacoes(self):
        transacoes = [
            {"tipo": "Depósito", "valor": 200.0, "saldo": 200.0},
            {"tipo": "Depósito", "valor": 50.0, "saldo": 250.0},
            {"tipo": "Saque", "valor": 80.0, "saldo": 170.0}
        ]

        saida = StringIO()

        with redirect_stdout(saida):
            relatorio.mostrar_relatorio(transacoes, 170.0)

        resultado = saida.getvalue()

        self.assertIn("Saldo atual: R$ 170.00", resultado)
        self.assertIn("Total depositado: R$ 250.00", resultado)
        self.assertIn("Total sacado: R$ 80.00", resultado)
        self.assertIn("Quantidade de depósitos: 2", resultado)
        self.assertIn("Quantidade de saques: 1", resultado)
        self.assertIn("Total de transações: 3", resultado)

    def test_relatorio_sem_transacoes(self):
        transacoes = []
        saida = StringIO()

        with redirect_stdout(saida):
            relatorio.mostrar_relatorio(transacoes, 0.0)

        resultado = saida.getvalue()

        self.assertIn("Saldo atual: R$ 0.00", resultado)
        self.assertIn("Total depositado: R$ 0.00", resultado)
        self.assertIn("Total sacado: R$ 0.00", resultado)
        self.assertIn("Quantidade de depósitos: 0", resultado)
        self.assertIn("Quantidade de saques: 0", resultado)
        self.assertIn("Total de transações: 0", resultado)

    def test_relatorio_apenas_depositos(self):
        transacoes = [
            {"tipo": "Depósito", "valor": 100.0, "saldo": 100.0},
            {"tipo": "Depósito", "valor": 50.0, "saldo": 150.0}
        ]

        saida = StringIO()

        with redirect_stdout(saida):
            relatorio.mostrar_relatorio(transacoes, 150.0)

        resultado = saida.getvalue()

        self.assertIn("Total depositado: R$ 150.00", resultado)
        self.assertIn("Total sacado: R$ 0.00", resultado)
        self.assertIn("Quantidade de depósitos: 2", resultado)
        self.assertIn("Quantidade de saques: 0", resultado)

if __name__ == "__main__":
    unittest.main()