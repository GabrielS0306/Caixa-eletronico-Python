import json
import unittest
import tempfile

from datetime import datetime
from decimal import Decimal
from io import StringIO
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from caixa_eletronico.armazenamento import persistencia

from caixa_eletronico.nucleo.banco import Banco
from caixa_eletronico.nucleo.conta_bancaria import ContaBancaria, TipoTransacao

def nova_conta(numero="1001", **dados):
    return ContaBancaria(numero=numero, **dados)

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

    def ler_json(self):
        return json.loads(self.arquivo.read_text(encoding="utf-8"))

    def arquivos_na_pasta(self):
        return sorted(p.name for p in Path(self.diretorio.name).iterdir())

    def salvar(self, *contas):
        return persistencia.salvar_banco(Banco(contas))

    def carregar(self):
        with redirect_stdout(StringIO()):
            return persistencia.carregar_banco()

    def carregar_unica_conta(self):
        banco = self.carregar()

        self.assertEqual(len(banco.contas), 1)
        return banco.contas[0]

    def test_salvar_e_carregar_conta(self):
        conta = nova_conta(titular="Gabriel")
        conta.depositar(200)
        conta.sacar("50.10")

        self.assertTrue(self.salvar(conta))

        carregada = self.carregar_unica_conta()

        self.assertEqual(carregada.numero, "1001")
        self.assertEqual(carregada.titular, "Gabriel")
        self.assertEqual(carregada.saldo, Decimal("149.90"))
        self.assertEqual(carregada.transacoes, conta.transacoes)

    def test_salvar_e_carregar_varias_contas_com_transferencia(self):
        origem = nova_conta("1001", titular="Ana", saldo=100)
        destino = nova_conta("1002", titular="Bruno")
        origem.transferir(destino, 30)

        self.salvar(origem, destino)

        banco = self.carregar()

        self.assertEqual(banco.buscar("1001").saldo, Decimal("70.00"))
        self.assertEqual(banco.buscar("1002").saldo, Decimal("30.00"))
        self.assertEqual(
            banco.buscar("1002").transacoes[0].contraparte, "1001"
        )
        self.assertEqual(banco.buscar("1001").transacoes, origem.transacoes)

    def test_valores_salvos_como_texto(self):
        conta = nova_conta()
        conta.depositar("10.50")

        self.salvar(conta)

        dados = self.ler_json()["contas"][0]

        self.assertEqual(dados["saldo"], "10.50")
        self.assertEqual(dados["transacoes"][0]["valor"], "10.50")

    def test_arquivo_inexistente(self):
        self.assertEqual(self.carregar().contas, ())

    def test_arquivo_json_invalido(self):
        self.arquivo.write_text(
            "{ conteúdo inválido }",
            encoding="utf-8"
        )

        self.assertEqual(self.carregar().contas, ())

    def test_carrega_formato_antigo_com_float(self):
        self.escrever_json({
            "saldo": 1170.0,
            "transacoes": [
                {"tipo": "Depósito", "valor": 1250.0, "saldo": 1250.0},
                {"tipo": "Saque", "valor": 80.0, "saldo": 1170.0}
            ]
        })

        conta = self.carregar_unica_conta()

        self.assertEqual(conta.numero, "1001")
        self.assertEqual(conta.titular, "")
        self.assertEqual(conta.saldo, Decimal("1170.00"))
        self.assertEqual(conta.transacoes[1].tipo, TipoTransacao.SAQUE)
        self.assertIsNone(conta.transacoes[1].data)

    def test_formato_antigo_e_convertido_e_regravado(self):
        conta = nova_conta(saldo=50)
        conta.definir_pin("1234")

        # Grava como o programa gravava antes: uma conta só, sem "numero"
        dados_antigos = persistencia.conta_para_dados(conta)
        del dados_antigos["numero"]
        self.escrever_json(dados_antigos)

        saida = StringIO()

        with redirect_stdout(saida):
            banco = persistencia.carregar_banco()

        self.assertIn("conta agora é a de número 1001", saida.getvalue())
        self.assertTrue(banco.buscar("1001").autenticar("1234"))
        self.assertEqual(self.ler_json()["contas"][0]["numero"], "1001")

        # Na segunda vez o arquivo já está no formato novo
        with redirect_stdout(StringIO()) as saida:
            persistencia.carregar_banco()

        self.assertEqual(saida.getvalue(), "")

    def test_data_salva_em_formato_iso(self):
        conta = nova_conta()

        with patch(
            "caixa_eletronico.nucleo.conta_bancaria.agora",
            return_value=datetime(2026, 10, 25, 14, 30, 5)
        ):
            conta.depositar(10)

        self.salvar(conta)

        transacao = self.ler_json()["contas"][0]["transacoes"][0]

        self.assertEqual(transacao["data"], "2026-10-25T14:30:05")

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

    def test_contraparte_invalida(self):
        for contraparte in (1002, "abc", ""):
            with self.subTest(contraparte=contraparte):
                with self.assertRaises(ValueError):
                    persistencia.dados_para_conta({
                        "saldo": "10",
                        "transacoes": [{
                            "tipo": "Transferência recebida",
                            "valor": "10",
                            "saldo": "10",
                            "contraparte": contraparte
                        }]
                    })

    def test_contas_invalidas(self):
        conta = persistencia.conta_para_dados(nova_conta("1001"))
        sem_numero = dict(conta, numero="")

        for dados in (
            {"contas": "abc"},
            {"contas": [conta, conta]},
            {"contas": [sem_numero]},
            []
        ):
            with self.subTest(dados=dados):
                with self.assertRaises(ValueError):
                    persistencia.dados_para_banco(dados)

    def test_salvar_e_carregar_pin(self):
        conta = nova_conta()
        conta.definir_pin("1234")
        conta.autenticar("0000")

        self.salvar(conta)

        carregada = self.carregar_unica_conta()

        self.assertTrue(carregada.autenticar("1234"))

        seguranca = self.ler_json()["contas"][0]["seguranca"]

        self.assertEqual(seguranca["tentativas_falhas"], 1)
        self.assertNotIn("1234", self.arquivo.read_text(encoding="utf-8"))

    def test_bloqueio_continua_apos_carregar(self):
        conta = nova_conta()
        conta.definir_pin("1234")

        for _ in range(3):
            conta.autenticar("0000")

        self.salvar(conta)

        self.assertTrue(self.carregar_unica_conta().bloqueada)

    def test_formato_antigo_sem_pin(self):
        self.escrever_json({"saldo": "10", "transacoes": []})

        self.assertFalse(self.carregar_unica_conta().possui_pin)

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

    def salvar_original_e_alterar(self):
        conta = nova_conta(saldo=100)
        banco = Banco([conta])
        persistencia.salvar_banco(banco)

        original = self.arquivo.read_text(encoding="utf-8")
        conta.depositar(50)

        return banco, original

    def test_salvar_nao_deixa_arquivo_temporario(self):
        self.salvar(nova_conta(saldo=10))
        self.salvar(nova_conta(saldo=20))

        self.assertEqual(self.arquivos_na_pasta(), ["dados.json"])
        self.assertEqual(self.carregar_unica_conta().saldo, Decimal("20.00"))

    def test_erro_no_meio_da_gravacao_preserva_original(self):
        banco, original = self.salvar_original_e_alterar()

        def gravar_pela_metade(dados, arquivo, **opcoes):
            arquivo.write('{"contas": [{"saldo": "15')
            raise OSError("disco cheio")

        with patch("json.dump", side_effect=gravar_pela_metade):
            with redirect_stdout(StringIO()) as saida:
                sucesso = persistencia.salvar_banco(banco)

        self.assertFalse(sucesso)
        self.assertIn("disco cheio", saida.getvalue())
        self.assertEqual(self.arquivo.read_text(encoding="utf-8"), original)
        self.assertEqual(self.arquivos_na_pasta(), ["dados.json"])

    def test_ctrl_c_no_meio_da_gravacao_preserva_original(self):
        banco, original = self.salvar_original_e_alterar()

        def interromper(dados, arquivo, **opcoes):
            arquivo.write('{"contas": [{"saldo": "15')
            raise KeyboardInterrupt

        with patch("json.dump", side_effect=interromper):
            with self.assertRaises(KeyboardInterrupt):
                persistencia.salvar_banco(banco)

        self.assertEqual(self.arquivo.read_text(encoding="utf-8"), original)
        self.assertEqual(self.arquivos_na_pasta(), ["dados.json"])

    def test_falha_na_troca_preserva_original(self):
        banco, original = self.salvar_original_e_alterar()

        with patch("os.replace", side_effect=PermissionError("em uso")):
            with redirect_stdout(StringIO()):
                sucesso = persistencia.salvar_banco(banco)

        self.assertFalse(sucesso)
        self.assertEqual(self.arquivo.read_text(encoding="utf-8"), original)
        self.assertEqual(self.arquivos_na_pasta(), ["dados.json"])

    def test_dados_invalidos_iniciam_banco_vazio(self):
        self.escrever_json({"saldo": "abc", "transacoes": []})

        self.assertEqual(self.carregar().contas, ())

if __name__ == "__main__":
    unittest.main()
