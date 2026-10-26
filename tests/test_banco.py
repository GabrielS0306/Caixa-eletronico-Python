import unittest

from caixa_eletronico.nucleo.banco import Banco, ContaNaoEncontradaError
from caixa_eletronico.nucleo.conta_bancaria import ContaBancaria
from caixa_eletronico.nucleo.seguranca import PinInvalidoError

class TestBanco(unittest.TestCase):
    def setUp(self):
        self.banco = Banco()

    def test_banco_vazio(self):
        self.assertEqual(self.banco.contas, ())

    def test_numeros_sequenciais(self):
        primeira = self.banco.abrir_conta("Ana", "1234")
        segunda = self.banco.abrir_conta("Bruno", "5678")

        self.assertEqual(primeira.numero, "1001")
        self.assertEqual(segunda.numero, "1002")

    def test_proximo_numero_continua_do_maior(self):
        banco = Banco([ContaBancaria(numero="1005"), ContaBancaria(numero="1002")])

        self.assertEqual(banco.abrir_conta("Carla", "1234").numero, "1006")

    def test_conta_aberta_tem_pin_e_titular(self):
        conta = self.banco.abrir_conta("  Ana  ", "1234")

        self.assertEqual(conta.titular, "Ana")
        self.assertTrue(conta.autenticar("1234"))

    def test_titular_vazio(self):
        with self.assertRaises(ValueError):
            self.banco.abrir_conta("   ", "1234")

        self.assertEqual(self.banco.contas, ())

    def test_pin_invalido_nao_abre_conta(self):
        with self.assertRaises(PinInvalidoError):
            self.banco.abrir_conta("Ana", "12")

        self.assertEqual(self.banco.contas, ())

    def test_buscar(self):
        conta = self.banco.abrir_conta("Ana", "1234")

        self.assertIs(self.banco.buscar(" 1001 "), conta)

    def test_buscar_inexistente(self):
        with self.assertRaises(ContaNaoEncontradaError):
            self.banco.buscar("9999")

    def test_numeros_invalidos_ou_repetidos(self):
        for contas in (
            [ContaBancaria(numero="")],
            [ContaBancaria(numero="abc")],
            [ContaBancaria(numero="1001"), ContaBancaria(numero="1001")]
        ):
            with self.subTest(contas=[c.numero for c in contas]):
                with self.assertRaises(ValueError):
                    Banco(contas)

if __name__ == "__main__":
    unittest.main()
