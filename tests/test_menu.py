import unittest

from datetime import date, datetime
from decimal import Decimal
from io import StringIO
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from caixa_eletronico.interface import menu

from caixa_eletronico.nucleo.banco import Banco
from caixa_eletronico.nucleo.conta_bancaria import ContaBancaria
from caixa_eletronico.formatacao import formatar_moeda

class TestObterValor(unittest.TestCase):
    def obter(self, entrada):
        with patch("builtins.input", return_value=entrada):
            with redirect_stdout(StringIO()):
                return menu.obter_valor("Valor: ")

    def test_aceita_virgula(self):
        self.assertEqual(self.obter("10,50"), Decimal("10.50"))

    def test_aceita_ponto(self):
        self.assertEqual(self.obter(" 99.9 "), Decimal("99.90"))

    def test_rejeita_entradas_invalidas(self):
        for entrada in ("", "abc", "0", "-5", "nan", "inf", "1,234"):
            with self.subTest(entrada=entrada):
                self.assertIsNone(self.obter(entrada))

class TestRealizarSaque(unittest.TestCase):
    def sacar(self, conta, valor):
        saida = StringIO()

        with redirect_stdout(saida):
            sucesso = menu.realizar_saque(conta, Decimal(valor))

        return sucesso, saida.getvalue()

    def test_saque_mostra_cedulas(self):
        conta = ContaBancaria(saldo=500)

        sucesso, resultado = self.sacar(conta, "270")

        self.assertTrue(sucesso)
        self.assertEqual(conta.saldo, Decimal("230.00"))
        self.assertIn("1 x R$ 200,00", resultado)
        self.assertIn("1 x R$ 50,00", resultado)
        self.assertIn("1 x R$ 20,00", resultado)

    def test_valor_indisponivel_nao_debita(self):
        conta = ContaBancaria(saldo=500)

        sucesso, resultado = self.sacar(conta, "25")

        self.assertFalse(sucesso)
        self.assertEqual(conta.saldo, Decimal("500.00"))
        self.assertEqual(conta.transacoes, ())
        self.assertIn("Valor indisponível", resultado)

    def test_saldo_insuficiente(self):
        conta = ContaBancaria(saldo=50)

        sucesso, resultado = self.sacar(conta, "100")

        self.assertFalse(sucesso)
        self.assertEqual(conta.saldo, Decimal("50.00"))
        self.assertIn("Saldo insuficiente!", resultado)

class TestPin(unittest.TestCase):
    def setUp(self):
        # Evita gravar no dados.json real durante os testes
        patcher = patch(
            "caixa_eletronico.interface.menu.persistencia.salvar_banco"
        )
        self.salvar = patcher.start()
        self.addCleanup(patcher.stop)

        self.conta = ContaBancaria(numero="1001")
        self.conta.definir_pin("1234")
        self.banco = Banco([self.conta])

    def executar(self, funcao, pins):
        saida = StringIO()

        with patch(
            "caixa_eletronico.interface.menu.ler_pin", side_effect=pins
        ):
            with redirect_stdout(saida):
                resultado = funcao()

        return resultado, saida.getvalue()

    def autenticar(self):
        return menu.autenticar(self.banco, self.conta)

    def test_autenticar_na_primeira(self):
        sucesso, _ = self.executar(self.autenticar, ["1234"])

        self.assertTrue(sucesso)

    def test_autenticar_depois_de_errar(self):
        sucesso, resultado = self.executar(
            self.autenticar, ["0000", "1111", "1234"]
        )

        self.assertTrue(sucesso)
        self.assertIn("Tentativas restantes: 2", resultado)
        self.assertIn("Tentativas restantes: 1", resultado)
        self.assertEqual(self.conta.tentativas_falhas, 0)

    def test_tres_erros_bloqueiam(self):
        sucesso, resultado = self.executar(
            self.autenticar, ["0000", "1111", "2222"]
        )

        self.assertFalse(sucesso)
        self.assertTrue(self.conta.bloqueada)
        self.assertIn("Conta bloqueada", resultado)
        self.assertEqual(self.salvar.call_count, 3)

    def test_conta_ja_bloqueada_nao_pede_pin(self):
        for _ in range(3):
            self.conta.autenticar("0000")

        sucesso, resultado = self.executar(self.autenticar, [])

        self.assertFalse(sucesso)
        self.assertIn("Conta bloqueada", resultado)

    def test_cadastrar_pin(self):
        _, resultado = self.executar(
            lambda: menu.cadastrar_pin(self.conta),
            ["12", "5678", "5679", "5678", "5678"]
        )

        self.assertIn("O PIN deve ter de 4 a 6 dígitos", resultado)
        self.assertIn("Os PINs não conferem", resultado)
        self.assertTrue(self.conta.autenticar("5678"))

