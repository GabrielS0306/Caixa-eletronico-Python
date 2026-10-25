import json
import unittest
import tempfile

from datetime import datetime
from decimal import Decimal
from io import StringIO
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import persistencia

from conta_bancaria import ContaBancaria, TipoTransacao

class TestPersistencia(unittest.TestCase):
    def setUp(self):
        self.diretorio = tempfile.TemporaryDirectory()
        self.addCleanup(self.diretorio.cleanup)

        self.arquivo = Path(self.diretorio.name) / "dados.json"

        self.patch_arquivo = patch.object(
            persistencia, "ARQUIVO_DADOS", self.arquivo
        )
        self.patch_arquivo.start()
        self.addCleanup(self.patch_arquivo.stop)

    def escrever_json(self, dados):
        self.arquivo.write_text(json.dumps(dados), encoding="utf-8")

    def carregar_silencioso(self):
        with redirect_stdout(StringIO()):
            return persistencia.carregar_conta()

    def test_salvar_e_carregar_conta(self):
        conta = ContaBancaria("Gabriel")
        conta.depositar(200)
        conta.sacar("50.10")

        self.assertTrue(persistencia.salvar_conta(conta))

        carregada = persistencia.carregar_conta()

        self.assertEqual(carregada.titular, "Gabriel")
        self.assertEqual(carregada.saldo, Decimal("149.90"))
        self.assertEqual(carregada.transacoes, conta.transacoes)

    def test_valores_salvos_como_texto(self):
        conta = ContaBancaria()
        conta.depositar("10.50")

        persistencia.salvar_conta(conta)

        dados = json.loads(self.arquivo.read_text(encoding="utf-8"))

        self.assertEqual(dados["saldo"], "10.50")
        self.assertEqual(dados["transacoes"][0]["valor"], "10.50")

    def test_arquivo_inexistente(self):
        conta = persistencia.carregar_conta()

        self.assertEqual(conta.saldo, Decimal("0.00"))
        self.assertEqual(conta.transacoes, ())

    def test_arquivo_json_invalido(self):
        self.arquivo.write_text(
            "{ conteúdo inválido }",
            encoding="utf-8"
        )

        conta = self.carregar_silencioso()

        self.assertEqual(conta.saldo, Decimal("0.00"))
        self.assertEqual(conta.transacoes, ())

    def test_carrega_formato_antigo_com_float(self):
        self.escrever_json({
            "saldo": 1170.0,
            "transacoes": [
                {"tipo": "Depósito", "valor": 1250.0, "saldo": 1250.0},
                {"tipo": "Saque", "valor": 80.0, "saldo": 1170.0}
            ]
        })

        conta = persistencia.carregar_conta()

        self.assertEqual(conta.titular, "")
        self.assertEqual(conta.saldo, Decimal("1170.00"))
        self.assertEqual(conta.transacoes[1].tipo, TipoTransacao.SAQUE)
        self.assertIsNone(conta.transacoes[1].data)

    def test_data_salva_em_formato_iso(self):
        conta = ContaBancaria()

        with patch(
            "conta_bancaria.agora",
            return_value=datetime(2026, 10, 25, 14, 30, 5)
        ):
            conta.depositar(10)

        persistencia.salvar_conta(conta)

        dados = json.loads(self.arquivo.read_text(encoding="utf-8"))

        self.assertEqual(
            dados["transacoes"][0]["data"], "2026-10-25T14:30:05"
        )

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
            persistencia.dados_para_conta(dados)

    def test_saldo_negativo(self):
        with self.assertRaises(ValueError):
            persistencia.dados_para_conta({"saldo": "-100", "transacoes": []})

    def test_saldo_infinito(self):
        with self.assertRaises(ValueError):
            persistencia.dados_para_conta(
                {"saldo": float("inf"), "transacoes": []}
            )

    def test_saldo_booleano(self):
        with self.assertRaises(ValueError):
            persistencia.dados_para_conta({"saldo": True, "transacoes": []})

    def test_transacao_invalida(self):
        dados = {
            "saldo": "100",
            "transacoes": [
                {"tipo": "Transferência", "valor": "50", "saldo": "100"}
            ]
        }

        with self.assertRaises(ValueError):
            persistencia.dados_para_conta(dados)

    def test_valor_negativo_na_transacao(self):
        dados = {
            "saldo": "100",
            "transacoes": [
                {"tipo": "Depósito", "valor": "-50", "saldo": "100"}
            ]
        }

        with self.assertRaises(ValueError):
            persistencia.dados_para_conta(dados)

    def test_salvar_e_carregar_pin(self):
        conta = ContaBancaria()
        conta.definir_pin("1234")
        conta.autenticar("0000")

        persistencia.salvar_conta(conta)

        carregada = persistencia.carregar_conta()

        self.assertTrue(carregada.autenticar("1234"))

        dados = json.loads(self.arquivo.read_text(encoding="utf-8"))

        self.assertEqual(dados["seguranca"]["tentativas_falhas"], 1)
        self.assertNotIn("1234", self.arquivo.read_text(encoding="utf-8"))

    def test_bloqueio_continua_apos_carregar(self):
        conta = ContaBancaria()
        conta.definir_pin("1234")

        for _ in range(3):
            conta.autenticar("0000")

        persistencia.salvar_conta(conta)

        self.assertTrue(persistencia.carregar_conta().bloqueada)

    def test_formato_antigo_sem_pin(self):
        self.escrever_json({"saldo": "10", "transacoes": []})

        self.assertFalse(persistencia.carregar_conta().possui_pin)

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
                    persistencia.dados_para_conta({
                        "saldo": "10",
                        "transacoes": [],
                        "seguranca": seguranca
                    })

    def test_dados_invalidos_iniciam_conta_vazia(self):
        self.escrever_json({"saldo": "abc", "transacoes": []})

        conta = self.carregar_silencioso()

        self.assertEqual(conta.saldo, Decimal("0.00"))

if __name__ == "__main__":
    unittest.main()
