import unittest
import historico

from io import StringIO
from contextlib import redirect_stdout

from conta_bancaria import ContaBancaria

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

    def test_historico_vazio(self):
        resultado = self.mostrar(())

        self.assertIn("Nenhuma transação registrada.", resultado)

if __name__ == "__main__":
    unittest.main()