class TestContas(unittest.TestCase):
    def setUp(self):
        patcher = patch(
            "caixa_eletronico.interface.menu.persistencia.salvar_banco"
        )
        self.salvar = patcher.start()
        self.addCleanup(patcher.stop)

        self.conta = ContaBancaria("Ana", saldo=100, numero="1001")
        self.conta.definir_pin("1234")
        self.destino = ContaBancaria("Bruno", numero="1002")
        self.banco = Banco([self.conta, self.destino])

    def executar(self, funcao, entradas=(), pins=()):
        saida = StringIO()

        with patch("builtins.input", side_effect=entradas), \
                patch("caixa_eletronico.interface.menu.ler_pin", side_effect=pins):
            with redirect_stdout(saida):
                resultado = funcao(self.banco)

        return resultado, saida.getvalue()

    def test_abrir_conta(self):
        conta, resultado = self.executar(
            menu.abrir_conta, entradas=["", "  Carla  "], pins=["4321", "4321"]
        )

        self.assertEqual(conta.numero, "1003")
        self.assertEqual(conta.titular, "Carla")
        self.assertIs(self.banco.buscar("1003"), conta)
        self.assertTrue(conta.autenticar("4321"))
        self.assertIn("Informe o nome do titular.", resultado)
        self.assertIn("O número da sua conta é 1003", resultado)
        self.salvar.assert_called_once()

    def test_acessar_conta_com_pin(self):
        conta, _ = self.executar(
            menu.acessar_conta, entradas=[" 1001 "], pins=["1234"]
        )

        self.assertIs(conta, self.conta)

    def test_conta_com_pin_sem_titular_pede_o_nome(self):
        self.conta.titular = ""

        conta, resultado = self.executar(
            menu.acessar_conta, entradas=["1001", "Ana Maria"], pins=["1234"]
        )

        self.assertIs(conta, self.conta)
        self.assertEqual(conta.titular, "Ana Maria")
        self.assertIn("ainda não tem o nome do titular", resultado)
        self.salvar.assert_called()

    def test_acessar_conta_inexistente(self):
        conta, resultado = self.executar(menu.acessar_conta, entradas=["9999"])

        self.assertIsNone(conta)
        self.assertIn("Conta 9999 não encontrada.", resultado)

    def test_acessar_conta_com_pin_errado(self):
        conta, resultado = self.executar(
            menu.acessar_conta,
            entradas=["1001"],
            pins=["0000", "1111", "2222"]
        )

        self.assertIsNone(conta)
        self.assertIn("Conta bloqueada", resultado)

    def test_conta_antiga_sem_pin_cadastra_pin_e_titular(self):
        antiga = ContaBancaria(numero="1003")
        self.banco = Banco([antiga])

        conta, resultado = self.executar(
            menu.acessar_conta,
            entradas=["1003", "Gabriel"],
            pins=["2468", "2468"]
        )

        self.assertIs(conta, antiga)
        self.assertEqual(conta.titular, "Gabriel")
        self.assertTrue(conta.autenticar("2468"))
        self.assertIn("ainda não tem PIN", resultado)

    def transferir(self, entradas):
        return self.executar(
            lambda banco: menu.realizar_transferencia(banco, self.conta),
            entradas=entradas
        )

    def test_transferencia_confirmada(self):
        sucesso, resultado = self.transferir(["1002", "40,50", "s"])

        self.assertTrue(sucesso)
        self.assertIn("para a conta 1002 (Bruno)?", resultado)
        self.assertEqual(self.conta.saldo, Decimal("59.50"))
        self.assertEqual(self.destino.saldo, Decimal("40.50"))

    def test_transferencia_cancelada(self):
        sucesso, resultado = self.transferir(["1002", "40", "n"])

        self.assertFalse(sucesso)
        self.assertIn("Transferência cancelada.", resultado)
        self.assertEqual(self.conta.saldo, Decimal("100.00"))
        self.assertEqual(self.destino.transacoes, ())

    def test_transferencia_para_conta_inexistente(self):
        sucesso, resultado = self.transferir(["9999"])

        self.assertFalse(sucesso)
        self.assertIn("não encontrada", resultado)

    def test_transferencia_para_a_propria_conta(self):
        sucesso, resultado = self.transferir(["1001"])

        self.assertFalse(sucesso)
        self.assertIn("própria conta", resultado)

    def test_transferencia_com_saldo_insuficiente(self):
        sucesso, resultado = self.transferir(["1002", "500", "s"])

        self.assertFalse(sucesso)
        self.assertIn("Saldo insuficiente!", resultado)
        self.assertEqual(self.destino.saldo, Decimal("0.00"))

    def test_transferencia_com_valor_invalido(self):
        sucesso, resultado = self.transferir(["1002", "abc"])

        self.assertFalse(sucesso)
        self.assertIn("Entrada inválida", resultado)

