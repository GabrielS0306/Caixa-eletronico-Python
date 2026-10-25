import unittest

from decimal import Decimal

import cedulas

from cedulas import CEDULAS, CedulasIndisponiveisError

def menor_quantidade_de_notas(valor):
    # Força bruta (programação dinâmica) para conferir o algoritmo guloso
    infinito = float("inf")
    minimo = [0] + [infinito] * valor

    for parcial in range(1, valor + 1):
        for cedula in CEDULAS:
            if cedula <= parcial:
                minimo[parcial] = min(minimo[parcial], minimo[parcial - cedula] + 1)

    return minimo[valor]

class TestCalcularCedulas(unittest.TestCase):
    def test_combinacao_de_cedulas(self):
        resultado = cedulas.calcular_cedulas(Decimal("370.00"))

        self.assertEqual(resultado, {200: 1, 100: 1, 50: 1, 20: 1})

    def test_menor_cedula(self):
        self.assertEqual(cedulas.calcular_cedulas(Decimal("10.00")), {10: 1})

    def test_varias_cedulas_iguais(self):
        self.assertEqual(cedulas.calcular_cedulas(Decimal("1000.00")), {200: 5})

    def test_valores_indisponiveis(self):
        for valor in ("5.00", "15.00", "10.50", "0.99"):
            with self.subTest(valor=valor):
                with self.assertRaises(CedulasIndisponiveisError):
                    cedulas.calcular_cedulas(Decimal(valor))

    def test_soma_e_quantidade_minima(self):
        for valor in range(10, 2001, 10):
            with self.subTest(valor=valor):
                resultado = cedulas.calcular_cedulas(Decimal(valor))

                soma = sum(cedula * qtd for cedula, qtd in resultado.items())

                self.assertEqual(soma, valor)
                self.assertEqual(
                    sum(resultado.values()),
                    menor_quantidade_de_notas(valor)
                )

if __name__ == "__main__":
    unittest.main()
