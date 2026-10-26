import json
import sqlite3
import unittest
import tempfile

from contextlib import closing, redirect_stdout
from decimal import Decimal
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from caixa_eletronico.armazenamento import formato_json
from caixa_eletronico.armazenamento import persistencia

from caixa_eletronico.armazenamento.persistencia import (
    ArmazenamentoIndisponivelError
)
from caixa_eletronico.nucleo.banco import Banco
from caixa_eletronico.nucleo.conta_bancaria import (
    ContaBancaria,
    TipoTransacao,
    Transacao
)

def nova_conta(numero="1001", **dados):
    return ContaBancaria(numero=numero, **dados)

class TestPersistencia(unittest.TestCase):
    def setUp(self):
        self.diretorio = tempfile.TemporaryDirectory()
        self.addCleanup(self.diretorio.cleanup)

        self.pasta = Path(self.diretorio.name)
        self.arquivo_banco = self.pasta / "banco.db"
        self.arquivo_json = self.pasta / "dados.json"

        for nome, caminho in (
            ("ARQUIVO_BANCO", self.arquivo_banco),
            ("ARQUIVO_JSON", self.arquivo_json)
        ):
            patcher = patch.object(persistencia, nome, caminho)
            patcher.start()
            self.addCleanup(patcher.stop)

    def arquivos_na_pasta(self):
        return sorted(p.name for p in self.pasta.iterdir())

    def consultar(self, sql):
        with closing(sqlite3.connect(self.arquivo_banco)) as conexao:
            return conexao.execute(sql).fetchall()

    def salvar(self, *contas):
        return persistencia.salvar_banco(Banco(contas))

    def carregar(self):
        saida = StringIO()

        with redirect_stdout(saida):
            banco = persistencia.carregar_banco()

        return banco, saida.getvalue()

    def carregar_unica_conta(self):
        banco, _ = self.carregar()

        self.assertEqual(len(banco.contas), 1)
        return banco.contas[0]

    # --- SQLite ---

    def test_sem_arquivos_comeca_vazio(self):
        banco, saida = self.carregar()

        self.assertEqual(banco.contas, ())
        self.assertEqual(saida, "")

    def test_salvar_e_carregar_conta(self):
        conta = nova_conta(titular="Gabriel")
        conta.definir_pin("1234")
        conta.autenticar("0000")
        conta.depositar(200)
        conta.sacar("50.10")

        self.assertTrue(self.salvar(conta))

        carregada = self.carregar_unica_conta()

        self.assertEqual(carregada.numero, "1001")
        self.assertEqual(carregada.titular, "Gabriel")
        self.assertEqual(carregada.saldo, Decimal("149.90"))
        self.assertEqual(carregada.transacoes, conta.transacoes)
        self.assertEqual(carregada.tentativas_falhas, 1)
        self.assertTrue(carregada.autenticar("1234"))

    def test_varias_contas_com_transferencia(self):
        origem = nova_conta("1001", titular="Ana", saldo=100)
        destino = nova_conta("1002", titular="Bruno")
        origem.transferir(destino, 30)

        self.salvar(origem, destino)

        banco, _ = self.carregar()

        self.assertEqual(banco.buscar("1001").saldo, Decimal("70.00"))
        self.assertEqual(banco.buscar("1002").transacoes, destino.transacoes)

    def test_contas_em_ordem_numerica(self):
        self.salvar(nova_conta("1010"), nova_conta("1002"), nova_conta("999"))

        banco, _ = self.carregar()

        self.assertEqual([c.numero for c in banco.contas], ["999", "1002", "1010"])

    def test_valores_guardados_em_centavos(self):
        conta = nova_conta()
        conta.depositar("10.50")

        self.salvar(conta)

        self.assertEqual(
            self.consultar("SELECT saldo_centavos FROM contas"), [(1050,)]
        )
        self.assertEqual(
            self.consultar("SELECT valor_centavos FROM transacoes"), [(1050,)]
        )

    def test_salvar_de_novo_so_insere_transacoes_novas(self):
        conta = nova_conta(saldo=100)
        banco = Banco([conta])

        conta.depositar(10)
        persistencia.salvar_banco(banco)
        conta.sacar(20)
        persistencia.salvar_banco(banco)
        persistencia.salvar_banco(banco)

        self.assertEqual(
            self.consultar("SELECT COUNT(*) FROM transacoes"), [(2,)]
        )
        self.assertEqual(self.carregar_unica_conta().saldo, Decimal("90.00"))

    def test_pin_nao_fica_no_banco(self):
        conta = nova_conta()
        conta.definir_pin("1234")

        self.salvar(conta)

        self.assertNotIn(b"1234", self.arquivo_banco.read_bytes())

    def test_bloqueio_continua_apos_carregar(self):
        conta = nova_conta()
        conta.definir_pin("1234")

        for _ in range(3):
            conta.autenticar("0000")

        self.salvar(conta)

        self.assertTrue(self.carregar_unica_conta().bloqueada)

    def test_falha_na_gravacao_nao_salva_nada(self):
        conta = nova_conta(saldo=100)
        banco = Banco([conta])
        persistencia.salvar_banco(banco)

        conta.depositar(50)
        # Transação inválida: o CHECK do banco recusa, e o depósito também
        # deve ser desfeito, porque tudo é gravado numa única transação
        conta._transacoes.append(
            Transacao(TipoTransacao.SAQUE, Decimal("-1"), Decimal("0"))
        )

        with redirect_stdout(StringIO()) as saida:
            sucesso = persistencia.salvar_banco(banco)

        self.assertFalse(sucesso)
        self.assertIn("Erro ao salvar os dados", saida.getvalue())
        self.assertEqual(
            self.consultar("SELECT saldo_centavos FROM contas"), [(10000,)]
        )
        self.assertEqual(
            self.consultar("SELECT COUNT(*) FROM transacoes"), [(0,)]
        )

    def test_ctrl_c_no_meio_da_gravacao_nao_salva_nada(self):
        primeira = nova_conta("1001", saldo=100)
        segunda = nova_conta("1002", saldo=200)
        banco = Banco([primeira, segunda])
        persistencia.salvar_banco(banco)

        primeira.depositar(50)
        segunda.depositar(50)

        conversoes = []

        def interromper_na_segunda_conta(valor):
            conversoes.append(valor)

            if len(conversoes) > 2:
                raise KeyboardInterrupt

            return int(valor * 100)

        with patch.object(
            persistencia, "para_centavos",
            side_effect=interromper_na_segunda_conta
        ):
            with self.assertRaises(KeyboardInterrupt):
                persistencia.salvar_banco(banco)

        self.assertEqual(
            self.consultar("SELECT saldo_centavos FROM contas ORDER BY numero"),
            [(10000,), (20000,)]
        )

    # --- banco.db corrompido ou inacessível ---

    def test_banco_corrompido_e_guardado(self):
        self.arquivo_banco.write_bytes(b"isto nao e um banco SQLite " * 50)

        banco, saida = self.carregar()

        self.assertEqual(banco.contas, ())
        self.assertIn("banco.db.corrompido-", saida)

        arquivos = self.arquivos_na_pasta()

        self.assertNotIn("banco.db", arquivos)
        self.assertEqual(len(arquivos), 1)
        self.assertTrue(arquivos[0].startswith("banco.db.corrompido-"))

    def test_banco_com_dados_invalidos_e_guardado(self):
        self.salvar(nova_conta())

        with closing(sqlite3.connect(self.arquivo_banco)) as conexao:
            with conexao:
                conexao.execute(
                    "INSERT INTO transacoes (numero_conta, tipo, "
                    "valor_centavos, saldo_centavos, data) "
                    "VALUES ('1001', 'Saque', 100, 0, 'ontem')"
                )

        banco, saida = self.carregar()

        self.assertEqual(banco.contas, ())
        self.assertIn("Data inválida", saida)

    def test_banco_inacessivel_nao_comeca_vazio(self):
        self.salvar(nova_conta())

        with patch.object(
            persistencia, "conectar",
            side_effect=sqlite3.OperationalError("database is locked")
        ):
            with self.assertRaises(ArmazenamentoIndisponivelError):
                persistencia.carregar_banco()

        self.assertEqual(self.arquivos_na_pasta(), ["banco.db"])

    def test_sem_copia_do_corrompido_nao_continua(self):
        self.arquivo_banco.write_bytes(b"lixo " * 200)

        with patch.object(Path, "replace", side_effect=PermissionError("em uso")):
            with self.assertRaises(ArmazenamentoIndisponivelError):
                persistencia.carregar_banco()

        self.assertEqual(self.arquivos_na_pasta(), ["banco.db"])

    # --- importação do dados.json ---

    def escrever_json(self, dados):
        self.arquivo_json.write_text(json.dumps(dados), encoding="utf-8")

    def test_importa_json_atual(self):
        origem = nova_conta("1001", titular="Ana", saldo=100)
        origem.definir_pin("1234")
        destino = nova_conta("1002", titular="Bruno")
        origem.transferir(destino, 30)

        self.escrever_json(formato_json.banco_para_dados(Banco([origem, destino])))

        banco, saida = self.carregar()

        self.assertIn("Dados importados de dados.json", saida)
        self.assertTrue(banco.buscar("1001").autenticar("1234"))
        self.assertEqual(banco.buscar("1002").transacoes, destino.transacoes)
        self.assertEqual(
            self.arquivos_na_pasta(), ["banco.db", "dados.json.migrado"]
        )

        # A partir daí os dados vêm do SQLite, sem nova importação
        banco, saida = self.carregar()

        self.assertEqual(saida, "")
        self.assertEqual(banco.buscar("1001").saldo, Decimal("70.00"))

    def test_importa_json_do_formato_antigo(self):
        self.escrever_json({
            "saldo": 1170.0,
            "transacoes": [
                {"tipo": "Depósito", "valor": 1250.0, "saldo": 1250.0},
                {"tipo": "Saque", "valor": 80.0, "saldo": 1170.0}
            ]
        })

        conta = self.carregar_unica_conta()

        self.assertEqual(conta.numero, "1001")
        self.assertEqual(conta.saldo, Decimal("1170.00"))
        self.assertEqual(len(conta.transacoes), 2)

    def test_json_corrompido_e_guardado(self):
        self.arquivo_json.write_text("{ conteúdo inválido }", encoding="utf-8")

        banco, saida = self.carregar()

        self.assertEqual(banco.contas, ())
        self.assertIn("dados.json.corrompido-", saida)

        arquivos = self.arquivos_na_pasta()

        self.assertEqual(len(arquivos), 1)
        self.assertTrue(arquivos[0].startswith("dados.json.corrompido-"))

    def test_json_com_dados_invalidos_e_guardado(self):
        self.escrever_json({"saldo": "abc", "transacoes": []})

        banco, _ = self.carregar()

        self.assertEqual(banco.contas, ())
        self.assertNotIn("dados.json", self.arquivos_na_pasta())

    def test_json_inacessivel_nao_comeca_vazio(self):
        self.escrever_json({"contas": []})

        with patch("builtins.open", side_effect=PermissionError("negado")):
            with self.assertRaises(ArmazenamentoIndisponivelError):
                persistencia.carregar_banco()

        self.assertEqual(self.arquivos_na_pasta(), ["dados.json"])

    def test_falha_na_importacao_mantem_o_json(self):
        self.escrever_json({"saldo": "10", "transacoes": []})

        with patch.object(
            persistencia, "gravar_banco",
            side_effect=sqlite3.OperationalError("disco cheio")
        ):
            with self.assertRaises(ArmazenamentoIndisponivelError):
                persistencia.carregar_banco()

        # Sem banco.db pela metade: na próxima vez a importação é tentada de novo
        self.assertEqual(self.arquivos_na_pasta(), ["dados.json"])

if __name__ == "__main__":
    unittest.main()
