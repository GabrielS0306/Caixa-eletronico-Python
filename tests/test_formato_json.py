import unittest

from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

from caixa_eletronico.armazenamento import formato_json

from caixa_eletronico.nucleo.banco import Banco
from caixa_eletronico.nucleo.conta_bancaria import ContaBancaria, TipoTransacao

def nova_conta(numero="1001", **dados):
    return ContaBancaria(numero=numero, **dados)

def ida_e_volta(*contas):
    dados = formato_json.banco_para_dados(Banco(contas))

    return formato_json.dados_para_banco(dados)

class TestConversaoJson(unittest.TestCase):
    def test_ida_e_volta_preserva_a_conta(self):
        conta = nova_conta(titular="Gabriel")
        conta.definir_pin("1234")
        conta.autenticar("0000")
        conta.depositar(200)
        conta.sacar("50.10")

        carregada = ida_e_volta(conta).buscar("1001")

        self.assertEqual(carregada.titular, "Gabriel")
        self.assertEqual(carregada.saldo, Decimal("149.90"))
        self.assertEqual(carregada.transacoes, conta.transacoes)
        self.assertEqual(carregada.tentativas_falhas, 1)
        self.assertTrue(carregada.autenticar("1234"))

    def test_ida_e_volta_com_transferencia(self):
        origem = nova_conta("1001", saldo=100)
        destino = nova_conta("1002")
        origem.transferir(destino, 30)

        banco = ida_e_volta(origem, destino)

        self.assertEqual(banco.buscar("1002").transacoes, destino.transacoes)

    def test_valores_e_data_como_texto(self):
        conta = nova_conta()

        with patch(
            "caixa_eletronico.nucleo.conta_bancaria.agora",
            return_value=datetime(2026, 10, 25, 14, 30, 5)
        ):
            conta.depositar("10.50")

        dados = formato_json.conta_para_dados(conta)

        self.assertEqual(dados["saldo"], "10.50")
        self.assertEqual(dados["transacoes"][0]["valor"], "10.50")
        self.assertEqual(dados["transacoes"][0]["data"], "2026-10-25T14:30:05")

    def test_formato_antigo_com_float(self):
        banco = formato_json.dados_para_banco({
            "saldo": 1170.0,
            "transacoes": [
                {"tipo": "Depósito", "valor": 1250.0, "saldo": 1250.0},
                {"tipo": "Saque", "valor": 80.0, "saldo": 1170.0}
            ]
        })

        conta = banco.buscar("1001")

        self.assertEqual(conta.titular, "")
        self.assertFalse(conta.possui_pin)
        self.assertEqual(conta.saldo, Decimal("1170.00"))
        self.assertEqual(conta.transacoes[1].tipo, TipoTransacao.SAQUE)
        self.assertIsNone(conta.transacoes[1].data)

    def test_data_invalida(self):
        dados = {
            "saldo": "10",
            "transacoes": [
                {
                    "tipo": "Depósito",
                    "valor": "10",
                    "saldo": "10",
                    "data": "ontem"
                }
            ]
        }

        with self.assertRaises(ValueError):
            formato_json.dados_para_conta(dados)

    def test_saldos_invalidos(self):
        for saldo in ("-100", float("inf"), True, "abc"):
            with self.subTest(saldo=saldo):
                with self.assertRaises(ValueError):
                    formato_json.dados_para_conta(
                        {"saldo": saldo, "transacoes": []}
                    )

    def test_transacao_invalida(self):
        dados = {
            "saldo": "100",
            "transacoes": [
                {"tipo": "Transferência", "valor": "50", "saldo": "100"}
            ]
        }

        with self.assertRaises(ValueError):
            formato_json.dados_para_conta(dados)

    def test_valor_negativo_na_transacao(self):
        dados = {
            "saldo": "100",
            "transacoes": [
                {"tipo": "Depósito", "valor": "-50", "saldo": "100"}
            ]
        }

        with self.assertRaises(ValueError):
            formato_json.dados_para_conta(dados)

    def test_contraparte_invalida(self):
        for contraparte in (1002, "abc", ""):
            with self.subTest(contraparte=contraparte):
                with self.assertRaises(ValueError):
                    formato_json.dados_para_conta({
                        "saldo": "10",
                        "transacoes": [{
                            "tipo": "Transferência recebida",
                            "valor": "10",
                            "saldo": "10",
                            "contraparte": contraparte
                        }]
                    })

    def test_contas_invalidas(self):
        conta = formato_json.conta_para_dados(nova_conta("1001"))
        sem_numero = dict(conta, numero="")

        for dados in (
            {"contas": "abc"},
            {"contas": [conta, conta]},
            {"contas": [sem_numero]},
            []
        ):
            with self.subTest(dados=dados):
                with self.assertRaises(ValueError):
                    formato_json.dados_para_banco(dados)

    def test_seguranca_invalida(self):
        for seguranca in (
            "abc",
            {"salt": "zz", "hash": "00"},
            {"salt": "", "hash": "00"},
            {"salt": "00", "hash": "00", "tentativas_falhas": -1},
            {"salt": "00", "hash": "00", "tentativas_falhas": True}
        ):
            with self.subTest(seguranca=seguranca):
                with self.assertRaises(ValueError):
                    formato_json.dados_para_conta({
                        "saldo": "10",
                        "transacoes": [],
                        "seguranca": seguranca
                    })

if __name__ == "__main__":
    unittest.main()
