import unittest
import tempfile

from pathlib import Path
from unittest.mock import patch

import persistencia

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

    def test_salvar_e_carregar_dados(self):
        saldo = 150.0
        transacoes = [
            {
                "tipo": "Depósito",
                "valor": 200.0,
                "saldo": 200.0
            },
            {
                "tipo": "Saque",
                "valor": 50.0,
                "saldo": 150.0
            }
        ]

        persistencia.salvar_dados(saldo, transacoes)

        saldo_carregado, transacoes_carregadas = (
            persistencia.carregar_dados()
        )

        self.assertEqual(saldo_carregado, saldo)
        self.assertEqual(transacoes_carregadas, transacoes)
        self.assertTrue(self.arquivo.exists())

    def test_arquivo_inexistente(self):
        saldo, transacoes = persistencia.carregar_dados()

        self.assertEqual(saldo, 0.0)
        self.assertEqual(transacoes, [])

    def test_arquivo_json_invalido(self):
        self.arquivo.write_text(
            "{ conteúdo inválido }",
            encoding="utf-8"
        )

        saldo, transacoes = persistencia.carregar_dados()

        self.assertEqual(saldo, 0.0)
        self.assertEqual(transacoes, [])

    def test_salvar_historico_vazio(self):
        persistencia.salvar_dados(300.0, [])

        saldo, transacoes = persistencia.carregar_dados()

        self.assertEqual(saldo, 300.0)
        self.assertEqual(transacoes, [])

if __name__ == "__main__":
    unittest.main()