class TestObterData(unittest.TestCase):
    def obter(self, entradas):
        saida = StringIO()

        with patch("builtins.input", side_effect=entradas):
            with redirect_stdout(saida):
                return menu.obter_data("Data: "), saida.getvalue()

    def test_data_valida(self):
        data, _ = self.obter(["25/10/2026"])

        self.assertEqual(data, date(2026, 10, 25))

    def test_em_branco_nao_limita(self):
        data, _ = self.obter(["  "])

        self.assertIsNone(data)

    def test_pede_de_novo_se_invalida(self):
        data, resultado = self.obter(["2026-10-25", "31/02/2026", "01/10/2026"])

        self.assertEqual(data, date(2026, 10, 1))
        self.assertEqual(resultado.count("Data inválida!"), 2)

class TestEmitirExtrato(unittest.TestCase):
    def setUp(self):
        self.conta = ContaBancaria()

        for dia, valor in ((1, 100), (15, 50), (31, 30)):
            with patch(
                "caixa_eletronico.nucleo.conta_bancaria.agora",
                return_value=datetime(2026, 10, dia, 10, 0)
            ):
                self.conta.depositar(valor)

        patcher = patch(
            "caixa_eletronico.interface.menu.exportacao.exportar_csv",
            return_value=Path("extratos/extrato.csv")
        )
        self.exportar = patcher.start()
        self.addCleanup(patcher.stop)

    def emitir(self, entradas):
        saida = StringIO()

        with patch("builtins.input", side_effect=entradas):
            with redirect_stdout(saida):
                menu.emitir_extrato(self.conta)

        return saida.getvalue()

    def test_extrato_do_periodo_sem_exportar(self):
        resultado = self.emitir(["10/10/2026", "31/10/2026", "n"])

        self.assertIn("=== EXTRATO ===", resultado)
        self.assertNotIn("Data: 01/10/2026", resultado)
        self.assertIn("Data: 15/10/2026", resultado)
        self.assertIn("Total depositado no período: R$ 80,00", resultado)
        self.exportar.assert_not_called()

    def test_exporta_as_transacoes_filtradas(self):
        resultado = self.emitir(["", "15/10/2026", "s"])

        transacoes = self.exportar.call_args.args[0]

        self.assertEqual(len(transacoes), 2)
        self.assertIn("Extrato salvo em:", resultado)

    def test_periodo_sem_transacoes(self):
        resultado = self.emitir(["01/11/2026", "30/11/2026"])

        self.assertIn("Nenhuma transação no período", resultado)

    def test_periodo_invertido(self):
        resultado = self.emitir(["31/10/2026", "01/10/2026"])

        self.assertIn("A data inicial deve ser anterior", resultado)

    def test_erro_ao_exportar(self):
        self.exportar.side_effect = PermissionError("arquivo aberto no Excel")

        resultado = self.emitir(["", "", "s"])

        self.assertIn("Erro ao exportar o extrato", resultado)

class TestLerPin(unittest.TestCase):
    def ler(self, plataforma, ambiente):
        with patch("caixa_eletronico.interface.menu.sys.platform", plataforma), \
                patch.dict("os.environ", ambiente, clear=True), \
                patch("caixa_eletronico.interface.menu.getpass", return_value="1111"), \
                patch("builtins.input", return_value=" 2222 "):
            return menu.ler_pin("PIN: ")

    def test_terminal_comum_esconde_o_pin(self):
        self.assertEqual(self.ler("win32", {}), "1111")

    def test_vscode_no_windows_usa_input(self):
        self.assertEqual(self.ler("win32", {"TERM_PROGRAM": "vscode"}), "2222")

    def test_vscode_fora_do_windows_esconde_o_pin(self):
        self.assertEqual(self.ler("linux", {"TERM_PROGRAM": "vscode"}), "1111")

class TestFormatarMoeda(unittest.TestCase):
    def test_formato_brasileiro(self):
        self.assertEqual(formatar_moeda(Decimal("1234567.8")), "R$ 1.234.567,80")

    def test_valor_pequeno(self):
        self.assertEqual(formatar_moeda(Decimal("0.5")), "R$ 0,50")

if __name__ == "__main__":
    unittest.main()
