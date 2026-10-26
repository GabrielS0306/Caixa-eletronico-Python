import unittest
import tempfile

from datetime import datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from caixa_eletronico.armazenamento import exportacao

from caixa_eletronico.nucleo.conta_bancaria import TipoTransacao, Transacao

class TestExportarCsv(unittest.TestCase):
    def setUp(self):
        self.diretorio = tempfile.TemporaryDirectory()
        self.addCleanup(self.diretorio.cleanup)

        # Pasta que ainda não existe, para testar que ela é criada
        self.pasta = Path(self.diretorio.name) / "extratos"

        patcher = patch.object(exportacao, "PASTA_EXTRATOS", self.pasta)
        patcher.start()
        self.addCleanup(patcher.stop)

        self.transacoes = [
            Transacao(
                TipoTransacao.DEPOSITO,
                Decimal("1500.00"),
                Decimal("1500.00"),
                datetime(2026, 10, 25, 14, 30, 5)
            ),
            Transacao(
                TipoTransacao.SAQUE,
                Decimal("80.50"),
                Decimal("1419.50"),
                None
            ),
            Transacao(
                TipoTransacao.TRANSFERENCIA_ENVIADA,
                Decimal("19.50"),
                Decimal("1400.00"),
                datetime(2026, 10, 25, 14, 45, 0),
                "1002"
            )
        ]

    def exportar(self):
        return exportacao.exportar_csv(
            self.transacoes, "1001", momento=datetime(2026, 10, 25, 15, 0, 0)
        )

    def test_cria_pasta_e_nomeia_arquivo(self):
        caminho = self.exportar()

        self.assertEqual(caminho, self.pasta / "extrato_1001_2026-10-25_15-00-00.csv")
        self.assertTrue(caminho.exists())

    def test_conteudo_no_formato_do_excel(self):
        caminho = self.exportar()

        linhas = caminho.read_text(encoding="utf-8-sig").splitlines()

        self.assertEqual(linhas, [
            "Data;Tipo;Valor;Saldo após operação;Outra conta",
            "25/10/2026 14:30:05;Depósito;1500,00;1500,00;",
            ";Saque;80,50;1419,50;",
            "25/10/2026 14:45:00;Transferência enviada;19,50;1400,00;1002"
        ])

    def test_arquivo_comeca_com_bom(self):
        caminho = self.exportar()

        self.assertTrue(caminho.read_bytes().startswith(b"\xef\xbb\xbf"))

    def test_extrato_vazio_tem_so_cabecalho(self):
        self.transacoes = []

        caminho = self.exportar()

        linhas = caminho.read_text(encoding="utf-8-sig").splitlines()

        self.assertEqual(
            linhas, ["Data;Tipo;Valor;Saldo após operação;Outra conta"]
        )

if __name__ == "__main__":
    unittest.main()
