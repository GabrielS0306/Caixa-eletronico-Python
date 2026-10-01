import unittest
import saque

class TestSaque(unittest.TestCase):
    def test_saque_valido(self):
        resultado = saque.sacar(30, 100)

        self.assertEqual(resultado, 70)

    def test_saque_saldo_insuficiente(self):
        resultado = saque.sacar(150, 100)

        self.assertEqual(resultado, 100)

    def test_saque_zero(self):
        resultado = saque.sacar(0, 100)

        self.assertEqual(resultado, 100)

    def test_saque_negativo(self):
        resultado = saque.sacar(-20, 100)

        self.assertEqual(resultado, 100)

    def test_saque_saldo_exato(self):
        resultado = saque.sacar(100, 100)

        self.assertEqual(resultado, 0)

if __name__ == "__main__":
    unittest.main()
