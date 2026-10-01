import unittest
import historico

class TestHistorico(unittest.TestCase):
    def setUp(self):
        self.transacoes = []

    def test_registrar_transacao(self):
        historico.registrar_transacao(
            self.transacoes, "Depósito", 100, 100
        )

        self.assertEqual(len(self.transacoes), 1)
        self.assertEqual(self.transacoes[0]["tipo"], "Depósito")
        self.assertEqual(self.transacoes[0]["valor"], 100)
        self.assertEqual(self.transacoes[0]["saldo"], 100)

    def test_registrar_varias_transacoes(self):
        historico.registrar_transacao(
            self.transacoes, "Depósito", 200, 200
        )

        historico.registrar_transacao(
            self.transacoes, "Saque", 50, 150
        )

        self.assertEqual(len(self.transacoes), 2)

    def test_historico_vazio(self):
        self.assertEqual(self.transacoes, [])

if __name__ == "__main__":
    unittest.main()
