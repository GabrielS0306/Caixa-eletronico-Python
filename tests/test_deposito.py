import unittest
import deposito

class TestDeposito(unittest.TestCase):
    def test_deposito_valido(self):
        resultado = deposito.depositar(100, 50)

        self.assertEqual(resultado, 150)

    def test_deposito_zero(self):
        resultado = deposito.depositar(0, 50)

        self.assertEqual(resultado, 50)

    def test_deposito_negativo(self):
        resultado = deposito.depositar(-20, 50)

        self.assertEqual(resultado, 50)

if __name__ == "__main__":
    unittest.main()
